"""Silent data errors: tests 1, 2, 3, 4, 10 and 11 of the science test plan."""
from __future__ import annotations

import copy
import json

import numpy as np
import pytest

from conftest import ALMATY_RAW, PARAMS, make_power_json, month_index
from earth_senses.catalog import describe
from earth_senses.normalize import (PowerFormatError, annual_mean, annual_total, check_annual_consistency,
                                    days_in_month, parse_power_monthly, rate_to_monthly_total, seasonal_mean)
from earth_senses.power_client import DataUnavailable, PowerStore, canonical_data_hash, sha256_bytes


# ---- 1. YYYY13 is the annual summary, not a thirteenth month ----------------------

def test_yyyy13_keys_exist_in_real_response_and_are_not_months(pavlodar_bytes, pavlodar):
    raw = json.loads(pavlodar_bytes)
    keys = list(raw["properties"]["parameter"]["T2M"])
    assert sum(k.endswith("13") for k in keys) == 24, "real API response carries one YYYY13 key per year"
    assert len(keys) == 312
    assert len(pavlodar.monthly) == 288
    assert set(pavlodar.monthly.index.month) == set(range(1, 13))
    assert list(pavlodar.annual_reported.index) == list(range(2001, 2025))


def test_treating_yyyy13_as_a_month_would_bias_the_series(pavlodar_bytes, pavlodar):
    raw = json.loads(pavlodar_bytes)
    naive = np.array(list(raw["properties"]["parameter"]["PRECTOTCORR"].values()))   # 312 values
    assert len(naive) != len(pavlodar.monthly)
    # the annual value would be counted twice: the naive mean is not the monthly mean
    assert abs(naive.mean() - pavlodar.monthly["PRECTOTCORR"].mean()) > 1e-4


def test_unknown_month_code_is_rejected():
    doc = make_power_json({"X": np.arange(24.0)})
    doc["properties"]["parameter"]["X"]["200114"] = 1.0
    with pytest.raises(PowerFormatError, match="month code"):
        parse_power_monthly(doc)


def test_annual_summary_matches_day_weighted_mean_of_months(pavlodar):
    report = check_annual_consistency(pavlodar)
    for name, r in report.items():
        assert r["max_abs_diff_day_weighted"] <= 0.0051, name          # two-decimal rounding only
    # a plain mean of the 12 months is measurably different for T and RH
    assert report["T2M"]["max_abs_diff_simple_mean"] > 0.05
    assert report["RH2M"]["max_abs_diff_simple_mean"] > 0.05


# ---- 2. -999 is missing data ------------------------------------------------------------

def test_fill_value_becomes_nan_and_is_counted():
    vals = np.full(120, 5.0)
    vals[[3, 40]] = -999.0
    norm = parse_power_monthly(make_power_json({"X": vals}))
    assert norm.missing == {"X": 2}
    assert np.isnan(norm.monthly["X"].iloc[3]) and np.isnan(norm.monthly["X"].iloc[40])
    assert norm.monthly["X"].mean() == pytest.approx(5.0)              # not dragged towards -999
    assert any("missing" in w for w in norm.warnings)


def test_real_response_declares_fill_value_and_has_no_gaps(pavlodar):
    assert pavlodar.fill_value == -999.0
    assert pavlodar.missing == {"PRECTOTCORR": 0, "RH2M": 0, "T2M": 0}


def test_missing_fill_value_declaration_is_rejected():
    doc = make_power_json({"X": np.arange(24.0)})
    del doc["header"]["fill_value"]
    with pytest.raises(PowerFormatError, match="fill_value"):
        parse_power_monthly(doc)


def test_incomplete_year_gives_nan_annual_mean_not_a_biased_one():
    vals = np.arange(24.0)
    vals[5] = -999.0
    norm = parse_power_monthly(make_power_json({"X": vals}))
    ann = annual_mean(norm.monthly["X"])
    assert np.isnan(ann.loc[2001]) and not np.isnan(ann.loc[2002])


# ---- 3. mm/day -> mm/month -----------------------------------------------------------

def test_days_in_month_handles_leap_years():
    idx = month_index(2023, 2)
    d = days_in_month(idx)
    assert d[idx[1]] == 28 and d[idx[13]] == 29          # Feb 2023, Feb 2024
    assert d.groupby(idx.year).sum().tolist() == [365, 366]


def test_rate_conversion_uses_real_month_lengths(pavlodar):
    total = rate_to_monthly_total(pavlodar.monthly["PRECTOTCORR"], pavlodar.units["PRECTOTCORR"])
    feb2001 = total[total.index == "2001-02"].iloc[0]
    assert feb2001 == pytest.approx(0.56 * 28)
    assert abs(0.56 * 30 - feb2001) > 1.0                  # the 30-day shortcut is off by 7% here
    annual = annual_total(total)
    assert annual.loc[2024] == pytest.approx(526.0, abs=0.5)
    wrong = pavlodar.monthly["PRECTOTCORR"].groupby(pavlodar.monthly.index.year).sum() * 30
    assert (wrong - annual).abs().max() > 3.0


def test_rate_conversion_refuses_other_units(pavlodar):
    with pytest.raises(ValueError, match="mm/day"):
        rate_to_monthly_total(pavlodar.monthly["PRECTOTCORR"], "mm/hour")
    with pytest.raises(ValueError, match="mm/day"):
        rate_to_monthly_total(pavlodar.monthly["T2M"], pavlodar.units["T2M"])


def test_units_come_from_the_response_and_mismatch_is_a_hard_error(pavlodar):
    assert pavlodar.units == {"PRECTOTCORR": "mm/day", "RH2M": "%", "T2M": "C"}
    with pytest.raises(ValueError, match="unit trap"):
        describe("T2M", "K", "Temperature at 2 Meters")
    doc = make_power_json({"X": np.arange(24.0)})
    doc["parameters"]["X"]["units"] = ""
    with pytest.raises(PowerFormatError, match="units"):
        parse_power_monthly(doc)


# ---- 4. calendar alignment ------------------------------------------------------------

def test_variables_on_different_calendars_are_rejected():
    doc = make_power_json({"A": np.arange(24.0), "B": np.arange(24.0)})
    del doc["properties"]["parameter"]["B"]["200107"]
    with pytest.raises(PowerFormatError, match="calendar mismatch"):
        parse_power_monthly(doc)


def test_djf_never_borrows_december_of_the_same_year(pavlodar):
    djf = seasonal_mean(pavlodar.monthly["T2M"], "DJF")
    assert djf.index[0] == 2002 and len(djf) == 23       # Dec 2000 is not in the file
    m = pavlodar.monthly["T2M"]
    dec01, jan02, feb02 = float(m["2001-12"]), float(m["2002-01"]), float(m["2002-02"])
    assert djf.loc[2002] == pytest.approx((dec01 * 31 + jan02 * 31 + feb02 * 28) / 90)


# ---- 10. empty or partial responses ------------------------------------------------------

@pytest.mark.parametrize("body", [b"", b"   ", b"<html>503</html>", b"[]", b"{}",
                                   b'{"properties": {"parameter": {}}}'])
def test_empty_or_non_json_bodies_are_rejected(body):
    with pytest.raises(PowerFormatError):
        parse_power_monthly(body)


def test_http_200_with_missing_months_is_rejected():
    doc = make_power_json({"X": np.arange(36.0)})
    for k in ("200206", "200207"):
        del doc["properties"]["parameter"]["X"][k]
    with pytest.raises(PowerFormatError, match="partial response"):
        parse_power_monthly(doc)


def test_missing_requested_parameter_or_short_period_is_rejected(pavlodar_bytes):
    with pytest.raises(PowerFormatError, match="requested parameters missing"):
        parse_power_monthly(pavlodar_bytes, expect_parameters=["T2M", "WS2M"])
    with pytest.raises(PowerFormatError, match="period mismatch"):
        parse_power_monthly(pavlodar_bytes, expect_end=2025)


# ---- 11. the cache must describe the region it is used for -----------------------------

def test_wrong_region_in_response_is_rejected(pavlodar_bytes):
    with pytest.raises(PowerFormatError, match="region mismatch"):
        parse_power_monthly(pavlodar_bytes, expect_lat=43.24, expect_lon=76.95)


def test_cache_file_swapped_for_another_region_is_detected(tmp_store):
    victim = tmp_store.raw_dir / "power_monthly_point_lat52.29_lon76.97_2001-2024_PRECTOTCORR-RH2M-T2M_AG.json"
    victim.write_bytes(ALMATY_RAW.read_bytes())           # valid NASA file, wrong place
    with pytest.raises(PowerFormatError, match="SHA-256"):
        tmp_store.load(52.29, 76.97, 2001, 2024, PARAMS)
    # even with a forged hash the geometry check still refuses it
    rec_path = tmp_store.prov_dir / (victim.stem + ".provenance.json")
    rec = json.loads(rec_path.read_text())
    rec["sha256"] = sha256_bytes(victim.read_bytes())
    rec_path.write_text(json.dumps(rec))
    with pytest.raises(PowerFormatError, match="region mismatch"):
        tmp_store.load(52.29, 76.97, 2001, 2024, PARAMS)


def test_tampered_cache_value_is_detected(tmp_store):
    victim = tmp_store.raw_dir / "power_monthly_point_lat52.29_lon76.97_2001-2024_PRECTOTCORR-RH2M-T2M_AG.json"
    victim.write_bytes(victim.read_bytes().replace(b'"200101":-18.11', b'"200101":-18.12'))
    with pytest.raises(PowerFormatError, match="SHA-256"):
        tmp_store.load(52.29, 76.97, 2001, 2024, PARAMS)


def test_uncached_region_offline_raises_instead_of_inventing_data(store):
    with pytest.raises(DataUnavailable, match="no data will be invented"):
        store.load(51.17, 71.43, 2001, 2024, PARAMS)


def test_sub_period_and_tiled_period_come_from_verified_files(store):
    sub = store.load(52.29, 76.97, 2005, 2020, PARAMS)
    assert len(sub.monthly) == 16 * 12 and str(sub.monthly.index[0]) == "2005-01"
    long = store.load(52.29, 76.97, 1981, 2024, PARAMS)
    assert len(long.monthly) == 44 * 12 and len(long.provenance) == 2
    assert long.monthly.index.is_monotonic_increasing and not long.monthly.index.has_duplicates
    assert long.data_hash != sub.data_hash


def test_canonical_hash_ignores_server_timings_but_not_values(pavlodar_bytes):
    a = json.loads(pavlodar_bytes)
    b = copy.deepcopy(a)
    b["times"]["data"] = 9.99                               # differs on every real request
    assert canonical_data_hash(a) == canonical_data_hash(b)
    b["properties"]["parameter"]["T2M"]["200101"] = -18.12
    assert canonical_data_hash(a) != canonical_data_hash(b)
