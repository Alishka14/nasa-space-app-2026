"""Golden values for the Pavlodar 2001-2024 case on the REAL NASA file.

Left column: what Gemini reported. These tests pin what this engine computes
from the bytes whose SHA-256 is asserted first, so a silent change of data or
method cannot go unnoticed.
"""
from __future__ import annotations

import numpy as np
import pytest

from earth_senses.normalize import annual_mean
from earth_senses.power_client import sha256_bytes
from earth_senses.relationships import analyze_pair
from earth_senses.trends import benjamini_hochberg, mann_kendall, summarize_trend, theil_sen

YEARS = np.arange(2001, 2025, dtype=float)


def test_the_bytes_are_the_ones_that_were_retrieved_from_nasa(pavlodar_bytes):
    assert len(pavlodar_bytes) == 14282
    assert sha256_bytes(pavlodar_bytes) == "8a65f9e56b005f77eec3783a09903ad2842031590cc0c8084441d92b19f87de6"


@pytest.mark.parametrize("a,b,raw,deseason", [
    ("T2M", "RH2M", -0.945, -0.316),
    ("T2M", "PRECTOTCORR", +0.439, -0.125),
    ("PRECTOTCORR", "RH2M", -0.285, +0.593),
])
def test_correlations_reported_by_gemini_are_reproduced(pavlodar, a, b, raw, deseason):
    res = analyze_pair(pavlodar.monthly[a], pavlodar.monthly[b], n_perm=200)
    assert res["raw"]["pearson_r"] == pytest.approx(raw, abs=5e-4)
    assert res["deseasonalized"]["pearson_r"] == pytest.approx(deseason, abs=5e-4)


def test_precipitation_humidity_p_value_claim_holds_with_and_without_adjustment(pavlodar):
    res = analyze_pair(pavlodar.monthly["PRECTOTCORR"], pavlodar.monthly["RH2M"], n_perm=200)
    assert res["deseasonalized"]["p_naive"] < 1e-4 and res["deseasonalized"]["p_adjusted"] < 1e-4


@pytest.mark.parametrize("name,slope,p,slope_tol", [
    ("T2M", -0.021, 0.427, 6e-4), ("PRECTOTCORR", +0.005, 0.275, 6e-4), ("RH2M", +0.16, 0.035, 6e-3)])
def test_trend_numbers_reported_by_gemini_match_sen_and_mk_on_the_api_annual_values(pavlodar, name, slope, p, slope_tol):
    rep = pavlodar.annual_reported[name].to_numpy()
    assert theil_sen(YEARS, rep)["slope"] == pytest.approx(slope, abs=slope_tol)
    assert mann_kendall(rep)["p"] == pytest.approx(p, abs=1.5e-3)


def test_fdr_value_reported_by_gemini_is_reproduced(pavlodar):
    ps = [mann_kendall(pavlodar.annual_reported[n].to_numpy())["p"] for n in ("T2M", "PRECTOTCORR", "RH2M")]
    assert benjamini_hochberg(ps)[2] == pytest.approx(0.105, abs=1.5e-3)


def test_our_primary_estimates_from_monthly_values(pavlodar):
    """Our own choice: day-weighted annual means computed from the months."""
    expected = {"T2M": (-0.0212, 0.413), "PRECTOTCORR": (0.0048, 0.264), "RH2M": (0.1645, 0.035)}
    for name, (slope, mk_p) in expected.items():
        s = summarize_trend(YEARS, annual_mean(pavlodar.monthly[name]).to_numpy())
        assert s["primary_slope"] == pytest.approx(slope, abs=1e-4)
        assert s["mann_kendall"]["p"] == pytest.approx(mk_p, abs=1e-3)
        assert s["primary_p"] >= s["mann_kendall_hamed_rao"]["p"]       # never more liberal than either test
    rh = summarize_trend(YEARS, annual_mean(pavlodar.monthly["RH2M"]).to_numpy())
    assert rh["primary_ci"][0] > 0 and rh["primary_p"] == pytest.approx(0.035, abs=1e-3)
