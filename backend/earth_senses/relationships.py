"""Relationship Engine: anomalies, detrending, correlations with
autocorrelation-aware inference, lag analysis, stability checks and negative
controls.

Three views of every pair are kept strictly apart:

* ``raw``            - the series as delivered (dominated by the seasonal cycle);
* ``deseasonalized`` - monthly anomalies from a stated climatological baseline;
* ``detrended``      - those anomalies with a linear trend removed.

Association is not causation, and a lag does not establish the direction of a
physical influence. This module reports statistics; it never names a cause.
"""
from __future__ import annotations

import math
from typing import Any, Sequence

import numpy as np
import pandas as pd
from scipy import stats

from .normalize import SEASONS
from .trends import acf, benjamini_hochberg

# ---------------------------------------------------------------------------
# Baseline, anomalies, detrending
# ---------------------------------------------------------------------------

def monthly_climatology(series: pd.Series, baseline: tuple[int, int] | None = None,
                        min_years: int = 10) -> pd.Series:
    """Mean of each calendar month over the baseline years (inclusive)."""
    s = series
    if baseline is not None:
        s = s[(s.index.year >= baseline[0]) & (s.index.year <= baseline[1])]
    counts = s.groupby(s.index.month).count()
    if len(counts) < 12 or (counts < min_years).any():
        raise ValueError(
            f"baseline {baseline} has fewer than {min_years} years for some calendar months "
            f"(counts: {counts.to_dict()})")
    clim = s.groupby(s.index.month).mean()
    clim.index.name = "calendar_month"
    return clim


def anomalies(series: pd.Series, climatology: pd.Series) -> pd.Series:
    """Value minus the climatological mean of its own calendar month."""
    return series - series.index.month.map(climatology).to_numpy()


def detrend_linear(series: pd.Series) -> pd.Series:
    """Remove a least-squares line (NaN-safe). Returns residuals."""
    y = series.to_numpy(dtype=float)
    t = np.arange(len(y), dtype=float)
    ok = ~np.isnan(y)
    if ok.sum() < 3:
        return series.copy()
    slope, intercept = np.polyfit(t[ok], y[ok], 1)
    return pd.Series(y - (slope * t + intercept), index=series.index, name=series.name)


def climatology_cycle(series: pd.Series, climatology: pd.Series) -> pd.Series:
    """The repeating seasonal cycle alone (used as an explanatory control)."""
    return pd.Series(series.index.month.map(climatology).to_numpy(dtype=float), index=series.index)


# ---------------------------------------------------------------------------
# Correlation with effective sample size
# ---------------------------------------------------------------------------

def _pair(x: Sequence[float], y: Sequence[float]) -> tuple[np.ndarray, np.ndarray]:
    a = np.asarray(x, dtype=float)
    b = np.asarray(y, dtype=float)
    if a.shape != b.shape:
        raise ValueError("series are not aligned: different lengths")
    ok = ~(np.isnan(a) | np.isnan(b))
    return a[ok], b[ok]


def effective_n(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """Bretherton et al. (1999): n_eff = n (1 - r1x r1y) / (1 + r1x r1y)."""
    n = len(x)
    r1x, r1y = float(acf(x, 1)[1]), float(acf(y, 1)[1])
    prod = r1x * r1y
    n_eff = n * (1 - prod) / (1 + prod) if prod > 0 else float(n)
    return float(min(n_eff, n)), r1x, r1y


def _p_from_r(r: float, n: float) -> float:
    dof = n - 2
    if dof <= 0 or abs(r) >= 1:
        return float("nan") if dof <= 0 else 0.0
    t = r * math.sqrt(dof / (1 - r * r))
    return float(2 * stats.t.sf(abs(t), dof))


def _fisher_ci(r: float, n: float, confidence: float = 0.95) -> tuple[float, float]:
    if n <= 3 or abs(r) >= 1:
        return float("nan"), float("nan")
    z = math.atanh(r)
    half = stats.norm.ppf(0.5 + confidence / 2) / math.sqrt(n - 3)
    return float(math.tanh(z - half)), float(math.tanh(z + half))


def correlate(x: Sequence[float], y: Sequence[float]) -> dict[str, Any]:
    """Pearson and Spearman with naive and autocorrelation-adjusted inference."""
    a, b = _pair(x, y)
    n = len(a)
    if n < 8 or np.ptp(a) == 0 or np.ptp(b) == 0:
        return {"n": n, "pearson_r": None, "note": "too few points or a constant series"}
    r = float(np.corrcoef(a, b)[0, 1])
    rho, p_rho = stats.spearmanr(a, b)
    n_eff, r1x, r1y = effective_n(a, b)
    lo, hi = _fisher_ci(r, n_eff)
    return {
        "n": n, "pearson_r": r, "p_naive": _p_from_r(r, n),
        "n_eff": n_eff, "p_adjusted": _p_from_r(r, n_eff), "ci95_adjusted": [lo, hi],
        "lag1_autocorr_x": r1x, "lag1_autocorr_y": r1y,
        "spearman_rho": float(rho), "spearman_p_naive": float(p_rho),
        "r_squared": r * r,
    }


# ---------------------------------------------------------------------------
# Lag analysis
# ---------------------------------------------------------------------------

def lagged_correlations(x: pd.Series, y: pd.Series, max_lag: int = 6) -> dict[str, Any]:
    """r(k) = corr(x[t], y[t+k]) for k = -max_lag..max_lag.

    k > 0 pairs x with LATER y ("x leads y by k months"); k < 0 pairs x with
    EARLIER y. A lead is a timing statistic, not evidence of direction of
    influence. q-values apply Benjamini-Hochberg across the whole lag family
    using the autocorrelation-adjusted p-values.
    """
    if not x.index.equals(y.index):
        raise ValueError("series are not aligned on the same calendar")
    xa, ya = x.to_numpy(dtype=float), y.to_numpy(dtype=float)
    n = len(xa)
    rows = []
    for k in range(-max_lag, max_lag + 1):
        if k >= 0:
            a, b = xa[: n - k], ya[k:]
        else:
            a, b = xa[-k:], ya[: n + k]
        c = correlate(a, b)
        rows.append({"lag": k, "n": c["n"], "r": c.get("pearson_r"), "p_naive": c.get("p_naive"),
                     "n_eff": c.get("n_eff"), "p_adjusted": c.get("p_adjusted")})
    qs = benjamini_hochberg([row["p_adjusted"] for row in rows])
    for row, q in zip(rows, qs):
        row["q"] = q
    valid = [row for row in rows if row["r"] is not None]
    peak = max(valid, key=lambda row: abs(row["r"])) if valid else None
    nonzero_sig = [row["lag"] for row in valid if row["lag"] != 0 and row["q"] is not None and row["q"] < 0.05]
    return {
        "definition": "r(k) = corr(x[t], y[t+k]); k>0: x paired with later y",
        "max_lag": max_lag, "n_tests": len(valid), "rows": rows,
        "peak_lag": peak["lag"] if peak else None, "peak_r": peak["r"] if peak else None,
        "significant_nonzero_lags": nonzero_sig,
    }


# ---------------------------------------------------------------------------
# Stability, seasons, negative controls
# ---------------------------------------------------------------------------

def subperiod_stability(x: pd.Series, y: pd.Series, window_years: int = 10) -> dict[str, Any]:
    """Correlation in each half of the record and in sliding windows."""
    years = sorted(set(x.index.year))
    mid = years[len(years) // 2]
    first = x.index.year < mid
    halves = []
    for label, mask in (("first_half", first), ("second_half", ~first)):
        c = correlate(x[mask], y[mask])
        yrs = x.index.year[mask]
        halves.append({"label": label, "start": int(yrs.min()), "end": int(yrs.max()),
                       "r": c.get("pearson_r"), "n": c["n"], "p_adjusted": c.get("p_adjusted")})
    rolling = []
    for start in range(years[0], years[-1] - window_years + 2):
        mask = (x.index.year >= start) & (x.index.year < start + window_years)
        c = correlate(x[mask], y[mask])
        if c.get("pearson_r") is not None:
            rolling.append({"start": start, "end": start + window_years - 1, "r": c["pearson_r"]})
    rs = [r["r"] for r in rolling]
    hr = [h["r"] for h in halves if h["r"] is not None]
    return {
        "halves": halves, "rolling_window_years": window_years, "rolling": rolling,
        "rolling_r_min": min(rs) if rs else None, "rolling_r_max": max(rs) if rs else None,
        "sign_consistent_halves": len(hr) == 2 and hr[0] * hr[1] > 0,
        "sign_consistent_rolling": bool(rs) and (min(rs) > 0 or max(rs) < 0),
    }


def _lag1_adjacent(values: np.ndarray, ordinals: np.ndarray) -> float:
    """Lag-1 autocorrelation from pairs that really are consecutive months.
    A season subset jumps from February to December; those neighbours in the
    array are ten months apart and must not be treated as lag 1."""
    adjacent = np.diff(ordinals) == 1
    if adjacent.sum() < 8:
        return 0.0
    a, b = values[:-1][adjacent], values[1:][adjacent]
    if np.ptp(a) == 0 or np.ptp(b) == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def seasonal_correlations(x: pd.Series, y: pd.Series) -> dict[str, Any]:
    """Anomaly correlation inside each meteorological season. A relationship
    whose sign differs between seasons is a counterexample to any single
    all-year statement."""
    out = {}
    for name, months in SEASONS.items():
        mask = x.index.month.isin(months)
        xs, ys = x[mask], y[mask]
        ok = ~(xs.isna() | ys.isna()).to_numpy()
        a, b = xs.to_numpy(dtype=float)[ok], ys.to_numpy(dtype=float)[ok]
        n = len(a)
        if n < 8 or np.ptp(a) == 0 or np.ptp(b) == 0:
            out[name] = {"r": None, "n": n, "n_eff": None, "p_naive": None, "p_adjusted": None}
            continue
        r = float(np.corrcoef(a, b)[0, 1])
        ordinals = (xs.index.year * 12 + xs.index.month).to_numpy()[ok]
        prod = _lag1_adjacent(a, ordinals) * _lag1_adjacent(b, ordinals)
        n_eff = n * (1 - prod) / (1 + prod) if prod > 0 else float(n)
        out[name] = {"r": r, "n": n, "n_eff": float(n_eff), "p_naive": _p_from_r(r, n),
                     "p_adjusted": _p_from_r(r, n_eff)}
    rs = [v["r"] for v in out.values() if v["r"] is not None]
    return {"seasons": out, "sign_differs_between_seasons": bool(rs) and min(rs) < 0 < max(rs)}


def year_block_permutation(x: pd.Series, y: pd.Series, n_perm: int = 2000, seed: int = 20261114) -> dict[str, Any]:
    """Negative control. Whole years of ``y`` are shuffled against ``x``:
    the within-year structure of both series survives, the year-to-year
    pairing does not. The observed r should sit in the tail of this null
    distribution if the association is more than an artefact of persistence
    and seasonality."""
    years = np.array(sorted(set(x.index.year)))
    xm = np.full((len(years), 12), np.nan)
    ym = np.full((len(years), 12), np.nan)
    for i, yr in enumerate(years):
        for series, mat in ((x, xm), (y, ym)):
            sel = series[series.index.year == yr]
            mat[i, sel.index.month - 1] = sel.to_numpy(dtype=float)

    def corr(a: np.ndarray, b: np.ndarray) -> float:
        fa, fb = a.ravel(), b.ravel()
        ok = ~(np.isnan(fa) | np.isnan(fb))
        return float(np.corrcoef(fa[ok], fb[ok])[0, 1])

    observed = corr(xm, ym)
    rng = np.random.default_rng(seed)
    null = np.empty(n_perm)
    for i in range(n_perm):
        null[i] = corr(xm, ym[rng.permutation(len(years))])
    p = float((1 + (np.abs(null) >= abs(observed)).sum()) / (n_perm + 1))
    return {"observed_r": observed, "n_perm": n_perm, "seed": seed, "p_permutation": p,
            "null_abs_r_p95": float(np.quantile(np.abs(null), 0.95)),
            "null_r_mean": float(null.mean()), "null_r_sd": float(null.std(ddof=1))}


# ---------------------------------------------------------------------------
# Pair analysis
# ---------------------------------------------------------------------------

DEFAULT_THRESHOLDS = {"alpha": 0.05, "min_abs_r": 0.2}


def classify(detr: dict, perm: dict, stability: dict, thresholds: dict | None = None) -> tuple[str, list[str]]:
    """Map the checks onto an edge status. Rules are fixed in advance and
    listed in docs/SCIENCE_METHOD.md; they are not tuned per dataset."""
    th = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    r = detr.get("pearson_r")
    if r is None:
        return "INCONCLUSIVE", ["correlation could not be computed"]
    reasons = []
    sig_adj = detr["p_adjusted"] < th["alpha"]
    sig_perm = perm["p_permutation"] < th["alpha"]
    strong = abs(r) >= th["min_abs_r"]
    stable = stability["sign_consistent_halves"]
    reasons.append(f"detrended anomaly r = {r:+.3f} (n_eff = {detr['n_eff']:.0f}, adjusted p = {detr['p_adjusted']:.3g})")
    reasons.append(f"year-block permutation p = {perm['p_permutation']:.3g}")
    reasons.append("sign is consistent across both halves of the record" if stable
                   else "sign differs between the two halves of the record")
    if sig_adj and sig_perm and stable and strong:
        return "SUPPORTED", reasons
    if sig_adj and sig_perm and stable:
        reasons.append(f"|r| below the pre-set threshold {th['min_abs_r']}")
        return "WEAK", reasons
    if sig_adj or sig_perm:
        return "INCONCLUSIVE", reasons
    return "NOT_SUPPORTED", reasons


def analyze_pair(x: pd.Series, y: pd.Series, *, baseline: tuple[int, int] | None = None,
                 max_lag: int = 6, n_perm: int = 2000, seed: int = 20261114,
                 thresholds: dict | None = None) -> dict[str, Any]:
    """Full relationship analysis of two aligned monthly series."""
    if not x.index.equals(y.index):
        raise ValueError("series are not aligned on the same calendar")
    cx, cy = monthly_climatology(x, baseline), monthly_climatology(y, baseline)
    ax, ay = anomalies(x, cx), anomalies(y, cy)
    dx, dy = detrend_linear(ax), detrend_linear(ay)

    raw = correlate(x, y)
    cycle = correlate(climatology_cycle(x, cx), climatology_cycle(y, cy))
    deseason = correlate(ax, ay)
    detr = correlate(dx, dy)
    perm = year_block_permutation(dx, dy, n_perm=n_perm, seed=seed)
    stability = subperiod_stability(dx, dy)
    seasons = seasonal_correlations(dx, dy)
    lags = lagged_correlations(dx, dy, max_lag=max_lag)
    lags_deseason = lagged_correlations(ax, ay, max_lag=max_lag)
    status, reasons = classify(detr, perm, stability, thresholds)

    return {
        "baseline": list(baseline) if baseline else [int(x.index.year.min()), int(x.index.year.max())],
        "raw": raw, "seasonal_cycle_only": cycle, "deseasonalized": deseason, "detrended": detr,
        "negative_control_year_shuffle": perm, "stability": stability, "by_season": seasons,
        "lags": lags, "lags_deseasonalized": lags_deseason, "status": status, "status_reasons": reasons,
        "thresholds": {**DEFAULT_THRESHOLDS, **(thresholds or {})},
        "seasonality_share_note": (
            "raw r mixes the shared seasonal cycle with year-to-year co-variation; "
            "compare 'seasonal_cycle_only' with 'deseasonalized' to see which dominates"),
    }
