"""Shared fixtures.

Two kinds of data appear in these tests and are never mixed:

* REAL  - the raw NASA POWER files under data/raw (SHA-256 recorded);
* SYNTHETIC - series generated here with a known answer, used only as
  controls for the engines. Synthetic series never reach the app or the docs
  as if they were observations.
"""
from __future__ import annotations

import calendar
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data"
PAVLODAR_RAW = DATA / "raw" / "power" / "power_monthly_point_lat52.29_lon76.97_2001-2024_PRECTOTCORR-RH2M-T2M_AG.json"
ALMATY_RAW = DATA / "raw" / "power" / "power_monthly_point_lat43.24_lon76.95_2001-2024_PRECTOTCORR-RH2M-T2M_AG.json"
PARAMS = ["T2M", "PRECTOTCORR", "RH2M"]


@pytest.fixture(scope="session")
def pavlodar_bytes() -> bytes:
    return PAVLODAR_RAW.read_bytes()


@pytest.fixture(scope="session")
def pavlodar(pavlodar_bytes):
    from earth_senses.normalize import parse_power_monthly
    return parse_power_monthly(pavlodar_bytes, expect_lat=52.29, expect_lon=76.97, expect_start=2001, expect_end=2024)


@pytest.fixture(scope="session")
def store():
    from earth_senses.power_client import PowerStore
    return PowerStore(DATA, allow_network=False)


@pytest.fixture()
def tmp_store(tmp_path):
    """A private copy of the data directory that a test may damage."""
    from earth_senses.power_client import PowerStore
    shutil.copytree(DATA / "raw", tmp_path / "raw")
    shutil.copytree(DATA / "provenance", tmp_path / "provenance")
    return PowerStore(tmp_path, allow_network=False)


def month_index(start_year: int, n_years: int) -> pd.PeriodIndex:
    return pd.period_range(f"{start_year}-01", periods=n_years * 12, freq="M")


def make_power_json(series: dict[str, np.ndarray], start_year: int = 2001, lat: float = 10.0, lon: float = 20.0,
                    units: dict[str, str] | None = None, fill: float = -999.0, annual: bool = True) -> dict:
    """SYNTHETIC response in the exact shape of the POWER monthly API."""
    units = units or {}
    params = {}
    n_months = len(next(iter(series.values())))
    for name, vals in series.items():
        block = {}
        for i in range(n_months):
            y, m = start_year + i // 12, i % 12 + 1
            block[f"{y}{m:02d}"] = float(vals[i])
            if annual and m == 12:
                yr = np.asarray(vals[i - 11:i + 1], dtype=float)
                w = np.array([calendar.monthrange(y, k)[1] for k in range(1, 13)], dtype=float)
                block[f"{y}13"] = fill if np.isclose(yr, fill).any() else round(float((yr * w).sum() / w.sum()), 2)
        params[name] = block
    end_year = start_year + n_months // 12 - 1
    return {
        "type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat, 100.0]},
        "properties": {"parameter": params},
        "header": {"title": "SYNTHETIC TEST DATA", "api": {"version": "test", "name": "synthetic"},
                   "sources": ["SYNTHETIC"], "fill_value": fill, "time_standard": "LST",
                   "start": f"{start_year}0101", "end": f"{end_year}1231"},
        "messages": [],
        "parameters": {n: {"units": units.get(n, "1"), "longname": f"synthetic {n}"} for n in series},
        "times": {"data": 0.0, "process": 0.0},
    }


def seasonal_cycle(n_years: int, amplitude: float, phase_month: float = 7.0) -> np.ndarray:
    m = np.arange(n_years * 12) % 12 + 1
    return amplitude * np.cos(2 * np.pi * (m - phase_month) / 12)


def ar1(rng: np.random.Generator, n: int, phi: float, sd: float = 1.0) -> np.ndarray:
    x = np.empty(n)
    x[0] = rng.normal(0, sd / np.sqrt(1 - phi ** 2))
    for i in range(1, n):
        x[i] = phi * x[i - 1] + rng.normal(0, sd)
    return x
