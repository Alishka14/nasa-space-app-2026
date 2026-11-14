"""Trend Engine: Theil-Sen slopes, Mann-Kendall family, autocorrelation-aware
inference, Benjamini-Hochberg FDR, period and endpoint sensitivity.

All functions are pure and deterministic. Slopes are expressed per unit of the
time vector that is passed in (years in every caller of this module).

References
----------
Mann (1945); Kendall (1975); Sen (1968) - rank trend test and slope.
Hirsch, Slack & Smith (1982) - seasonal Kendall test and seasonal slope.
Hirsch & Slack (1984) - covariance correction for serially dependent seasons.
Hamed & Rao (1998) - variance correction for autocorrelated series.
Santer et al. (2000) - AR(1) effective sample size for least-squares trends.
Benjamini & Hochberg (1995) - false discovery rate.
"""
from __future__ import annotations

import math
from typing import Any, Sequence

import numpy as np
from scipy import stats

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _drop_nan(t: Sequence[float], x: Sequence[float]) -> tuple[np.ndarray, np.ndarray]:
    t = np.asarray(t, dtype=float)
    x = np.asarray(x, dtype=float)
    if t.shape != x.shape:
        raise ValueError("time and value vectors differ in length")
    keep = ~(np.isnan(t) | np.isnan(x))
    return t[keep], x[keep]


def acf(x: Sequence[float], nlags: int) -> np.ndarray:
    """Biased sample autocorrelation, lags 0..nlags."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    y = x - x.mean()
    denom = float(np.dot(y, y))
    if denom == 0.0:
        return np.r_[1.0, np.zeros(nlags)]
    return np.array([float(np.dot(y[: n - k], y[k:])) / denom for k in range(nlags + 1)])


def lag1_autocorr(x: Sequence[float]) -> float:
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) < 4:
        return float("nan")
    return float(acf(x, 1)[1])


def _z_from_s(s: float, var: float) -> float:
    """Continuity-corrected normal score for a Kendall S statistic."""
    if var <= 0:
        return 0.0
    if s > 0:
        return (s - 1) / math.sqrt(var)
    if s < 0:
        return (s + 1) / math.sqrt(var)
    return 0.0


def _two_sided_p(z: float) -> float:
    return float(2 * stats.norm.sf(abs(z)))


# ---------------------------------------------------------------------------
# Mann-Kendall
# ---------------------------------------------------------------------------

def mk_score(x: Sequence[float]) -> tuple[int, float]:
    """Kendall S and its tie-corrected variance under independence."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    s = 0.0
    for i in range(n - 1):
        s += float(np.sign(x[i + 1:] - x[i]).sum())
    _, counts = np.unique(x, return_counts=True)
    ties = sum(int(c) * (int(c) - 1) * (2 * int(c) + 5) for c in counts if c > 1)
    var = (n * (n - 1) * (2 * n + 5) - ties) / 18.0
    return int(s), float(var)


def mann_kendall(x: Sequence[float], tie_correction: bool = True) -> dict[str, Any]:
    """Classic Mann-Kendall test (assumes serially independent data).

    ``tie_correction=False`` uses the no-ties variance n(n-1)(2n+5)/18 even
    when values repeat. It exists only to reproduce analyses made that way;
    the engine's own tests always correct for ties.
    """
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n < 4:
        return {"n": n, "s": None, "var_s": None, "z": None, "p": None, "tau": None,
                "note": "fewer than 4 values"}
    s, var = mk_score(x)
    if not tie_correction:
        var = n * (n - 1) * (2 * n + 5) / 18.0
    z = _z_from_s(s, var)
    return {"n": n, "s": s, "var_s": var, "z": z, "p": _two_sided_p(z),
            "tau": s / (n * (n - 1) / 2.0)}


def hamed_rao_mk(x: Sequence[float], alpha: float = 0.05, max_lag: int | None = None,
                 conservative: bool = True) -> dict[str, Any]:
    """Mann-Kendall with the Hamed & Rao (1998) variance correction.

    The series is detrended with the Sen slope, ranked, and the significant
    rank autocorrelations inflate (or deflate) the variance of S.
    """
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n < 6:
        return {"n": n, "s": None, "var_s": None, "z": None, "p": None,
                "correction_factor": None, "note": "fewer than 6 values"}
    s, var = mk_score(x)
    idx = np.arange(1, n + 1, dtype=float)
    slope = float(stats.theilslopes(x, idx)[0])
    ranks = stats.rankdata(x - slope * idx)
    nl = n - 1 if max_lag is None else min(max_lag, n - 1)
    r = acf(ranks, nl)
    bound = stats.norm.ppf(1 - alpha / 2) / math.sqrt(n)
    sni = 0.0
    used = []
    for i in range(1, nl + 1):
        if abs(r[i]) > bound:
            sni += (n - i) * (n - i - 1) * (n - i - 2) * r[i]
            used.append(i)
    raw_factor = 1 + 2.0 / (n * (n - 1) * (n - 2)) * sni
    # Conservative rule (fixed in advance): the correction may widen the
    # variance but never narrow it, so this test is never more liberal than
    # the classic one. The unclipped factor is still reported.
    factor = max(1.0, raw_factor) if conservative else raw_factor
    note = None
    if factor <= 0:
        note = "correction factor non-positive; fell back to the uncorrected variance"
        factor = 1.0
    var_star = var * factor
    z = _z_from_s(s, var_star)
    out = {"n": n, "s": s, "var_s": var_star, "z": z, "p": _two_sided_p(z),
           "correction_factor": factor, "correction_factor_unclipped": raw_factor,
           "conservative": conservative, "significant_lags": used, "tau": s / (n * (n - 1) / 2.0)}
    if note:
        out["note"] = note
    return out


# ---------------------------------------------------------------------------
# Theil-Sen
# ---------------------------------------------------------------------------

def theil_sen(t: Sequence[float], x: Sequence[float], confidence: float = 0.95) -> dict[str, Any]:
    """Theil-Sen slope with a rank-based confidence interval (Sen 1968)."""
    t, x = _drop_nan(t, x)
    if len(x) < 4:
        return {"n": len(x), "slope": None, "intercept": None, "ci_low": None, "ci_high": None}
    slope, intercept, lo, hi = stats.theilslopes(x, t, alpha=confidence)
    return {"n": len(x), "slope": float(slope), "intercept": float(intercept),
            "ci_low": float(lo), "ci_high": float(hi), "confidence": confidence}


# ---------------------------------------------------------------------------
# Least squares with AR(1)-adjusted inference
# ---------------------------------------------------------------------------

def ols_trend(t: Sequence[float], x: Sequence[float], confidence: float = 0.95) -> dict[str, Any]:
    """OLS slope; p-values both naive and with the Santer et al. (2000)
    effective sample size n_eff = n (1 - r1) / (1 + r1) from residual lag-1
    autocorrelation (applied only when r1 > 0)."""
    t, x = _drop_nan(t, x)
    n = len(x)
    if n < 4:
        return {"n": n, "slope": None}
    tc = t - t.mean()
    sxx = float(np.dot(tc, tc))
    slope = float(np.dot(tc, x - x.mean()) / sxx)
    intercept = float(x.mean() - slope * t.mean())
    resid = x - (intercept + slope * t)
    sse = float(np.dot(resid, resid))

    def infer(n_used: float) -> tuple[float, float, float, float]:
        dof = n_used - 2
        if dof <= 0:
            return float("nan"), float("nan"), float("nan"), float("nan")
        se = math.sqrt(sse / dof / sxx)
        tval = slope / se if se > 0 else float("inf")
        p = float(2 * stats.t.sf(abs(tval), dof))
        half = float(stats.t.ppf(0.5 + confidence / 2, dof)) * se
        return se, p, slope - half, slope + half

    se, p, lo, hi = infer(n)
    r1 = float(acf(resid, 1)[1])
    n_eff = n * (1 - r1) / (1 + r1) if r1 > 0 else float(n)
    se_a, p_a, lo_a, hi_a = infer(n_eff)
    return {"n": n, "slope": slope, "intercept": intercept, "se": se, "p_naive": p,
            "ci_low": lo, "ci_high": hi, "resid_lag1_autocorr": r1, "n_eff": n_eff,
            "se_ar1": se_a, "p_ar1": p_a, "ci_low_ar1": lo_a, "ci_high_ar1": hi_a,
            "r_squared": float(1 - sse / np.dot(x - x.mean(), x - x.mean())) if np.ptp(x) > 0 else 0.0}


def minimum_detectable_trend(t: Sequence[float], x: Sequence[float], alpha: float = 0.05,
                             power: float = 0.80) -> dict[str, Any]:
    """Smallest linear trend this record could detect with the given power.

    Normal-theory approximation for a least-squares slope with the AR(1)
    effective sample size: MDT = (t[1-alpha/2] + t[power]) * se(slope).
    It answers "how large would a real trend have to be before this record
    would probably show it?" - the quantitative reason why a non-significant
    result is not evidence of no change.
    """
    o = ols_trend(t, x)
    if o.get("slope") is None or not np.isfinite(o.get("se_ar1", np.nan)):
        return {"mdt": None, "note": "insufficient data"}
    dof = o["n_eff"] - 2
    mdt = (stats.t.ppf(1 - alpha / 2, dof) + stats.t.ppf(power, dof)) * o["se_ar1"]
    return {"mdt": float(mdt), "alpha": alpha, "power": power, "se_slope": o["se_ar1"],
            "n_eff": o["n_eff"], "method": "OLS slope standard error with AR(1) effective sample size"}


# ---------------------------------------------------------------------------
# Seasonal Kendall (monthly data)
# ---------------------------------------------------------------------------

def seasonal_mann_kendall(matrix: np.ndarray, confidence: float = 0.95) -> dict[str, Any]:
    """Seasonal Kendall test on a (years x seasons) matrix.

    ``p_independent`` assumes seasons are independent (Hirsch et al. 1982);
    ``p_dependent`` adds the between-season covariance of Hirsch & Slack (1984)
    and is the one to trust for monthly climate data. The covariance term needs
    a complete matrix; with gaps only the independent version is returned.
    The slope is the median of all within-season pairwise slopes, per year.
    """
    m = np.asarray(matrix, dtype=float)
    n_years, n_seasons = m.shape
    s_total, var_indep = 0.0, 0.0
    slopes: list[float] = []
    for g in range(n_seasons):
        col = m[:, g]
        yrs = np.arange(n_years, dtype=float)[~np.isnan(col)]
        vals = col[~np.isnan(col)]
        if len(vals) < 4:
            continue
        s, var = mk_score(vals)
        s_total += s
        var_indep += var
        for i in range(len(vals) - 1):
            slopes.extend(((vals[i + 1:] - vals[i]) / (yrs[i + 1:] - yrs[i])).tolist())
    if not slopes:
        return {"n_years": n_years, "n_seasons": n_seasons, "s": None, "p_independent": None,
                "p_dependent": None, "slope": None, "note": "insufficient data"}

    complete = not np.isnan(m).any()
    var_dep = None
    if complete:
        ranks = np.apply_along_axis(stats.rankdata, 0, m)
        cov_sum = 0.0
        iu = np.triu_indices(n_years, k=1)
        diffs = [np.sign(m[iu[1], g] - m[iu[0], g]) for g in range(n_seasons)]
        for g in range(n_seasons):
            for h in range(g + 1, n_seasons):
                k_gh = float(np.dot(diffs[g], diffs[h]))
                cov = (k_gh + 4 * float(np.dot(ranks[:, g], ranks[:, h])) - n_years * (n_years + 1) ** 2) / 3.0
                cov_sum += cov
        var_dep = var_indep + 2 * cov_sum

    z_i = _z_from_s(s_total, var_indep)
    out: dict[str, Any] = {
        "n_years": n_years, "n_seasons": n_seasons, "s": int(s_total),
        "var_independent": var_indep, "z_independent": z_i, "p_independent": _two_sided_p(z_i),
        "slope": float(np.median(slopes)), "n_slopes": len(slopes),
    }
    var_ci = var_indep
    if var_dep is not None and var_dep > 0:
        z_d = _z_from_s(s_total, var_dep)
        out.update({"var_dependent": var_dep, "z_dependent": z_d, "p_dependent": _two_sided_p(z_d),
                    "variance_inflation": var_dep / var_indep})
        var_ci = var_dep
    else:
        out.update({"var_dependent": None, "z_dependent": None, "p_dependent": None,
                    "note": "covariance correction unavailable (gaps or degenerate variance)"})
    # Sen-type confidence interval from the ordered slopes
    srt = np.sort(slopes)
    c = stats.norm.ppf(0.5 + confidence / 2) * math.sqrt(var_ci)
    lo_i = int(math.floor((len(srt) - c) / 2.0))
    hi_i = int(math.ceil((len(srt) + c) / 2.0))
    out["ci_low"] = float(srt[max(lo_i - 1, 0)])
    out["ci_high"] = float(srt[min(hi_i, len(srt) - 1)])
    out["confidence"] = confidence
    return out


# ---------------------------------------------------------------------------
# Multiple testing
# ---------------------------------------------------------------------------

def benjamini_hochberg(pvalues: Sequence[float | None]) -> list[float | None]:
    """Benjamini-Hochberg adjusted p-values (q-values). None/NaN stay None and
    do not count towards the number of tests."""
    p = np.array([np.nan if v is None else float(v) for v in pvalues], dtype=float)
    valid = ~np.isnan(p)
    m = int(valid.sum())
    out: list[float | None] = [None] * len(p)
    if m == 0:
        return out
    idx = np.where(valid)[0]
    order = idx[np.argsort(p[idx], kind="mergesort")]
    ranked = p[order] * m / np.arange(1, m + 1)
    q = np.minimum(np.minimum.accumulate(ranked[::-1])[::-1], 1.0)
    for pos, val in zip(order, q):
        out[int(pos)] = float(val)
    return out


# ---------------------------------------------------------------------------
# Composite summaries
# ---------------------------------------------------------------------------

def summarize_trend(years: Sequence[float], values: Sequence[float], alpha: float = 0.05) -> dict[str, Any]:
    """Primary trend summary for one series sampled once per year.

    Primary estimate: Theil-Sen slope with 95% CI.
    Primary p-value: the LARGER of two autocorrelation-aware tests, the
    Hamed-Rao modified Mann-Kendall test and least squares with the AR(1)
    effective sample size. Both must reject for a trend to count.

    Why two: on trend-free AR(1) noise with n = 24 (3000 simulations)
    Hamed-Rao alone rejects in about 12% of cases at phi = 0.3 and 29% at
    phi = 0.7, against a nominal 5%. Requiring agreement with the
    AR(1)-adjusted least-squares test brings that to about 7.5% and 14%:
    better, still above nominal for strongly persistent series.
    Reported alongside: the classic Mann-Kendall test and naive least squares.
    """
    t, x = _drop_nan(years, values)
    sen = theil_sen(t, x, 1 - alpha)
    mk = mann_kendall(x)
    hr = hamed_rao_mk(x, alpha)
    ols = ols_trend(t, x, 1 - alpha)
    candidates = [v for v in (hr.get("p"), ols.get("p_ar1")) if v is not None and np.isfinite(v)]
    primary_p = max(candidates) if candidates else None
    return {
        "n": int(len(x)), "first_year": float(t[0]) if len(t) else None,
        "last_year": float(t[-1]) if len(t) else None,
        "theil_sen": sen, "mann_kendall": mk, "mann_kendall_hamed_rao": hr, "ols": ols,
        "lag1_autocorr": lag1_autocorr(x),
        "primary_slope": sen["slope"], "primary_ci": [sen["ci_low"], sen["ci_high"]],
        "primary_p": primary_p,
        "primary_test": "larger p of Hamed-Rao modified Mann-Kendall and AR(1)-adjusted least squares",
        "alpha": alpha, "minimum_detectable_trend": minimum_detectable_trend(t, x, alpha),
    }


def window_sensitivity(years: Sequence[float], values: Sequence[float], min_len: int = 15,
                       alpha: float = 0.05) -> dict[str, Any]:
    """Re-estimate the trend on every contiguous sub-period of at least
    ``min_len`` years. A conclusion that changes sign or significance with the
    window is period-dependent and must be reported as such."""
    t, x = _drop_nan(years, values)
    n = len(x)
    rows = []
    for i in range(n):
        for j in range(i + min_len - 1, n):
            seg_t, seg_x = t[i:j + 1], x[i:j + 1]
            slope = float(stats.theilslopes(seg_x, seg_t)[0])
            p = mann_kendall(seg_x)["p"]
            rows.append({"start": int(seg_t[0]), "end": int(seg_t[-1]), "n": int(len(seg_x)),
                         "slope": slope, "p": p})
    if not rows:
        return {"windows": [], "n_windows": 0, "note": f"series shorter than {min_len} years"}
    slopes = np.array([r["slope"] for r in rows])
    sig = np.array([r["p"] is not None and r["p"] < alpha for r in rows])
    pos, neg = int((slopes > 0).sum()), int((slopes < 0).sum())
    return {
        "windows": rows, "n_windows": len(rows), "min_len": min_len,
        "slope_min": float(slopes.min()), "slope_max": float(slopes.max()),
        "n_positive": pos, "n_negative": neg, "n_significant": int(sig.sum()),
        "n_significant_positive": int((sig & (slopes > 0)).sum()),
        "n_significant_negative": int((sig & (slopes < 0)).sum()),
        "sign_changes_with_period": pos > 0 and neg > 0,
        "significance_changes_with_period": 0 < int(sig.sum()) < len(rows),
    }


def leave_one_out(years: Sequence[float], values: Sequence[float], alpha: float = 0.05) -> dict[str, Any]:
    """Drop each year in turn: does a single year carry the conclusion?"""
    t, x = _drop_nan(years, values)
    full_p = mann_kendall(x)["p"]
    full_sig = full_p is not None and full_p < alpha
    rows = []
    for i in range(len(x)):
        keep = np.arange(len(x)) != i
        slope = float(stats.theilslopes(x[keep], t[keep])[0])
        p = mann_kendall(x[keep])["p"]
        rows.append({"dropped_year": int(t[i]), "slope": slope, "p": p,
                     "significant": p is not None and p < alpha})
    flips = [r for r in rows if r["significant"] != full_sig]
    return {"full_p": full_p, "full_significant": full_sig, "rows": rows,
            "years_that_flip_significance": [r["dropped_year"] for r in flips],
            "p_range_of_flipping_years": [min(r["p"] for r in flips), max(r["p"] for r in flips)] if flips else None,
            "max_p_after_drop": max(r["p"] for r in rows) if rows else None,
            "min_p_after_drop": min(r["p"] for r in rows) if rows else None}
