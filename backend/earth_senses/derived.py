"""Derived variables: when one "variable" is computed from others.

Relative humidity (RH2M) is not measured independently of temperature. It is
the ratio of the water vapour actually present to the amount the air could
hold at its temperature. NASA POWER states that its relative humidity is
calculated from MERRA-2 pressure, temperature and specific humidity, over
water only (https://power.larc.nasa.gov/docs/methodology/meteorology/relative-humidity/).
A correlation between RH2M and T2M is therefore partly built into the
definition.

This module makes that dependence measurable instead of leaving it as a
caveat:

* ``rh_from_t_q`` rebuilds relative humidity from temperature and specific
  humidity with a textbook formula (Magnus saturation vapour pressure over
  water, WMO-No. 8 coefficients) at a fixed standard-atmosphere pressure for
  the grid cell's elevation. Nothing is fitted.
* ``structural_check`` compares that reconstruction with the RH2M values in
  the same file and reports how much of the RH2M anomaly variance a linear
  combination of the T2M and QV2M anomalies reproduces, per season.

The reconstruction is an approximation on purpose: it uses monthly means
(the mean of a ratio is not the ratio of the means), a constant pressure and
a different saturation formula from POWER's (Magnus instead of a polynomial
fit; both over liquid water). The size of the mismatch is reported, not
hidden.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .catalog import DERIVED
from .normalize import SEASONS
from .relationships import anomalies, detrend_linear, monthly_climatology

EPSILON = 0.622          # ratio of the gas constants of dry air and water vapour


def standard_pressure_hpa(elevation_m: float) -> float:
    """ICAO standard-atmosphere pressure at a given height (troposphere)."""
    return float(1013.25 * (1.0 - 2.25577e-5 * float(elevation_m)) ** 5.25588)


def saturation_vapour_pressure_hpa(t_c: np.ndarray | float) -> np.ndarray:
    """Magnus formula over liquid water (WMO-No. 8, 2008 coefficients)."""
    t = np.asarray(t_c, dtype=float)
    return 6.112 * np.exp(17.62 * t / (243.12 + t))


def rh_from_t_q(t_c: np.ndarray | float, q_g_per_kg: np.ndarray | float, pressure_hpa: float) -> np.ndarray:
    """Relative humidity (%) from temperature (deg C), specific humidity (g/kg) and pressure (hPa)."""
    q = np.asarray(q_g_per_kg, dtype=float) / 1000.0
    e = q * pressure_hpa / (EPSILON + (1.0 - EPSILON) * q)          # vapour pressure
    return 100.0 * e / saturation_vapour_pressure_hpa(t_c)


def _fit(y: np.ndarray, cols: list[np.ndarray]) -> dict[str, Any]:
    """Least squares of y on the columns (plus an intercept); returns coefficients and R^2."""
    design = np.column_stack([np.ones(len(y))] + cols)
    beta, *_ = np.linalg.lstsq(design, y, rcond=None)
    resid = y - design @ beta
    total = float(np.sum((y - y.mean()) ** 2))
    r2 = float(1.0 - np.sum(resid ** 2) / total) if total > 0 else float("nan")
    return {"coefficients": [float(b) for b in beta[1:]], "r_squared": r2, "n": int(len(y))}


def structural_check(temperature: pd.Series, specific_humidity: pd.Series, relative_humidity: pd.Series, *,
                     elevation_m: float, baseline: tuple[int, int] | None = None) -> dict[str, Any]:
    """How far RH2M is determined by T2M and QV2M in the same file."""
    pressure = standard_pressure_hpa(elevation_m)
    rebuilt = pd.Series(rh_from_t_q(temperature.to_numpy(dtype=float), specific_humidity.to_numpy(dtype=float),
                                    pressure), index=relative_humidity.index)
    rh = relative_humidity.astype(float)
    diff = rebuilt - rh

    def anomaly(series: pd.Series) -> pd.Series:
        return detrend_linear(anomalies(series, monthly_climatology(series, baseline)))

    a_rh, a_t, a_q, a_rebuilt = anomaly(rh), anomaly(temperature), anomaly(specific_humidity), anomaly(rebuilt)
    overall = _fit(a_rh.to_numpy(), [a_t.to_numpy(), a_q.to_numpy()])
    by_season: dict[str, Any] = {}
    for name, months in SEASONS.items():
        pick = a_rh.index.month.isin(months)
        by_season[name] = _fit(a_rh.to_numpy()[pick], [a_t.to_numpy()[pick], a_q.to_numpy()[pick]])
    return {
        "derived": "RH2M", "inputs": list(DERIVED["RH2M"]["depends_on"]),
        "assumed_pressure_hpa": pressure, "elevation_m": float(elevation_m),
        "reconstruction": {
            "formula": "RH = 100 * e / es(T); e = q p / (0.622 + 0.378 q); "
                       "es(T) = 6.112 exp(17.62 T / (243.12 + T)) hPa (Magnus, over water)",
            "r_raw": float(np.corrcoef(rebuilt.to_numpy(), rh.to_numpy())[0, 1]),
            "mean_abs_error_pp": float(diff.abs().mean()), "bias_pp": float(diff.mean()),
            "r_detrended_anomalies": float(np.corrcoef(a_rebuilt.to_numpy(), a_rh.to_numpy())[0, 1]),
            "by_season_mean_abs_error_pp": {name: float(diff[diff.index.month.isin(months)].abs().mean())
                                            for name, months in SEASONS.items()},
        },
        "linear_fit_of_anomalies": {
            "model": "RH2M anomaly = a * T2M anomaly + b * QV2M anomaly (detrended monthly anomalies)",
            "coefficient_units": ["percentage points per deg C", "percentage points per g/kg"],
            "overall": overall, "by_season": by_season,
        },
        "approximations": [
            "monthly means are used, and the mean of a ratio is not the ratio of the means",
            "pressure is a constant standard-atmosphere value for the grid cell's elevation",
            "saturation vapour pressure from the Magnus formula over liquid water (NASA POWER also uses "
            "saturation over water, with a different formula)",
        ],
    }
