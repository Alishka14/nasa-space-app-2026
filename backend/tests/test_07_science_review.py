"""Science-review additions (FINAL DELIVERY): a variable that is computed from
another one, partial correlations, a real all-missing NASA variable, and
variables assembled from more than one verified file.

REAL data only, except the two tests marked SYNTHETIC, which use series with
a known answer as controls for the new functions.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pytest

os.environ["EARTH_SENSES_OFFLINE"] = "1"

from fastapi.testclient import TestClient  # noqa: E402

from conftest import DATA  # noqa: E402
from earth_senses.api import app  # noqa: E402
from earth_senses.catalog import DERIVED, VARIABLES  # noqa: E402
from earth_senses.derived import rh_from_t_q, saturation_vapour_pressure_hpa, standard_pressure_hpa  # noqa: E402
from earth_senses.investigate import investigate  # noqa: E402
from earth_senses.normalize import parse_power_monthly  # noqa: E402
from earth_senses.power_client import MISSING_CHECK  # noqa: E402
from earth_senses.relationships import correlate, partial_correlation  # noqa: E402

client = TestClient(app)
AUDIT_RAW = DATA / "raw" / "power" / "power_monthly_point_lat52.29_lon76.97_2001-2024_IMERG_PRECTOT-QV2M_AG.json"
AUDIT_SHA = "978b737e26d8e1c4b2b0de4e605b3952934da4fcacb2bc4ac3646055459c768c"
PAV = {"latitude": 52.29, "longitude": 76.97, "start": 2001, "end": 2024, "region_name": "Pavlodar, Kazakhstan"}

# Evidence ids and data hash of the default investigation as they were BEFORE the
# science-review changes. The additions must not silently re-key existing evidence.
BASELINE_HASH = "d9bebf2c77a09f4947ab24c7dd750d64e9dd9059a8324fde9dffdf85efcba0ea"
BASELINE_IDS = ["EV-7997ff910553", "EV-a28cc417ed2b", "EV-183c60c7f20d", "EV-3b6b68c6f1e3", "EV-3f760323195e",
                "EV-b14da6e2225f", "EV-5eb092cbce35", "EV-01be4b227209", "EV-85f154766dfc", "EV-d6888d4dbe3b",
                "EV-5f08da1044a1", "EV-7591f20da4ac", "EV-9d3a30f880bb"]


@pytest.fixture(scope="module")
def inv3():
    r = client.post("/api/investigate", json=PAV)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture(scope="module")
def inv4():
    r = client.post("/api/investigate", json={**PAV, "variables": ["T2M", "RH2M", "PRECTOTCORR", "QV2M"]})
    assert r.status_code == 200, r.text
    return r.json()


def rel(inv, pair):
    return next(r for r in inv["relationships"] if r["id"] == pair)


# ---- a real NASA variable that is entirely missing -------------------------------------------

def test_real_imerg_file_is_all_fill_values_and_is_stored_as_evidence_of_that():
    import hashlib
    raw = AUDIT_RAW.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == AUDIT_SHA
    obj = json.loads(raw)
    block = obj["properties"]["parameter"]["IMERG_PRECTOT"]
    assert len(block) == 312 and set(block.values()) == {obj["header"]["fill_value"]} == {-999.0}
    norm = parse_power_monthly(raw, expect_lat=52.29, expect_lon=76.97, expect_start=2001, expect_end=2024)
    assert norm.missing == {"QV2M": 0, "IMERG_PRECTOT": 288}
    assert norm.monthly["IMERG_PRECTOT"].isna().all() and norm.monthly["QV2M"].notna().all()
    assert norm.units["QV2M"] == "g/kg" == VARIABLES["QV2M"]["expected_units"]


def test_provenance_of_the_file_with_gaps_says_so():
    rec = json.loads((DATA / "provenance" / (AUDIT_RAW.stem + ".provenance.json")).read_text())
    assert rec["sha256"] == AUDIT_SHA
    assert rec["validation_status"] == "VALIDATED_WITH_MISSING_DATA"
    missing = next(c for c in rec["validation_checks"] if c["check"] == MISSING_CHECK)
    assert missing["passed"] is False and missing["detail"]["IMERG_PRECTOT"] == 288
    # the three original files have no gaps and keep their status
    for path in (DATA / "provenance").glob("*PRECTOTCORR-RH2M-T2M*.provenance.json"):
        assert json.loads(path.read_text())["validation_status"] == "VALIDATED"


def test_the_all_missing_variable_is_refused_and_no_number_is_produced():
    r = client.post("/api/investigate", json={**PAV, "variables": ["T2M", "IMERG_PRECTOT"]})
    assert r.status_code == 422
    assert "IMERG_PRECTOT has missing months" in r.json()["detail"]
    r = client.post("/api/investigate", json={**PAV, "variables": ["IMERG_PRECTOT"]})
    assert r.status_code == 422


# ---- variables assembled from two verified files ----------------------------------------------

def test_existing_evidence_ids_and_data_hash_did_not_change(inv3):
    assert inv3["data_hash"] == BASELINE_HASH
    assert [e["id"] for e in inv3["evidence"]] == BASELINE_IDS
    assert inv3["derived_checks"] == []


def test_four_variables_come_from_two_verified_files(inv4):
    shas = {p["sha256"] for p in inv4["provenance"]}
    assert AUDIT_SHA in shas and len(shas) == 2
    assert inv4["data_hash"] != BASELINE_HASH                       # different inputs, different hash
    raw = json.loads(AUDIT_RAW.read_bytes())["properties"]["parameter"]["QV2M"]
    months = inv4["series"]["months"]
    for i in (0, 100, 287):                                          # what is shown is what NASA sent
        assert inv4["series"]["raw"]["QV2M"][i] == raw[months[i].replace("-", "")]
    assert inv4["variables"]["QV2M"]["units"] == "g/kg"
    assert not any("IMERG" in w for w in inv4["warnings"])          # the unused variable's gaps are not ours
    assert any("assembled from 2 verified raw files" in w for w in inv4["warnings"])
    dv = inv4["evidence"][0]
    assert dv["verdict"] == "CHECKS_PASSED" and " 0 missing" in dv["claim"]


def test_adding_a_variable_does_not_change_the_other_pairs(inv3, inv4):
    for pair in ("T2M-PRECTOTCORR", "T2M-RH2M", "PRECTOTCORR-RH2M"):
        a, b = rel(inv3, pair), rel(inv4, pair)
        for key in ("raw", "deseasonalized", "detrended"):
            assert a[key]["pearson_r"] == pytest.approx(b[key]["pearson_r"], abs=1e-12)


# ---- partial correlation -----------------------------------------------------------------------

def test_partial_correlation_removes_a_shared_driver_synthetic():
    """SYNTHETIC control: x and y share only z, so the association vanishes when z is held fixed."""
    rng = np.random.default_rng(7)
    z = rng.normal(size=4000)
    x, y = z + rng.normal(size=4000), z + rng.normal(size=4000)
    assert correlate(x, y)["pearson_r"] == pytest.approx(0.5, abs=0.05)
    pc = partial_correlation(x, y, [z])
    assert abs(pc["pearson_r"]) < 0.05 and pc["ci95_adjusted"][0] < 0 < pc["ci95_adjusted"][1]
    assert pc["n_controls"] == 1


def test_partial_correlation_keeps_a_direct_link_synthetic():
    """SYNTHETIC control: y depends on x itself; holding an unrelated series fixed changes nothing."""
    rng = np.random.default_rng(8)
    x, z = rng.normal(size=3000), rng.normal(size=3000)
    y = 0.8 * x + rng.normal(scale=0.6, size=3000)
    assert partial_correlation(x, y, [z])["pearson_r"] == pytest.approx(correlate(x, y)["pearson_r"], abs=0.01)


def test_partial_correlation_matches_the_textbook_formula_on_real_data(inv3):
    r = {p: rel(inv3, p)["detrended"]["pearson_r"] for p in ("T2M-PRECTOTCORR", "T2M-RH2M", "PRECTOTCORR-RH2M")}
    r_pr, r_pt, r_rt = r["PRECTOTCORR-RH2M"], r["T2M-PRECTOTCORR"], r["T2M-RH2M"]
    expected = (r_pr - r_pt * r_rt) / np.sqrt((1 - r_pt ** 2) * (1 - r_rt ** 2))
    got = rel(inv3, "PRECTOTCORR-RH2M")["partial"][0]
    assert got["controls"] == ["T2M"]
    assert got["pearson_r"] == pytest.approx(expected, abs=1e-9)


def test_precipitation_humidity_link_survives_holding_temperature_and_moisture_fixed(inv4):
    """The demo story: is the +0.59 only temperature acting on relative humidity? Measured: no."""
    r = rel(inv4, "PRECTOTCORR-RH2M")
    assert r["detrended"]["pearson_r"] == pytest.approx(0.590, abs=0.001)
    by = {tuple(p["controls"]): p for p in r["partial"]}
    assert by[("T2M",)]["pearson_r"] == pytest.approx(0.586, abs=0.001)
    assert by[("QV2M",)]["pearson_r"] == pytest.approx(0.543, abs=0.001)
    both = by[("T2M", "QV2M")]
    assert both["pearson_r"] == pytest.approx(0.440, abs=0.001) and both["ci95_adjusted"][0] > 0.2
    # the weak temperature-precipitation link does not survive holding humidity fixed
    weak = {tuple(p["controls"]): p for p in rel(inv4, "T2M-PRECTOTCORR")["partial"]}[("RH2M",)]
    assert weak["ci95_adjusted"][0] < 0 < weak["ci95_adjusted"][1]


# ---- relative humidity is computed from temperature and moisture --------------------------------

def test_humidity_formula_against_known_values():
    assert saturation_vapour_pressure_hpa(0.0) == pytest.approx(6.112)
    assert saturation_vapour_pressure_hpa(20.0) == pytest.approx(23.33, abs=0.05)      # textbook: 23.4 hPa
    assert standard_pressure_hpa(0.0) == pytest.approx(1013.25)
    assert standard_pressure_hpa(1500.0) == pytest.approx(845.6, abs=0.5)
    # saturated air: q_s = 0.622 e_s / (p - 0.378 e_s)
    es = float(saturation_vapour_pressure_hpa(15.0))
    q_sat = 1000 * 0.622 * es / (1000.0 - 0.378 * es)
    assert float(rh_from_t_q(15.0, q_sat, 1000.0)) == pytest.approx(100.0, abs=1e-9)
    assert float(rh_from_t_q(15.0, q_sat / 2, 1000.0)) == pytest.approx(50.0, abs=0.4)
    # same moisture, warmer air -> lower relative humidity
    assert float(rh_from_t_q(25.0, q_sat, 1000.0)) < 60.0


def test_temperature_humidity_edge_is_flagged_as_built_in(inv3, inv4):
    assert DERIVED["RH2M"]["depends_on"] == ["T2M", "QV2M"]
    sd = rel(inv3, "T2M-RH2M")["structural_dependence"]
    assert sd["derived"] == "RH2M" and sd["input"] == "T2M" and sd["evidence_id"] is None
    assert rel(inv3, "PRECTOTCORR-RH2M")["structural_dependence"] is None
    assert rel(inv3, "T2M-PRECTOTCORR")["structural_dependence"] is None
    edge = next(e for e in inv3["graph"]["edges"] if e["id"] == "T2M-RH2M")
    assert edge["structural_dependence"]["derived"] == "RH2M"
    ev = next(e for e in inv3["evidence"] if e["id"] == rel(inv3, "T2M-RH2M")["evidence_id"])
    assert any("built into the definition" in c for c in ev["counterevidence"])
    assert any("computed from the first" in c for c in inv3["cannot_conclude"])
    # with specific humidity selected both humidity edges are flagged and point to the check
    assert {r["id"] for r in inv4["relationships"] if r["structural_dependence"]} == {"T2M-RH2M", "RH2M-QV2M"}
    check_id = inv4["derived_checks"][0]["evidence_id"]
    assert rel(inv4, "T2M-RH2M")["structural_dependence"]["evidence_id"] == check_id


def test_derived_variable_check_on_real_data(inv4):
    chk = inv4["derived_checks"][0]
    rc, fit = chk["reconstruction"], chk["linear_fit_of_anomalies"]
    assert chk["verdict"] == "DERIVED_VARIABLE_CONFIRMED"
    assert chk["assumed_pressure_hpa"] == pytest.approx(standard_pressure_hpa(inv4["region"]["grid_cell_elevation_m"]))
    assert rc["r_raw"] == pytest.approx(0.982, abs=0.001)            # nothing fitted
    assert rc["mean_abs_error_pp"] == pytest.approx(2.60, abs=0.01)
    assert fit["overall"]["r_squared"] == pytest.approx(0.504, abs=0.002)
    assert fit["by_season"]["JJA"]["r_squared"] == pytest.approx(0.980, abs=0.002)
    assert fit["by_season"]["DJF"]["r_squared"] == pytest.approx(0.193, abs=0.002)
    ev = next(e for e in inv4["evidence"] if e["id"] == chk["evidence_id"])
    assert ev["status"] == "OBSERVED" and sorted(ev["variables"]) == ["QV2M", "RH2M", "T2M"]
    assert ev["data_hash"] == inv4["data_hash"]
    assert "DJF" in ev["counterevidence"][0]                          # the weak season is reported, not hidden


def test_moisture_content_and_relative_humidity_respond_to_temperature_with_opposite_signs(inv4):
    """Golden values for the test the temperature-humidity hypothesis asked for."""
    t_q, t_rh = rel(inv4, "T2M-QV2M"), rel(inv4, "T2M-RH2M")
    assert t_q["detrended"]["pearson_r"] == pytest.approx(0.549, abs=0.001) and t_q["status"] == "SUPPORTED"
    assert t_rh["detrended"]["pearson_r"] == pytest.approx(-0.316, abs=0.001)
    held = {tuple(p["controls"]): p["pearson_r"] for p in t_rh["partial"]}
    assert held[("QV2M",)] == pytest.approx(-0.657, abs=0.001)       # stronger once moisture is held fixed
    # the explanation itself is still labelled as a hypothesis
    hyp = next(e for e in inv4["evidence"] if e["id"] == t_rh["hypothesis_id"])
    assert hyp["status"] == "HYPOTHESIS" and hyp["verdict"] == "UNTESTED"


def test_catalog_lists_derived_variables_and_the_unavailable_imerg_parameter():
    cat = client.get("/api/catalog").json()
    assert cat["derived"]["RH2M"]["depends_on"] == ["T2M", "QV2M"]
    assert cat["variables"]["QV2M"]["verified"] is True
    assert cat["variables"]["IMERG_PRECTOT"]["verified"] is False
    assert any(c["sha256"] == AUDIT_SHA for c in cat["cached_datasets"])


def test_all_year_precipitation_humidity_value_is_weighted_towards_the_warm_season(inv3):
    """With every calendar month weighted equally the +0.59 drops to +0.37, and winter shows nothing."""
    r = rel(inv3, "PRECTOTCORR-RH2M")
    assert r["month_standardized"]["pearson_r"] == pytest.approx(0.367, abs=0.001)
    seasons = {k: v["r"] for k, v in r["by_season"]["seasons"].items()}
    assert abs(seasons["DJF"]) < 0.1 and min(seasons["MAM"], seasons["JJA"], seasons["SON"]) > 0.5
    ev = next(e for e in inv3["evidence"] if e["id"] == r["evidence_id"])
    assert any("weighted towards the months with the largest variance" in c for c in ev["counterevidence"])
    # the temperature-humidity value does not shrink under equal weighting, so no such line there
    t_rh = rel(inv3, "T2M-RH2M")
    assert abs(t_rh["month_standardized"]["pearson_r"]) > abs(t_rh["deseasonalized"]["pearson_r"])
    ev = next(e for e in inv3["evidence"] if e["id"] == t_rh["evidence_id"])
    assert not any("weighted towards" in c for c in ev["counterevidence"])


def test_standardize_by_month_gives_every_month_unit_variance_synthetic():
    """SYNTHETIC control."""
    import pandas as pd
    from earth_senses.relationships import standardize_by_month
    rng = np.random.default_rng(3)
    idx = pd.period_range("2001-01", periods=240, freq="M")
    scale = np.where(np.isin(idx.month, (6, 7, 8)), 10.0, 1.0)
    s = pd.Series(rng.normal(size=240) * scale, index=idx)
    z = standardize_by_month(s - s.groupby(s.index.month).transform("mean"))
    assert np.allclose(z.groupby(z.index.month).std(), 1.0)
