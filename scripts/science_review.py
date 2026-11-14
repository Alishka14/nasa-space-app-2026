"""Scientific self-audit of the Pavlodar case (FINAL DELIVERY).

Recomputes every number of the audit from the raw NASA files and writes
docs/data/science_review.json and docs/SCIENCE_REVIEW.md. Nothing in the
review document is typed by hand except the prose around the numbers.

This audit was written by the same AI system that wrote the engines. It is a
self-check with stated tests, NOT an independent scientific validation.

Run from the repository root:  python scripts/science_review.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from earth_senses.evidence import load_independent_reports  # noqa: E402
from earth_senses.investigate import clean, investigate  # noqa: E402
from earth_senses.power_client import PowerStore  # noqa: E402
from earth_senses.relationships import anomalies, correlate, monthly_climatology  # noqa: E402
from earth_senses.trends import summarize_trend  # noqa: E402

PAV = {"lat": 52.29, "lon": 76.97, "region_name": "Pavlodar, Kazakhstan"}
V3 = ["T2M", "RH2M", "PRECTOTCORR"]
V4 = V3 + ["QV2M"]
PAIRS3 = ["T2M-PRECTOTCORR", "T2M-RH2M", "PRECTOTCORR-RH2M"]
SIM_SEED, SIM_N, SIM_YEARS = 20261114, 2000, 24


def r2(x: float | None) -> str:
    return "n/a" if x is None else f"{x:+.2f}"


def r3(x: float | None) -> str:
    return "n/a" if x is None else f"{x:+.3f}"


def p3(p: float | None) -> str:
    return "n/a" if p is None else ("< 0.001" if p < 0.001 else f"{p:.3f}")


def rel(inv: dict, pair: str) -> dict:
    return next(r for r in inv["relationships"] if r["id"] == pair)


def month_standardized(series) -> np.ndarray:
    """Anomalies divided by the standard deviation of their own calendar month."""
    a = anomalies(series, monthly_climatology(series))
    sd = a.groupby(a.index.month).transform("std")
    return (a / sd).to_numpy()


def false_positive_rates() -> list[dict]:
    """SYNTHETIC control: trend-free AR(1) noise, how often does each rule reject at 5%?"""
    rng = np.random.default_rng(SIM_SEED)
    years = np.arange(SIM_YEARS, dtype=float)
    rows = []
    for phi in (0.0, 0.3, 0.6):
        hits = {"classic": 0, "primary": 0}
        for _ in range(SIM_N):
            x = np.empty(SIM_YEARS)
            x[0] = rng.normal(0, 1 / np.sqrt(1 - phi ** 2))
            for i in range(1, SIM_YEARS):
                x[i] = phi * x[i - 1] + rng.normal()
            s = summarize_trend(years, x, 0.05)
            hits["classic"] += s["mann_kendall"]["p"] < 0.05
            hits["primary"] += s["primary_p"] < 0.05
        rows.append({"phi": phi, "classic_mann_kendall": hits["classic"] / SIM_N, "primary_rule": hits["primary"] / SIM_N})
    return rows


def main() -> int:
    store = PowerStore(ROOT / "data", allow_network=False)
    reports = load_independent_reports(ROOT / "data" / "independent_reports")
    inv3 = investigate(store, start=2001, end=2024, variables=V3, independent_reports=reports, **PAV)
    inv4 = investigate(store, start=2001, end=2024, variables=V4, independent_reports=reports, **PAV)
    early = investigate(store, start=1981, end=2000, variables=V3, **PAV)
    long_ = investigate(store, start=1981, end=2024, variables=V3, **PAV)
    ds = store.load(PAV["lat"], PAV["lon"], 2001, 2024, V4)
    m = ds.monthly

    # ---- 1. seasonality -----------------------------------------------------------------
    seasonality = []
    for r in inv4["relationships"]:
        a, b = r["x"], r["y"]
        std_r = r["month_standardized"]["pearson_r"]
        assert abs(std_r - correlate(month_standardized(m[a]), month_standardized(m[b]))["pearson_r"]) < 1e-9
        base = {}
        for lo, hi in ((2001, 2012), (2013, 2024)):
            xa = anomalies(m[a], monthly_climatology(m[a], (lo, hi)))
            xb = anomalies(m[b], monthly_climatology(m[b], (lo, hi)))
            base[f"{lo}-{hi}"] = correlate(xa, xb)["pearson_r"]
        seasonality.append({
            "pair": r["id"], "raw": r["raw"]["pearson_r"], "seasonal_cycles_only": r["seasonal_cycle_only"]["pearson_r"],
            "deseasonalized": r["deseasonalized"]["pearson_r"], "detrended": r["detrended"]["pearson_r"],
            "spearman_deseasonalized": r["deseasonalized"]["spearman_rho"], "month_standardized": std_r,
            "deseasonalized_with_baseline": base,
            "by_season": {k: v["r"] for k, v in r["by_season"]["seasons"].items()},
            "sign_differs_between_seasons": r["by_season"]["sign_differs_between_seasons"]})

    # ---- 2. significance and false discovery -----------------------------------------------
    trends = [{"variable": v, "slope": t["summary"]["primary_slope"], "units": t["slope_units"],
               "ci95": t["summary"]["primary_ci"], "mann_kendall_p": t["summary"]["mann_kendall"]["p"],
               "primary_p": t["summary"]["primary_p"], "q": t["q"], "verdict": t["verdict"],
               "lag1_autocorr_annual": t["summary"]["lag1_autocorr"],
               "flip_years": t["leave_one_out"]["years_that_flip_significance"]}
              for v, t in inv3["trends"].items()]
    pair_tests = [{"pair": r["id"], "r": r["detrended"]["pearson_r"], "ci95": r["detrended"]["ci95_adjusted"],
                   "n": r["detrended"]["n"], "n_eff": r["detrended"]["n_eff"],
                   "p_naive": r["detrended"]["p_naive"], "p_adjusted": r["detrended"]["p_adjusted"],
                   "p_permutation": r["negative_control_year_shuffle"]["p_permutation"],
                   "q_across_pairs": r["q_across_pairs"], "status": r["status"],
                   "lag1_x": r["detrended"]["lag1_autocorr_x"], "lag1_y": r["detrended"]["lag1_autocorr_y"]}
                  for r in inv3["relationships"]]
    pair_tests4 = [{"pair": r["id"], "r": r["detrended"]["pearson_r"], "p_adjusted": r["detrended"]["p_adjusted"],
                    "q_across_pairs": r["q_across_pairs"], "status": r["status"]} for r in inv4["relationships"]]
    lag_tests = [{"pair": r["id"], "n_tests": r["lags"]["n_tests"],
                  "naive_significant_nonzero": [x["lag"] for x in r["lags"]["rows"]
                                                if x["lag"] != 0 and x["p_naive"] is not None and x["p_naive"] < 0.05],
                  "significant_after_fdr": r["lags"]["significant_nonzero_lags"], "verdict": r["lag_verdict"]}
                 for r in inv3["relationships"]]
    n_tests = {"trend_tests": len(V3), "seasonal_trend_tests": len(V3) * 4, "pair_tests": len(PAIRS3),
               "lag_tests": sum(x["n_tests"] for x in lag_tests)}

    # ---- 3. autocorrelation -------------------------------------------------------------------
    fpr = false_positive_rates()

    # ---- 4. period dependence -----------------------------------------------------------------
    periods = []
    for pair in PAIRS3:
        row = {"pair": pair}
        for label, inv in (("1981-2000", early), ("2001-2024", inv3), ("1981-2024", long_)):
            r = rel(inv, pair)
            row[label] = {"detrended": r["detrended"]["pearson_r"], "ci95": r["detrended"]["ci95_adjusted"],
                          "status": r["status"]}
        st = rel(inv3, pair)["stability"]
        row["halves_2001_2024"] = [h["r"] for h in st["halves"]]
        row["ten_year_windows"] = [st["rolling_r_min"], st["rolling_r_max"]]
        periods.append(row)
    trend_periods = [{"variable": v, **{label: {"slope": inv["trends"][v]["summary"]["primary_slope"],
                                                "p": inv["trends"][v]["summary"]["primary_p"],
                                                "verdict": inv["trends"][v]["verdict"]}
                                        for label, inv in (("1981-2000", early), ("2001-2024", inv3), ("1981-2024", long_))}}
                     for v in V3]

    # ---- 5. correlation is not causation: what survives statistical control ----------------------
    partial = [{"pair": r["id"], "detrended": r["detrended"]["pearson_r"],
                "partial": [{"controls": p["controls"], "r": p["pearson_r"], "ci95": p["ci95_adjusted"]}
                            for p in r["partial"]],
                "structural_dependence": bool(r["structural_dependence"])} for r in inv4["relationships"]]

    # ---- 6. derived variable ---------------------------------------------------------------------
    chk = inv4["derived_checks"][0]

    # ---- 7. provenance -----------------------------------------------------------------------------
    prov = []
    for path in sorted((ROOT / "data" / "provenance").glob("*.provenance.json")):
        rec = json.loads(path.read_text())
        raw = json.loads((ROOT / "data" / rec["raw_path"]).read_bytes())
        prov.append({"file": rec["raw_path"], "sha256": rec["sha256"], "bytes": rec.get("size_bytes"),
                     "retrieved": rec["retrieval_timestamp"], "status": rec["validation_status"],
                     "parameters": rec["request"]["parameters"], "missing": rec["missing_values"]["counts"],
                     "api": raw["header"]["api"], "sources": raw["header"]["sources"]})

    out = clean({
        "generated_by": "scripts/science_review.py", "engine_version": inv3["engine_version"],
        "independence": "self-audit by the same AI system that wrote the code; not an independent validation",
        "data_hash_three_variables": inv3["data_hash"], "data_hash_four_variables": inv4["data_hash"],
        "seasonality": seasonality, "trend_tests": trends, "pair_tests": pair_tests,
        "pair_tests_four_variables": pair_tests4, "lag_tests": lag_tests, "number_of_tests": n_tests,
        "false_positive_rates_synthetic": {"seed": SIM_SEED, "n_sim": SIM_N, "n_years": SIM_YEARS, "rows": fpr},
        "period_dependence": {"relationships": periods, "trends": trend_periods},
        "partial_correlations": partial,
        "derived_variable_check": {k: chk[k] for k in ("assumed_pressure_hpa", "reconstruction",
                                                       "linear_fit_of_anomalies", "verdict", "evidence_id")},
        "provenance": prov,
    })
    (ROOT / "docs" / "data").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs" / "data" / "science_review.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    # =============================== the document ===============================
    S = {s["pair"]: s for s in out["seasonality"]}
    P = {p["pair"]: p for p in out["partial_correlations"]}
    T = {t["variable"]: t for t in out["trend_tests"]}
    PT = {p["pair"]: p for p in out["pair_tests"]}
    PD = {p["pair"]: p for p in out["period_dependence"]["relationships"]}
    TP = {t["variable"]: t for t in out["period_dependence"]["trends"]}
    rc, fit = chk["reconstruction"], chk["linear_fit_of_anomalies"]

    def held(pair: str, controls: list[str]) -> dict:
        return next(x for x in P[pair]["partial"] if x["controls"] == controls)

    L: list[str] = []
    add = L.append
    add("# Science Review — MIZAN + BATYR AGA + Ghost Busters audit")
    add("")
    add("> Generated by `scripts/science_review.py` from the raw NASA files. Numbers are recomputed on every run; "
        "machine-readable copy in `docs/data/science_review.json`. Do not edit by hand.")
    add("")
    add("## What this review is, and what it is not")
    add("")
    add("- It is a **self-audit**: the same AI system that wrote the engines wrote the checks below. Under the "
        "team's MIZAN rules that is **not independent scientific validation**, and no status is raised because of it. "
        "Every evidence record stays `OBSERVED` or `HYPOTHESIS`.")
    add("- An earlier verification pass by another session of the same model is likewise **not independent**.")
    add("- Gemini's report is an independent *computation* of sixteen numbers. Where our numbers agree with it, those "
        "single values are marked as replicated. Gemini's interpretations are not adopted, and nothing in the engines "
        "was tuned to match it (`docs/GEMINI_REPRODUCTION.md`).")
    add("- **Human scientific review: NOT DONE.** It is the first item under *Open items*.")
    add("")
    add("Case audited: Pavlodar grid cell (52.29 N, 76.97 E), 2001–2024, NASA POWER monthly data (MERRA-2).")
    add("")
    add("## Verdict by audit question")
    add("")
    add("| # | Question | Result | Where |")
    add("|---|---|---|---|")
    add("| 1 | Is a correlation produced by the shared seasonal cycle reported as a relationship? | **No.** Raw "
        "values are shown but every status is decided on detrended anomalies. | §1 |")
    add("| 2 | Are significance and multiple testing handled? | **Yes, with one gap closed in this review** "
        "(false-discovery control across pairs was missing; added, no status changed). | §2 |")
    add("| 3 | Is autocorrelation accounted for? | **Partly.** Effective sample sizes and a year-block permutation "
        "control are used; the trend rule is still too liberal for strongly persistent series. | §3 |")
    add("| 4 | Do results depend on the period? | **Yes, and it is reported.** The humidity trend reverses sign "
        "between 1981–2000 and 2001–2024. | §4 |")
    add("| 5 | Is correlation presented as causation? | **No.** The guard blocks causal wording; explanations are "
        "labelled hypotheses; partial correlations are reported as correlations. | §5 |")
    add("| 6 | Is RH2M treated as an independent variable although it is computed from temperature? | "
        "**It was. Fixed in this review**: the edge is flagged and the dependence is measured. | §6 |")
    add("| 7 | Can every number be traced to NASA bytes? | **Yes for the four bundled files** (SHA-256). A live "
        "request from the backend to NASA was **NOT RUN** in the build environment. | §7 |")
    add("")

    # ---- 1
    add("## 1. Spurious correlation from seasonality")
    add("")
    add("Two variables that both follow the calendar correlate strongly even if their year-to-year departures are "
        "unrelated. The engine therefore reports four numbers per pair and decides on the last one.")
    add("")
    add("| Pair | Raw | Seasonal cycles alone | Deseasonalized | Detrended | Spearman (deseas.) | Month-standardized |")
    add("|---|---|---|---|---|---|---|")
    for s in out["seasonality"]:
        add(f"| {s['pair']} | {r3(s['raw'])} | {r3(s['seasonal_cycles_only'])} | {r3(s['deseasonalized'])} | "
            f"{r3(s['detrended'])} | {r3(s['spearman_deseasonalized'])} | {r3(s['month_standardized'])} |")
    add("")
    pr, tr_, tp = S["PRECTOTCORR-RH2M"], S["T2M-RH2M"], S["T2M-PRECTOTCORR"]
    add(f"- **Precipitation–humidity:** raw {r3(pr['raw'])}, but the two seasonal cycles alone give "
        f"{r3(pr['seasonal_cycles_only'])}: the negative raw value is the calendar (humid winters with little "
        f"precipitation, drier-air summers with more). With the calendar removed the sign reverses to "
        f"{r3(pr['deseasonalized'])}.")
    add(f"- **Temperature–humidity:** raw {r3(tr_['raw'])} is almost entirely the seasonal cycle "
        f"({r3(tr_['seasonal_cycles_only'])}); the anomaly association is {r3(tr_['deseasonalized'])}.")
    add(f"- **Temperature–precipitation:** raw {r3(tp['raw'])} becomes {r3(tp['deseasonalized'])}; the sign differs "
        "between seasons (" + ", ".join(f"{k} {r2(v)}" for k, v in tp["by_season"].items()) + "), so the all-year "
        "number hides opposite behaviour.")
    add("- **Robustness of the removal.** Rank correlation (Spearman) gives the same signs and similar sizes, so "
        "outliers are not responsible. A climatology taken from only one half of the record changes the "
        f"deseasonalized precipitation–humidity value from {r3(pr['deseasonalized'])} to "
        f"{r3(pr['deseasonalized_with_baseline']['2001-2012'])} (the two halves give the same number by symmetry).")
    add(f"- **Finding: the pooled value is weighted towards the warm season.** When each calendar month's anomalies "
        f"are divided by that month's own standard deviation, so that every month counts equally, "
        f"precipitation–humidity falls from {r3(pr['deseasonalized'])} to {r3(pr['month_standardized'])}. The sign "
        "is unchanged, but the all-year number is carried by months with large precipitation variance. By season: "
        + ", ".join(f"{k} {r2(v)}" for k, v in pr["by_season"].items())
        + ". The association is a spring-to-autumn feature and is absent in winter; the demo and the submission "
          "text say so.")
    add("- **Residual risk.** A fixed monthly climatology does not remove a seasonal cycle whose shape changes over "
        "the record; by-season results are reported for that reason.")
    add("")

    # ---- 2
    add("## 2. Significance and false-discovery control")
    add("")
    add(f"One default investigation runs {n_tests['trend_tests']} annual trend tests, "
        f"{n_tests['seasonal_trend_tests']} seasonal trend tests, {n_tests['pair_tests']} pair tests and "
        f"{n_tests['lag_tests']} lag tests. Benjamini–Hochberg is applied inside each family.")
    add("")
    add("| Variable | Theil–Sen slope | 95% CI | Mann–Kendall p | Reported p | q | Verdict |")
    add("|---|---|---|---|---|---|---|")
    for t in out["trend_tests"]:
        add(f"| {t['variable']} | {r3(t['slope'])} {t['units']} | {r3(t['ci95'][0])} to {r3(t['ci95'][1])} | "
            f"{p3(t['mann_kendall_p'])} | {p3(t['primary_p'])} | {p3(t['q'])} | {t['verdict']} |")
    add("")
    rh = T["RH2M"]
    add(f"- The only nominally significant trend is relative humidity (Mann–Kendall p = {p3(rh['mann_kendall_p'])}). "
        f"After false-discovery control q = {p3(rh['q'])}, and leaving out any one of the years "
        f"{', '.join(str(y) for y in rh['flip_years'])} changes whether it is significant. It is reported as "
        "`FRAGILE_TREND`, not as a trend.")
    add("- For temperature and precipitation the result is *no significant trend detected*, which is not a finding "
        "of stability: the confidence intervals include change in either direction.")
    add("")
    add("| Pair | Detrended r | 95% CI | n | Effective n | Naive p | Adjusted p | Year-shuffle p | q across pairs | Status |")
    add("|---|---|---|---|---|---|---|---|---|---|")
    for p in out["pair_tests"]:
        add(f"| {p['pair']} | {r3(p['r'])} | {r2(p['ci95'][0])} to {r2(p['ci95'][1])} | {p['n']} | {p['n_eff']:.0f} | "
            f"{p3(p['p_naive'])} | {p3(p['p_adjusted'])} | {p3(p['p_permutation'])} | {p3(p['q_across_pairs'])} | "
            f"{p['status']} |")
    add("")
    add("- **Gap found and closed:** pair tests were not corrected across pairs. `q across pairs` is now computed "
        "and shown; with three pairs and with six pairs (specific humidity added) no status changes"
        + ("." if all(p["q_across_pairs"] is not None and p["q_across_pairs"] < 0.05
                      for p in out["pair_tests_four_variables"] if p["status"] in ("SUPPORTED", "WEAK"))
           else ", but at least one pair is no longer below 0.05 after correction (a warning is raised in the app)."))
    wk = PT["T2M-PRECTOTCORR"]
    add(f"- The temperature–precipitation association (r = {r3(wk['r'])}, upper confidence bound "
        f"{r3(wk['ci95'][1])}) is statistically detectable and practically negligible; it is labelled `WEAK`.")
    add("- Lag scans, non-zero lags passing an uncorrected test → still significant after correction: "
        + "; ".join(f"{x['pair']} {len(x['naive_significant_nonzero'])} → {len(x['significant_after_fdr'])}"
                    for x in out["lag_tests"]) + ".")
    add("- Thresholds (α = 0.05, |r| ≥ 0.2 for `SUPPORTED`) were fixed in code before the Pavlodar numbers were "
        "looked at and are the same for every region.")
    add("")

    # ---- 3
    add("## 3. Autocorrelation")
    add("")
    lag1 = {}
    for r in inv3["relationships"]:
        lag1[r["x"]] = r["detrended"]["lag1_autocorr_x"]
        lag1[r["y"]] = r["detrended"]["lag1_autocorr_y"]
    add("- **Monthly anomalies.** Lag-1 autocorrelation of the detrended anomalies: "
        + ", ".join(f"{v} {a:+.2f}" for v, a in lag1.items())
        + ". Effective sample sizes are " + ", ".join(f"{p['n_eff']:.0f}" for p in out["pair_tests"])
        + " of 288 months for the three pairs. The year-block permutation control, which keeps each variable's "
          "within-year structure intact, agrees with the adjusted p-values.")
    add("- **Annual means.** Lag-1 autocorrelation: "
        + ", ".join(f"{t['variable']} {t['lag1_autocorr_annual']:+.2f}" for t in out["trend_tests"])
        + ". The reported trend p is the larger of the Hamed–Rao modified Mann–Kendall p and the AR(1)-adjusted "
          "least-squares p.")
    add(f"- **Known weakness, measured.** SYNTHETIC control, {SIM_N} trend-free AR(1) series of {SIM_YEARS} years "
        "per row; share rejected at the 5% level (should be 5%):")
    add("")
    add("| Lag-1 autocorrelation of the noise | Classic Mann–Kendall | Reported rule |")
    add("|---|---|---|")
    for row in out["false_positive_rates_synthetic"]["rows"]:
        add(f"| {row['phi']:.1f} | {100 * row['classic_mann_kendall']:.1f}% | {100 * row['primary_rule']:.1f}% |")
    add("")
    add("  The reported rule is better than the classic test but still rejects too often when persistence is strong. "
        "With 24 annual values the autocorrelation itself is poorly estimated, which no correction fully repairs. "
        "This is why a significant p alone never yields `ROBUST_TREND`: the window and leave-one-out checks must "
        "also pass.")
    add("")

    # ---- 4
    add("## 4. Dependence on the period")
    add("")
    add("| Variable | 1981–2000 slope (p) | 2001–2024 slope (p) | 1981–2024 slope (p) |")
    add("|---|---|---|---|")
    for v in V3:
        t = TP[v]
        add(f"| {v} | " + " | ".join(f"{r3(t[k]['slope'])} ({p3(t[k]['p'])})" for k in ("1981-2000", "2001-2024", "1981-2024")) + " |")
    add("")
    add(f"- Relative humidity: {r3(TP['RH2M']['1981-2000']['slope'])} per year in 1981–2000 against "
        f"{r3(TP['RH2M']['2001-2024']['slope'])} in 2001–2024, and {r3(TP['RH2M']['1981-2024']['slope'])} over the "
        "whole record. A statement about \"the humidity trend\" without its period would be wrong.")
    add("")
    add("| Pair | 1981–2000 | 2001–2024 | 1981–2024 | Halves of 2001–2024 | 10-year windows |")
    add("|---|---|---|---|---|---|")
    for pair in PAIRS3:
        d = PD[pair]
        add(f"| {pair} | " + " | ".join(f"{r2(d[k]['detrended'])} {d[k]['status']}" for k in ("1981-2000", "2001-2024", "1981-2024"))
            + f" | {r2(d['halves_2001_2024'][0])} / {r2(d['halves_2001_2024'][1])} | "
              f"{r2(d['ten_year_windows'][0])} to {r2(d['ten_year_windows'][1])} |")
    add("")
    add("- The anomaly relationships are far more stable across periods than the trends. The 1981–2000 file is a "
        "separate NASA retrieval with its own SHA-256; MERRA-2's observing system changed over these decades and no "
        "homogeneity test is applied, so cross-period differences can be partly a property of the reanalysis.")
    add("")

    # ---- 5
    add("## 5. Correlation versus causation")
    add("")
    add("- Every published sentence passes the MIZAN Guard (`guard.py`), which rejects causal verbs, proof language, "
        "\"no change\" conclusions from a non-significant test, and reading a lag as a direction of influence, in "
        "English and Russian. The test suite includes adversarial sentences.")
    add("- Physical explanations exist only as records with status `HYPOTHESIS`, verdict `UNTESTED`, each with a "
        "proposed test. They annotate graph edges and never create one.")
    add("- New in this review: **partial correlations** of detrended anomalies with four variables in play. They "
        "show whether an association remains when another series is held fixed statistically; they are still "
        "correlations and assume linear relations.")
    add("")
    add("| Pair | Nothing held fixed | Held fixed | Partial r | 95% CI |")
    add("|---|---|---|---|---|")
    for p in out["partial_correlations"]:
        for x in p["partial"]:
            add(f"| {p['pair']}{' ⚙' if p['structural_dependence'] else ''} | {r3(p['detrended'])} | "
                f"{' + '.join(x['controls'])} | {r3(x['r'])} | {r2(x['ci95'][0])} to {r2(x['ci95'][1])} |")
    add("")
    h_t = held("PRECTOTCORR-RH2M", ["T2M"])
    h_tq = held("PRECTOTCORR-RH2M", ["T2M", "QV2M"])
    h_w = held("T2M-PRECTOTCORR", ["RH2M"])
    add(f"- **Precipitation–humidity survives.** {r3(P['PRECTOTCORR-RH2M']['detrended'])} becomes {r3(h_t['r'])} "
        f"with temperature held fixed and {r3(h_tq['r'])} (95% CI {r2(h_tq['ci95'][0])} to {r2(h_tq['ci95'][1])}) "
        "with temperature and specific humidity both held fixed. It is therefore not merely temperature acting on "
        "relative humidity. It remains an association inside one reanalysis.")
    add(f"- **Temperature–precipitation does not survive.** With relative humidity held fixed it is {r3(h_w['r'])} "
        f"(95% CI {r2(h_w['ci95'][0])} to {r2(h_w['ci95'][1])}, includes zero).")
    add("- What still cannot be concluded: which variable influences which; that wetter months *make* the air more "
        "humid (both may follow the same air masses); that the atmosphere has or lacks \"memory\" on the basis of "
        "lag coefficients.")
    add("")

    # ---- 6
    add("## 6. RH2M is a computed variable tied to temperature")
    add("")
    add("Relative humidity is the ratio of the water vapour present to the amount the air could hold at its "
        "temperature. NASA POWER's methodology page states that its relative humidity is calculated from MERRA-2 "
        "pressure, temperature and specific humidity, over water only "
        "([POWER: Relative Humidity](https://power.larc.nasa.gov/docs/methodology/meteorology/relative-humidity/)). "
        "Before this review the temperature–humidity edge was presented like any other association.")
    add("")
    add("**Check (nothing fitted).** Relative humidity was rebuilt from monthly T2M and QV2M with the Magnus formula "
        f"at a constant standard-atmosphere pressure of {chk['assumed_pressure_hpa']:.1f} hPa for the grid cell's "
        "elevation, and compared with the RH2M values in the NASA file:")
    add("")
    add(f"- raw series: r = {r3(rc['r_raw'])}, mean absolute difference {rc['mean_abs_error_pp']:.2f} percentage "
        f"points (bias {rc['bias_pp']:+.2f});")
    add(f"- detrended anomalies: r = {r3(rc['r_detrended_anomalies'])};")
    add("- share of the variance of relative-humidity anomalies reproduced by a linear combination of temperature "
        f"and specific-humidity anomalies: {100 * fit['overall']['r_squared']:.0f}% over all months; by season "
        + ", ".join(f"{k} {100 * v['r_squared']:.0f}%" for k, v in fit["by_season"].items()) + ".")
    add("")
    tq = P["T2M-QV2M"]["detrended"]
    t_rh_q = held("T2M-RH2M", ["QV2M"])
    add("**Reading.**")
    add("")
    add(f"- In summer relative humidity carries almost no information beyond temperature and moisture content "
        f"({100 * fit['by_season']['JJA']['r_squared']:.0f}%). The low winter figure "
        f"({100 * fit['by_season']['DJF']['r_squared']:.0f}%) does **not** show independent information: the "
        "check works on monthly means with a constant pressure and a *linear* fit, while the true relation is "
        f"strongly non-linear at low temperatures (mean absolute difference of the reconstruction in winter "
        f"{rc['by_season_mean_abs_error_pp']['DJF']:.1f} percentage points against "
        f"{rc['by_season_mean_abs_error_pp']['JJA']:.1f} in summer). Which of these accounts for the winter "
        "mismatch was not tested.")
    add(f"- Warmer-than-usual months hold **more** water vapour (temperature–specific humidity {r3(tq)}) and yet "
        f"have **lower** relative humidity ({r3(P['T2M-RH2M']['detrended'])}); with moisture content held fixed "
        f"the temperature–relative humidity value strengthens to {r3(t_rh_q['r'])}. That is what the definition "
        "of relative humidity predicts, so the temperature–humidity edge is **partly an identity, not a "
        "discovery**.")
    add("- Consequences in the product: the edge carries a ⚙ *built-in dependence* flag in the graph, the pair card "
        "and the evidence record; the episode timeline lists it as a counterexample; *What these data cannot tell "
        "us* states it; a `DERIVED_VARIABLE_CONFIRMED` evidence record holds the numbers above.")
    add("- The proposed explanation of the temperature–humidity association stays a `HYPOTHESIS`. The check above is "
        "consistent with it and does not prove it.")
    add("")

    # ---- 7
    add("## 7. Provenance of the NASA data")
    add("")
    add("| File | Parameters | Retrieved (UTC) | SHA-256 | Missing | Status |")
    add("|---|---|---|---|---|---|")
    for p in out["provenance"]:
        add(f"| `{Path(p['file']).name}` | {', '.join(p['parameters'])} | {p['retrieved']} | `{p['sha256'][:16]}…` | "
            f"{sum(p['missing'].values())} | {p['status']} |")
    add("")
    add("- Source: NASA POWER Monthly and Annual API "
        f"{out['provenance'][0]['api']['version']} (`power.larc.nasa.gov`), community AG. The response headers name "
        "MERRA-2 as the source. These are **model reanalysis values for one grid cell of about 0.5° × 0.625°**, not "
        "station measurements.")
    add("- Chain of custody: the build sandbox had no route to NASA, so each response was fetched in the team's "
        "Chrome browser, its SHA-256 was computed in the browser on the response body, the body was stored in "
        "`data/raw/` and re-hashed. `scripts/build_provenance.py` fails if any byte differs. The engine re-verifies "
        "the hash every time a file is read.")
    add("- The API's own annual values (`YYYY13` keys) are kept apart from the twelve months and are reproduced by "
        "our day-weighted means to within rounding.")
    add("- **Live path NOT RUN.** The code path in which the backend itself calls NASA (`PowerStore._fetch_live`) "
        "is covered by tests with a stubbed transport only. It has not been exercised against the real service "
        "from the build environment.")
    add("- **GPM IMERG.** The POWER service accepts the parameter `IMERG_PRECTOT`, but for this point it returned "
        "the missing-value code (−999) for all 288 months and all 24 annual keys, and its header lists MERRA-2 as "
        "the only source. The file is stored as evidence of that; the engine refuses to analyse the variable "
        "(HTTP 422, no numbers). An independent satellite check of precipitation is therefore **NOT AVAILABLE** by "
        "this route. NASA Giovanni / GES DISC was **NOT RUN**: access from the build environment was not permitted.")
    add("- Consequence: all four variables come from one model. Relationships between them may be tighter than in "
        "nature, and none has been confirmed against independent observations.")
    add("")

    add("## Changes made because of this review")
    add("")
    add("| Finding | Change | Effect on existing results |")
    add("|---|---|---|")
    add("| Temperature–humidity edge shown as an ordinary association although RH2M is computed from temperature | "
        "`DERIVED` registry, ⚙ flag on the edge, counterevidence line, derived-variable evidence record when QV2M "
        "is selected | Numbers unchanged; interpretation restricted |")
    add("| No false-discovery control across pairs | `q across pairs` computed and shown; warning if a detectable "
        "pair fails it | No status changed |")
    add("| No way to ask whether an association survives a third variable | Partial correlations of detrended "
        "anomalies for every pair | New numbers only |")
    add("| A NASA variable that is entirely missing would have crashed the consistency check | File is registered "
        "with status `VALIDATED_WITH_MISSING_DATA`; the variable is refused | None |")
    add("| The data-check sentence counted gaps of variables that were not requested | Count restricted to the "
        "requested variables | None on bundled cases |")
    add("| The test proposed in the temperature–humidity hypothesis was worded imprecisely | Reworded; the test is "
        "now implemented as the derived-variable check | Wording only |")
    add("| Test collection failed without `pymannkendall` (another verifier reproduced 105 of 129) | The five "
        "reference tests are skipped with a reason when the package is absent | None |")
    add("| Graph labels overlapped with four variables | Layout for four or more nodes | Display only |")
    add("")
    add("Evidence ids and the data hash of the default three-variable investigation are unchanged "
        f"(`{out['data_hash_three_variables'][:16]}…`); a test pins them.")
    add("")
    add("## Open items")
    add("")
    add("1. **Review by a human climate scientist — NOT DONE.**")
    add("2. Independent observational confirmation (stations, satellite precipitation) — NOT DONE; IMERG via POWER "
        "returned no data for this point.")
    add("3. Homogeneity (change-point) testing of the reanalysis series — NOT DONE.")
    add("4. Trend inference under strong persistence remains somewhat liberal (§3).")
    add("5. Partial correlations and the anomaly fit are linear; the temperature–humidity relation is not, "
        "especially in winter (§6).")
    add("6. One grid cell. Nothing here transfers to other places without rerunning the analysis there.")
    add("7. Live NASA request from the backend — NOT RUN in the build environment.")
    add("")
    (ROOT / "docs" / "SCIENCE_REVIEW.md").write_text("\n".join(L), encoding="utf-8")
    print("wrote docs/SCIENCE_REVIEW.md and docs/data/science_review.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
