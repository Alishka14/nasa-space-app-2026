"""Parse a raw NASA POWER monthly response into validated, unit-tagged series.

Every rule here exists because a silent error is possible without it
(see docs/SCIENCE_METHOD.md, "Data traps"):

* keys ``YYYY13`` are the API's annual summary, not a thirteenth month;
* the fill value from the response header marks missing data and must become NaN;
* units are read from the response metadata and are never assumed;
* all variables must share one complete calendar;
* the response must describe the place and period that was asked for.
"""
from __future__ import annotations

import calendar
import json
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


class PowerFormatError(ValueError):
    """The response is empty, partial, inconsistent, or not what was requested."""


@dataclass
class NormalizedPower:
    monthly: pd.DataFrame            # PeriodIndex[M] x parameter, NaN = missing
    annual_reported: pd.DataFrame    # year x parameter: the API's own YYYY13 values
    units: dict[str, str]
    longnames: dict[str, str]
    fill_value: float
    missing: dict[str, int]
    longitude: float
    latitude: float
    elevation_m: float | None
    header: dict[str, Any]
    warnings: list[str] = field(default_factory=list)

    @property
    def start_year(self) -> int:
        return int(self.monthly.index[0].year)

    @property
    def end_year(self) -> int:
        return int(self.monthly.index[-1].year)


def _load(raw: bytes | str | dict) -> dict:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    if not raw or not raw.strip():
        raise PowerFormatError("empty response body")
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PowerFormatError(f"response is not valid JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise PowerFormatError("response JSON is not an object")
    return obj


def parse_power_monthly(
    raw: bytes | str | dict,
    *,
    expect_lat: float | None = None,
    expect_lon: float | None = None,
    expect_start: int | None = None,
    expect_end: int | None = None,
    expect_parameters: list[str] | None = None,
    coord_tol: float = 1e-6,
) -> NormalizedPower:
    obj = _load(raw)
    warnings: list[str] = []

    try:
        params = obj["properties"]["parameter"]
    except (KeyError, TypeError) as exc:
        raise PowerFormatError("response has no properties.parameter block") from exc
    if not isinstance(params, dict) or not params:
        raise PowerFormatError("response contains no parameters")

    if expect_parameters is not None:
        absent = sorted(set(expect_parameters) - set(params))
        if absent:
            raise PowerFormatError(f"partial response: requested parameters missing: {absent}")

    header = obj.get("header") or {}
    if "fill_value" not in header:
        raise PowerFormatError("header.fill_value absent: cannot identify missing data safely")
    fill_value = float(header["fill_value"])

    meta = obj.get("parameters") or {}
    units: dict[str, str] = {}
    longnames: dict[str, str] = {}
    for name in params:
        info = meta.get(name) or {}
        if not info.get("units"):
            raise PowerFormatError(f"no units in response metadata for {name}: refusing to assume")
        units[name] = str(info["units"])
        longnames[name] = str(info.get("longname", name))

    # --- geometry: is this the place that was asked for? -------------------
    try:
        coords = obj["geometry"]["coordinates"]
        lon, lat = float(coords[0]), float(coords[1])
        elev = float(coords[2]) if len(coords) > 2 else None
    except (KeyError, TypeError, IndexError, ValueError) as exc:
        raise PowerFormatError("response has no usable geometry.coordinates") from exc
    if expect_lat is not None and abs(lat - expect_lat) > coord_tol:
        raise PowerFormatError(f"region mismatch: response latitude {lat} != requested {expect_lat}")
    if expect_lon is not None and abs(lon - expect_lon) > coord_tol:
        raise PowerFormatError(f"region mismatch: response longitude {lon} != requested {expect_lon}")

    # --- calendar: split months from the annual summary ---------------------
    key_sets = {name: set(series) for name, series in params.items()}
    first = next(iter(key_sets.values()))
    for name, keys in key_sets.items():
        if keys != first:
            diff = sorted(keys ^ first)[:6]
            raise PowerFormatError(f"calendar mismatch between variables ({name}): e.g. {diff}")

    monthly_keys: list[tuple[int, int, str]] = []
    annual_keys: list[tuple[int, str]] = []
    for key in sorted(first):
        if len(key) != 6 or not key.isdigit():
            raise PowerFormatError(f"unexpected time key {key!r} (want YYYYMM)")
        year, mm = int(key[:4]), int(key[4:])
        if 1 <= mm <= 12:
            monthly_keys.append((year, mm, key))
        elif mm == 13:
            annual_keys.append((year, key))      # annual summary, never a month
        else:
            raise PowerFormatError(f"unexpected month code in key {key!r}")
    if not monthly_keys:
        raise PowerFormatError("response has no monthly values")

    years = sorted({y for y, _, _ in monthly_keys})
    present = {(y, m) for y, m, _ in monthly_keys}
    gaps = [(y, m) for y in range(years[0], years[-1] + 1) for m in range(1, 13) if (y, m) not in present]
    if gaps:
        raise PowerFormatError(f"partial response: {len(gaps)} calendar months absent, e.g. {gaps[:6]}")
    if expect_start is not None and years[0] != expect_start:
        raise PowerFormatError(f"period mismatch: data start {years[0]} != requested {expect_start}")
    if expect_end is not None and years[-1] != expect_end:
        raise PowerFormatError(f"period mismatch: data end {years[-1]} != requested {expect_end}")

    index = pd.PeriodIndex([pd.Period(year=y, month=m, freq="M") for y, m, _ in monthly_keys], name="month")
    data: dict[str, list[float]] = {}
    annual: dict[str, list[float]] = {}
    missing: dict[str, int] = {}
    for name, series in params.items():
        vals = np.array([float(series[k]) for _, _, k in monthly_keys], dtype=float)
        is_fill = np.isclose(vals, fill_value, rtol=0.0, atol=1e-9)
        suspicious = (~is_fill) & (vals <= -900)
        if suspicious.any():
            warnings.append(f"{name}: {int(suspicious.sum())} values <= -900 that are not the declared fill value")
        vals[is_fill] = np.nan
        missing[name] = int(is_fill.sum())
        data[name] = vals.tolist()
        ann = np.array([float(series[k]) for _, k in annual_keys], dtype=float)
        ann[np.isclose(ann, fill_value, rtol=0.0, atol=1e-9)] = np.nan
        annual[name] = ann.tolist()

    monthly = pd.DataFrame(data, index=index)
    annual_reported = pd.DataFrame(annual, index=pd.Index([y for y, _ in annual_keys], name="year"))

    for msg in obj.get("messages") or []:
        warnings.append(f"API message: {msg}")
    for name, n in missing.items():
        if n:
            warnings.append(f"{name}: {n} missing monthly values (fill {fill_value}) converted to NaN")

    return NormalizedPower(
        monthly=monthly, annual_reported=annual_reported, units=units, longnames=longnames,
        fill_value=fill_value, missing=missing, longitude=lon, latitude=lat, elevation_m=elev,
        header=header, warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Units and aggregation
# ---------------------------------------------------------------------------

def days_in_month(index: pd.PeriodIndex) -> pd.Series:
    """Calendar days per month, leap years included."""
    return pd.Series([calendar.monthrange(p.year, p.month)[1] for p in index], index=index, dtype=float)


def rate_to_monthly_total(rate_mm_per_day: pd.Series, units: str) -> pd.Series:
    """mm/day (monthly mean rate) -> mm per month. Refuses any other unit."""
    if units.strip().lower() != "mm/day":
        raise ValueError(f"expected a rate in mm/day, got {units!r}: refusing to convert")
    return rate_mm_per_day * days_in_month(rate_mm_per_day.index)


def annual_mean(series: pd.Series, *, day_weighted: bool = True, min_months: int = 12) -> pd.Series:
    """Annual mean of a monthly series. Years with fewer than ``min_months`` values are NaN."""
    years = series.index.year
    if day_weighted:
        w = days_in_month(series.index).where(series.notna())
        num = (series * w).groupby(years).sum(min_count=1)
        den = w.groupby(years).sum(min_count=1)
        out = num / den
    else:
        out = series.groupby(years).mean()
    count = series.groupby(years).count()
    out[count < min_months] = np.nan
    out.index.name = "year"
    return out


def annual_total(monthly_total: pd.Series, *, min_months: int = 12) -> pd.Series:
    """Annual accumulation of monthly totals (e.g. precipitation in mm)."""
    years = monthly_total.index.year
    out = monthly_total.groupby(years).sum(min_count=1)
    out[monthly_total.groupby(years).count() < min_months] = np.nan
    out.index.name = "year"
    return out


SEASONS = {"DJF": (12, 1, 2), "MAM": (3, 4, 5), "JJA": (6, 7, 8), "SON": (9, 10, 11)}


def seasonal_mean(series: pd.Series, season: str) -> pd.Series:
    """Seasonal means indexed by the year of the season's last month.

    DJF of year Y uses December of Y-1, so the first year is dropped when its
    December is unavailable (never silently borrowed from the same year).
    """
    months = SEASONS[season]
    sel = series[series.index.month.isin(months)]
    season_year = sel.index.year + (sel.index.month == 12).astype(int) if season == "DJF" else sel.index.year
    w = days_in_month(sel.index).where(sel.notna())
    num = (sel * w).groupby(season_year).sum(min_count=1)
    den = w.groupby(season_year).sum(min_count=1)
    out = num / den
    out[sel.groupby(season_year).count() < 3] = np.nan
    out = out.dropna()
    out.index.name = "year"
    return out


def check_annual_consistency(norm: NormalizedPower) -> dict[str, dict[str, float]]:
    """Compare our annual means with the API's own YYYY13 values.

    A large gap means months and the annual summary were mixed up somewhere.
    """
    report: dict[str, dict[str, float]] = {}
    for name in norm.monthly.columns:
        if name not in norm.annual_reported:
            continue
        rep = norm.annual_reported[name]
        if norm.monthly[name].isna().all() or rep.isna().all():
            continue                                  # nothing to compare: the variable carries no data
        weighted = annual_mean(norm.monthly[name], day_weighted=True).reindex(rep.index)
        simple = annual_mean(norm.monthly[name], day_weighted=False).reindex(rep.index)
        report[name] = {
            "max_abs_diff_day_weighted": float(np.nanmax(np.abs(weighted - rep))),
            "max_abs_diff_simple_mean": float(np.nanmax(np.abs(simple - rep))),
        }
    return report
