"""Register the bundled raw NASA POWER files: provenance records + normalized CSVs.

The raw files were retrieved on 2026-11-14 through the team's Chrome browser,
because the build sandbox had no network route to power.larc.nasa.gov. For
each response the SHA-256 was computed in the browser on the response body;
the body was then written into this repository and re-hashed. The hashes
below are the browser-side values: this script fails if a file differs.

Run from the repository root:  python scripts/build_provenance.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from earth_senses.normalize import days_in_month, rate_to_monthly_total  # noqa: E402
from earth_senses.power_client import PowerStore, cache_stem, request_url, sha256_bytes  # noqa: E402

METHOD = ("HTTPS GET issued from a Chrome browser on the team's computer (the build sandbox had no route "
          "to power.larc.nasa.gov); SHA-256 computed in the browser on the response body and matched "
          "after the body was stored in the repository (byte-identical)")
PARAMS = ["T2M", "PRECTOTCORR", "RH2M"]          # order used in the original requests
FIXTURES = [
    {"lat": 52.29, "lon": 76.97, "start": 2001, "end": 2024, "retrieved_at": "2026-11-14T04:58:11.069Z",
     "sha256": "8a65f9e56b005f77eec3783a09903ad2842031590cc0c8084441d92b19f87de6"},
    {"lat": 52.29, "lon": 76.97, "start": 1981, "end": 2000, "retrieved_at": "2026-11-14T05:04:44.570Z",
     "sha256": "db5aa2495699186440353f8b9eb77cd8ce04c149b612b900b17cb95d33ae0a87"},
    {"lat": 43.24, "lon": 76.95, "start": 2001, "end": 2024, "retrieved_at": "2026-11-14T05:05:38.289Z",
     "sha256": "9c8fcb0467a87a63c20adcec96d9dff9240855aa2493ac0cb1426530ae4d6235"},
]


def main() -> int:
    store = PowerStore(ROOT / "data", allow_network=False)
    norm_dir = ROOT / "data" / "normalized"
    norm_dir.mkdir(parents=True, exist_ok=True)
    for fx in FIXTURES:
        stem = cache_stem(fx["lat"], fx["lon"], fx["start"], fx["end"], PARAMS)
        raw_path = store.raw_dir / f"{stem}.json"
        raw = raw_path.read_bytes()
        digest = sha256_bytes(raw)
        if digest != fx["sha256"]:
            print(f"FAIL {raw_path.name}: sha256 {digest} != browser-side {fx['sha256']}")
            return 1
        ds = store.register_raw(raw, lat=fx["lat"], lon=fx["lon"], start=fx["start"], end=fx["end"],
                                parameters=PARAMS, url=request_url(fx["lat"], fx["lon"], fx["start"], fx["end"], PARAMS),
                                retrieved_at=fx["retrieved_at"], method=METHOD)
        m = ds.norm.monthly.copy()
        out = m.rename(columns={c: f"{c} [{ds.norm.units[c]}]" for c in m.columns})
        out["days_in_month"] = days_in_month(m.index).astype(int)
        out["PRECTOTCORR [mm/month]"] = rate_to_monthly_total(m["PRECTOTCORR"], ds.norm.units["PRECTOTCORR"]).round(3)
        out.to_csv(norm_dir / f"{stem}.monthly.csv")
        ann = ds.norm.annual_reported.rename(columns={c: f"{c} [{ds.norm.units[c]}] (API annual, YYYY13)"
                                                      for c in ds.norm.annual_reported.columns})
        ann.to_csv(norm_dir / f"{stem}.annual_api.csv")
        rec = ds.provenance[0]
        print(f"OK   {raw_path.name}\n     sha256 {digest}  status {rec['validation_status']}  "
              f"months {rec['coverage']['n_months']}  missing {sum(rec['missing_values']['counts'].values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
