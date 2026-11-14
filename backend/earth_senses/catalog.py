"""Variable and region catalogue.

``expected_units`` is a tripwire, not a source of truth: units always come
from the API response, and a response whose units differ from the expectation
is rejected instead of being silently relabelled.

``verified`` means this build parsed a real NASA response for the parameter
and checked its units. Other parameters are passed through generically and
are flagged in the interface.
"""
from __future__ import annotations

VARIABLES: dict[str, dict] = {
    "T2M": {
        "label": "Air temperature (2 m)", "expected_units": "C", "display_units": "°C",
        "slope_units": "°C/year", "aggregation": "mean", "verified": True,
        "definition": "Average air temperature two metres above the ground, the height at which "
                      "weather stations measure it.",
    },
    "RH2M": {
        "label": "Relative humidity (2 m)", "expected_units": "%", "display_units": "%",
        "slope_units": "percentage points/year", "aggregation": "mean", "verified": True,
        "definition": "How close the air is to being saturated with water vapour, in percent. It depends "
                      "on both the amount of moisture and the temperature.",
    },
    "PRECTOTCORR": {
        "label": "Precipitation (bias-corrected)", "expected_units": "mm/day", "display_units": "mm/day",
        "slope_units": "mm/day per year", "aggregation": "rate", "verified": True,
        "definition": "Rain and snow (as liquid water) per day, averaged over the month. Multiply by the "
                      "number of days in the month to get the monthly total in millimetres.",
    },
    "QV2M": {
        "label": "Specific humidity (2 m)", "expected_units": "g/kg", "display_units": "g/kg",
        "slope_units": "g/kg per year", "aggregation": "mean", "verified": True,
        "definition": "Mass of water vapour per mass of moist air; unlike relative humidity it does not "
                      "change just because the air warms or cools.",
    },
    "T2M_MAX": {
        "label": "Maximum air temperature (2 m)", "expected_units": None, "display_units": None,
        "slope_units": None, "aggregation": "mean", "verified": False,
        "definition": "Highest air temperature two metres above the ground within the period.",
    },
    "T2M_MIN": {
        "label": "Minimum air temperature (2 m)", "expected_units": None, "display_units": None,
        "slope_units": None, "aggregation": "mean", "verified": False,
        "definition": "Lowest air temperature two metres above the ground within the period.",
    },
    "WS2M": {
        "label": "Wind speed (2 m)", "expected_units": None, "display_units": None,
        "slope_units": None, "aggregation": "mean", "verified": False,
        "definition": "Average wind speed two metres above the ground.",
    },
    "GWETTOP": {
        "label": "Surface soil wetness", "expected_units": None, "display_units": None,
        "slope_units": None, "aggregation": "mean", "verified": False,
        "definition": "How wet the top five centimetres of soil are, from 0 (completely dry) to 1 (saturated).",
    },
    "ALLSKY_SFC_SW_DWN": {
        "label": "Sunlight reaching the surface", "expected_units": None, "display_units": None,
        "slope_units": None, "aggregation": "mean", "verified": False,
        "definition": "Solar energy arriving at the ground under actual sky conditions, clouds included.",
    },
}

VARIABLES["IMERG_PRECTOT"] = {
    "label": "Precipitation, GPM IMERG (via POWER)", "expected_units": None, "display_units": None,
    "slope_units": None, "aggregation": "rate", "verified": False,
    "definition": "Satellite-based precipitation. Checked on 2026-11-14: for Pavlodar the POWER monthly service "
                  "returned only its missing-value code for 2001-2024, so this tool refuses to analyse it there.",
}

DEFAULT_VARIABLES = ["T2M", "RH2M", "PRECTOTCORR"]

# Variables that are computed from other variables. A correlation between a derived
# variable and one of its inputs is partly built into the definition.
DERIVED: dict[str, dict] = {
    "RH2M": {
        "depends_on": ["T2M", "QV2M"],
        "note": "Relative humidity is a derived quantity: the ratio of the water vapour present to the amount "
                "the air could hold at its temperature. NASA POWER calculates it from MERRA-2 pressure, "
                "temperature and specific humidity, so part of any association with temperature or moisture "
                "content is built into the definition.",
        "source": "https://power.larc.nasa.gov/docs/methodology/meteorology/relative-humidity/",
    },
}

REGIONS: list[dict] = [
    {"id": "pavlodar", "name": "Pavlodar, Kazakhstan", "latitude": 52.29, "longitude": 76.97,
     "note": "Steppe on the Irtysh river; strongly continental climate."},
    {"id": "almaty", "name": "Almaty, Kazakhstan", "latitude": 43.24, "longitude": 76.95,
     "note": "Foothills of the Tien Shan. The MERRA-2 grid cell here averages high mountains and "
             "plain: its mean elevation is far above the city, so values describe the cell, not the city."},
    {"id": "astana", "name": "Astana, Kazakhstan", "latitude": 51.17, "longitude": 71.43,
     "note": "Northern steppe. Not in the bundled cache: needs a live NASA request."},
    {"id": "aralsk", "name": "Aralsk (Aral Sea), Kazakhstan", "latitude": 46.80, "longitude": 61.67,
     "note": "Former Aral Sea shore. Not in the bundled cache: needs a live NASA request."},
]


def describe(name: str, response_units: str, longname: str) -> dict:
    """Catalogue entry merged with what the response itself declares."""
    info = VARIABLES.get(name)
    if info is None:
        return {"name": name, "label": longname, "units": response_units, "display_units": response_units,
                "slope_units": f"{response_units} per year", "aggregation": "mean", "verified": False,
                "definition": longname, "longname": longname}
    expected = info["expected_units"]
    if expected is not None and response_units.strip() != expected:
        raise ValueError(
            f"unit trap: {name} arrived in {response_units!r}, expected {expected!r}; refusing to relabel")
    display = info["display_units"] or response_units
    return {"name": name, "label": info["label"], "units": response_units, "display_units": display,
            "slope_units": info["slope_units"] or f"{display} per year",
            "aggregation": info["aggregation"], "verified": info["verified"],
            "definition": info["definition"], "longname": longname}
