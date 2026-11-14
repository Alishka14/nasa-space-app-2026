"""The onboarding globe's images are the files their provenance record says they are.

SOURCES.json is written by scripts/build_earth_textures.py, which copies the two NASA images byte for
byte from NASA's WorldWind repository and draws the water mask from Natural Earth. These tests fail if a
texture is swapped, edited or left without a credit.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEX = ROOT / "frontend" / "src" / "onboarding" / "earth" / "textures"
SOURCES = json.loads((TEX / "SOURCES.json").read_text(encoding="utf-8"))["textures"]


def test_every_texture_matches_its_recorded_hash_and_size():
    for rec in SOURCES:
        data = (TEX / rec["file"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == rec["sha256"], rec["file"]
        assert len(data) == rec["bytes"], rec["file"]


def test_only_recorded_images_are_shipped():
    shipped = {p.name for p in TEX.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}}
    assert shipped == {r["file"] for r in SOURCES}


def test_nasa_images_are_unmodified_copies_with_the_mandatory_credit():
    nasa = [r for r in SOURCES if r["file"].startswith("nasa-")]
    assert len(nasa) == 2
    for r in nasa:
        assert r["processing"].startswith("none")
        assert "github.com/NASAWorldWind/WebWorldWind/blob/" in r["obtained_from"]
        assert "NASA" in r["credit"]
        assert "only mandatory credit is NASA" in r["terms"]


def test_the_globe_loads_exactly_these_files():
    scene = (ROOT / "frontend" / "src" / "onboarding" / "earth" / "EarthScene.ts").read_text(encoding="utf-8")
    imported = set(re.findall(r"from '\./textures/([^']+)'", scene))
    assert imported == {r["file"] for r in SOURCES}


def test_credits_are_published_in_the_licence_document():
    doc = (ROOT / "docs" / "visual" / "ASSETS_AND_LICENSES.md").read_text(encoding="utf-8")
    for r in SOURCES:
        assert r["file"] in doc
    assert "NASA Earth Observatory" in doc and "Natural Earth" in doc
