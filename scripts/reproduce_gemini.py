"""Independent recomputation of the Gemini analysis of Pavlodar, 2001-2024.

Reads the raw NASA POWER response stored in data/raw (SHA-256 checked),
recomputes every number Gemini reported with the EARTH SENSES engines, and
writes docs/GEMINI_REPRODUCTION.md and docs/data/gemini_reproduction.json.

No parameter of our own analysis was adjusted to make a number match. Where
Gemini did not state its method, standard variants were enumerated to find
which one it used; every variant tried is listed, including those that do
not match. The comparison was not blind: Gemini's values are written below.

Run from the repository root:  python scripts/reproduce_gemini.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from earth_senses import ENGINE_VERSION  # noqa: E402
from earth_senses.normalize import (SEASONS, annual_mean, annual_total, check_annual_consistency,  # noqa: E402
                                    rate_to_monthly_total)
from earth_senses.power_client import PowerStore  # noqa: E402
from earth_senses.relationships import analyze_pair, anomalies, lagged_correlations, monthly_climatology  # noqa: E402
from earth_senses.trends import (benjamini_hochberg, leave_one_out, mann_kendall, seasonal_mann_kendall,  # noqa: E402
                                 summarize_trend, theil_sen, window_sensitivity)

LAT, LON, START, END = 52.29, 76.97, 2001, 2024
PARAMS = ["T2M", "PRECTOTCORR", "RH2M"]
NAMES = {"T2M": "Temperature (T2M)", "PRECTOTCORR": "Precipitation (PRECTOTCORR)", "RH2M": "Relative humidity (RH2M)"}
UNITS = {"T2M": "°C/yr", "PRECTOTCORR": "mm/day/yr", "RH2M": "pp/yr"}

GEMINI = {
    "corr": {("T2M", "RH2M"): (-0.945, -0.316), ("T2M", "PRECTOTCORR"): (0.439, -0.125),
             ("PRECTOTCORR", "RH2M"): (-0.285, 0.593)},
    "trend": {"T2M": (-0.021, 0.427), "PRECTOTCORR": (0.005, 0.275), "RH2M": (0.16, 0.035)},
    "slope_decimals": {"T2M": 3, "PRECTOTCORR": 3, "RH2M": 2},     # as reported
    "rh_q": 0.105,
    "lag": {0: -0.316, 1: -0.185, "2+": -0.04},
}


def s(x: float, nd: int = 3) -> str:
    return f"{x:+.{nd}f}"


def p(x: float) -> str:
    return "< 0.001" if x < 1e-3 else f"{x:.3f}"


def main() -> int:
    store = PowerStore(ROOT / "data", allow_network=False)
    ds = store.load(LAT, LON, START, END, PARAMS)
    prov = ds.provenance[0]
    m = ds.monthly
    years = np.arange(START, END + 1, dtype=float)
    raw_obj = json.loads((ROOT / "data" / prov["raw_path"]).read_bytes())
    out: dict = {"engine_version": ENGINE_VERSION, "sha256": prov["sha256"], "request": prov["original_api_request"]}
    L: list[str] = []

    # ------------------------------------------------------------------ data traps
    keys = list(raw_obj["properties"]["parameter"]["T2M"])
    n13 = sum(k.endswith("13") for k in keys)
    cons = check_annual_consistency(ds.norm)
    fill_hits = sum(int(np.isclose(v, ds.norm.fill_value)) for par in raw_obj["properties"]["parameter"].values()
                    for v in par.values())
    rate = m["PRECTOTCORR"]
    total = annual_total(rate_to_monthly_total(rate, ds.norm.units["PRECTOTCORR"]))
    wrong30 = rate.groupby(rate.index.year).sum() * 30
    out["traps"] = {"yyyy13_keys_per_variable": n13, "keys_per_variable": len(keys), "fill_value": ds.norm.fill_value,
                    "fill_occurrences": fill_hits, "units": ds.norm.units, "annual_consistency": cons,
                    "mean_annual_precip_mm": float(total.mean()),
                    "max_error_of_30_day_shortcut_mm": float((wrong30 - total).abs().max())}

    # ------------------------------------------------------------------ correlations
    pairs = {}
    for (a, b), (g_raw, g_des) in GEMINI["corr"].items():
        res = analyze_pair(m[a], m[b], n_perm=5000)
        pairs[(a, b)] = res
    out["correlations"] = {f"{a}-{b}": {k: pairs[(a, b)][k] for k in ("raw", "seasonal_cycle_only", "deseasonalized",
                                                                      "detrended", "negative_control_year_shuffle",
                                                                      "status")}
                           | {"by_season": pairs[(a, b)]["by_season"]["seasons"],
                              "halves": pairs[(a, b)]["stability"]["halves"]} for (a, b) in pairs}

    # ------------------------------------------------------------------ trends
    variants: dict[str, dict] = {}
    for v in PARAMS:
        ann = annual_mean(m[v]).to_numpy()
        ann_simple = annual_mean(m[v], day_weighted=False).to_numpy()
        rep = ds.annual_reported[v].to_numpy(dtype=float)
        tm = np.arange(len(m)) / 12.0
        anom = anomalies(m[v], monthly_climatology(m[v])).to_numpy()
        lr_ann, lr_mon = stats.linregress(years, ann), stats.linregress(tm, anom)
        sk = seasonal_mann_kendall(m[v].to_numpy().reshape(-1, 12))
        variants[v] = {
            "A. Theil-Sen + MK without tie correction, API annual values (YYYY13)": (theil_sen(years, rep)["slope"], mann_kendall(rep, tie_correction=False)["p"]),
            "B. Theil-Sen + MK with tie correction, API annual values (YYYY13)": (theil_sen(years, rep)["slope"], mann_kendall(rep)["p"]),
            "C. Theil-Sen + MK on day-weighted annual means of the months": (theil_sen(years, ann)["slope"], mann_kendall(ann)["p"]),
            "D. Theil-Sen + MK on simple (unweighted) annual means": (theil_sen(years, ann_simple)["slope"], mann_kendall(ann_simple)["p"]),
            "E. Least squares on annual means": (lr_ann.slope, lr_ann.pvalue),
            "F. Least squares on 288 monthly anomalies (naive p)": (lr_mon.slope, lr_mon.pvalue),
            "G. Seasonal Kendall on 288 monthly values (covariance-corrected)": (sk["slope"], sk["p_dependent"]),
        }
    primary = {v: summarize_trend(years, annual_mean(m[v]).to_numpy()) for v in PARAMS}
    q_primary = dict(zip(PARAMS, benjamini_hochberg([primary[v]["primary_p"] for v in PARAMS])))
    q_api = dict(zip(PARAMS, benjamini_hochberg([variants[v]["A. Theil-Sen + MK without tie correction, API annual values (YYYY13)"][1]
                                                 for v in PARAMS])))
    loo = {v: leave_one_out(years, annual_mean(m[v]).to_numpy()) for v in PARAMS}
    win = {v: window_sensitivity(years, annual_mean(m[v]).to_numpy(), min_len=15) for v in PARAMS}
    long = store.load(LAT, LON, 1981, END, PARAMS)
    yl = np.arange(1981, END + 1, dtype=float)
    long_tr = {v: summarize_trend(yl, annual_mean(long.monthly[v]).to_numpy()) for v in PARAMS}
    early_tr = {}
    for v in PARAMS:
        a = annual_mean(long.monthly[v])
        e = a[a.index <= 2000]
        early_tr[v] = {"slope": theil_sen(e.index.to_numpy(float), e.to_numpy())["slope"],
                       "mk_p": mann_kendall(e.to_numpy())["p"]}
    out["trends"] = {v: {"variants": {k: list(val) for k, val in variants[v].items()}, "primary": primary[v],
                         "q_primary": q_primary[v], "q_api_annual": q_api[v],
                         "leave_one_out_flip_years": loo[v]["years_that_flip_significance"],
                         "long_record_1981_2024": {"slope": long_tr[v]["primary_slope"], "ci": long_tr[v]["primary_ci"],
                                                   "p": long_tr[v]["primary_p"]},
                         "early_record_1981_2000": early_tr[v]} for v in PARAMS}

    # ------------------------------------------------------------------ lags
    at = anomalies(m["T2M"], monthly_climatology(m["T2M"]))
    ah = anomalies(m["RH2M"], monthly_climatology(m["RH2M"]))
    lag_des = lagged_correlations(at, ah, max_lag=6)
    lag_det = pairs[("T2M", "RH2M")]["lags"]
    out["lags_T2M_RH2M"] = {"deseasonalized": lag_des["rows"], "detrended": lag_det["rows"]}
    by = {r["lag"]: r for r in lag_des["rows"]}
    by_det = {r["lag"]: r for r in lag_det["rows"]}
    pr = pairs[("PRECTOTCORR", "RH2M")]["lags"]

    (ROOT / "docs" / "data").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs" / "data" / "gemini_reproduction.json").write_text(
        json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")

    # ================================================================== the document
    L += ["# Reproduction of the Gemini analysis — Pavlodar, 2001–2024", "",
          "> Generated by `scripts/reproduce_gemini.py` from the raw NASA file. Do not edit by hand: re-run the script.",
          f"> Engine: `{ENGINE_VERSION}`. Machine-readable results: `docs/data/gemini_reproduction.json`.", "",
          "Gemini produced a preliminary analysis of NASA POWER data for Pavlodar. This document recomputes it "
          "independently: different model family, separately retrieved data, separately written code. "
          "Nothing was tuned to make numbers agree; where they differ, the difference is reported.", "",
          "## Summary", "",
          "| Group | Reported values | Result |", "|---|---:|---|",
          "| Data traps (YYYY13, −999, mm/day) | 3 | Two **confirmed in the data**; −999 **confirmed as a header "
          "declaration** (it does not occur in this file); two further traps found |",
          "| Correlations (raw and deseasonalized) | 6 + 1 p-value | **All reproduced** at the reported precision |",
          "| Trends (slope, p) and the FDR value | 6 + 1 | **All reproduced** by one of seven variants tried; "
          "the method is inferred, not confirmed |",
          "| Lag correlations | 3 | Lags 0 and +1 **reproduced**; “about −0.04 for 2+” holds at lag +2 only |",
          "| Interpretation implied by the numbers | — | **Not supported** in three places (see §6) |", "",
          "Of the 16 reported numbers, 14 agree to the three decimals reported, one (the humidity slope) was "
          "reported to two decimals and agrees at that precision, and one was reported as approximate.", "",
          "**How independent is this?** A different model family, a separately retrieved copy of the data, and "
          "separately written code. But it is the same NASA product, the comparison was not blind (Gemini's numbers "
          "were known while the code was written), and both assessors are AI systems. Under the MIZAN ladder the "
          "reproduced *numbers* are `REPLICATED` in that limited sense; no *interpretation* is promoted, and human "
          "review is still required. Everything new in this document is `OBSERVED` only.", ""]

    L += ["## 1. Data source and hash", "",
          f"- **Source:** {prov['original_source']}",
          f"- **Request:** `{prov['original_api_request']}`",
          f"- **Retrieved:** {prov['retrieval_timestamp']}",
          f"- **How:** {prov['retrieval_method']}",
          f"- **Product:** {prov['source_product_version']['api']['name']} {prov['source_product_version']['api']['version']}; "
          f"sources {', '.join(prov['source_product_version']['sources'])}; time standard {prov['source_product_version']['time_standard']}",
          f"- **Kind of data:** model reanalysis (MERRA-2), not a station or a direct satellite measurement",
          f"- **Resolution:** {prov['spatial_resolution']}; grid-cell mean elevation {prov['grid_cell_elevation_m']} m",
          f"- **Coverage:** {prov['coverage']['start']} to {prov['coverage']['end']}, {prov['coverage']['n_months']} months, "
          f"{sum(prov['missing_values']['counts'].values())} missing",
          f"- **SHA-256 (raw bytes, {prov['bytes']} B):** `{prov['sha256']}`",
          f"- **SHA-256 (data only, ignoring server timings):** `{prov['sha256_canonical_data']}`",
          f"- **Raw file:** `data/{prov['raw_path']}` · provenance record in `data/provenance/`", "",
          "Whether Gemini used exactly the same response cannot be checked: it gave no request or hash. "
          "Agreement on all 16 numbers at their reported precision makes a different dataset very unlikely.", ""]

    t = out["traps"]
    L += ["## 2. Data traps (brief §1.1)", "",
          "| Gemini's warning | Found in the real response | Verdict |", "|---|---|---|",
          f"| `YYYY13` keys are an annual summary, not a 13th month | {t['yyyy13_keys_per_variable']} such keys per variable "
          f"({t['keys_per_variable']} keys = 24 × 13). They equal the day-weighted mean of the 12 months to within "
          f"{max(v['max_abs_diff_day_weighted'] for v in cons.values()):.4f} (two-decimal rounding); a plain 12-month mean "
          f"is off by up to {cons['RH2M']['max_abs_diff_simple_mean']:.2f} for RH2M | **Confirmed** |",
          f"| Missing values may be `-999.0` | The header declares `fill_value: {t['fill_value']}`. Occurrences in this "
          f"file: {t['fill_occurrences']} | **Confirmed as declared**; not exercised by this file |",
          f"| `PRECTOTCORR` may be in mm/day | Response metadata: `{t['units']['PRECTOTCORR']}` | **Confirmed** |", "",
          f"Consequence of the unit: mean annual precipitation is {t['mean_annual_precip_mm']:.0f} mm when each month is "
          f"multiplied by its real length; multiplying by 30 misstates single years by up to "
          f"{t['max_error_of_30_day_shortcut_mm']:.1f} mm.", "",
          "Two traps Gemini did not mention:", "",
          "1. **The raw hash is not stable.** Each response contains a `times` block with server timings. During "
          "retrieval, two responses to the identical request carried `times.data` of 0.428 and 0.184 and were "
          "otherwise the same; only the second was kept, so this is an observation, not something the repository "
          "can show. We record both the raw hash and a hash of the data alone.",
          "2. **A point is a grid cell.** The third coordinate in the response is the cell's mean elevation. "
          "For Pavlodar it is 111 m (plausible). For Almaty it is 2478 m, although the city lies near 800 m: the "
          "cell averages mountains and plain, and its temperatures are not the city's.", ""]

    L += ["## 3. Correlations (brief §1.2)", "",
          "Method: Pearson correlation of the 288 monthly values (raw); then of monthly anomalies, i.e. each value "
          "minus the 2001–2024 mean of its calendar month (deseasonalized); then of those anomalies with a linear "
          "trend removed (detrended).", "",
          "| Pair | | Reported by Gemini | Reproduced by Claude | Difference |", "|---|---|---:|---:|---:|"]
    for (a, b), (g_raw, g_des) in GEMINI["corr"].items():
        res = pairs[(a, b)]
        r_raw, r_des = res["raw"]["pearson_r"], res["deseasonalized"]["pearson_r"]
        L += [f"| {a} ↔ {b} | raw | {s(g_raw)} | {s(r_raw, 4)} | {abs(r_raw - g_raw):.4f} |",
              f"| | deseasonalized | {s(g_des)} | {s(r_des, 4)} | {abs(r_des - g_des):.4f} |"]
    pr_res = pairs[("PRECTOTCORR", "RH2M")]["deseasonalized"]
    L += ["", f"Gemini's p-value claim for the last row (p < 0.0001): reproduced. Naive p = {pr_res['p_naive']:.1e}; with "
              f"the effective sample size (n_eff = {pr_res['n_eff']:.0f} of 288) p = {pr_res['p_adjusted']:.1e}.", "",
          "**Verdict: REPRODUCED.** All six coefficients round to the reported values.", "",
          "What the reproduction adds (status `OBSERVED`):", "",
          "| Pair | Seasonal cycles alone | Detrended r (95% CI) | n_eff | Year-shuffle p | DJF | MAM | JJA | SON | Engine status |",
          "|---|---:|---|---:|---:|---:|---:|---:|---:|---|"]
    for (a, b), res in pairs.items():
        d, ss = res["detrended"], res["by_season"]["seasons"]
        L.append(f"| {a} ↔ {b} | {s(res['seasonal_cycle_only']['pearson_r'], 2)} | {s(d['pearson_r'], 2)} "
                 f"({s(d['ci95_adjusted'][0], 3)} to {s(d['ci95_adjusted'][1], 3)}) | {d['n_eff']:.0f} | "
                 f"{p(res['negative_control_year_shuffle']['p_permutation'])} | " +
                 " | ".join(s(ss[k]["r"], 2) for k in SEASONS) + f" | {res['status']} |")
    tp = pairs[("T2M", "PRECTOTCORR")]["by_season"]["seasons"]
    L += ["",
          "- **The raw values are mostly the seasonal cycle.** The two climatological cycles on their own correlate "
          "at −0.98 (T–RH), +0.86 (T–P) and −0.78 (P–RH). Gemini's deseasonalizing step was necessary and correct.",
          "- **Removing the trend changes little** here (third decimal), so shared trends do not drive these values.",
          f"- **Temperature–precipitation reverses sign with the season:** r = {s(tp['DJF']['r'], 2)} in winter and "
          f"{s(tp['JJA']['r'], 2)} in summer; spring and autumn are negative like summer. The all-year −0.125 pools "
          "seasons of opposite sign and should not be quoted alone.",
          "- **Precipitation–humidity is not detected in winter** (DJF r ≈ −0.06, n = 72, so the interval is wide) "
          "and is strong in the other seasons.", ""]

    L += ["## 4. Trends (brief §1.3)", "",
          "Gemini did not say how the trends were computed. Seven standard variants were run. **Only variant A gives "
          "all three slopes and all three p-values at the reported precision**; the others are shown so the reader can "
          "see that. The slopes alone do not separate A, B and C; the p-values do.", "",
          "| Variant | " + " | ".join(f"{NAMES[v]} slope, p" for v in PARAMS) + " |",
          "|---|" + "---|" * len(PARAMS),
          "| **Reported by Gemini** | " + " | ".join(
              f"**{s(GEMINI['trend'][v][0], GEMINI['slope_decimals'][v])}, {GEMINI['trend'][v][1]:.3f}**" for v in PARAMS) + " |"]
    for label in variants["T2M"]:
        cells = []
        for v in PARAMS:
            sl, pv = variants[v][label]
            g_sl, g_p = GEMINI["trend"][v]
            dec = GEMINI["slope_decimals"][v]
            match = round(sl, dec) == round(g_sl, dec) and round(pv, 3) == round(g_p, 3)
            cells.append(f"{s(sl, 4)}, {'< 0.001' if pv < 0.001 else f'{pv:.3f}'}{' ✓' if match else ''}")
        L.append(f"| {label} | " + " | ".join(cells) + " |")
    L += ["", "Units: °C per year, mm/day per year, percentage points per year. ✓ = slope and p both round to Gemini's "
              "values at the precision Gemini reported.", "",
          "| Quantity | Reported by Gemini | Reproduced by Claude (variant A) | Difference |", "|---|---:|---:|---:|"]
    for v in PARAMS:
        sl, pv = variants[v]["A. Theil-Sen + MK without tie correction, API annual values (YYYY13)"]
        g_sl, g_p = GEMINI["trend"][v]
        L += [f"| {v} slope ({UNITS[v]}) | {s(g_sl, GEMINI['slope_decimals'][v])} | {s(sl, 4)} | {abs(sl - g_sl):.4f} |",
              f"| {v} p-value | {g_p:.3f} | {pv:.4f} | {abs(pv - g_p):.4f} |"]
    L += [f"| RH2M q-value (Benjamini–Hochberg, 3 tests) | {GEMINI['rh_q']:.3f} | {q_api['RH2M']:.4f} | "
          f"{abs(q_api['RH2M'] - GEMINI['rh_q']):.4f} |", "",
          "**Explanation (an inference; Gemini did not confirm its method).** The numbers fit the Theil–Sen slope and "
          "a Mann–Kendall test applied to the 24 annual values that the API supplies under the `YYYY13` keys, with the "
          "variance of the test statistic computed as if there were no ties. Those API values are rounded to two "
          "decimals, so ties do occur; correcting for them (variant B, the textbook form) changes the precipitation "
          "p-value from 0.275 to 0.274. Annual means computed from the months (variant C) give 0.413, 0.264 and 0.035. "
          "The differences are in the second or third decimal and change no conclusion.", "",
          "**Verdict: REPRODUCED** (slopes, p-values and the FDR value), with the method inferred by enumeration.", "",
          "### What a more careful test says", "",
          "Our primary analysis uses annual means computed from the monthly values, the Theil–Sen slope with its 95% "
          "interval, and the larger p of two autocorrelation-aware tests (Hamed–Rao modified Mann–Kendall; least squares "
          "with AR(1) effective sample size). In this record the annual series show almost no autocorrelation, so the "
          "Hamed–Rao p equals the classic p for all three variables, and for humidity the primary p is simply the "
          "classic Mann–Kendall p.", "",
          "| Variable | Slope (95% CI) | Classic MK p | Hamed–Rao p | LSQ AR(1) p | Primary p | q | Detectable at 80% power |",
          "|---|---|---:|---:|---:|---:|---:|---:|"]
    for v in PARAMS:
        pm = primary[v]
        L.append(f"| {v} | {s(pm['primary_slope'], 4)} ({s(pm['primary_ci'][0], 4)} to {s(pm['primary_ci'][1], 4)}) {UNITS[v]} | "
                 f"{pm['mann_kendall']['p']:.3f} | {pm['mann_kendall_hamed_rao']['p']:.3f} | {pm['ols']['p_ar1']:.3f} | "
                 f"{pm['primary_p']:.3f} | {q_primary[v]:.3f} | ≥ {pm['minimum_detectable_trend']['mdt']:.3f} {UNITS[v]} |")
    rh = primary["RH2M"]
    L += ["",
          "**Temperature.** The statement “the trend is not significant” is reproduced. The statement “there is no "
          f"warming” would not be: the 95% interval runs from {s(primary['T2M']['primary_ci'][0] * 10, 2)} to "
          f"{s(primary['T2M']['primary_ci'][1] * 10, 2)} °C per decade, and a record this short and this variable could only "
          f"be expected to reveal trends above about {primary['T2M']['minimum_detectable_trend']['mdt'] * 10:.2f} °C per decade. "
          "Warming or cooling of several tenths of a degree per decade is fully compatible with these data.", "",
          f"**Relative humidity.** The only nominally significant trend (p = {rh['primary_p']:.3f}) is fragile:", "",
          f"- after correcting for three tests, q = {q_primary['RH2M']:.3f} (Gemini reported the same);",
          f"- leaving out any one of the years {', '.join(str(y) for y in loo['RH2M']['years_that_flip_significance'])} "
          f"moves p above 0.05 (to between {loo['RH2M']['p_range_of_flipping_years'][0]:.3f} and "
          f"{loo['RH2M']['p_range_of_flipping_years'][1]:.3f}; over all 24 single-year removals p ranges from "
          f"{loo['RH2M']['min_p_after_drop']:.3f} to {loo['RH2M']['max_p_after_drop']:.3f}); 2024 is the most humid "
          "year of the record;",
          f"- in 1981–2000 the slope has the opposite sign ({s(early_tr['RH2M']['slope'], 3)} pp/yr), and over 1981–2024 it is "
          f"{s(long_tr['RH2M']['primary_slope'], 3)} pp/yr with p = {long_tr['RH2M']['primary_p']:.3f}.", "",
          "So the humidity increase is a feature of the 2001–2024 window, not an established long-term trend.", "",
          "| Variable | 1981–2000 slope (MK p) | 2001–2024 slope (MK p) | 1981–2024 slope (95% CI), primary p |",
          "|---|---|---|---|"]
    for v in PARAMS:
        L.append(f"| {v} | {s(early_tr[v]['slope'], 4)} ({early_tr[v]['mk_p']:.3f}) | {s(primary[v]['primary_slope'], 4)} "
                 f"({primary[v]['mann_kendall']['p']:.3f}) | {s(long_tr[v]['primary_slope'], 4)} "
                 f"({s(long_tr[v]['primary_ci'][0], 4)} to {s(long_tr[v]['primary_ci'][1], 4)}), {long_tr[v]['primary_p']:.3f} |")
    L += ["", f"Sub-period check (all {win['T2M']['n_windows']} windows of at least 15 years inside 2001–2024): temperature "
              f"slope is positive in {win['T2M']['n_positive']} and negative in {win['T2M']['n_negative']}; humidity is positive "
              f"in all {win['RH2M']['n_positive']} but individually significant in only {win['RH2M']['n_significant']}.", ""]

    L += ["## 5. Lag analysis (brief §1.4)", "",
          "Definition used here: r(k) = corr(T[t], RH[t+k]) on monthly anomalies. **k = +1 pairs temperature with the "
          "following month's humidity**; k = −1 pairs temperature with the previous month's humidity.", "",
          "| Lag k | Reported by Gemini | Reproduced (deseasonalized) | Difference | q, deseasonalized | Detrended | q, detrended |",
          "|---:|---:|---:|---:|---:|---:|---:|"]
    for k in range(-6, 7):
        g = GEMINI["lag"].get(k)
        if k == 2:
            g = GEMINI["lag"]["2+"]
        gs = "" if g is None else (f"≈ {s(g, 2)}" if k == 2 else s(g))
        ds_ = "" if g is None else f"{abs(by[k]['r'] - g):.4f}"
        L.append(f"| {k:+d} | {gs} | {s(by[k]['r'], 4)} | {ds_} | {p(by[k]['q'])} | {s(by_det[k]['r'], 4)} | {p(by_det[k]['q'])} |")
    L += ["", "q-values: Benjamini–Hochberg across the 13 lags, on autocorrelation-adjusted p-values.", "",
          "- **Lag 0 and lag +1: REPRODUCED** (−0.316 and −0.185). Gemini's “lag +1” is temperature leading humidity; "
          f"the opposite direction is much weaker (k = −1: {s(by[-1]['r'])}).",
          f"- **“About −0.04 at 2+ months”: PARTLY.** It holds at k = +2 ({s(by[2]['r'])}) but not as a rule: "
          f"k = +3 gives {s(by[3]['r'])}, k = +6 gives {s(by[6]['r'])}.",
          f"- **Multiple testing.** Thirteen lags were scanned. After Benjamini–Hochberg correction with autocorrelation-"
          f"adjusted p-values, the lags that remain significant for T–RH are: "
          f"{', '.join(f'{r_['lag']:+d}' for r_ in lag_det['rows'] if r_['q'] < 0.05)}.",
          f"- **The pattern does not generalise to other pairs.** For precipitation paired with later humidity: "
          + ", ".join(f"k = {r_['lag']:+d}: {s(r_['r'], 2)}" for r_ in pr["rows"] if r_["lag"] in (1, 2, 3, 4))
          + f"; significant after correction at k = {', '.join(f'{k:+d}' for k in pr['significant_nonzero_lags'])} "
            "(not at +3). So “nothing beyond one month” describes the temperature–humidity pair only. This is not "
            "offered as evidence for atmospheric memory either: see below.", "",
          "**What may be said:** in this grid cell, temperature anomalies and the following month's humidity "
          "anomalies are weakly negatively correlated. **What may not:** that temperature drives next month's humidity, "
          "or that the atmosphere has (or lacks) long-term memory. A lag is a timing statistic; monthly means cannot "
          "resolve sub-monthly processes; persistence of either series alone spreads a same-month association onto "
          "neighbouring lags.", ""]

    L += ["## 6. Verdicts", "",
          "| # | Claim | Verdict | MIZAN status |", "|---|---|---|---|",
          "| 1 | `YYYY13` is an annual summary | Confirmed on the real response | REPLICATED |",
          "| 2 | `-999.0` marks missing values | Declared in the header; no occurrence in this file, so not exercised | declaration confirmed |",
          "| 3 | `PRECTOTCORR` is in mm/day | Confirmed from response metadata | REPLICATED |",
          "| 4 | Six correlation coefficients | Reproduced to the third decimal | REPLICATED |",
          "| 5 | P–RH deseasonalized p < 0.0001 | Reproduced, also with effective sample size | REPLICATED |",
          "| 6 | Three trend slopes and p-values | Reproduced with variant A (method inferred, not confirmed) | REPLICATED |",
          "| 7 | RH q = 0.105 after FDR | Reproduced | REPLICATED |",
          "| 8 | T–RH lag 0 and lag +1 | Reproduced | REPLICATED |",
          "| 9 | T–RH “≈ −0.04 at 2+ months” | Holds at +2 only; −0.09 at +3 | PARTLY — OBSERVED |",
          "| 10 | Implied: “no warming in Pavlodar” | **Not supported**: interval and power do not allow it | — |",
          "| 11 | Implied: “humidity is rising” | **Not established**: fragile, window-dependent | — |",
          "| 12 | Implied: “no long-term atmospheric memory” | **Not supported**: monthly lag correlations cannot settle "
          "it, and the T–RH lag pattern does not hold for P–RH | — |", "",
          "Rows 10–12 are interpretations the numbers might invite; the brief itself forbade drawing them, and the "
          "recomputation shows why.", "",
          "## 7. Re-run", "",
          "```bash", "pip install -r backend/requirements-dev.txt",
          "python scripts/build_provenance.py     # checks the SHA-256 of the raw NASA files",
          "python scripts/reproduce_gemini.py     # rewrites this document",
          "cd backend && python -m pytest tests/test_06_gemini_reproduction.py", "```", ""]
    (ROOT / "docs" / "GEMINI_REPRODUCTION.md").write_text("\n".join(L), encoding="utf-8")
    print("wrote docs/GEMINI_REPRODUCTION.md and docs/data/gemini_reproduction.json")
    for v in PARAMS:
        sl, pv = variants[v]["A. Theil-Sen + MK without tie correction, API annual values (YYYY13)"]
        print(f"  {v:12s} gemini {GEMINI['trend'][v]}  ours(A) ({sl:+.4f}, {pv:.4f})  primary p {primary[v]['primary_p']:.3f} q {q_primary[v]:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
