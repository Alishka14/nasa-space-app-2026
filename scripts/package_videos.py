"""Finish the recorded films: metadata, a decode check and a manifest.

    python scripts/package_videos.py

For every docs/video/renders/<variant>_<lang>.mp4 the narration is already burned into the picture. This adds
title and description metadata stating that the film is a screen recording of the app, checks that the whole file
decodes, and writes renders/MANIFEST.md and MANIFEST.json (length, picture, size, SHA-256). Streams are copied,
not re-encoded. Subtitle files for upload (e.g. English captions on YouTube for the Russian and Kazakh films) are
in docs/video/subtitles/.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from intro_content import ROOT  # noqa: E402

R = ROOT / "docs" / "video" / "renders"
NAME = {"hero": "Full film", "explainer": "Explainer", "teaser": "Short"}
LANG = {"en": "English", "ru": "Русский", "kk": "Қазақша"}
COMMENT = ("Screen recording of the running EARTH SENSES app (in-app intro, software WebGL), not generated footage. "
           "App code and texts were written with AI assistance (Claude, Anthropic). Earth imagery: NASA Earth "
           "Observatory (Blue Marble: Next Generation; Earth at Night 2012, with NOAA NGDC). Data: NASA POWER (MERRA-2).")


def probe(p: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", "-show_format", str(p)],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def decodes(p: Path) -> bool:
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-map", "0:v", "-f", "null", "-"],
                       capture_output=True, text=True)
    return r.returncode == 0 and not r.stderr.strip()


def set_metadata(p: Path, variant: str, lang: str) -> None:
    """Title and description only; streams are copied. Subtitles stay as SRT files beside the films: an MP4
    subtitle track is switched on automatically by some players, which would double the burned-in narration."""
    tmp = p.with_suffix(".tmp.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(p), "-map", "0:v", "-c", "copy",
                    "-metadata", f"title=EARTH SENSES — {NAME[variant]} ({LANG[lang]})",
                    "-metadata", f"comment={COMMENT}", "-movflags", "+faststart", str(tmp)], check=True)
    shutil.move(tmp, p)


def main() -> int:
    rows = []
    for p in sorted(R.glob("*.mp4")):
        stem = p.stem
        if "_" in stem and stem.split("_")[0] in NAME:
            variant, lang = stem.split("_", 1)
            if "EARTH SENSES" not in probe(p)["format"].get("tags", {}).get("title", ""):
                set_metadata(p, variant, lang)
        info = probe(p)
        v = next(s for s in info["streams"] if s["codec_type"] == "video")
        num, den = (int(x) for x in v["r_frame_rate"].split("/"))
        rows.append({"file": p.name, "seconds": round(float(info["format"]["duration"]), 2),
                     "width": v["width"], "height": v["height"], "fps": num / den, "codec": v["codec_name"],
                     "mb": round(p.stat().st_size / 1e6, 1), "decodes": decodes(p),
                     "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
        print(f"{p.name:22s} {rows[-1]['seconds']:6.2f} s  {v['width']}×{v['height']}  {rows[-1]['mb']:5.1f} MB  "
              f"decodes {rows[-1]['decodes']}")
    (R / "MANIFEST.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    L = ["# Recorded films", "",
         "Screen recordings of the running app, made frame by frame with `scripts/record_intro.mjs` (in-app intro, "
         "1280×720 layout rendered at 1920×1080, software WebGL) and `scripts/make_demo.sh` (the 30-second demo, "
         "from the Short intro and screenshots of the app). Not generated footage. Silent: the narration is in the "
         "picture as subtitles. SRT files for every film and language are in `../subtitles/` (upload the English "
         "file as captions when publishing a Russian or Kazakh film). Regenerate this list with `python scripts/package_videos.py`.", "",
         "| File | Length | Picture | Size | Decodes cleanly | SHA-256 |", "|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| [`{r['file']}`]({r['file']}) | {r['seconds']:.1f} s | {r['width']}×{r['height']}, {r['fps']:g} fps "
                 f"{r['codec'].upper()} | {r['mb']:.1f} MB | "
                 f"{'yes' if r['decodes'] else '**NO**'} | `{r['sha256'][:16]}…` |")
    L += ["", "For the NASA form use **`demo_en.mp4`** (30 seconds or less, English). The other films are for "
          "presentations: the form allows at most 30 seconds."]
    (R / "MANIFEST.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return 0 if all(r["decodes"] for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
