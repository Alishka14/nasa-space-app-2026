"""Trend Engine: correctness against an independent implementation, known
synthetic answers, autocorrelation (test 7), FDR (test 8), period
sensitivity (test 12) and unit separation."""
from __future__ import annotations

import numpy as np
import pymannkendall as pmk
import pytest
from statsmodels.stats.multitest import multipletests

from conftest import PARAMS, ar1
from earth_senses.normalize import annual_mean, annual_total, rate_to_monthly_total
from earth_senses.trends import (benjamini_hochberg, hamed_rao_mk, leave_one_out, mann_kendall,
                                 minimum_detectable_trend, ols_trend, seasonal_mann_kendall, summarize_trend,
                                 theil_sen, window_sensitivity)

YEARS = np.arange(2001, 2025, dtype=float)


# ---- agreement with an independent implementation (pymannkendall) ---------------------------

@pytest.mark.parametrize("name", PARAMS)
def test_mann_kendall_and_sen_match_pymannkendall_on_real_data(pavlodar, name):
    x = annual_mean(pavlodar.monthly[name]).to_numpy()
    ours, ref = mann_kendall(x), pmk.original_test(x)
    assert ours["s"] == ref.s
    assert ours["var_s"] == pytest.approx(ref.var_s)
    assert ours["z"] == pytest.approx(ref.z)
    assert ours["p"] == pytest.approx(ref.p)
    assert theil_sen(YEARS, x)["slope"] == pytest.approx(ref.slope)


def test_mann_kendall_tie_correction_matches_reference():
    x = np.array([1, 2, 2, 3, 3, 3, 4, 2, 5, 5, 6, 1, 7.0])
    ours, ref = mann_kendall(x), pmk.original_test(x)
    assert ours["var_s"] == pytest.approx(ref.var_s) and ours["p"] == pytest.approx(ref.p)


def test_hamed_rao_matches_reference_when_not_clipped():
    rng = np.random.default_rng(7)
    for phi in (0.0, 0.5, 0.8):
        x = ar1(rng, 60, phi) + 0.02 * np.arange(60)
        ours, ref = hamed_rao_mk(x, conservative=False), pmk.hamed_rao_modification_test(x)
        assert ours["var_s"] == pytest.approx(ref.var_s, rel=1e-9)
        assert ours["p"] == pytest.approx(ref.p, rel=1e-9)


def test_conservative_hamed_rao_is_never_more_liberal_than_classic():
    rng = np.random.default_rng(11)
    for _ in range(60):
        x = ar1(rng, 40, rng.uniform(-0.6, 0.8))
        assert hamed_rao_mk(x)["p"] >= mann_kendall(x)["p"] - 1e-12


@pytest.mark.parametrize("name", PARAMS)
def test_seasonal_kendall_matches_reference_under_independence(pavlodar, name):
    x = pavlodar.monthly[name].to_numpy()
    ours, ref = seasonal_mann_kendall(x.reshape(-1, 12)), pmk.seasonal_test(x, period=12)
    assert ours["s"] == ref.s
    assert ours["var_independent"] == pytest.approx(ref.var_s)
    assert ours["p_independent"] == pytest.approx(ref.p)
    assert ours["slope"] == pytest.approx(ref.slope)


def test_seasonal_kendall_covariance_term_matches_reference(pavlodar):
    x = pavlodar.monthly["RH2M"].to_numpy()
    ours, ref = seasonal_mann_kendall(x.reshape(-1, 12)), pmk.correlated_seasonal_test(x, period=12)
    assert ours["var_dependent"] == pytest.approx(ref.var_s, rel=1e-9)
    # the reference omits the continuity correction; compare like with like, then check ours is not more liberal
    from scipy import stats
    assert 2 * stats.norm.sf(abs(ours["s"]) / np.sqrt(ours["var_dependent"])) == pytest.approx(ref.p, rel=1e-9)
    assert ours["p_dependent"] >= ref.p
    assert ours["var_dependent"] > ours["var_independent"]     # months are positively dependent here


# ---- known answers on SYNTHETIC series ------------------------------------------------------

def test_recovers_a_known_trend_and_its_interval_covers_the_truth():
    rng = np.random.default_rng(1)
    t = np.arange(40.0)
    x = 3.0 + 0.05 * t + rng.normal(0, 0.4, 40)
    s = summarize_trend(t, x)
    assert s["primary_ci"][0] < 0.05 < s["primary_ci"][1]
    assert s["primary_p"] < 0.001 and s["primary_slope"] == pytest.approx(0.05, abs=0.01)


def test_false_positive_rate_is_near_alpha_for_white_noise():
    rng = np.random.default_rng(2)
    hits = sum(mann_kendall(rng.normal(size=30))["p"] < 0.05 for _ in range(600))
    assert 0.02 <= hits / 600 <= 0.085


# ---- 7. autocorrelation must not manufacture significance -----------------------------------

def test_autocorrelation_inflates_classic_tests_and_the_combined_rule_contains_it():
    """SYNTHETIC AR(1) noise with NO trend: every 'significant' result is false.

    Characterises each test at the length of the real record (24 years).
    Finding that shaped the engine: Hamed-Rao alone under-corrects, so the
    primary p-value is the larger of Hamed-Rao and AR(1)-adjusted least squares.
    """
    rates = {}
    for phi in (0.3, 0.7):
        rng = np.random.default_rng(3)
        n_sim, n = 600, 24
        t = np.arange(float(n))
        c = {"mk": 0, "hr": 0, "ols": 0, "ols_adj": 0, "primary": 0}
        for _ in range(n_sim):
            x = ar1(rng, n, phi)
            c["mk"] += mann_kendall(x)["p"] < 0.05
            c["hr"] += hamed_rao_mk(x)["p"] < 0.05
            o = ols_trend(t, x)
            c["ols"] += o["p_naive"] < 0.05
            c["ols_adj"] += o["p_ar1"] < 0.05
            c["primary"] += summarize_trend(t, x)["primary_p"] < 0.05
        rates[phi] = {k: v / n_sim for k, v in c.items()}
    mild, strong = rates[0.3], rates[0.7]
    assert strong["mk"] > 0.25 and strong["ols"] > 0.25            # classic tests: far above the nominal 5%
    assert mild["mk"] > 0.07                                       # already inflated at modest autocorrelation
    assert strong["hr"] < strong["mk"] and strong["hr"] > 0.15     # Hamed-Rao helps, but not enough on its own
    for r in (mild, strong):
        assert r["primary"] <= r["hr"] and r["primary"] <= r["ols_adj"]
    assert mild["primary"] < 0.08                                  # near nominal for realistic annual series
    assert strong["primary"] < 0.5 * strong["mk"]                  # and much better under strong persistence
    assert strong["primary"] > 0.05                                # documented residual inflation (KNOWN_LIMITATIONS)


def test_effective_sample_size_shrinks_with_positive_autocorrelation():
    rng = np.random.default_rng(4)
    t = np.arange(60.0)
    o = ols_trend(t, ar1(rng, 60, 0.8))
    assert o["n_eff"] < 0.6 * o["n"] and o["p_ar1"] >= o["p_naive"]
    o2 = ols_trend(t, rng.normal(size=60))
    assert o2["n_eff"] > 0.7 * o2["n"]


# ---- 8. false discovery rate ------------------------------------------------------------------

def test_bh_matches_hand_calculation_for_the_three_trend_tests():
    q = benjamini_hochberg([0.427, 0.275, 0.035])
    assert q == pytest.approx([0.427, 0.4125, 0.105])


def test_bh_matches_statsmodels_and_is_monotone():
    rng = np.random.default_rng(5)
    p = np.r_[rng.uniform(0, 1, 40), rng.uniform(0, 0.01, 10)]
    ours = np.array(benjamini_hochberg(p))
    assert ours == pytest.approx(multipletests(p, method="fdr_bh")[1])
    order = np.argsort(p)
    assert (np.diff(ours[order]) >= -1e-15).all() and (ours >= p - 1e-15).all() and ours.max() <= 1


def test_bh_is_neither_bonferroni_nor_the_raw_p_values():
    p = [0.01, 0.02, 0.03, 0.04]
    q = benjamini_hochberg(p)
    assert q != pytest.approx(p) and q != pytest.approx([min(1, v * 4) for v in p])
    assert q == pytest.approx([0.04, 0.04, 0.04, 0.04])


def test_bh_skips_missing_tests_instead_of_counting_them():
    assert benjamini_hochberg([0.01, None, 0.04]) == pytest.approx([0.02, None, 0.04], nan_ok=True)
    assert benjamini_hochberg([None, None]) == [None, None]


def test_bh_controls_false_discoveries_on_pure_noise():
    rng = np.random.default_rng(6)
    any_hit = sum(min(benjamini_hochberg(rng.uniform(size=13))) < 0.05 for _ in range(1000))
    naive_hit = sum(rng.uniform(size=13).min() < 0.05 for _ in range(1000))
    assert any_hit / 1000 < 0.08 and naive_hit / 1000 > 0.35     # 13 lags tested: naive is wrong ~49% of the time


# ---- 12. the answer depends on the period ---------------------------------------------------

def test_real_humidity_trend_changes_with_the_period(store):
    long = store.load(52.29, 76.97, 1981, 2024, ["RH2M"]).monthly["RH2M"]
    ann = annual_mean(long)
    recent = ann[ann.index >= 2001]
    early = ann[ann.index <= 2000]
    p_recent = mann_kendall(recent.to_numpy())["p"]
    p_long = mann_kendall(ann.to_numpy())["p"]
    assert p_recent < 0.05 < p_long                                  # significant, then not
    assert theil_sen(recent.index.to_numpy(float), recent.to_numpy())["slope"] > 0
    assert theil_sen(early.index.to_numpy(float), early.to_numpy())["slope"] < 0   # opposite sign before 2001
    ws = window_sensitivity(ann.index.to_numpy(float), ann.to_numpy(), min_len=20)
    assert ws["sign_changes_with_period"] and ws["significance_changes_with_period"]


def test_window_sensitivity_flags_a_reversal_in_synthetic_data():
    t = np.arange(40.0)
    x = np.abs(t - 20) + np.random.default_rng(8).normal(0, 0.3, 40)   # falls, then rises
    ws = window_sensitivity(t, x, min_len=15)
    assert ws["sign_changes_with_period"] and ws["n_significant_positive"] > 0 and ws["n_significant_negative"] > 0
    steady = window_sensitivity(t, 0.3 * t + np.random.default_rng(9).normal(0, 0.3, 40), min_len=15)
    assert not steady["sign_changes_with_period"] and not steady["significance_changes_with_period"]


def test_leave_one_out_exposes_dependence_on_single_years(pavlodar):
    rh = annual_mean(pavlodar.monthly["RH2M"]).to_numpy()
    loo = leave_one_out(YEARS, rh)
    assert loo["full_significant"] and 2024 in loo["years_that_flip_significance"]
    t2m = annual_mean(pavlodar.monthly["T2M"]).to_numpy()
    assert leave_one_out(YEARS, t2m)["years_that_flip_significance"] == []


# ---- a non-significant trend is not "no change" ------------------------------------------------

def test_minimum_detectable_trend_is_larger_than_the_estimate_for_real_temperature(pavlodar):
    x = annual_mean(pavlodar.monthly["T2M"]).to_numpy()
    mdt = minimum_detectable_trend(YEARS, x)["mdt"]
    assert mdt > 0.05                       # deg C per year: only changes above ~0.5 C/decade were detectable
    s = summarize_trend(YEARS, x)
    assert s["primary_ci"][0] < 0 < s["primary_ci"][1] and s["primary_p"] > 0.05


# ---- units must not be mixed --------------------------------------------------------------------

def test_precipitation_intensity_and_accumulation_trends_are_distinct_quantities(pavlodar):
    rate = pavlodar.monthly["PRECTOTCORR"]
    intensity = annual_mean(rate)                                            # mm/day
    total = annual_total(rate_to_monthly_total(rate, pavlodar.units["PRECTOTCORR"]))   # mm/year
    assert total.to_numpy() == pytest.approx(intensity.to_numpy() * np.where(intensity.index % 4 == 0, 366, 365))
    s_int = theil_sen(YEARS, intensity.to_numpy())["slope"]                  # mm/day per year
    s_tot = theil_sen(YEARS, total.to_numpy())["slope"]                      # mm/year per year
    assert s_tot == pytest.approx(s_int * 365.25, rel=0.05)
    assert abs(s_tot) > 100 * abs(s_int)                                     # confusing them is a 365x error
