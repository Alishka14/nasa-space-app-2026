"""MIZAN Guard and Evidence Engine (test 9 and the evidence invariants)."""
from __future__ import annotations

import copy

import pytest

from conftest import DATA
from earth_senses.evidence import attach_independent_reports, ledger_markdown, load_independent_reports, make_record
from earth_senses.guard import GuardViolation, check_claim, enforce
from earth_senses.investigate import investigate

REGION = {"name": "test", "latitude": 52.29, "longitude": 76.97}


@pytest.fixture(scope="module")
def inv(store):
    return investigate(store, lat=52.29, lon=76.97, start=2001, end=2024, variables=["T2M", "RH2M", "PRECTOTCORR"],
                       region_name="Pavlodar, Kazakhstan", n_perm=400,
                       independent_reports=load_independent_reports(DATA / "independent_reports"))


# ---- 9. unjustified causal conclusions are blocked ---------------------------------------------

CAUSAL = [
    "Higher temperature causes relative humidity to fall.",
    "The humidity increase is due to more precipitation.",
    "Precipitation drives humidity in Pavlodar.",
    "Warming leads to drier air.",
    "Humidity rises because of rainfall.",
    "Temperature determines humidity one month later.",
    "Рост температуры вызывает снижение влажности.",
    "Влажность растёт из-за осадков.",
    "Осадки приводят к росту влажности.",
    "Температура влияет на влажность.",
]


@pytest.mark.parametrize("text", CAUSAL)
def test_causal_wording_on_a_statistical_result_is_blocked(text):
    v = check_claim(text, "statistical_relationship")
    assert not v["allowed"] and any(x["rule"] == "CAUSAL_LANGUAGE" for x in v["violations"])
    with pytest.raises(GuardViolation):
        enforce(text, "computed_observation")


@pytest.mark.parametrize("text", [
    "Monthly anomalies of temperature and humidity vary in opposite directions (r = -0.32).",
    "No statistically significant monotonic trend was detected over 2001-2024.",
    "Аномалии осадков и влажности изменяются согласованно (r = +0.59).",
])
def test_associational_wording_passes(text):
    assert check_claim(text, "statistical_relationship")["allowed"]


def test_mechanism_is_admissible_only_as_a_labelled_hypothesis():
    text = "Warmer air causes lower relative humidity at fixed moisture."
    assert not check_claim(text, "unverified_physical_explanation", status="HYPOTHESIS")["allowed"]   # no label
    labelled = "Hypothesis (untested here): " + text
    assert not check_claim(labelled, "unverified_physical_explanation", status="OBSERVED")["allowed"]  # wrong status
    ok = check_claim(labelled, "unverified_physical_explanation", status="HYPOTHESIS")
    assert ok["allowed"] and ok["required_label"].startswith("HYPOTHESIS")


@pytest.mark.parametrize("text", [
    "There is no warming in Pavlodar.", "The data show no trend in temperature.",
    "Temperature has not changed since 2001.", "The atmosphere has no memory beyond one month.",
    "В Павлодаре нет потепления.", "Тренд отсутствует: отсутствие тренда подтверждено.",
])
def test_non_significance_may_not_be_worded_as_absence(text):
    v = check_claim(text, "computed_observation", significant=False)
    assert not v["allowed"] and any(x["rule"] == "ABSENCE_OF_EVIDENCE" for x in v["violations"])


@pytest.mark.parametrize("text", [
    "The one-month lag shows the direction of influence from temperature to humidity.",
    "Humidity responds to temperature with a one-month delay.",
    "Влажность реагирует на температуру с задержкой в месяц.",
])
def test_a_lag_may_not_be_worded_as_direction_of_influence(text):
    v = check_claim(text, "statistical_relationship")
    assert not v["allowed"] and any(x["rule"] == "LAG_AS_DIRECTION" for x in v["violations"])


def test_proof_language_and_status_inflation_are_blocked():
    assert not check_claim("This proves the link between rain and humidity.", "statistical_relationship")["allowed"]
    v = check_claim("The correlation was independently verified and replicated.", "statistical_relationship",
                    status="OBSERVED")
    assert any(x["rule"] == "STATUS_INFLATION" for x in v["violations"])
    assert check_claim("The correlation was replicated by a second assessor.", "statistical_relationship",
                       status="REPLICATED")["allowed"]


def test_scope_notice_for_universal_wording():
    v = check_claim("Humidity and precipitation anomalies always vary together globally.", "statistical_relationship")
    assert any(n["rule"] == "SCOPE" for n in v["notices"])


# ---- the engine holds itself to the same rules ---------------------------------------------------

def test_every_sentence_the_engine_publishes_passes_the_guard(inv):
    for e in inv["evidence"]:
        ctype = e["claim_type"]
        status = "HYPOTHESIS" if e["status"] == "HYPOTHESIS" else "OBSERVED"
        for line in [e["claim"], *e["supporting_evidence"], *e["counterevidence"]]:
            assert check_claim(line, ctype, status=status)["allowed"], line
    for t in inv["trends"].values():
        assert check_claim(t["statement"], "computed_observation")["allowed"]
    for r in inv["relationships"]:
        assert check_claim(r["statement"], "statistical_relationship")["allowed"]
        assert check_claim(r["lag_statement"], "statistical_relationship")["allowed"]
    for ep in inv["episodes"]:
        for step in ep["steps"]:
            if step["stage"] == "Hypothesis":
                assert check_claim(step["text"], "exploratory_hypothesis", status="HYPOTHESIS")["allowed"], step
            else:
                assert check_claim(step["text"], "computed_observation")["allowed"], step["text"]


def test_engine_cannot_be_made_to_publish_a_causal_claim_or_a_high_status():
    base = dict(claim_type="statistical_relationship", region=REGION, period=[2001, 2024], variables=["A", "B"],
                method="m", parameters={}, data_hash="abc", result={}, uncertainty={})
    with pytest.raises(GuardViolation):
        make_record(claim="A causes B.", **base)
    with pytest.raises(GuardViolation):
        make_record(claim="A and B vary together.", supporting_evidence=["B rises because of A."], **base)
    with pytest.raises(ValueError, match="OBSERVED or HYPOTHESIS"):
        make_record(claim="A and B vary together.", status="REPLICATED", **base)
    with pytest.raises(ValueError, match="hash"):
        make_record(claim="A and B vary together.", **{**base, "data_hash": ""})


# ---- evidence invariants ------------------------------------------------------------------------------

REQUIRED = ["id", "claim", "region", "period", "variables", "method", "parameters", "data_hash", "result",
            "uncertainty", "status", "supporting_evidence", "counterevidence", "limitations"]


def test_every_result_has_a_complete_evidence_record(inv):
    ids = [e["id"] for e in inv["evidence"]]
    assert len(ids) == len(set(ids))
    for e in inv["evidence"]:
        assert all(k in e for k in REQUIRED), e["id"]
        assert e["data_hash"] == inv["data_hash"] and e["period"] == [2001, 2024]
        assert e["status"] in ("OBSERVED", "REPLICATED", "HYPOTHESIS")
    for t in inv["trends"].values():
        assert t["evidence_id"] in ids
    for r in inv["relationships"]:
        assert r["evidence_id"] in ids and r["lag_evidence_id"] in ids


def test_no_graph_edge_exists_without_computed_evidence(inv):
    by_id = {e["id"]: e for e in inv["evidence"]}
    assert len(inv["graph"]["edges"]) == 3
    for edge in inv["graph"]["edges"]:
        ev = by_id[edge["evidence_id"]]
        assert ev["claim_type"] == "statistical_relationship"            # never a hypothesis
        assert ev["result"]["r_detrended"] == pytest.approx(edge["r_detrended"])
        if edge["hypothesis_id"]:
            hyp = by_id[edge["hypothesis_id"]]
            assert hyp["status"] == "HYPOTHESIS" and hyp["verdict"] == "UNTESTED" and hyp["result"] == {}
    hyp_ids = {e["id"] for e in inv["evidence"] if e["status"] == "HYPOTHESIS"}
    assert hyp_ids and not hyp_ids & {edge["evidence_id"] for edge in inv["graph"]["edges"]}


def test_evidence_ids_are_deterministic_and_change_with_the_data(store, inv):
    again = investigate(store, lat=52.29, lon=76.97, start=2001, end=2024, variables=["T2M", "RH2M", "PRECTOTCORR"],
                        region_name="Pavlodar, Kazakhstan", n_perm=400,
                        independent_reports=load_independent_reports(DATA / "independent_reports"))
    assert [e["id"] for e in again["evidence"]] == [e["id"] for e in inv["evidence"]]
    assert again["trends"]["RH2M"]["summary"] == inv["trends"]["RH2M"]["summary"]
    other = investigate(store, lat=52.29, lon=76.97, start=2005, end=2024, variables=["T2M", "RH2M", "PRECTOTCORR"],
                        n_perm=200)
    assert other["data_hash"] != inv["data_hash"]
    assert not {e["id"] for e in other["evidence"]} & {e["id"] for e in inv["evidence"]}


def test_variable_order_does_not_change_pair_ids_or_lag_signs(store, inv):
    shuffled = investigate(store, lat=52.29, lon=76.97, start=2001, end=2024,
                           variables=["PRECTOTCORR", "T2M", "RH2M"], n_perm=400)
    assert [r["id"] for r in shuffled["relationships"]] == [r["id"] for r in inv["relationships"]]
    assert shuffled["relationships"][1]["lags"]["rows"] == inv["relationships"][1]["lags"]["rows"]


# ---- replication status ---------------------------------------------------------------------------------

def test_replicated_only_where_an_independent_report_agrees(inv, store):
    statuses = {e["id"]: e["status"] for e in inv["evidence"]}
    rep = [e for e in inv["evidence"] if e["independent_reports"]]
    assert rep and all(e["status"] == "REPLICATED" for e in rep)
    assert all(m["agrees"] for e in rep for m in e["independent_reports"])
    assert sum(len(e["independent_reports"]) for e in rep) == 16          # every registered Gemini value
    no_report = [e for e in inv["evidence"] if not e["independent_reports"]]
    assert no_report and all(e["status"] in ("OBSERVED", "HYPOTHESIS") for e in no_report)
    # the P-RH lag scan was not reported by anyone else: it must stay OBSERVED
    lag = next(e for e in inv["evidence"] if e["variables"] == ["PRECTOTCORR", "RH2M"] and "Lag scan" in e["claim"])
    assert statuses[lag["id"]] == "OBSERVED"
    # another period or place: no report applies, nothing is promoted
    other = investigate(store, lat=52.29, lon=76.97, start=2005, end=2024, variables=["T2M", "RH2M"], n_perm=200,
                        independent_reports=load_independent_reports(DATA / "independent_reports"))
    assert all(e["status"] != "REPLICATED" for e in other["evidence"])
    almaty = investigate(store, lat=43.24, lon=76.95, start=2001, end=2024, variables=["T2M", "RH2M"], n_perm=200,
                         independent_reports=load_independent_reports(DATA / "independent_reports"))
    assert all(e["status"] != "REPLICATED" for e in almaty["evidence"])


def test_a_disagreeing_report_blocks_promotion():
    rec = make_record(claim="A and B vary together.", claim_type="statistical_relationship", region=REGION,
                      period=[2001, 2024], variables=["A", "B"], method="m", parameters={}, data_hash="abc",
                      result={}, uncertainty={})
    scope = {"latitude": 52.29, "longitude": 76.97, "period": [2001, 2024]}
    good = {"metric": "r", "reported": 0.50, "tolerance": 0.001, "scope": scope, "source": "s", "assessor": "a",
            "independence": "i"}
    bad = {**good, "reported": 0.70}
    a = attach_independent_reports(copy.deepcopy(rec), {"r": 0.5004}, [good])
    assert a.status == "REPLICATED" and any("numeric values only" in x for x in a.limitations)
    b = attach_independent_reports(copy.deepcopy(rec), {"r": 0.5004}, [good, bad])
    assert b.status == "OBSERVED" and not b.independent_reports[1]["agrees"]
    c = attach_independent_reports(copy.deepcopy(rec), {"r": 0.5004}, [{**good, "scope": {**scope, "period": [1981, 2024]}}])
    assert c.status == "OBSERVED" and c.independent_reports == []


def test_ledger_renders_every_record(inv):
    md = ledger_markdown(inv["evidence"])
    for e in inv["evidence"]:
        assert e["id"] in md
    assert "Counterevidence" in md and "Independent reports" in md
