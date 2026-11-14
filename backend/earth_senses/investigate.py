"""Investigation orchestrator: data -> trends -> relationships -> evidence ->
relationship graph -> change episodes.

Every sentence produced here is a fixed template filled with computed numbers
and passes the MIZAN Guard before it is published. Decision rules (alpha,
thresholds, test families) are constants declared below, set before looking at
any particular dataset.
"""
from __future__ import annotations

import itertools
import math
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from . import ENGINE_VERSION
from .catalog import describe
from .evidence import attach_independent_reports, make_record
from .guard import enforce
from .normalize import SEASONS, annual_mean, annual_total, rate_to_monthly_total, seasonal_mean
from .power_client import POWER_FIRST_YEAR, DataUnavailable, PowerDataset, PowerStore
from .relationships import analyze_pair, anomalies, correlate, detrend_linear, monthly_climatology
from .trends import (benjamini_hochberg, leave_one_out, mann_kendall, seasonal_mann_kendall,
                     summarize_trend, theil_sen, window_sensitivity)

ALPHA = 0.05
MAX_LAG = 6
N_PERM = 2000
SEED = 20261114

GENERAL_LIMITATIONS = [
    "One MERRA-2 grid cell (about 0.5 x 0.625 degrees) at the cell's mean elevation: it describes the "
    "cell, not a station or a city.",
    "MERRA-2 is a model reanalysis. Changes in the observations it assimilates can create steps that "
    "look like trends; no homogeneity test is applied here.",
    "Only monotonic (Theil-Sen / Mann-Kendall) and linear trends are tested.",
    "Correlations describe co-variation of monthly anomalies. They do not identify causes, and a lead "
    "or lag is a timing statistic only.",
    "Results hold for the stated period; other periods can and do give different answers.",
]

HYPOTHESES = {
    frozenset(("T2M", "RH2M")):
        "Hypothesis (untested here): for a fixed amount of water vapour, warmer air is further from "
        "saturation, so relative humidity is lower in warmer-than-usual months. A test: repeat with "
        "specific humidity (QV2M), which should co-vary with temperature far less if this is the reason.",
    frozenset(("PRECTOTCORR", "RH2M")):
        "Hypothesis (untested here): wetter-than-usual months bring moister air and wetter soil, and both "
        "raise near-surface humidity; humidity staying high in the following month would fit soil-moisture "
        "memory. A test: add surface soil wetness (GWETTOP) and check whether it carries the one-month lag.",
    frozenset(("T2M", "PRECTOTCORR")):
        "Hypothesis (untested here): in the warm season wet months are cloudier and evaporation cools the "
        "surface, while in winter mild air masses are also the moist ones, which would reverse the sign. "
        "A test: analyse seasons separately and add cloud amount or surface solar radiation.",
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def clean(obj: Any) -> Any:
    """JSON-safe copy: numpy scalars -> Python, NaN/inf -> None."""
    if isinstance(obj, dict):
        return {str(k): clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        return None if not math.isfinite(float(obj)) else float(obj)
    if isinstance(obj, np.ndarray):
        return clean(obj.tolist())
    return obj


def f(x: float | None, nd: int = 3, sign: bool = True) -> str:
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "n/a"
    return f"{x:+.{nd}f}" if sign else f"{x:.{nd}f}"


def fr(x: float | None) -> str:
    """Correlation or bound to two decimals, three when it would otherwise print as zero."""
    return f(x, 3) if x is not None and abs(x) < 0.005 else f(x, 2)


def fp(p: float | None) -> str:
    if p is None:
        return "n/a"
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


_PAIR_RANK = {"T2M": 0, "PRECTOTCORR": 1, "RH2M": 2}


def pair_order(variables: list[str]) -> list[str]:
    """Fixed ordering for pairs so that ids and lag signs do not depend on the
    order in which the user ticked the variables."""
    return sorted(variables, key=lambda v: (_PAIR_RANK.get(v, 99), v))


def _window_len(n: int) -> int:
    if n >= 40:
        return 20
    if n >= 20:
        return 15
    return max(8, n - 4)


# ---------------------------------------------------------------------------
# trends
# ---------------------------------------------------------------------------

def _trend_block(series: pd.Series, alpha: float) -> dict[str, Any]:
    ann = annual_mean(series)
    years, vals = ann.index.to_numpy(dtype=float), ann.to_numpy(dtype=float)
    seasons = {}
    for name in SEASONS:
        sm = seasonal_mean(series, name)
        st = theil_sen(sm.index.to_numpy(dtype=float), sm.to_numpy(dtype=float), 1 - alpha)
        seasons[name] = {"n": int(len(sm)), "slope": st["slope"], "ci": [st["ci_low"], st["ci_high"]],
                         "p": mann_kendall(sm.to_numpy(dtype=float))["p"]}
    return {
        "annual": {"years": [int(y) for y in years], "values": vals.tolist()},
        "summary": summarize_trend(years, vals, alpha),
        "seasonal_kendall": seasonal_mann_kendall(series.to_numpy(dtype=float).reshape(-1, 12), 1 - alpha),
        "window_sensitivity": window_sensitivity(years, vals, min_len=_window_len(len(vals)), alpha=alpha),
        "leave_one_out": leave_one_out(years, vals, alpha),
        "by_season": seasons,
    }


def _trend_verdict(block: dict[str, Any], q: float | None, alpha: float) -> tuple[str, list[str]]:
    s = block["summary"]
    lo, hi = s["primary_ci"]
    p, p_mk = s["primary_p"], s["mann_kendall"]["p"]
    p_sk = block["seasonal_kendall"].get("p_dependent")
    flips = block["leave_one_out"]["years_that_flip_significance"]
    ci_excl = lo is not None and (lo > 0 or hi < 0)
    reasons = []
    if p is not None and p < alpha and q is not None and q < alpha and ci_excl and not flips:
        return "ROBUST_TREND", reasons
    any_sig = any(v is not None and v < alpha for v in (p, p_mk, p_sk))
    if any_sig:
        if q is not None and q >= alpha:
            reasons.append(f"not significant after false-discovery correction (q = {q:.3f})")
        if flips:
            reasons.append("significance depends on single years (" + ", ".join(str(y) for y in flips) + ")")
        if not ci_excl:
            reasons.append("the 95% confidence interval of the slope includes zero")
        if p is not None and p >= alpha:
            reasons.append("the autocorrelation-adjusted tests do not both reject")
        return "FRAGILE_TREND", reasons
    return "NO_SIGNIFICANT_TREND_DETECTED", reasons


def _trend_statement(info: dict, block: dict, verdict: str, reasons: list[str], q: float | None,
                     period: list[int]) -> str:
    s = block["summary"]
    lo, hi = s["primary_ci"]
    unit = info["slope_units"]
    core = (f"Theil-Sen slope {f(s['primary_slope'])} {unit} (95% CI {f(lo)} to {f(hi)}), "
            f"autocorrelation-adjusted p = {fp(s['primary_p'])}, q = {fp(q)}")
    span = f"{period[0]}-{period[1]}"
    if verdict == "ROBUST_TREND":
        word = "an increasing" if s["primary_slope"] > 0 else "a decreasing"
        return f"{info['label']} shows {word} monotonic trend over {span}: {core}."
    if verdict == "FRAGILE_TREND":
        return (f"{info['label']} over {span}: {core}. Some tests indicate a trend, but the result is "
                f"fragile: {'; '.join(reasons)}.")
    mdt = s["minimum_detectable_trend"].get("mdt")
    tail = (f" A record of this length and variability would only be likely to show trends larger than "
            f"about {f(mdt, sign=False)} {unit} (80% power), so smaller real changes cannot be ruled out."
            if mdt else "")
    return (f"{info['label']}: no statistically significant monotonic trend was detected over {span} "
            f"({core}).{tail}")


# ---------------------------------------------------------------------------
# main entry
# ---------------------------------------------------------------------------

def investigate(store: PowerStore, *, lat: float, lon: float, start: int, end: int,
                variables: list[str], region_name: str | None = None,
                baseline: tuple[int, int] | None = None, independent_reports: list[dict] | None = None,
                refresh: bool = False, alpha: float = ALPHA, n_perm: int = N_PERM) -> dict[str, Any]:
    variables = list(dict.fromkeys(variables))
    ds = store.load(lat, lon, start, end, variables, refresh=refresh)
    monthly = ds.monthly
    period = [start, end]
    region = {"name": region_name or f"{lat:.2f}, {lon:.2f}", "latitude": lat, "longitude": lon,
              "grid_cell_elevation_m": ds.norm.elevation_m}
    base = list(baseline) if baseline else period
    if not (start <= base[0] <= base[1] <= end):
        raise ValueError(f"baseline {base} must lie inside the analysed period {period}")
    infos = {v: describe(v, ds.norm.units[v], ds.norm.longnames[v]) for v in variables}
    warnings = list(ds.norm.warnings) + list(ds.notes)
    for v in variables:
        if monthly[v].isna().any():
            raise ValueError(f"{v} has missing months in the requested period; gap handling is not "
                             "implemented, so no result is produced")
        if not infos[v]["verified"]:
            warnings.append(f"{v}: this parameter was not exercised against a real response in this "
                            "build's tests; units are taken from the live response metadata.")
    if end - start + 1 < 20:
        warnings.append("Fewer than 20 years: trend tests have little power and confidence intervals are wide.")
    reports = independent_reports or []

    # optional longer context for period-sensitivity counterevidence
    context: PowerDataset | None = None
    if start > POWER_FIRST_YEAR:
        try:
            context = store.load(lat, lon, POWER_FIRST_YEAR, end, variables)
        except (DataUnavailable, ValueError) as exc:
            warnings.append(f"Longer-record check ({POWER_FIRST_YEAR}-{end}) not available: {exc}")

    # ---- series ---------------------------------------------------------------
    clim = {v: monthly_climatology(monthly[v], tuple(base)) for v in variables}
    anom = {v: anomalies(monthly[v], clim[v]) for v in variables}
    detr = {v: detrend_linear(anom[v]) for v in variables}

    # ---- trends ---------------------------------------------------------------
    blocks = {v: _trend_block(monthly[v], alpha) for v in variables}
    qs = benjamini_hochberg([blocks[v]["summary"]["primary_p"] for v in variables])
    season_keys = [(v, s) for v in variables for s in SEASONS]
    season_q = benjamini_hochberg([blocks[v]["by_season"][s]["p"] for v, s in season_keys])
    for (v, s), q in zip(season_keys, season_q):
        blocks[v]["by_season"][s]["q"] = q

    evidence: list[Any] = []
    trends: dict[str, Any] = {}
    for v, q in zip(variables, qs):
        info, block = infos[v], blocks[v]
        summ = block["summary"]
        verdict, reasons = _trend_verdict(block, q, alpha)
        statement = _trend_statement(info, block, verdict, reasons, q, period)
        sk, win, loo = block["seasonal_kendall"], block["window_sensitivity"], block["leave_one_out"]
        unit = info["slope_units"]

        api_variant = None
        if ds.annual_reported is not None and len(ds.annual_reported) == end - start + 1:
            rep = ds.annual_reported[v].to_numpy(dtype=float)
            yrs = ds.annual_reported.index.to_numpy(dtype=float)
            api_variant = {"sen_slope": theil_sen(yrs, rep, 1 - alpha)["slope"], "mk_p": mann_kendall(rep)["p"],
                           "mk_p_no_tie_correction": mann_kendall(rep, tie_correction=False)["p"],
                           "note": "same test on the API's own two-decimal annual means (YYYY13); the variant "
                                   "without tie correction is kept only for comparison with outside reports"}

        support = [
            f"Theil-Sen slope {f(summ['primary_slope'])} {unit} (95% CI {f(summ['primary_ci'][0])} to "
            f"{f(summ['primary_ci'][1])}) on {summ['n']} annual means.",
            f"Classic Mann-Kendall p = {fp(summ['mann_kendall']['p'])}; Hamed-Rao modified p = "
            f"{fp(summ['mann_kendall_hamed_rao']['p'])}; least-squares slope {f(summ['ols']['slope'])} with "
            f"AR(1)-adjusted p = {fp(summ['ols']['p_ar1'])}. The reported p is the larger of the last two.",
            f"Seasonal Kendall test on {len(monthly)} monthly values: slope {f(sk['slope'])} {unit}, "
            f"p = {fp(sk.get('p_dependent'))} allowing for dependence between months "
            f"(p = {fp(sk['p_independent'])} if months are treated as independent).",
            f"Benjamini-Hochberg q = {fp(q)} across the {len(variables)} variables tested together.",
        ]
        counter = [
            f"Across {win['n_windows']} sub-periods of at least {win.get('min_len')} years the slope is "
            f"positive in {win.get('n_positive')} and negative in {win.get('n_negative')}; "
            f"{win.get('n_significant')} are individually significant.",
        ]
        if loo["years_that_flip_significance"]:
            counter.append(
                "Leaving out any one of the years " + ", ".join(str(y) for y in loo["years_that_flip_significance"])
                + f" changes whether the classic test is significant (p between "
                  f"{fp(loo['p_range_of_flipping_years'][0])} and {fp(loo['p_range_of_flipping_years'][1])} "
                  f"for those years; {fp(loo['full_p'])} with all years).")
        ctx = None
        if context is not None:
            cann = annual_mean(context.monthly[v])
            cs = summarize_trend(cann.index.to_numpy(dtype=float), cann.to_numpy(dtype=float), alpha)
            ctx = {"period": [POWER_FIRST_YEAR, end], "slope": cs["primary_slope"], "ci": cs["primary_ci"],
                   "p": cs["primary_p"], "data_hash": context.data_hash,
                   "annual": {"years": [int(y) for y in cann.index], "values": cann.tolist()}}
            counter.append(
                f"Over the longer record {POWER_FIRST_YEAR}-{end} the slope is {f(cs['primary_slope'])} {unit} "
                f"(95% CI {f(cs['primary_ci'][0])} to {f(cs['primary_ci'][1])}, p = {fp(cs['primary_p'])}).")

        rec = make_record(
            claim=statement, claim_type="computed_observation", region=region, period=period, variables=[v],
            method="Theil-Sen slope; larger p of Hamed-Rao modified Mann-Kendall and AR(1)-adjusted least "
                   "squares, on day-weighted annual means; seasonal Kendall on monthly values; "
                   "Benjamini-Hochberg across variables",
            parameters={"alpha": alpha, "aggregation": "day-weighted annual mean", "fdr_family": sorted(variables),
                        "window_min_years": win.get("min_len")},
            data_hash=ds.data_hash,
            result={"slope": summ["primary_slope"], "slope_units": unit, "p": summ["primary_p"], "q": q,
                    "mann_kendall_p": summ["mann_kendall"]["p"],
                    "hamed_rao_p": summ["mann_kendall_hamed_rao"]["p"], "ols_ar1_p": summ["ols"]["p_ar1"],
                    "seasonal_kendall_p": sk.get("p_dependent"),
                    "api_annual_variant": api_variant},
            uncertainty={"slope_ci95": summ["primary_ci"],
                         "minimum_detectable_trend_80pct_power": summ["minimum_detectable_trend"].get("mdt"),
                         "lag1_autocorrelation_of_annual_means": summ["lag1_autocorr"]},
            supporting_evidence=support, counterevidence=counter, verdict=verdict,
            significant=verdict == "ROBUST_TREND",
            alternatives=["A step change in the observations assimilated by the reanalysis could appear as a trend.",
                          "Multi-decadal variability can produce a monotonic change inside a short window."],
            limitations=GENERAL_LIMITATIONS[:3] + [GENERAL_LIMITATIONS[4]], engine_version=ENGINE_VERSION)
        metrics = {f"trend.{v}.sen_slope": summ["primary_slope"], f"trend.{v}.mk_p": summ["mann_kendall"]["p"],
                   f"trend.{v}.q": q}
        if api_variant:
            metrics[f"trend.{v}.sen_slope_api_annual"] = api_variant["sen_slope"]
            metrics[f"trend.{v}.mk_p_api_annual"] = api_variant["mk_p"]
            metrics[f"trend.{v}.mk_p_api_annual_no_tie_correction"] = api_variant["mk_p_no_tie_correction"]
        attach_independent_reports(rec, metrics, reports)
        evidence.append(rec)

        entry = {**block, "q": q, "verdict": verdict, "verdict_reasons": reasons, "statement": statement,
                 "slope_units": unit, "per_decade": None if summ["primary_slope"] is None else summ["primary_slope"] * 10,
                 "evidence_id": rec.id, "context": ctx, "api_annual_variant": api_variant}
        if info["aggregation"] == "rate" and info["units"].strip().lower() == "mm/day":
            totals = annual_total(rate_to_monthly_total(monthly[v], info["units"]))
            ts = summarize_trend(totals.index.to_numpy(dtype=float), totals.to_numpy(dtype=float), alpha)
            entry["annual_total"] = {"years": [int(y) for y in totals.index], "values": totals.tolist(),
                                     "units": "mm/year", "slope_units": "mm/year per year",
                                     "mean": float(totals.mean()), "summary": ts,
                                     "note": "monthly mean rate (mm/day) x days in each month, summed per year"}
        trends[v] = entry

    # ---- relationships ----------------------------------------------------------
    relationships: list[dict[str, Any]] = []
    for a, b in itertools.combinations(pair_order(variables), 2):
        res = analyze_pair(monthly[a], monthly[b], baseline=tuple(base), max_lag=MAX_LAG, n_perm=n_perm, seed=SEED)
        la, lb = infos[a]["label"], infos[b]["label"]
        d, raw, cyc, des = res["detrended"], res["raw"], res["seasonal_cycle_only"], res["deseasonalized"]
        direction = "in opposite directions" if d["pearson_r"] < 0 else "in the same direction"
        tails = {
            "SUPPORTED": "The association holds in both halves of the record and against a year-shuffled control.",
            "WEAK": "The association is statistically detectable but small.",
            "INCONCLUSIVE": "The checks disagree, so the association is not established.",
            "NOT_SUPPORTED": "No statistically significant association of the anomalies was detected.",
        }
        claim = (f"Monthly anomalies of {la} and {lb} vary {direction} over {start}-{end}: detrended "
                 f"r = {f(d['pearson_r'], 2)} (95% CI {fr(d['ci95_adjusted'][0])} to {fr(d['ci95_adjusted'][1])}, "
                 f"effective n = {d['n_eff']:.0f}). Raw r = {f(raw['pearson_r'], 2)}; the two seasonal cycles "
                 f"alone give r = {f(cyc['pearson_r'], 2)}. {tails[res['status']]}")
        support = [
            f"Raw monthly series: r = {f(raw['pearson_r'])} (n = {raw['n']}).",
            f"Seasonal cycles alone (climatology repeated each year): r = {f(cyc['pearson_r'])}.",
            f"Deseasonalized anomalies (baseline {base[0]}-{base[1]}): r = {f(des['pearson_r'])}, "
            f"naive p = {fp(des['p_naive'])}, autocorrelation-adjusted p = {fp(des['p_adjusted'])} "
            f"(effective n = {des['n_eff']:.0f}); Spearman rho = {f(des['spearman_rho'])}.",
            f"Detrended anomalies: r = {f(d['pearson_r'])}, adjusted p = {fp(d['p_adjusted'])}.",
            f"Year-shuffled control ({res['negative_control_year_shuffle']['n_perm']} permutations): "
            f"p = {fp(res['negative_control_year_shuffle']['p_permutation'])}; 95% of shuffled |r| are below "
            f"{f(res['negative_control_year_shuffle']['null_abs_r_p95'], sign=False)}.",
        ]
        counter = []
        st = res["stability"]
        hv = st["halves"]
        counter.append(f"Halves of the record: r = {f(hv[0]['r'], 2)} ({hv[0]['start']}-{hv[0]['end']}) and "
                       f"r = {f(hv[1]['r'], 2)} ({hv[1]['start']}-{hv[1]['end']}); 10-year windows range from "
                       f"{f(st['rolling_r_min'], 2)} to {f(st['rolling_r_max'], 2)}.")
        ss = res["by_season"]["seasons"]
        season_line = ", ".join(f"{k} {f(v['r'], 2)}" for k, v in ss.items())
        if res["by_season"]["sign_differs_between_seasons"]:
            counter.append(f"The sign differs between seasons ({season_line}), so a single all-year "
                           "statement hides opposite behaviour.")
        else:
            counter.append(f"By season: {season_line}.")
        rec = make_record(
            claim=claim, claim_type="statistical_relationship", region=region, period=period, variables=[a, b],
            method="Pearson/Spearman correlation of raw, deseasonalized and linearly detrended monthly anomalies; "
                   "effective sample size (Bretherton et al. 1999); year-block permutation control",
            parameters={"baseline": base, "alpha": alpha, "n_perm": n_perm, "seed": SEED,
                        "thresholds": res["thresholds"]},
            data_hash=ds.data_hash,
            result={"r_raw": raw["pearson_r"], "r_seasonal_cycle_only": cyc["pearson_r"],
                    "r_deseasonalized": des["pearson_r"], "r_detrended": d["pearson_r"],
                    "p_adjusted": d["p_adjusted"], "p_permutation": res["negative_control_year_shuffle"]["p_permutation"]},
            uncertainty={"r_detrended_ci95": d["ci95_adjusted"], "n_eff": d["n_eff"]},
            supporting_evidence=support, counterevidence=counter, verdict=res["status"],
            significant=res["status"] in ("SUPPORTED", "WEAK"),
            alternatives=["A third factor that varies from month to month (for example the passage of air "
                          "masses) could move both variables together.",
                          "Both variables come from one model, which may link them more tightly than nature does."],
            limitations=[GENERAL_LIMITATIONS[0], GENERAL_LIMITATIONS[1], GENERAL_LIMITATIONS[3], GENERAL_LIMITATIONS[4]],
            engine_version=ENGINE_VERSION)
        pair = f"{a}-{b}"
        metrics = {f"corr.{pair}.raw": raw["pearson_r"], f"corr.{pair}.deseasonalized": des["pearson_r"],
                   f"corr.{pair}.deseasonalized.p_naive": des["p_naive"]}
        attach_independent_reports(rec, metrics, reports)
        evidence.append(rec)

        # lag scan -----------------------------------------------------------------
        lags = res["lags"]
        nz = lags["significant_nonzero_lags"]
        naive_nz = [r_["lag"] for r_ in lags["rows"] if r_["lag"] != 0 and r_["p_naive"] is not None
                    and r_["p_naive"] < alpha]
        by_lag = {r_["lag"]: r_ for r_ in lags["rows"]}
        if nz:
            lag_verdict = "LAGGED_ASSOCIATION_DETECTED"
            detail = ("Non-zero lags that stay significant after correction: "
                      + ", ".join(f"{k:+d} (r = {f(by_lag[k]['r'], 2)})" for k in nz) + ".")
        elif naive_nz:
            lag_verdict = "INCONCLUSIVE"
            detail = ("Some non-zero lags pass an uncorrected test (" + ", ".join(f"{k:+d}" for k in naive_nz)
                      + ") but none stays significant after correcting for the number of lags tried.")
        else:
            lag_verdict = "NO_LAGGED_ASSOCIATION_DETECTED"
            detail = "No non-zero lag is significant, with or without correction."
        lag_claim = (f"Lag scan of detrended anomalies, {la} against {lb}, lags -{MAX_LAG} to +{MAX_LAG} months "
                     f"({lags['n_tests']} tests, Benjamini-Hochberg): the largest |r| is at lag "
                     f"{lags['peak_lag']:+d} (r = {f(lags['peak_r'], 2)}). {detail} Positive lags pair {la} with "
                     f"later {lb}. A lead or lag is a timing statistic only.")
        lag_rec = make_record(
            claim=lag_claim, claim_type="statistical_relationship", region=region, period=period, variables=[a, b],
            method="Lagged Pearson correlation of detrended monthly anomalies with effective sample size; "
                   "Benjamini-Hochberg across all lags",
            parameters={"max_lag": MAX_LAG, "alpha": alpha, "baseline": base,
                        "definition": lags["definition"]},
            data_hash=ds.data_hash,
            result={"rows": [{"lag": r_["lag"], "r": r_["r"], "q": r_["q"]} for r_ in lags["rows"]],
                    "peak_lag": lags["peak_lag"], "significant_nonzero_lags": nz},
            uncertainty={"n_tests": lags["n_tests"],
                         "note": "each lag loses |k| months; adjacent lags are not independent tests"},
            supporting_evidence=[f"Lag {r_['lag']:+d}: r = {f(r_['r'])}, q = {fp(r_['q'])}." for r_ in lags["rows"]
                                 if abs(r_["lag"]) <= 2],
            counterevidence=[], verdict=lag_verdict, significant=bool(nz),
            alternatives=["Persistence of one variable alone can spread a same-month association onto "
                          "neighbouring lags."],
            limitations=[GENERAL_LIMITATIONS[3], "Monthly means cannot resolve lead-lag behaviour shorter than a month."],
            engine_version=ENGINE_VERSION)
        ld = {r_["lag"]: r_["r"] for r_ in res["lags_deseasonalized"]["rows"]}
        attach_independent_reports(lag_rec, {f"lag.{pair}.deseasonalized.{k:+d}": ld[k] for k in ld}, reports)
        evidence.append(lag_rec)

        hyp_id = None
        text = HYPOTHESES.get(frozenset((a, b)))
        if text:
            hyp = make_record(
                claim=text, claim_type="unverified_physical_explanation", region=region, period=period,
                variables=[a, b], method="none: proposed explanation, not tested by this analysis",
                parameters={"attached_to": rec.id}, data_hash=ds.data_hash, result={}, uncertainty={},
                status="HYPOTHESIS", verdict="UNTESTED",
                limitations=["Not tested here. It must not be reported as a finding."],
                engine_version=ENGINE_VERSION)
            evidence.append(hyp)
            hyp_id = hyp.id

        relationships.append({"id": pair, "x": a, "y": b, **res, "statement": claim, "lag_statement": lag_claim,
                              "lag_verdict": lag_verdict, "evidence_id": rec.id, "lag_evidence_id": lag_rec.id,
                              "hypothesis_id": hyp_id})

    # ---- data validation record ---------------------------------------------------
    prov = ds.provenance
    n_annual = sum(int(p["coverage"]["n_months"]) // 12 for p in prov)   # YYYY13 keys in the raw files
    dv = make_record(
        claim=(f"Input data checks passed: {len(monthly)} monthly values per variable for {start}-{end}, "
               f"{sum(sum(p['missing_values']['counts'].values()) for p in prov)} missing; annual-summary keys "
               f"(YYYY13) kept apart from months; units taken from the response; values are {ds.source}-sourced "
               f"from {len(prov)} raw file(s) whose SHA-256 matches the provenance record."),
        claim_type="computed_observation", region=region, period=period, variables=variables,
        method="Structural validation of the raw NASA POWER response", parameters={"n_raw_files": len(prov)},
        data_hash=ds.data_hash,
        result={"n_months": len(monthly), "annual_summary_keys_per_variable": n_annual,
                "raw_sha256": [p["sha256"] for p in prov], "units": {v: infos[v]["units"] for v in variables}},
        uncertainty={}, verdict="CHECKS_PASSED", engine_version=ENGINE_VERSION,
        supporting_evidence=[f"{c['check']}: {'passed' if c['passed'] else 'FAILED'}."
                             for c in prov[0]["validation_checks"]],
        limitations=["Validation covers structure and internal consistency, not the physical accuracy of MERRA-2."])
    evidence.insert(0, dv)

    # ---- what these data cannot tell us (prohibitions, not claims) ----------------
    cannot = []
    for v in variables:
        t = trends[v]
        ci = t["summary"]["primary_ci"]
        if t["verdict"] == "NO_SIGNIFICANT_TREND_DETECTED":
            cannot.append(f"Stability of {infos[v]['label']} cannot be concluded: the 95% interval of its slope "
                          f"runs from {f(ci[0])} to {f(ci[1])} {t['slope_units']}, which includes change in "
                          "either direction.")
        elif t["verdict"] == "FRAGILE_TREND":
            cannot.append(f"A lasting trend in {infos[v]['label']} cannot be concluded: "
                          + "; ".join(t["verdict_reasons"]) + ".")
    for r in relationships:
        cannot.append(f"A cause-and-effect link between {infos[r['x']]['label']} and {infos[r['y']]['label']} "
                      "cannot be concluded from co-variation of anomalies, however strong.")
    if relationships:
        cannot.append("Which variable influences which cannot be read from a lead or lag.")
        cannot.append("That the atmosphere has or lacks 'memory' cannot be concluded from monthly correlation "
                      "coefficients at a few lags.")
    cannot += [
        f"Nothing can be said about years outside {start}-{end} from this analysis alone.",
        "Values at a particular station or city inside the grid cell cannot be inferred, least of all where "
        "the terrain is uneven.",
        "That the same holds in other places cannot be concluded: one grid cell was analysed.",
    ]

    ev = [e.to_dict() for e in evidence]
    graph = build_graph(variables, infos, trends, relationships)
    episodes = build_episodes(infos, trends, relationships, ds.data_hash, period)

    return clean({
        "engine_version": ENGINE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "request": {"latitude": lat, "longitude": lon, "start": start, "end": end, "variables": variables,
                    "baseline": base},
        "region": region, "data_source": ds.source, "data_hash": ds.data_hash, "provenance": prov,
        "warnings": warnings, "variables": infos,
        "decision_rules": {"alpha": alpha, "max_lag": MAX_LAG, "n_perm": n_perm, "seed": SEED,
                           "trend_primary_test": "larger p of Hamed-Rao modified Mann-Kendall and AR(1)-adjusted "
                                                 "least squares, on annual means (both must reject)",
                           "fdr": "Benjamini-Hochberg within each declared family"},
        "series": {
            "months": [str(p) for p in monthly.index],
            "raw": {v: monthly[v].tolist() for v in variables},
            "climatology": {v: [float(clim[v][m]) for m in range(1, 13)] for v in variables},
            "anomaly": {v: anom[v].tolist() for v in variables},
            "detrended_anomaly": {v: detr[v].tolist() for v in variables},
        },
        "trends": trends, "relationships": relationships, "graph": graph, "evidence": ev,
        "episodes": episodes, "limitations": GENERAL_LIMITATIONS, "cannot_conclude": cannot,
    })


# ---------------------------------------------------------------------------
# Relationship graph and change episodes
# ---------------------------------------------------------------------------

def build_graph(variables: list[str], infos: dict, trends: dict, relationships: list[dict]) -> dict[str, Any]:
    """Nodes are variables; an edge exists only where a relationship was
    computed, and it carries the id of the evidence record behind it."""
    nodes = [{"id": v, "label": infos[v]["label"], "units": infos[v]["display_units"],
              "trend_verdict": trends[v]["verdict"], "slope": trends[v]["summary"]["primary_slope"],
              "slope_units": trends[v]["slope_units"], "evidence_id": trends[v]["evidence_id"]}
             for v in variables]
    edges = []
    for r in relationships:
        edges.append({
            "id": r["id"], "source": r["x"], "target": r["y"], "kind": "association (undirected)",
            "status": r["status"], "r_raw": r["raw"]["pearson_r"], "r_deseasonalized": r["deseasonalized"]["pearson_r"],
            "r_detrended": r["detrended"]["pearson_r"], "ci95": r["detrended"]["ci95_adjusted"],
            "peak_lag": r["lags"]["peak_lag"], "significant_nonzero_lags": r["lags"]["significant_nonzero_lags"],
            "lag_verdict": r["lag_verdict"], "sign_differs_between_seasons": r["by_season"]["sign_differs_between_seasons"],
            "evidence_id": r["evidence_id"], "lag_evidence_id": r["lag_evidence_id"],
            "hypothesis_id": r["hypothesis_id"],
        })
    return {"nodes": nodes, "edges": edges,
            "rule": "An edge is drawn only from a computed evidence record. Hypotheses annotate edges; "
                    "they never create one."}


def build_episodes(infos: dict, trends: dict, relationships: list[dict], data_hash: str,
                   period: list[int]) -> list[dict[str, Any]]:
    """EarthChangeEpisode: Observation -> Hypothesis -> Test -> Counterexample
    -> Revision -> Conclusion. Each step cites the evidence it rests on."""
    episodes = []
    for r in relationships:
        la, lb = infos[r["x"]]["label"], infos[r["y"]]["label"]
        raw, cyc = r["raw"]["pearson_r"], r["seasonal_cycle_only"]["pearson_r"]
        des, det = r["deseasonalized"]["pearson_r"], r["detrended"]["pearson_r"]
        ss = r["by_season"]["seasons"]
        if r["by_season"]["sign_differs_between_seasons"]:
            counter = ("The sign differs between seasons: "
                       + ", ".join(f"{k} {f(v['r'], 2)}" for k, v in ss.items()) + ".")
        else:
            weakest = min(ss.items(), key=lambda kv: abs(kv[1]["r"] or 0))
            counter = f"Weakest season: {weakest[0]} with r = {f(weakest[1]['r'], 2)}."
        shrink = abs(des) < 0.5 * abs(raw) or raw * des < 0
        episodes.append({
            "id": f"EP-REL-{r['id']}", "kind": "relationship", "subject": [r["x"], r["y"]],
            "data_version": data_hash, "period": period, "evidence_ids": [r["evidence_id"], r["lag_evidence_id"]],
            "steps": [
                {"stage": "Observation", "text": f"Raw monthly {la} and {lb} correlate at r = {f(raw, 2)}."},
                {"stage": "Hypothesis", "text": "Methodological hypothesis: the shared seasonal cycle, not "
                                                "year-to-year co-variation, accounts for most of the raw value."},
                {"stage": "Test", "text": f"Seasonal cycles alone give r = {f(cyc, 2)}. After removing the monthly "
                                          f"climatology r = {f(des, 2)}; after also removing linear trends r = {f(det, 2)}."},
                {"stage": "Counterexample", "text": counter},
                {"stage": "Revision", "text": ("The raw value overstated or mis-signed the link between anomalies; "
                                               "the interpretation is revised to the anomaly result."
                                               if shrink else
                                               "The anomaly result is close to the raw value; the interpretation stands."),
                 "reason": "seasonality removed"},
                {"stage": "Conclusion", "text": f"Status {r['status']}. Lag scan: {r['lag_verdict']}."},
            ]})
    for v, t in trends.items():
        s = t["summary"]
        win, loo = t["window_sensitivity"], t["leave_one_out"]
        counter_bits = [f"{win.get('n_positive')} of {win['n_windows']} sub-periods have a positive slope, "
                        f"{win.get('n_negative')} a negative one."]
        if loo["years_that_flip_significance"]:
            counter_bits.append("Significance flips when single years are left out: "
                                + ", ".join(str(y) for y in loo["years_that_flip_significance"]) + ".")
        if t.get("context"):
            c = t["context"]
            counter_bits.append(f"Over {c['period'][0]}-{c['period'][1]} the slope is {f(c['slope'])} "
                                f"(p = {fp(c['p'])}).")
        episodes.append({
            "id": f"EP-TREND-{v}", "kind": "trend", "subject": [v], "data_version": data_hash, "period": period,
            "evidence_ids": [t["evidence_id"]],
            "steps": [
                {"stage": "Observation", "text": f"Annual means of {infos[v]['label']} have a Theil-Sen slope of "
                                                 f"{f(s['primary_slope'])} {t['slope_units']}."},
                {"stage": "Hypothesis", "text": "Statistical hypothesis: the series has a monotonic trend over the period."},
                {"stage": "Test", "text": f"Mann-Kendall p = {fp(s['mann_kendall']['p'])}, autocorrelation-adjusted "
                                          f"p = {fp(s['primary_p'])}, false-discovery q = {fp(t['q'])}; 95% CI "
                                          f"{f(s['primary_ci'][0])} to {f(s['primary_ci'][1])}."},
                {"stage": "Counterexample", "text": " ".join(counter_bits)},
                {"stage": "Revision", "text": {"ROBUST_TREND": "No revision: the trend survives the checks applied.",
                                               "FRAGILE_TREND": "Downgraded from 'trend' to 'fragile': "
                                                                + "; ".join(t["verdict_reasons"]) + ".",
                                               "NO_SIGNIFICANT_TREND_DETECTED":
                                                   "Not established. The interval still allows changes in either "
                                                   "direction, so this is not a finding of stability."}[t["verdict"]],
                 "reason": "robustness checks"},
                {"stage": "Conclusion", "text": t["verdict"]},
            ]})
    return episodes


# ---------------------------------------------------------------------------
# Region comparison
# ---------------------------------------------------------------------------

def compare_regions(store: PowerStore, region_a: dict, region_b: dict, *, start: int, end: int,
                    variables: list[str], alpha: float = ALPHA) -> dict[str, Any]:
    """Same variables, same years, two places. Reports each trend, the trend of
    the difference series (do the places diverge?) and how strongly their
    monthly anomalies move together."""
    variables = list(dict.fromkeys(variables))
    da = store.load(region_a["latitude"], region_a["longitude"], start, end, variables)
    db = store.load(region_b["latitude"], region_b["longitude"], start, end, variables)
    if not da.monthly.index.equals(db.monthly.index):
        raise ValueError("the two regions are not on the same calendar")
    out = []
    for v in variables:
        ia = describe(v, da.norm.units[v], da.norm.longnames[v])
        ib = describe(v, db.norm.units[v], db.norm.longnames[v])
        if ia["units"] != ib["units"]:
            raise ValueError(f"unit mismatch between regions for {v}")
        aa, ab = annual_mean(da.monthly[v]), annual_mean(db.monthly[v])
        years = aa.index.to_numpy(dtype=float)
        sa = summarize_trend(years, aa.to_numpy(dtype=float), alpha)
        sb = summarize_trend(years, ab.to_numpy(dtype=float), alpha)
        diff = (aa - ab)
        sd = summarize_trend(years, diff.to_numpy(dtype=float), alpha)
        xa = detrend_linear(anomalies(da.monthly[v], monthly_climatology(da.monthly[v])))
        xb = detrend_linear(anomalies(db.monthly[v], monthly_climatology(db.monthly[v])))
        cc = correlate(xa, xb)
        opposite = sa["primary_slope"] * sb["primary_slope"] < 0
        both_sig = (sa["primary_p"] < alpha) and (sb["primary_p"] < alpha)
        diverge = sd["primary_p"] is not None and sd["primary_p"] < alpha
        if opposite and both_sig:
            verdict = "OPPOSITE_SIGNIFICANT_TRENDS"
        elif diverge:
            verdict = "REGIONS_DIVERGE"
        elif opposite:
            verdict = "OPPOSITE_SIGNS_NOT_SIGNIFICANT"
        else:
            verdict = "NO_SIGNIFICANT_DIFFERENCE_DETECTED"
        unit = ia["slope_units"]
        statement = (
            f"{ia['label']}, {start}-{end}: {region_a['name']} {f(sa['primary_slope'])} {unit} "
            f"(p = {fp(sa['primary_p'])}); {region_b['name']} {f(sb['primary_slope'])} {unit} "
            f"(p = {fp(sb['primary_p'])}). Difference series (first minus second): {f(sd['primary_slope'])} {unit} "
            f"(95% CI {f(sd['primary_ci'][0])} to {f(sd['primary_ci'][1])}, p = {fp(sd['primary_p'])}). "
            f"Monthly anomalies of the two places correlate at r = {f(cc.get('pearson_r'), 2)}.")
        enforce(statement, "computed_observation", significant=diverge)
        out.append({"variable": v, "label": ia["label"], "units": ia["display_units"], "slope_units": unit,
                    "years": [int(y) for y in years], "a": {"annual": aa.tolist(), "summary": sa},
                    "b": {"annual": ab.tolist(), "summary": sb},
                    "difference": {"annual": diff.tolist(), "summary": sd},
                    "anomaly_correlation": cc, "opposite_signs": bool(opposite), "verdict": verdict,
                    "statement": statement})
    return clean({
        "engine_version": ENGINE_VERSION, "period": [start, end],
        "region_a": {**region_a, "grid_cell_elevation_m": da.norm.elevation_m, "data_hash": da.data_hash,
                     "data_source": da.source},
        "region_b": {**region_b, "grid_cell_elevation_m": db.norm.elevation_m, "data_hash": db.data_hash,
                     "data_source": db.source},
        "variables": out,
        "limitations": [GENERAL_LIMITATIONS[0], GENERAL_LIMITATIONS[1],
                        "Annual means of two grid cells at different elevations differ in level; only their "
                        "changes over time are compared."],
    })
