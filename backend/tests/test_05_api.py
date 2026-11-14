"""API contract: what the interface shows is what the engines computed from
the NASA bytes (Ghost Busters: 'the chart shows other data than the API')."""
from __future__ import annotations

import json
import os

import pytest

os.environ["EARTH_SENSES_OFFLINE"] = "1"       # tests never touch the network

from fastapi.testclient import TestClient  # noqa: E402

from conftest import PAVLODAR_RAW  # noqa: E402
from earth_senses.api import app  # noqa: E402

client = TestClient(app)
PAV = {"latitude": 52.29, "longitude": 76.97, "start": 2001, "end": 2024, "region_name": "Pavlodar, Kazakhstan"}


@pytest.fixture(scope="module")
def inv():
    r = client.post("/api/investigate", json=PAV)
    assert r.status_code == 200, r.text
    return r.json()


def test_health_and_catalog():
    h = client.get("/api/health").json()
    assert h["status"] == "ok" and h["network_allowed"] is False and h["cached_datasets"] >= 3
    cat = client.get("/api/catalog").json()
    assert {"T2M", "RH2M", "PRECTOTCORR"} <= set(cat["variables"])
    assert all(cat["variables"][v]["definition"] for v in cat["variables"])      # plain-language definitions
    pav = next(r for r in cat["regions"] if r["id"] == "pavlodar")
    assert [1981, 2000] in pav["cached_periods"] and [2001, 2024] in pav["cached_periods"]


def test_series_in_the_response_are_the_values_in_the_raw_nasa_file(inv):
    raw = json.loads(PAVLODAR_RAW.read_bytes())["properties"]["parameter"]
    months = inv["series"]["months"]
    assert len(months) == 288 and months[0] == "2001-01" and months[-1] == "2024-12"
    for var in ("T2M", "RH2M", "PRECTOTCORR"):
        values = inv["series"]["raw"][var]
        assert len(values) == 288
        for i in (0, 1, 143, 287):
            key = months[i].replace("-", "")
            assert values[i] == raw[var][key], (var, key)
        # anomalies + climatology rebuild the raw series exactly: the chart layers are consistent
        clim, anom = inv["series"]["climatology"][var], inv["series"]["anomaly"][var]
        for i in (0, 100, 287):
            assert anom[i] + clim[int(months[i][5:]) - 1] == pytest.approx(values[i], abs=1e-9)
    assert inv["provenance"][0]["sha256"] == "8a65f9e56b005f77eec3783a09903ad2842031590cc0c8084441d92b19f87de6"
    assert inv["data_source"] == "cache"


def test_response_carries_everything_the_console_needs(inv):
    for key in ("provenance", "trends", "relationships", "graph", "evidence", "episodes", "limitations",
                "cannot_conclude", "decision_rules", "variables"):
        assert inv[key], key
    assert inv["region"]["grid_cell_elevation_m"] == pytest.approx(110.97)
    t = inv["trends"]["PRECTOTCORR"]
    assert t["slope_units"] == "mm/day per year" and t["annual_total"]["slope_units"] == "mm/year per year"
    assert inv["trends"]["T2M"]["slope_units"] == "°C/year"
    assert inv["trends"]["RH2M"]["slope_units"] == "percentage points/year"
    assert json.dumps(inv)                                    # no NaN / numpy leftovers


def test_evidence_endpoint_returns_the_record_behind_a_result(inv):
    eid = inv["relationships"][0]["evidence_id"]
    r = client.get(f"/api/evidence/{eid}")
    assert r.status_code == 200 and r.json()["id"] == eid and r.json()["data_hash"] == inv["data_hash"]
    assert client.get("/api/evidence/EV-does-not-exist").status_code == 404


def test_uncached_region_offline_is_an_error_not_invented_data():
    r = client.post("/api/investigate", json={**PAV, "latitude": 51.17, "longitude": 71.43})
    assert r.status_code == 503 and "no data will be invented" in r.json()["detail"]


@pytest.mark.parametrize("patch", [
    {"start": 2020, "end": 2024},                    # too short for a climatology
    {"start": 1975},                                 # before the product begins
    {"end": 2099},                                   # future
    {"variables": ["T2M; DROP"]},                    # not a parameter name
    {"baseline_start": 2001, "baseline_end": 2004},  # baseline too short
    {"baseline_start": 1990, "baseline_end": 2010},  # baseline outside the period
])
def test_bad_requests_are_rejected_with_a_reason(patch):
    r = client.post("/api/investigate", json={**PAV, **patch})
    assert r.status_code == 422 and r.json()["detail"]


def test_period_and_variables_can_be_chosen(inv):
    r = client.post("/api/investigate", json={**PAV, "start": 1981, "end": 2024, "variables": ["RH2M", "T2M"]})
    j = r.json()
    assert r.status_code == 200 and len(j["series"]["months"]) == 528 and len(j["provenance"]) == 2
    assert j["trends"]["RH2M"]["verdict"] == "NO_SIGNIFICANT_TREND_DETECTED"
    assert inv["trends"]["RH2M"]["verdict"] == "FRAGILE_TREND"       # the conclusion depends on the period
    assert len(j["relationships"]) == 1 and j["data_hash"] != inv["data_hash"]


def test_explicit_baseline_changes_anomalies_but_is_recorded():
    r = client.post("/api/investigate", json={**PAV, "baseline_start": 2001, "baseline_end": 2012})
    j = r.json()
    assert r.status_code == 200 and j["request"]["baseline"] == [2001, 2012]
    rel = next(e for e in j["evidence"] if e["claim_type"] == "statistical_relationship")
    assert rel["parameters"]["baseline"] == [2001, 2012]


def test_two_regions_can_be_compared():
    body = {"region_a": {"name": "Pavlodar", "latitude": 52.29, "longitude": 76.97},
            "region_b": {"name": "Almaty", "latitude": 43.24, "longitude": 76.95}, "start": 2001, "end": 2024}
    r = client.post("/api/compare", json=body)
    j = r.json()
    assert r.status_code == 200 and len(j["variables"]) == 3
    t = next(v for v in j["variables"] if v["variable"] == "T2M")
    assert t["a"]["summary"]["primary_slope"] < 0 < t["b"]["summary"]["primary_slope"]
    assert t["opposite_signs"] and t["verdict"] == "OPPOSITE_SIGNS_NOT_SIGNIFICANT"   # not over-claimed
    assert j["region_b"]["grid_cell_elevation_m"] > 2000          # the cell is not the city: must be visible
    assert j["region_a"]["data_hash"] != j["region_b"]["data_hash"]


def test_guard_endpoint_blocks_a_causal_explanation_submitted_from_outside():
    r = client.post("/api/guard/check", json={"text": "Rainfall causes the humidity trend, which proves the link.",
                                              "claim_type": "statistical_relationship"})
    j = r.json()
    assert r.status_code == 200 and j["allowed"] is False
    assert {"CAUSAL_LANGUAGE", "PROOF_LANGUAGE"} <= {v["rule"] for v in j["violations"]}
    assert client.post("/api/guard/check", json={"text": "x", "claim_type": "nonsense"}).status_code == 422


def test_report_is_generated_from_the_same_investigation(inv):
    md = client.post("/api/report", json=PAV).json()["markdown"]
    assert "8a65f9e56b005f77eec3783a09903ad2842031590cc0c8084441d92b19f87de6" in md
    assert "What cannot be concluded" in md and "Hypotheses — proposed, not tested here" in md
    for e in inv["evidence"]:
        assert e["id"] in md
