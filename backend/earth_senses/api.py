"""FastAPI application for EARTH SENSES.

Run:  uvicorn earth_senses.api:app --app-dir backend --port 8000
Env:  EARTH_SENSES_DATA_DIR  (default: <repo>/data)
      EARTH_SENSES_OFFLINE=1 (serve only the verified cache; never call NASA)
"""
from __future__ import annotations

import os
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import ENGINE_VERSION
from .catalog import DEFAULT_VARIABLES, DERIVED, REGIONS, VARIABLES
from .evidence import load_independent_reports
from .guard import CLAIM_TYPES, STATUS_ORDER, check_claim
from .investigate import compare_regions, investigate
from .normalize import PowerFormatError
from .power_client import POWER_FIRST_YEAR, DataUnavailable, PowerStore
from .report import render_report

REPO = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("EARTH_SENSES_DATA_DIR", REPO / "data"))
OFFLINE = os.environ.get("EARTH_SENSES_OFFLINE", "") == "1"

store = PowerStore(DATA_DIR, allow_network=not OFFLINE)
app = FastAPI(title="EARTH SENSES API", version=ENGINE_VERSION,
              description="Trend and relationship investigation of NASA Earth-system data with evidence records.")
app.add_middleware(CORSMiddleware, allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
                   allow_methods=["*"], allow_headers=["*"])

_results: "OrderedDict[tuple, dict]" = OrderedDict()
_evidence: dict[str, dict] = {}
_MAX_RESULTS = 24


class InvestigateRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    start: int
    end: int
    variables: list[str] = Field(default_factory=lambda: list(DEFAULT_VARIABLES), min_length=1, max_length=6)
    region_name: str | None = None
    baseline_start: int | None = None
    baseline_end: int | None = None
    refresh: bool = False


class RegionRef(BaseModel):
    name: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class CompareRequest(BaseModel):
    region_a: RegionRef
    region_b: RegionRef
    start: int
    end: int
    variables: list[str] = Field(default_factory=lambda: list(DEFAULT_VARIABLES), min_length=1, max_length=6)


class GuardRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    claim_type: str = "statistical_relationship"
    status: str = "OBSERVED"
    significant: bool | None = None


def _guarded(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except DataUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PowerFormatError as exc:
        raise HTTPException(status_code=502, detail=f"NASA response rejected: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _run(req: InvestigateRequest) -> dict[str, Any]:
    baseline = None
    if req.baseline_start is not None and req.baseline_end is not None:
        baseline = (req.baseline_start, req.baseline_end)
    key = (req.latitude, req.longitude, req.start, req.end, tuple(req.variables), baseline, req.region_name)
    if not req.refresh and key in _results:
        _results.move_to_end(key)
        return _results[key]
    result = _guarded(
        investigate, store, lat=req.latitude, lon=req.longitude, start=req.start, end=req.end,
        variables=req.variables, region_name=req.region_name, baseline=baseline,
        independent_reports=load_independent_reports(DATA_DIR / "independent_reports"), refresh=req.refresh)
    _results[key] = result
    while len(_results) > _MAX_RESULTS:
        _results.popitem(last=False)
    for e in result["evidence"]:
        _evidence[e["id"]] = e
    return result


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "engine_version": ENGINE_VERSION, "network_allowed": store.allow_network,
            "cached_datasets": len(store._records())}


@app.get("/api/catalog")
def catalog() -> dict[str, Any]:
    cached = [{"latitude": r["request"]["latitude"], "longitude": r["request"]["longitude"],
               "start": r["request"]["start"], "end": r["request"]["end"],
               "parameters": r["request"]["parameters"], "sha256": r["sha256"],
               "retrieved": r["retrieval_timestamp"]} for r in store._records()]
    regions = []
    for reg in REGIONS:
        spans = [(c["start"], c["end"]) for c in cached
                 if abs(c["latitude"] - reg["latitude"]) < 1e-9 and abs(c["longitude"] - reg["longitude"]) < 1e-9]
        regions.append({**reg, "cached_periods": sorted(set(spans))})
    return {"variables": VARIABLES, "default_variables": DEFAULT_VARIABLES, "regions": regions, "derived": DERIVED,
            "first_year": POWER_FIRST_YEAR, "last_complete_year": datetime.now(timezone.utc).year - 1,
            "network_allowed": store.allow_network, "cached_datasets": cached,
            "claim_types": list(CLAIM_TYPES), "statuses": STATUS_ORDER}


@app.post("/api/investigate")
def api_investigate(req: InvestigateRequest) -> dict[str, Any]:
    return _run(req)


@app.post("/api/report")
def api_report(req: InvestigateRequest) -> dict[str, str]:
    return {"markdown": render_report(_run(req))}


@app.get("/api/evidence/{evidence_id}")
def api_evidence(evidence_id: str) -> dict[str, Any]:
    if evidence_id not in _evidence:
        raise HTTPException(status_code=404, detail="unknown evidence id (run the investigation first; "
                                                    "ids are deterministic and can be recomputed)")
    return _evidence[evidence_id]


@app.post("/api/compare")
def api_compare(req: CompareRequest) -> dict[str, Any]:
    return _guarded(compare_regions, store, req.region_a.model_dump(), req.region_b.model_dump(),
                    start=req.start, end=req.end, variables=req.variables)


@app.post("/api/guard/check")
def api_guard(req: GuardRequest) -> dict[str, Any]:
    return _guarded(check_claim, req.text, req.claim_type, status=req.status, significant=req.significant)


_dist = REPO / "frontend" / "dist"
if _dist.exists():                      # single-process demo: serve the built UI
    app.mount("/", StaticFiles(directory=_dist, html=True), name="ui")
