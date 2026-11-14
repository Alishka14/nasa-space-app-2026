"""Relationship Engine: seasonality (test 5), shared trend (test 6),
calendar alignment (test 4), lag convention, negative controls."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from conftest import ar1, month_index, seasonal_cycle
from earth_senses.relationships import (analyze_pair, anomalies, correlate, detrend_linear, effective_n,
                                        lagged_correlations, monthly_climatology, year_block_permutation)

N_YEARS = 24


def _series(values: np.ndarray) -> pd.Series:
    return pd.Series(values, index=month_index(2001, len(values) // 12))


# ---- 5. a shared seasonal cycle is not a relationship ----------------------------------------

def test_independent_noise_with_opposed_seasonal_cycles_looks_strongly_related_until_deseasonalized():
    """SYNTHETIC: two independent noises, each riding its own seasonal cycle."""
    rng = np.random.default_rng(21)
    n = N_YEARS * 12
    x = _series(seasonal_cycle(N_YEARS, 20.0, 7) + rng.normal(0, 1.5, n))
    y = _series(seasonal_cycle(N_YEARS, -25.0, 7) + 70 + rng.normal(0, 2.0, n))
    res = analyze_pair(x, y, n_perm=400)
    assert res["raw"]["pearson_r"] < -0.95                  # looks like a near-perfect link
    assert res["seasonal_cycle_only"]["pearson_r"] < -0.99  # produced by the cycles alone
    assert abs(res["deseasonalized"]["pearson_r"]) < 0.15   # nothing is left between the anomalies
    assert res["status"] == "NOT_SUPPORTED"


def test_real_temperature_humidity_link_shrinks_threefold_without_the_seasonal_cycle(pavlodar):
    res = analyze_pair(pavlodar.monthly["T2M"], pavlodar.monthly["RH2M"], n_perm=400)
    assert res["raw"]["pearson_r"] == pytest.approx(-0.945, abs=5e-4)
    assert res["seasonal_cycle_only"]["pearson_r"] < -0.97
    assert res["deseasonalized"]["pearson_r"] == pytest.approx(-0.316, abs=5e-4)
    assert res["status"] == "SUPPORTED"                      # modest, but real in the anomalies


def test_real_precipitation_humidity_link_changes_sign_when_deseasonalized(pavlodar):
    res = analyze_pair(pavlodar.monthly["PRECTOTCORR"], pavlodar.monthly["RH2M"], n_perm=400)
    assert res["raw"]["pearson_r"] < -0.25 and res["deseasonalized"]["pearson_r"] > 0.55


def test_climatology_needs_enough_years_and_an_explicit_baseline(pavlodar):
    s = pavlodar.monthly["T2M"]
    full = monthly_climatology(s)
    part = monthly_climatology(s, (2001, 2012))
    assert not np.allclose(full.to_numpy(), part.to_numpy())          # the baseline matters
    assert anomalies(s, full).groupby(s.index.month).mean().abs().max() < 1e-9
    with pytest.raises(ValueError, match="baseline"):
        monthly_climatology(s, (2001, 2005))


# ---- 6. a shared trend is not a relationship ---------------------------------------------------

def test_independent_noise_with_shared_trends_is_related_only_until_detrended():
    """SYNTHETIC: two independent noises, each with a strong linear trend."""
    rng = np.random.default_rng(22)
    n = N_YEARS * 12
    t = np.arange(n) / 12.0
    x = _series(0.25 * t + rng.normal(0, 1.0, n))
    y = _series(0.40 * t + rng.normal(0, 1.5, n))
    res = analyze_pair(x, y, n_perm=400)
    assert res["deseasonalized"]["pearson_r"] > 0.6        # deseasonalizing does not help here
    assert abs(res["detrended"]["pearson_r"]) < 0.12       # detrending does
    assert res["status"] == "NOT_SUPPORTED"


def test_detrending_removes_a_line_and_keeps_the_residual_structure():
    rng = np.random.default_rng(23)
    noise = rng.normal(0, 1, 240)
    s = _series(5 + 0.03 * np.arange(240) + noise)
    d = detrend_linear(s)
    assert abs(np.polyfit(np.arange(240), d.to_numpy(), 1)[0]) < 1e-12
    assert np.corrcoef(d.to_numpy(), noise)[0, 1] > 0.99


# ---- a real relationship is found, with the right sign and lag ---------------------------------

def test_known_relationship_is_recovered_and_lag_sign_follows_the_stated_convention():
    """SYNTHETIC: y[t] = 0.8 * x[t-2] + noise, so x LEADS y by two months."""
    rng = np.random.default_rng(24)
    n = N_YEARS * 12
    x = rng.normal(0, 1, n + 2)
    y = 0.8 * x[:-2] + rng.normal(0, 0.6, n)
    xs, ys = _series(x[2:]), _series(y)
    lags = lagged_correlations(xs, ys, max_lag=6)
    assert lags["peak_lag"] == 2 and lags["peak_r"] > 0.7           # k > 0: x paired with later y
    assert 2 in lags["significant_nonzero_lags"]
    swapped = lagged_correlations(ys, xs, max_lag=6)
    assert swapped["peak_lag"] == -2
    by_lag = {r["lag"]: r for r in lags["rows"]}
    assert by_lag[2]["n"] == n - 2 and abs(by_lag[0]["r"]) < 0.15   # each lag loses |k| months


def test_real_lag_values_and_direction(pavlodar):
    t = anomalies(pavlodar.monthly["T2M"], monthly_climatology(pavlodar.monthly["T2M"]))
    h = anomalies(pavlodar.monthly["RH2M"], monthly_climatology(pavlodar.monthly["RH2M"]))
    by = {r["lag"]: r["r"] for r in lagged_correlations(t, h, max_lag=3)["rows"]}
    assert by[0] == pytest.approx(-0.316, abs=5e-4)
    assert by[1] == pytest.approx(-0.185, abs=5e-4)      # temperature paired with NEXT month's humidity
    assert by[-1] == pytest.approx(-0.081, abs=5e-4)     # the other direction is much weaker
    assert by[2] == pytest.approx(-0.045, abs=5e-4)
    assert by[3] == pytest.approx(-0.090, abs=5e-4)      # "about -0.04 for lags of 2+" does not hold at 3


# ---- 4. calendars must be aligned -----------------------------------------------------------------

def test_misaligned_calendars_are_refused():
    a = _series(np.arange(240.0))
    b = pd.Series(np.arange(240.0), index=month_index(2002, 20))
    with pytest.raises(ValueError, match="not aligned"):
        analyze_pair(a, b)
    with pytest.raises(ValueError, match="not aligned"):
        lagged_correlations(a, b)
    with pytest.raises(ValueError, match="not aligned"):
        correlate(np.arange(10.0), np.arange(11.0))


def test_one_month_shift_would_have_changed_the_answer(pavlodar):
    t, h = pavlodar.monthly["T2M"], pavlodar.monthly["RH2M"]
    at = anomalies(t, monthly_climatology(t)).to_numpy()
    ah = anomalies(h, monthly_climatology(h)).to_numpy()
    aligned = np.corrcoef(at, ah)[0, 1]
    shifted = np.corrcoef(at[1:], ah[:-1])[0, 1]
    assert abs(aligned) > 3 * abs(shifted)


# ---- autocorrelation and negative controls ---------------------------------------------------------

def test_effective_sample_size_and_adjusted_p_for_persistent_series():
    rng = np.random.default_rng(25)
    x, y = ar1(rng, 288, 0.8), ar1(rng, 288, 0.8)
    n_eff, r1x, r1y = effective_n(x, y)
    assert n_eff < 0.45 * 288 and r1x > 0.6 and r1y > 0.6
    c = correlate(x, y)
    assert c["p_adjusted"] > c["p_naive"]


def test_persistence_inflates_naive_correlation_tests_and_the_adjustment_contains_it():
    """SYNTHETIC: independent AR(1) pairs. Every 'significant' correlation is false."""
    rng = np.random.default_rng(26)
    naive = adj = 0
    for _ in range(400):
        c = correlate(ar1(rng, 288, 0.8), ar1(rng, 288, 0.8))
        naive += c["p_naive"] < 0.05
        adj += c["p_adjusted"] < 0.05
    assert naive / 400 > 0.25 and adj / 400 < 0.09


def test_year_shuffle_control_separates_real_from_unrelated_pairs(pavlodar):
    rng = np.random.default_rng(27)
    p = pavlodar.monthly["PRECTOTCORR"]
    h = pavlodar.monthly["RH2M"]
    ap, ah = anomalies(p, monthly_climatology(p)), anomalies(h, monthly_climatology(h))
    assert year_block_permutation(ap, ah, n_perm=500)["p_permutation"] < 0.01
    noise = pd.Series(rng.normal(size=len(ap)), index=ap.index)          # SYNTHETIC control series
    assert year_block_permutation(ap, noise, n_perm=500)["p_permutation"] > 0.05
    again = year_block_permutation(ap, ah, n_perm=500)
    assert again == year_block_permutation(ap, ah, n_perm=500)            # seeded: reproducible


def test_seasonal_split_exposes_a_sign_reversal_in_real_data(pavlodar):
    res = analyze_pair(pavlodar.monthly["T2M"], pavlodar.monthly["PRECTOTCORR"], n_perm=300)
    seasons = res["by_season"]["seasons"]
    assert res["by_season"]["sign_differs_between_seasons"]
    assert seasons["DJF"]["r"] > 0.25 and seasons["JJA"]["r"] < -0.25     # opposite in winter and summer
    assert res["status"] in ("WEAK", "INCONCLUSIVE")                      # the all-year number is small
