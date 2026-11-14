"""Earth textures for the onboarding globe, with a provenance record for each file.

    python scripts/build_earth_textures.py /path/to/WebWorldWind

Day and night images are copied byte for byte from NASA's own WorldWind repository
(github.com/NASAWorldWind/WebWorldWind, `images/`), which ships them for its Blue Marble and
atmosphere layers; the script refuses any file whose SHA-256 differs from the pinned value.
The water mask is drawn here from Natural Earth land polygons (public domain) as packaged in
world-atlas. Output: frontend/src/onboarding/earth/textures/ and SOURCES.json beside them.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "src" / "onboarding" / "earth" / "textures"
LAND = ROOT / "frontend" / "node_modules" / "world-atlas" / "land-50m.json"
WORLDWIND_COMMIT = "5ffe2dfc54ab4d744fc9e587af9639c9910db228"

NASA_FILES = [
    {
        "file": "nasa-blue-marble-ng-200405-2048x1024.jpg",
        "source_path": "images/BMNG_world.topo.bathy.200405.3.2048x1024.jpg",
        "sha256": "7405c39a220bc37519474eba54625a0d1a02b6ad954895147c103a1bc8dd61fb",
        "role": "day surface",
        "title": "Blue Marble: Next Generation with topography and bathymetry, May 2004",
        "record": "NASA Visible Earth, Blue Marble collection; NASA Earth Observatory feature "
                  "https://earthobservatory.nasa.gov/features/BlueMarble/BlueMarble.php",
        "credit": "NASA Earth Observatory (Blue Marble: Next Generation, Reto Stöckli)",
    },
    {
        "file": "nasa-earth-at-night-2012-2048x1024.png",
        "source_path": "images/dnb_land_ocean_ice_2012.png",
        "sha256": "c1893c1a97634f9d9dc45a62f83916c77cae742d5128551f8d7c4e4f5296ed36",
        "role": "night side (city lights)",
        "title": "Earth at Night 2012 (land, ocean, ice), Suomi NPP VIIRS day-night band",
        "record": "NASA Earth Observatory, Earth at Night 2012; NASA SVS https://svs.gsfc.nasa.gov/30028",
        "credit": "NASA Earth Observatory/NOAA NGDC (image by Robert Simmon, Suomi NPP VIIRS data courtesy "
                  "of Chris Elvidge, NOAA National Geophysical Data Center)",
    },
]

TERMS = ("NASA Visible Earth image use policy: most images are freely available for re-publication or re-use, "
         "including commercial purposes, except where copyright is indicated; the only mandatory credit is NASA "
         "(https://www.visibleearth.nasa.gov/image-use-policy). NASA does not endorse this project.")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_arcs(topo: dict) -> list[list[tuple[float, float]]]:
    sx, sy = topo["transform"]["scale"]
    tx, ty = topo["transform"]["translate"]
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)
    return arcs


def ring(arcs: list, indices: list[int]) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in indices:
        a = arcs[i] if i >= 0 else arcs[~i][::-1]
        pts.extend(a if not pts else a[1:])
    return pts


def water_mask(width: int = 2048, height: int = 1024, ss: int = 4) -> Image.Image:
    """White = water, black = land, equirectangular, drawn at ss× and averaged down for soft coasts."""
    topo = json.loads(LAND.read_text(encoding="utf-8"))
    arcs = decode_arcs(topo)
    W, H = width * ss, height * ss
    img = Image.new("L", (W, H), 255)
    draw = ImageDraw.Draw(img)

    def xy(lon, lat):
        return ((lon + 180.0) / 360.0 * W, (90.0 - lat) / 180.0 * H)

    def unwrap(pts):
        """Make longitudes continuous across ±180°; close rings around a pole along the map edge."""
        out = [pts[0]]
        for lon, lat in pts[1:]:
            prev = out[-1][0]
            while lon - prev > 180:
                lon -= 360
            while lon - prev < -180:
                lon += 360
            out.append((lon, lat))
        span = out[-1][0] - out[0][0]
        if abs(span) > 180:                     # the ring goes once round the globe: Antarctica
            pole = -90.0 if sum(p[1] for p in out) < 0 else 90.0
            out += [(out[-1][0], pole), (out[0][0], pole)]
        return out

    geoms = topo["objects"]["land"]
    geoms = geoms["geometries"] if geoms["type"] == "GeometryCollection" else [geoms]
    for g in geoms:
        polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]]
        for poly in polys:
            for k, r in enumerate(poly):
                pts = unwrap(ring(arcs, r))
                if len(pts) < 3:
                    continue
                for shift in (-360.0, 0.0, 360.0):     # copies left and right cover the wrap-around
                    draw.polygon([xy(lon + shift, lat) for lon, lat in pts], fill=0 if k == 0 else 255)
    return img.resize((width, height), Image.LANCZOS)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    ww = Path(sys.argv[1])
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    for f in NASA_FILES:
        src = ww / f["source_path"]
        got = sha256(src)
        if got != f["sha256"]:
            raise SystemExit(f"{src}: SHA-256 {got} differs from the pinned {f['sha256']} — not copied")
        dst = OUT / f["file"]
        shutil.copyfile(src, dst)
        with Image.open(dst) as im:
            size = list(im.size)
        records.append({**f, "bytes": dst.stat().st_size, "pixels": size, "processing": "none — byte-identical copy",
                        "obtained_from": f"https://github.com/NASAWorldWind/WebWorldWind/blob/{WORLDWIND_COMMIT}/"
                                         f"{f['source_path']}",
                        "distributor": "NASA WorldWind (NASA Ames Research Center), official repository listed at "
                                       "https://worldwind.arc.nasa.gov",
                        "terms": TERMS})
    mask = OUT / "water-mask-natural-earth-50m.png"
    water_mask().save(mask, optimize=True)
    land_meta = json.loads((LAND.parent / "package.json").read_text(encoding="utf-8"))
    records.append({
        "file": mask.name, "sha256": sha256(mask), "bytes": mask.stat().st_size, "pixels": [2048, 1024],
        "role": "water mask for sun glint (white = water)",
        "title": "Land/water mask drawn from Natural Earth 1:50m land polygons",
        "record": "https://www.naturalearthdata.com — public domain",
        "obtained_from": f"npm package world-atlas {land_meta['version']} (ISC), file land-50m.json",
        "processing": "generated by scripts/build_earth_textures.py (polygon fill at 4× and Lanczos downsampling)",
        "credit": "Made with Natural Earth", "terms": "Natural Earth: public domain. world-atlas: ISC licence.",
    })
    (OUT / "SOURCES.json").write_text(json.dumps({"textures": records}, ensure_ascii=False, indent=2) + "\n",
                                      encoding="utf-8")
    for r in records:
        print(f"{r['file']:44s} {r['pixels'][0]}×{r['pixels'][1]}  {r['bytes'] / 1e3:7.0f} kB  {r['sha256'][:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
