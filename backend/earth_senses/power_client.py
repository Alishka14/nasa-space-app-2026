"""NASA POWER monthly point data: retrieval, verbatim storage, provenance.

Raw responses are stored byte-for-byte under ``data/raw/power`` and are never
edited. Each has a Data Provenance Record under ``data/provenance``. Cached
files are re-verified against their recorded SHA-256 and against the place and
period they claim to describe every time they are used, so a cache entry can
never silently stand in for a different region.

This module never fabricates data: if neither the cache nor the network can
supply a request, it raises ``DataUnavailable``.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .normalize import NormalizedPower, PowerFormatError, check_annual_consistency, parse_power_monthly

POWER_BASE = "https://power.larc.nasa.gov/api/temporal/monthly/point"
POWER_FIRST_YEAR = 1981
COMMUNITY = "AG"

SOURCE_DESCRIPTION = (
    "NASA POWER (Prediction Of Worldwide Energy Resources) Monthly & Annual API, "
    "NASA Langley Research Center; meteorological parameters from MERRA-2 (NASA GMAO)")
SPATIAL_RESOLUTION = (
    "MERRA-2 native grid, 0.5 deg latitude x 0.625 deg longitude; a point query returns the "
    "enclosing grid cell, at the grid cell's mean elevation (per POWER documentation)")
DATA_KIND = "model reanalysis (assimilates satellite and conventional observations); not a direct measurement"


MISSING_CHECK = "no missing monthly values in any variable of the file"


class DataUnavailable(RuntimeError):
    """Neither the verified cache nor the network could provide the data."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_data_hash(obj: dict) -> str:
    """SHA-256 of the scientific content only.

    The raw body contains a ``times`` block with server timings that differ on
    every request, so two downloads of identical data have different raw
    hashes. This hash covers values, units, geometry, fill value and period.
    """
    header = obj.get("header") or {}
    core = {
        "geometry": obj.get("geometry"),
        "parameter": obj["properties"]["parameter"],
        "parameters": obj.get("parameters"),
        "fill_value": header.get("fill_value"),
        "start": header.get("start"), "end": header.get("end"),
        "sources": header.get("sources"), "api": header.get("api"),
    }
    return sha256_bytes(json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def request_url(lat: float, lon: float, start: int, end: int, parameters: list[str],
                community: str = COMMUNITY) -> str:
    return (f"{POWER_BASE}?parameters={','.join(parameters)}&community={community}"
            f"&longitude={lon}&latitude={lat}&start={start}&end={end}&format=JSON")


def cache_stem(lat: float, lon: float, start: int, end: int, parameters: list[str],
               community: str = COMMUNITY) -> str:
    return (f"power_monthly_point_lat{lat}_lon{lon}_{start}-{end}_"
            f"{'-'.join(sorted(parameters))}_{community}")


def validate_request(lat: float, lon: float, start: int, end: int, parameters: list[str]) -> None:
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise ValueError(f"coordinates out of range: lat={lat}, lon={lon}")
    last_complete = datetime.now(timezone.utc).year - 1
    if start < POWER_FIRST_YEAR:
        raise ValueError(f"POWER monthly data begin in {POWER_FIRST_YEAR}; requested start {start}")
    if end > last_complete:
        raise ValueError(f"last complete year is {last_complete}; requested end {end}")
    if end - start + 1 < 10:
        raise ValueError("at least 10 years are required for a monthly climatology and a trend test")
    if not parameters or len(parameters) > 20:
        raise ValueError("between 1 and 20 parameters are required")
    for p in parameters:
        if not p.replace("_", "").isalnum():
            raise ValueError(f"invalid parameter name: {p!r}")


def build_provenance(raw: bytes, *, url: str, retrieved_at: str, method: str, norm: NormalizedPower,
                     raw_path: str, lat: float, lon: float, start: int, end: int,
                     parameters: list[str], community: str = COMMUNITY) -> dict[str, Any]:
    obj = json.loads(raw)
    consistency = check_annual_consistency(norm)
    worst = max((v["max_abs_diff_day_weighted"] for v in consistency.values()), default=0.0)
    checks = [
        {"check": "calendar complete and identical for all variables", "passed": True},
        {"check": "YYYY13 annual summaries separated from the 12 calendar months", "passed": True,
         "detail": f"{len(norm.annual_reported)} annual keys per variable"},
        {"check": "fill value converted to NaN", "passed": True,
         "detail": {"fill_value": norm.fill_value, "missing_counts": norm.missing}},
        {"check": "units present in response metadata", "passed": True, "detail": norm.units},
        {"check": "response geometry matches the request", "passed": True},
        {"check": "our day-weighted annual means agree with the API's own annual values",
         "passed": bool(worst <= 0.011), "detail": consistency},
    ]
    n_missing = int(sum(norm.missing.values()))
    structural_ok = all(c["passed"] for c in checks)
    checks.append({"check": MISSING_CHECK, "passed": n_missing == 0, "detail": norm.missing})
    if not structural_ok:
        status = "FAILED"
    elif n_missing:
        status = "VALIDATED_WITH_MISSING_DATA"     # stored as evidence; variables with gaps are not analysed
    else:
        status = "VALIDATED"
    return {
        "record_type": "DataProvenanceRecord",
        "original_source": SOURCE_DESCRIPTION,
        "original_api_request": url,
        "retrieval_timestamp": retrieved_at,
        "retrieval_method": method,
        "request": {"latitude": lat, "longitude": lon, "start": start, "end": end,
                    "parameters": sorted(parameters), "community": community},
        "variables": {name: {"units": norm.units[name], "longname": norm.longnames[name], "kind": DATA_KIND}
                      for name in norm.monthly.columns},
        "spatial_resolution": SPATIAL_RESOLUTION,
        "grid_cell_elevation_m": norm.elevation_m,
        "temporal_resolution": "monthly means (keys YYYY01..YYYY12) plus the API's annual mean (YYYY13)",
        "coverage": {"start": f"{norm.start_year}-01", "end": f"{norm.end_year}-12",
                     "n_months": int(len(norm.monthly))},
        "missing_values": {"fill_value": norm.fill_value, "counts": norm.missing},
        "source_product_version": {"api": (obj.get("header") or {}).get("api"),
                                   "sources": (obj.get("header") or {}).get("sources"),
                                   "time_standard": (obj.get("header") or {}).get("time_standard")},
        "sha256": sha256_bytes(raw), "bytes": len(raw),
        "sha256_canonical_data": canonical_data_hash(obj),
        "raw_path": raw_path,
        "validation_status": status,
        "validation_checks": checks,
        "warnings": norm.warnings,
    }


@dataclass
class PowerDataset:
    norm: NormalizedPower
    monthly: pd.DataFrame                 # sliced to the requested period and variables
    provenance: list[dict[str, Any]]      # one record per raw file used
    source: str                           # "cache" | "live"
    request: dict[str, Any]
    notes: list[str] = field(default_factory=list)
    annual_reported: pd.DataFrame | None = None   # the API's own YYYY13 values for the period
    extra: dict[str, Any] = field(default_factory=dict)   # merged metadata when variables come from several files

    @property
    def units(self) -> dict[str, str]:
        return self.extra.get("units") or self.norm.units

    @property
    def longnames(self) -> dict[str, str]:
        return self.extra.get("longnames") or self.norm.longnames

    @property
    def warnings(self) -> list[str]:
        """Parser warnings that concern the requested variables (a file may hold others)."""
        requested = set(self.request["parameters"])
        others = {c for p in self.provenance for c in p["request"]["parameters"]} - requested
        base = self.extra.get("warnings", self.norm.warnings)
        return [w for w in base if not any(w.startswith(f"{o}:") for o in others)]

    @property
    def data_hash(self) -> str:
        """Identifies exactly which bytes and which slice produced a result."""
        core = {"raw_sha256": sorted(p["sha256"] for p in self.provenance),
                "period": [self.request["start"], self.request["end"]],
                "parameters": sorted(self.request["parameters"]),
                "point": [self.request["latitude"], self.request["longitude"]]}
        return sha256_bytes(json.dumps(core, sort_keys=True).encode("utf-8"))


class PowerStore:
    """Verified cache plus optional live retrieval."""

    def __init__(self, data_dir: str | Path, *, allow_network: bool = True, timeout: float = 60.0):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw" / "power"
        self.prov_dir = self.data_dir / "provenance"
        self.allow_network = allow_network
        self.timeout = timeout

    # -- cache ---------------------------------------------------------------
    def _records(self) -> list[dict[str, Any]]:
        if not self.prov_dir.exists():
            return []
        out = []
        for path in sorted(self.prov_dir.glob("*.provenance.json")):
            rec = json.loads(path.read_text(encoding="utf-8"))
            if rec.get("record_type") == "DataProvenanceRecord":
                out.append(rec)
        return out

    def _load_verified(self, rec: dict[str, Any]) -> NormalizedPower:
        """Re-read a cached raw file and prove it is what its record says."""
        raw_path = self.data_dir / rec["raw_path"]
        if not raw_path.exists():
            raise DataUnavailable(f"provenance record points to a missing file: {rec['raw_path']}")
        raw = raw_path.read_bytes()
        if sha256_bytes(raw) != rec["sha256"]:
            raise PowerFormatError(f"cache corruption: SHA-256 of {rec['raw_path']} differs from its record")
        req = rec["request"]
        return parse_power_monthly(raw, expect_lat=req["latitude"], expect_lon=req["longitude"],
                                   expect_start=req["start"], expect_end=req["end"],
                                   expect_parameters=req["parameters"])

    def _from_cache(self, lat: float, lon: float, start: int, end: int, parameters: list[str],
                    community: str) -> PowerDataset | None:
        cands = [r for r in self._records()
                 if abs(r["request"]["latitude"] - lat) < 1e-9 and abs(r["request"]["longitude"] - lon) < 1e-9
                 and r["request"]["community"] == community
                 and set(parameters) <= set(r["request"]["parameters"])
                 and r["request"]["end"] >= start and r["request"]["start"] <= end]
        if not cands:
            return None
        cands.sort(key=lambda r: (r["request"]["start"], -r["request"]["end"]))
        used, cursor = [], start
        for rec in cands:                         # greedy tiling of the requested years
            if rec["request"]["start"] <= cursor <= rec["request"]["end"]:
                used.append(rec)
                cursor = rec["request"]["end"] + 1
            if cursor > end:
                break
        if cursor <= end:
            return None
        norms = [self._load_verified(rec) for rec in used]
        frames = []
        cursor = start
        for rec, norm in zip(used, norms):
            hi = min(rec["request"]["end"], end)
            part = norm.monthly[(norm.monthly.index.year >= cursor) & (norm.monthly.index.year <= hi)]
            frames.append(part[parameters])
            cursor = hi + 1
        monthly = pd.concat(frames)
        if len(monthly) != (end - start + 1) * 12 or not monthly.index.is_monotonic_increasing \
                or monthly.index.has_duplicates:
            raise PowerFormatError("cached files do not tile the requested period cleanly")
        for a, b in zip(norms, norms[1:]):
            if a.units != b.units:
                raise PowerFormatError("cached files disagree on units")
        notes = []
        if len(used) > 1:
            notes.append(f"period assembled from {len(used)} verified raw files")
        if (used[0]["request"]["start"], used[-1]["request"]["end"]) != (start, end):
            notes.append("requested period is a slice of the cached retrieval")
        annual = pd.concat([n.annual_reported for n in norms])
        annual = annual[~annual.index.duplicated(keep="first")].sort_index()
        annual = annual[(annual.index >= start) & (annual.index <= end)][parameters]
        return PowerDataset(norm=norms[0], monthly=monthly, provenance=used, source="cache",
                            request={"latitude": lat, "longitude": lon, "start": start, "end": end,
                                     "parameters": list(parameters), "community": community},
                            notes=notes, annual_reported=annual)

    def _from_cache_by_parameter(self, lat: float, lon: float, start: int, end: int, parameters: list[str],
                                 community: str) -> PowerDataset | None:
        """Fallback when no single retrieval holds every requested variable:
        resolve each variable from its own verified file(s) and join them on
        the calendar. Every file is still re-verified by ``_from_cache``."""
        parts = []
        for name in parameters:
            part = self._from_cache(lat, lon, start, end, [name], community)
            if part is None:
                return None
            parts.append(part)
        monthly = pd.concat([p.monthly for p in parts], axis=1)
        if any(not p.monthly.index.equals(parts[0].monthly.index) for p in parts):
            raise PowerFormatError("cached files for different variables are not on the same calendar")
        provenance, seen = [], set()
        for p in parts:
            for rec in p.provenance:
                if rec["sha256"] not in seen:
                    seen.add(rec["sha256"])
                    provenance.append(rec)
        annual = None
        if all(p.annual_reported is not None for p in parts):
            annual = pd.concat([p.annual_reported for p in parts], axis=1)
        notes = [n for p in parts for n in p.notes]
        notes.append(f"variables assembled from {len(provenance)} verified raw files")
        extra = {"units": {n: p.units[n] for n, p in zip(parameters, parts)},
                 "longnames": {n: p.longnames[n] for n, p in zip(parameters, parts)},
                 "warnings": [w for p in parts for w in p.norm.warnings]}
        return PowerDataset(norm=parts[0].norm, monthly=monthly[parameters], provenance=provenance, source="cache",
                            request={"latitude": lat, "longitude": lon, "start": start, "end": end,
                                     "parameters": list(parameters), "community": community},
                            notes=list(dict.fromkeys(notes)), annual_reported=annual, extra=extra)

    # -- live ----------------------------------------------------------------
    def _fetch_live(self, lat: float, lon: float, start: int, end: int, parameters: list[str],
                    community: str) -> PowerDataset:
        import httpx

        url = request_url(lat, lon, start, end, parameters, community)
        try:
            resp = httpx.get(url, timeout=self.timeout, follow_redirects=True)
        except httpx.HTTPError as exc:
            raise DataUnavailable(f"NASA POWER could not be reached: {exc}") from exc
        if resp.status_code != 200:
            raise DataUnavailable(f"NASA POWER returned HTTP {resp.status_code}: {resp.text[:300]}")
        raw = resp.content
        # Validate BEFORE caching: an HTTP 200 with a partial body must not be stored.
        norm = parse_power_monthly(raw, expect_lat=lat, expect_lon=lon, expect_start=start,
                                   expect_end=end, expect_parameters=parameters)
        return self.register_raw(raw, lat=lat, lon=lon, start=start, end=end, parameters=parameters,
                                 community=community, url=url,
                                 retrieved_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                 method="direct HTTPS GET by the EARTH SENSES backend (httpx)",
                                 norm=norm, source="live")

    def register_raw(self, raw: bytes, *, lat: float, lon: float, start: int, end: int,
                     parameters: list[str], community: str = COMMUNITY, url: str, retrieved_at: str,
                     method: str, norm: NormalizedPower | None = None, source: str = "cache") -> PowerDataset:
        """Store a raw response verbatim with its provenance record."""
        norm = norm or parse_power_monthly(raw, expect_lat=lat, expect_lon=lon, expect_start=start,
                                           expect_end=end, expect_parameters=parameters)
        stem = cache_stem(lat, lon, start, end, parameters, community)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.prov_dir.mkdir(parents=True, exist_ok=True)
        raw_path = self.raw_dir / f"{stem}.json"
        if raw_path.exists():
            if raw_path.read_bytes() != raw:
                # never overwrite stored evidence; keep the new retrieval beside it
                raw_path = self.raw_dir / f"{stem}__{sha256_bytes(raw)[:12]}.json"
                raw_path.write_bytes(raw)
        else:
            raw_path.write_bytes(raw)
        rel = raw_path.relative_to(self.data_dir).as_posix()
        rec = build_provenance(raw, url=url, retrieved_at=retrieved_at, method=method, norm=norm,
                               raw_path=rel, lat=lat, lon=lon, start=start, end=end,
                               parameters=parameters, community=community)
        (self.prov_dir / f"{raw_path.stem}.provenance.json").write_text(
            json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return PowerDataset(norm=norm, monthly=norm.monthly[parameters], provenance=[rec], source=source,
                            request={"latitude": lat, "longitude": lon, "start": start, "end": end,
                                     "parameters": list(parameters), "community": community},
                            annual_reported=norm.annual_reported[parameters])

    # -- public ----------------------------------------------------------------
    def load(self, lat: float, lon: float, start: int, end: int, parameters: list[str], *,
             community: str = COMMUNITY, refresh: bool = False) -> PowerDataset:
        validate_request(lat, lon, start, end, parameters)
        if not refresh:
            cached = self._from_cache(lat, lon, start, end, parameters, community)
            if cached is None and len(parameters) > 1:
                cached = self._from_cache_by_parameter(lat, lon, start, end, parameters, community)
            if cached is not None:
                return cached
        if not self.allow_network:
            raise DataUnavailable(
                "this request is not in the verified cache and network access is disabled; "
                "no data will be invented")
        return self._fetch_live(lat, lon, start, end, parameters, community)
