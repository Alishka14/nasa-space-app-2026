"""Evidence Engine: every conclusion is a record that can be recomputed.

A record's ``id`` is derived from what defines it (claim type, region, period,
variables, method, parameters, data hash), so the same analysis on the same
bytes always produces the same id, and a change of data or method produces a
new one. Nothing here calls an LLM.

Status follows the MIZAN ladder. A record as a whole is only ever
``OBSERVED`` (computed on real data) or ``HYPOTHESIS`` (a proposed, untested
explanation). Replication is tracked per VALUE, not per record: a number
inside a record is listed in ``replicated_values`` when an independent report
of the same quantity (another assessor, independently obtained data) is
registered and agrees within its stated tolerance. A record's claim usually
contains more than the replicated numbers, so the record itself is not
promoted.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .guard import CLAIM_TYPES, STATUS_ORDER, enforce


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


@dataclass
class EvidenceRecord:
    id: str
    claim: str
    claim_type: str
    region: dict[str, Any]
    period: list[int]
    variables: list[str]
    method: str
    parameters: dict[str, Any]
    data_hash: str
    result: dict[str, Any]
    uncertainty: dict[str, Any]
    status: str
    supporting_evidence: list[str]
    counterevidence: list[str]
    limitations: list[str]
    alternatives: list[str] = field(default_factory=list)
    verdict: str | None = None
    independent_reports: list[dict[str, Any]] = field(default_factory=list)
    replicated_values: list[str] = field(default_factory=list)
    engine_version: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def make_record(*, claim: str, claim_type: str, region: dict[str, Any], period: list[int],
                variables: list[str], method: str, parameters: dict[str, Any], data_hash: str,
                result: dict[str, Any], uncertainty: dict[str, Any], status: str = "OBSERVED",
                supporting_evidence: list[str] | None = None, counterevidence: list[str] | None = None,
                limitations: list[str] | None = None, alternatives: list[str] | None = None,
                verdict: str | None = None, significant: bool | None = None,
                engine_version: str = "") -> EvidenceRecord:
    if claim_type not in CLAIM_TYPES:
        raise ValueError(f"unknown claim_type {claim_type!r}")
    if status not in STATUS_ORDER:
        raise ValueError(f"unknown status {status!r}")
    if status not in ("OBSERVED", "HYPOTHESIS"):
        raise ValueError("the engine may only assign OBSERVED or HYPOTHESIS; "
                         "higher statuses require a registered independent report")
    if not data_hash:
        raise ValueError("an evidence record needs the hash of the data it was computed from")
    # every published sentence must pass the guard
    enforce(claim, claim_type, status=status, significant=significant)
    for line in (supporting_evidence or []) + (counterevidence or []):
        enforce(line, claim_type, status=status, significant=None if significant is None else significant)
    core = {"claim_type": claim_type, "region": region, "period": period, "variables": sorted(variables),
            "method": method, "parameters": parameters, "data_hash": data_hash}
    rid = "EV-" + hashlib.sha256(_canonical(core).encode("utf-8")).hexdigest()[:12]
    return EvidenceRecord(
        id=rid, claim=claim, claim_type=claim_type, region=region, period=period, variables=variables,
        method=method, parameters=parameters, data_hash=data_hash, result=result,
        uncertainty=uncertainty, status=status, supporting_evidence=supporting_evidence or [],
        counterevidence=counterevidence or [], limitations=limitations or [],
        alternatives=alternatives or [], verdict=verdict, engine_version=engine_version)


# ---------------------------------------------------------------------------
# Independent reports (replication registry)
# ---------------------------------------------------------------------------

def load_independent_reports(path: str | Path) -> list[dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        return []
    reports: list[dict[str, Any]] = []
    for f in sorted(path.glob("*.json")):
        doc = json.loads(f.read_text(encoding="utf-8"))
        for entry in doc.get("reports", []):
            reports.append({**entry, "source": doc.get("source"), "assessor": doc.get("assessor"),
                            "independence": doc.get("independence"), "scope": doc.get("scope")})
    return reports


def _scope_matches(scope: dict[str, Any], region: dict[str, Any], period: list[int]) -> bool:
    return (abs(scope["latitude"] - region["latitude"]) < 1e-9
            and abs(scope["longitude"] - region["longitude"]) < 1e-9
            and list(scope["period"]) == list(period))


def attach_independent_reports(record: EvidenceRecord, metrics: dict[str, float],
                               reports: list[dict[str, Any]]) -> EvidenceRecord:
    """Compare our metrics with independently reported values for the same
    region, period and quantity. Values that agree are listed as replicated,
    but only if every report matched to this record agrees. The record's own
    status is never changed here."""
    matched = []
    for rep in reports:
        if not _scope_matches(rep["scope"], record.region, record.period):
            continue
        key = rep["metric"]
        if key not in metrics or metrics[key] is None:
            continue
        ours = float(metrics[key])
        diff = abs(ours - float(rep["reported"]))
        matched.append({"metric": key, "source": rep["source"], "assessor": rep["assessor"],
                        "independence": rep["independence"], "reported": rep["reported"],
                        "ours": ours, "abs_diff": diff, "tolerance": rep["tolerance"],
                        "agrees": bool(diff <= rep["tolerance"])})
    if matched:
        record.independent_reports = matched
        if all(m["agrees"] for m in matched) and record.status == "OBSERVED":
            record.replicated_values = [m["metric"] for m in matched]
            record.limitations = record.limitations + [
                "Replication covers the listed numeric values only (two assessors, independently "
                "retrieved data). The rest of this record, and any interpretation, is OBSERVED. Both "
                "assessors are AI systems: human review remains required."]
    return record


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def ledger_markdown(records: list[dict[str, Any]], title: str = "Evidence Ledger") -> str:
    lines = [f"# {title}", "",
             "Each entry can be recomputed from the raw NASA file identified by `data_hash` "
             "with the stated method and parameters. No LLM is involved in the computation.", ""]
    lines += ["| id | status | verdict | variables | period | claim |", "|---|---|---|---|---|---|"]
    for r in records:
        status = r["status"] + (f" · {len(r['replicated_values'])} values replicated" if r.get("replicated_values") else "")
        lines.append(f"| `{r['id']}` | {status} | {r.get('verdict') or ''} | {', '.join(r['variables'])} | "
                     f"{r['period'][0]}–{r['period'][1]} | {r['claim']} |")
    lines.append("")
    for r in records:
        lines += [f"## {r['id']} — {r['status']}", "",
                  f"**Claim.** {r['claim']}", "",
                  f"- **Type:** {r['claim_type']}",
                  f"- **Region:** {r['region'].get('name', '')} ({r['region']['latitude']}, {r['region']['longitude']})",
                  f"- **Period:** {r['period'][0]}–{r['period'][1]}",
                  f"- **Variables:** {', '.join(r['variables'])}",
                  f"- **Method:** {r['method']}",
                  f"- **Parameters:** `{json.dumps(r['parameters'], sort_keys=True)}`",
                  f"- **Data hash:** `{r['data_hash']}`",
                  f"- **Verdict:** {r.get('verdict') or 'n/a'}", ""]
        if r["supporting_evidence"]:
            lines += ["**Evidence**", ""] + [f"- {s}" for s in r["supporting_evidence"]] + [""]
        if r["counterevidence"]:
            lines += ["**Counterevidence**", ""] + [f"- {s}" for s in r["counterevidence"]] + [""]
        if r.get("alternatives"):
            lines += ["**Alternatives not excluded**", ""] + [f"- {s}" for s in r["alternatives"]] + [""]
        if r["limitations"]:
            lines += ["**Limitations**", ""] + [f"- {s}" for s in r["limitations"]] + [""]
        if r.get("independent_reports"):
            lines += ["**Independent reports** (values that agree are REPLICATED; the record stays OBSERVED)", "",
                      "| metric | source | reported | ours | abs. diff | agrees |", "|---|---|---:|---:|---:|---|"]
            for m in r["independent_reports"]:
                lines.append(f"| {m['metric']} | {m['source']} | {m['reported']} | {m['ours']:.4f} | "
                             f"{m['abs_diff']:.4f} | {'yes' if m['agrees'] else 'NO'} |")
            lines.append("")
    return "\n".join(lines) + "\n"
