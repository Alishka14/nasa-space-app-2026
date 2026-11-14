"""Live-retrieval path of the backend, exercised with a STUBBED HTTP transport.

These tests do NOT contact NASA and do not show that the live service works.
They replace ``httpx.get`` with a local function and check what the backend
does with each kind of answer: a good body is validated, stored byte-for-byte
with a provenance record and then analysed; every bad answer is refused and
nothing is cached or invented. The first real request to NASA from a running
backend remains NOT RUN in the build environment (docs/KNOWN_LIMITATIONS.md).
"""
from __future__ import annotations

import json

import httpx
import pytest

from conftest import ALMATY_RAW, PARAMS, PAVLODAR_RAW
from earth_senses.normalize import PowerFormatError
from earth_senses.power_client import DataUnavailable, PowerStore, request_url, sha256_bytes

PAV = dict(lat=52.29, lon=76.97, start=2001, end=2024, parameters=PARAMS)


class Stub:
    """Stands in for httpx.get and records the URLs it was asked for."""

    def __init__(self, status: int = 200, body: bytes = b"", error: Exception | None = None):
        self.status, self.body, self.error, self.urls = status, body, error, []

    def __call__(self, url, **kwargs):
        self.urls.append(url)
        if self.error is not None:
            raise self.error
        return httpx.Response(self.status, content=self.body, request=httpx.Request("GET", url))


@pytest.fixture()
def live_store(tmp_path):
    """An empty data directory with network access allowed (the network itself is stubbed)."""
    return PowerStore(tmp_path, allow_network=True)


def cached_files(store: PowerStore) -> list[str]:
    return sorted(p.name for d in (store.raw_dir, store.prov_dir) if d.exists() for p in d.iterdir())


def test_good_response_is_stored_verbatim_with_provenance_then_served_from_cache(live_store, monkeypatch):
    body = PAVLODAR_RAW.read_bytes()
    stub = Stub(200, body)
    monkeypatch.setattr(httpx, "get", stub)
    ds = live_store.load(**PAV)
    assert stub.urls == [request_url(52.29, 76.97, 2001, 2024, PARAMS)]
    assert stub.urls[0].startswith("https://power.larc.nasa.gov/api/temporal/monthly/point?")
    assert ds.source == "live" and len(ds.monthly) == 288
    rec = ds.provenance[0]
    assert rec["sha256"] == sha256_bytes(body) and rec["validation_status"] == "VALIDATED"
    assert "httpx" in rec["retrieval_method"]
    assert (live_store.data_dir / rec["raw_path"]).read_bytes() == body          # byte-for-byte
    again = live_store.load(**PAV)                                               # second call: no HTTP request
    assert again.source == "cache" and len(stub.urls) == 1
    assert again.data_hash == ds.data_hash


@pytest.mark.parametrize("status", [404, 422, 429, 500, 503])
def test_http_error_is_reported_and_nothing_is_cached(live_store, monkeypatch, status):
    monkeypatch.setattr(httpx, "get", Stub(status, b'{"header": "error", "messages": ["no data"]}'))
    with pytest.raises(DataUnavailable, match=f"HTTP {status}"):
        live_store.load(**PAV)
    assert cached_files(live_store) == []


@pytest.mark.parametrize("error", [httpx.ConnectError("connection refused"), httpx.ReadTimeout("timed out")])
def test_network_failure_is_reported_and_nothing_is_cached(live_store, monkeypatch, error):
    monkeypatch.setattr(httpx, "get", Stub(error=error))
    with pytest.raises(DataUnavailable, match="could not be reached"):
        live_store.load(**PAV)
    assert cached_files(live_store) == []


def test_http_200_with_a_truncated_calendar_is_refused_before_caching(live_store, monkeypatch):
    obj = json.loads(PAVLODAR_RAW.read_bytes())
    for block in obj["properties"]["parameter"].values():
        for key in [k for k in block if k.startswith("2024")]:
            del block[key]
    monkeypatch.setattr(httpx, "get", Stub(200, json.dumps(obj).encode()))
    with pytest.raises(PowerFormatError):
        live_store.load(**PAV)
    assert cached_files(live_store) == []


def test_http_200_for_another_place_is_refused_before_caching(live_store, monkeypatch):
    monkeypatch.setattr(httpx, "get", Stub(200, ALMATY_RAW.read_bytes()))      # right shape, wrong grid cell
    with pytest.raises(PowerFormatError):
        live_store.load(**PAV)
    assert cached_files(live_store) == []


@pytest.mark.parametrize("body", [b"", b"<html>Service Unavailable</html>", b'{"unexpected": true}'])
def test_http_200_with_a_non_power_body_is_refused(live_store, monkeypatch, body):
    monkeypatch.setattr(httpx, "get", Stub(200, body))
    with pytest.raises(PowerFormatError):
        live_store.load(**PAV)
    assert cached_files(live_store) == []


def test_api_returns_503_when_nasa_cannot_be_reached_and_invents_nothing(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from earth_senses import api
    monkeypatch.setattr(api, "store", PowerStore(tmp_path, allow_network=True))
    monkeypatch.setattr(httpx, "get", Stub(error=httpx.ConnectError("no route to host")))
    r = TestClient(api.app).post("/api/investigate", json={"latitude": 10.0, "longitude": 20.0,
                                                           "start": 2001, "end": 2024})
    assert r.status_code == 503 and "could not be reached" in r.json()["detail"]
    assert set(r.json()) == {"detail"}                                           # an error, not partial results
