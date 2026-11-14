"""Facts and series for the onboarding intro, computed by the engine itself.

Writes frontend/src/onboarding/content/facts.json and series.json from the
bundled, hash-verified NASA files. The intro never types a number by hand:
scripts in intro-scripts.json refer to these facts by key, and
backend/tests/test_09_intro_content.py checks that the stored values still
match what the engine computes.

Run from the repository root:  python scripts/build_intro_assets.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from earth_senses.investigate import investigate  # noqa: E402
from earth_senses.power_client import PowerStore  # noqa: E402
from earth_senses.relationships import anomalies, monthly_climatology  # noqa: E402

OUT = ROOT / "frontend" / "src" / "onboarding" / "content"
PAV = dict(lat=52.29, lon=76.97, start=2001, end=2024, region_name="Pavlodar, Kazakhstan")


def fact(value: float, digits: int, signed: bool = True, note: str = "") -> dict:
    return {"value": float(value), "digits": digits, "signed": signed, "note": note}


def compute() -> tuple[dict, dict]:
    store = PowerStore(ROOT / "data", allow_network=False)
    inv3 = investigate(store, variables=["T2M", "RH2M", "PRECTOTCORR"], **PAV)
    inv4 = investigate(store, variables=["T2M", "RH2M", "PRECTOTCORR", "QV2M"], **PAV)
    rel = {r["id"]: r for r in inv3["relationships"]}
    pr, tr = rel["PRECTOTCORR-RH2M"], rel["T2M-RH2M"]
    held = {tuple(p["controls"]): p for p in next(r for r in inv4["relationships"]
                                                    if r["id"] == "PRECTOTCORR-RH2M")["partial"]}
    t2m = inv3["trends"]["T2M"]
    rh = inv3["trends"]["RH2M"]
    seasons = pr["by_season"]["seasons"]
    derived = inv4["derived_checks"][0]["reconstruction"]

    facts = {
        "source": {"place": "Pavlodar, Kazakhstan", "lat": 52.29, "lon": 76.97, "start": 2001, "end": 2024,
                   "months": int(rel["PRECTOTCORR-RH2M"]["raw"]["n"]), "dataset": "NASA POWER (MERRA-2)",
                   "data_hash": inv3["data_hash"], "generated_by": "scripts/build_intro_assets.py"},
        "p_rh_raw": fact(pr["raw"]["pearson_r"], 3, note="precipitation-relative humidity, raw monthly values"),
        "p_rh_cycles": fact(pr["seasonal_cycle_only"]["pearson_r"], 3, note="the two seasonal cycles alone"),
        "p_rh_deseason": fact(pr["deseasonalized"]["pearson_r"], 3, note="monthly anomalies (seasonal cycle removed)"),
        "p_rh_detrended": fact(pr["detrended"]["pearson_r"], 3, note="detrended anomalies"),
        "p_rh_ci_low": fact(pr["detrended"]["ci95_adjusted"][0], 2, note="95% CI, detrended anomalies"),
        "p_rh_ci_high": fact(pr["detrended"]["ci95_adjusted"][1], 2, note="95% CI, detrended anomalies"),
        "p_rh_winter": fact(seasons["DJF"]["r"], 2, note="December-February only"),
        "p_rh_summer": fact(seasons["JJA"]["r"], 2, note="June-August only"),
        "p_rh_equal_months": fact(pr["month_standardized"]["pearson_r"], 2, note="every calendar month weighted equally"),
        "p_rh_held_t": fact(held[("T2M",)]["pearson_r"], 2, note="partial correlation, temperature held fixed"),
        "p_rh_held_t_qv": fact(held[("T2M", "QV2M")]["pearson_r"], 2,
                               note="partial correlation, temperature and specific humidity held fixed"),
        "t_rh_raw": fact(tr["raw"]["pearson_r"], 3, note="temperature-relative humidity, raw"),
        "t_rh_deseason": fact(tr["deseasonalized"]["pearson_r"], 3, note="temperature-relative humidity, anomalies"),
        "rh_rebuilt_r": fact(derived["r_raw"], 2, signed=False,
                             note="relative humidity rebuilt from temperature and specific humidity vs NASA values"),
        "t_trend_decade": fact(t2m["summary"]["primary_slope"] * 10, 2, note="deg C per decade, 2001-2024"),
        "t_trend_ci_low": fact(t2m["summary"]["primary_ci"][0] * 10, 2, note="deg C per decade, 95% CI"),
        "t_trend_ci_high": fact(t2m["summary"]["primary_ci"][1] * 10, 2, note="deg C per decade, 95% CI"),
        "rh_trend_p": fact(rh["summary"]["mann_kendall"]["p"], 3, signed=False, note="Mann-Kendall p"),
        "rh_trend_q": fact(rh["q"], 3, signed=False, note="after false-discovery correction"),
        "rh_flip_years": fact(len(rh["leave_one_out"]["years_that_flip_significance"]), 0, signed=False,
                              note="years whose removal flips significance"),
    }
    verdicts = {"T2M": t2m["verdict"], "RH2M": rh["verdict"], "PRECTOTCORR-RH2M": pr["status"]}
    facts["source"]["verdicts"] = verdicts

    ds = store.load(52.29, 76.97, 2001, 2024, ["PRECTOTCORR", "RH2M"])
    m = ds.monthly
    series = {"months": [str(p) for p in m.index], "units": {"PRECTOTCORR": "mm/day", "RH2M": "%"}}
    for v in ("PRECTOTCORR", "RH2M"):
        s = m[v].astype(float)
        a = anomalies(s, monthly_climatology(s))
        series[v] = {"raw": [round(float(x), 3) for x in s], "anomaly": [round(float(x), 3) for x in a]}
    # sanity: the series reproduce the facts
    assert abs(np.corrcoef(series["PRECTOTCORR"]["raw"], series["RH2M"]["raw"])[0, 1] - facts["p_rh_raw"]["value"]) < 5e-4
    assert abs(np.corrcoef(series["PRECTOTCORR"]["anomaly"], series["RH2M"]["anomaly"])[0, 1]
               - facts["p_rh_deseason"]["value"]) < 5e-4
    return facts, series


def main() -> int:
    facts, series = compute()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "facts.json").write_text(json.dumps(facts, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "series.json").write_text(json.dumps(series, separators=(",", ":")) + "\n", encoding="utf-8")
    for k, v in facts.items():
        if k != "source":
            print(f"{k:20s} {v['value']:+.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
