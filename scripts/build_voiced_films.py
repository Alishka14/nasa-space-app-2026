#!/usr/bin/env python3
"""Add the voice-over to the rendered films. Writes new files; the silent renders are left untouched.

    python scripts/build_voiced_films.py --clips /path/to/vo_clips [--only hero_en,demo_en] [--allow-partial]

Inputs
  --clips      folder with <film>/<scene>.mp3 (ElevenLabs speech, one clip per scene line;
               see docs/video/VOICEOVER_FINAL.md for the texts)
  docs/video/renders/<film>.mp4   the silent screen recordings of the in-app intro (and the demo)
Outputs
  docs/video/renders/voiced/<film>_voice.mp4  (+ <film>_voice.srt: docs/video/subtitles/<film>.srt re-timed)
  docs/video/renders/voiced/VOICE_TIMING.json  what was placed where, and how much each scene was slowed

Rules
  * A clip starts LEAD s after its scene starts and must end TAIL s before the next scene.
    If it does not fit, the whole scene is slowed down uniformly (never sped up, never cut), so the
    picture, the burned-in subtitles and the speech stay together. The 30 s demo is never slowed:
    a clip that does not fit there is an error.
  * Leading/trailing silence of each clip is trimmed; the mix is loudness-normalised to -16 LUFS
    (two-pass, linear) with a -1.5 dBTP ceiling.
  * A film with a missing clip is skipped unless --allow-partial (a half-voiced film is worse than a
    silent one with subtitles).
  * A small "AI voice" label is burned into the corner of every voiced file: the speech is synthetic.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RENDERS = ROOT / "docs/video/renders"
OUT = Path(__import__("os").environ.get("VOICED_OUT", RENDERS / "voiced"))
LINES = ROOT / "docs/video/voiceover_lines.json"
FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
FPS = 24
LEAD, TAIL = 0.25, 0.45

SCENES = {
    "hero": [("h1", 6.0), ("h2", 6.5), ("h3", 6.5), ("h4", 8.0), ("h5", 8.0), ("h6", 5.5),
             ("h7", 7.0), ("h8", 7.5), ("h9", 4.5)],
    "explainer": [("e1", 6.5), ("e2", 6.5), ("e3", 6.5), ("e4", 8.5), ("e5", 7.0), ("e6", 5.5), ("e7", 4.5)],
    "teaser": [("t1", 4.0), ("t2", 5.0), ("t3", 3.5), ("t4", 4.0)],
}
# demo_en.mp4 (scripts/make_demo.sh): splash 3.0 s, Short intro 16.5 s, three app screenshots
DEMO = [("d0", 0.0, 3.0), ("d1", 3.0, 4.0), ("d2b", 7.0, 5.0), ("d3", 12.0, 3.5), ("d4", 15.5, 4.0),
        ("d5", 19.5, 3.0), ("d6b", 22.5, 3.4), ("d7c", 25.9, 3.4)]
DEMO_LEAD = 0.15
DEMO_GAP = 0.12     # minimum silence between two demo lines
DEMO_EARLY = 0.3    # a line may start this much before its picture cut …
DEMO_SPILL = 0.12   # … or end this much after the next cut (imperceptible; the demo cannot be slowed)
LABEL = "AI voice (ElevenLabs)"


def run(cmd: list[str]) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"command failed: {' '.join(cmd[:6])} …\n{p.stderr[-2000:]}")
    return p.stderr + p.stdout


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          str(path)], capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def trim_clip(src: Path, dst: Path) -> float:
    af = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03,areverse,"
          "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,areverse,"
          "aresample=48000")
    run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", af, "-ac", "1", str(dst)])
    return duration(dst)


def mix(placements: list[tuple[Path, float]], total: float, dst: Path) -> dict:
    """Place clips at absolute times, then two-pass loudnorm."""
    raw = dst.with_suffix(".raw.wav")
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-t", f"{total:.3f}", "-i",
           "anullsrc=r=48000:cl=mono"]
    parts = []
    for i, (clip, t) in enumerate(placements, start=1):
        cmd += ["-i", str(clip)]
        ms = int(round(t * 1000))
        parts.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
    labels = "[0:a]" + "".join(f"[a{i}]" for i in range(1, len(placements) + 1))
    fc = ";".join(parts + [f"{labels}amix=inputs={len(placements) + 1}:normalize=0:duration=first,"
                           f"atrim=0:{total:.3f}[m]"])
    run(cmd + ["-filter_complex", fc, "-map", "[m]", str(raw)])
    meas = run(["ffmpeg", "-v", "info", "-i", str(raw), "-af",
                "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    m = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
    ln = (f"loudnorm=I=-16:TP=-1.5:LRA=11:linear=true:measured_I={m['input_i']}:"
          f"measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
          f"offset={m['target_offset']},aresample=48000")
    run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af", ln, "-ac", "1", str(dst)])
    raw.unlink()
    return {"input_lufs": float(m["input_i"]), "target_lufs": -16.0}


def label_filter() -> str:
    return (f"drawtext=fontfile={FONT}:text='{LABEL}':fontsize=22:fontcolor=white@0.78:"
            f"box=1:boxcolor=black@0.45:boxborderw=8:x=w-text_w-28:y=24")


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def parse_srt(path: Path) -> list[tuple[float, float, str]]:
    def sec(x: str) -> float:
        h, m, rest = x.strip().split(":")
        s, ms = rest.split(",")
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    cues = []
    for block in path.read_text(encoding="utf-8").strip().split("\n\n"):
        lines = block.strip().splitlines()
        if len(lines) >= 3 and "-->" in lines[1]:
            a, b = lines[1].split("-->")
            cues.append((sec(a), sec(b), "\n".join(lines[2:])))
    return cues


def retime(t: float, timing: list[dict]) -> float:
    """Map a time of the silent film onto the voiced (possibly slowed) film."""
    orig = 0.0
    for sc in timing:
        if t <= orig + sc["scene_s"] + 1e-6:
            return sc["start"] + (t - orig) * sc["factor"]
        orig += sc["scene_s"]
    last = timing[-1]
    return last["start"] + last["slowed_to_s"] + (t - orig)


def build_film(film: str, clips: Path, texts: dict, allow_partial: bool, tmp: Path) -> dict:
    variant, lang = film.split("_")
    scenes = SCENES[variant]
    src = RENDERS / f"{film}.mp4"
    missing = [s for s, _ in scenes if not (clips / film / f"{s}.mp3").exists()]
    if missing and not allow_partial:
        return {"film": film, "status": "SKIPPED", "missing_clips": missing}
    t0, new_t0, segs, placements, vf, timing, srt = 0.0, 0.0, [], [], [], [], []
    for i, (s, dur) in enumerate(scenes):
        clip = clips / film / f"{s}.mp3"
        d = trim_clip(clip, tmp / f"{film}_{s}.wav") if clip.exists() else 0.0
        factor = max(1.0, (LEAD + d + TAIL) / dur) if d else 1.0
        new_dur = dur * factor
        vf.append(f"[0:v]trim=start={t0:.4f}:end={t0 + dur:.4f},setpts=(PTS-STARTPTS)*{factor:.5f}[v{i}]")
        if d:
            placements.append((tmp / f"{film}_{s}.wav", new_t0 + LEAD))
        timing.append({"scene": s, "start": round(new_t0, 3), "scene_s": dur, "slowed_to_s": round(new_dur, 3),
                       "factor": round(factor, 4), "speech_s": round(d, 3),
                       "speech_at": round(new_t0 + LEAD, 3) if d else None})
        t0 += dur
        new_t0 += new_dur
    total = new_t0
    wav = tmp / f"{film}_mix.wav"
    loud = mix(placements, total, wav)
    OUT.mkdir(parents=True, exist_ok=True)
    dst = OUT / f"{film}_voice.mp4"
    n = len(scenes)
    fc = ";".join(vf + ["".join(f"[v{i}]" for i in range(n)) +
                        f"concat=n={n}:v=1:a=0,fps={FPS},{label_filter()},format=yuv420p[v]"])
    run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-i", str(wav), "-filter_complex", fc,
         "-map", "[v]", "-map", "1:a", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
         "-metadata", f"title=EARTH SENSES — {variant} ({lang}), with voice-over",
         "-metadata", "comment=Screen recording of the EARTH SENSES in-app intro; not generated footage. "
                      "Voice-over: synthetic speech generated with ElevenLabs (AI voice). Earth imagery: NASA "
                      "Earth Observatory. Data: NASA POWER (MERRA-2).",
         str(dst)])
    silent_srt = ROOT / "docs/video/subtitles" / f"{film}.srt"
    if silent_srt.exists():  # the same on-screen subtitles, re-timed to the slowed scenes
        srt = [(retime(a, timing), retime(b, timing), t) for a, b, t in parse_srt(silent_srt)]
    if srt:
        (OUT / f"{film}_voice.srt").write_text(
            "".join(f"{k}\n{srt_time(a)} --> {srt_time(b)}\n{t}\n\n" for k, (a, b, t) in enumerate(srt, 1)),
            encoding="utf-8")
    return {"film": film, "status": "PARTIAL" if missing else "DONE", "missing_clips": missing,
            "duration_s": round(duration(dst), 3), "silent_duration_s": round(t0, 3),
            "bytes": dst.stat().st_size, "loudness": loud, "scenes": timing}


def build_demo(clips: Path, tmp: Path) -> dict:
    src = RENDERS / "demo_en.mp4"
    total = duration(src)
    placements, timing, prev_end = [], [], 0.0
    for i, (s, start, dur) in enumerate(DEMO):
        d = trim_clip(clips / "demo_en" / f"{s}.mp3", tmp / f"demo_{s}.wav")
        end_limit = DEMO[i + 1][1] if i + 1 < len(DEMO) else total
        at = max(start + DEMO_LEAD, prev_end + DEMO_GAP)
        if at + d > end_limit - 0.05:  # a long line may start up to DEMO_EARLY s before its cut
            at = max(prev_end + DEMO_GAP, start - DEMO_EARLY, end_limit - 0.05 - d)
        ok = at + d <= end_limit + DEMO_SPILL and (i + 1 < len(DEMO) or at + d <= total - 0.2)
        prev_end = at + d
        timing.append({"segment": s, "start": start, "speech_at": round(at, 3), "speech_s": round(d, 3),
                       "ends": round(at + d, 3), "limit": round(end_limit, 3), "fits": ok})
        if not ok:
            sys.exit(f"demo clip {s} ({d:.2f} s) does not fit before {end_limit:.2f} s; shorten the line")
        placements.append((tmp / f"demo_{s}.wav", at))
    wav = tmp / "demo_mix.wav"
    loud = mix(placements, total, wav)
    OUT.mkdir(parents=True, exist_ok=True)
    dst = OUT / "demo_en_voice.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-i", str(wav),
         "-filter_complex", f"[0:v]{label_filter()},format=yuv420p[v]", "-map", "[v]", "-map", "1:a",
         "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
         "-metadata", "title=EARTH SENSES — demo (NASA Space Apps Challenge 2026), with voice-over",
         "-metadata", "comment=Screen recording and screenshots of the running EARTH SENSES app; not generated "
                      "footage. Voice-over: synthetic speech generated with ElevenLabs (AI voice). App code and "
                      "texts were written with AI assistance (Claude, Anthropic). Earth imagery: NASA Earth "
                      "Observatory. Data: NASA POWER (MERRA-2).",
         str(dst)])
    return {"film": "demo_en", "status": "DONE", "duration_s": round(duration(dst), 3), "bytes": dst.stat().st_size,
            "loudness": loud, "segments": timing}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clips", type=Path, required=True)
    ap.add_argument("--only", default="")
    ap.add_argument("--allow-partial", action="store_true")
    a = ap.parse_args()
    texts = {}
    if LINES.exists():
        for x in json.loads(LINES.read_text(encoding="utf-8")):
            texts[(f"{x['variant']}_{x['lang']}", x["scene"])] = x["text"]
    films = ["demo_en"] + [f"{v}_{l}" for v in ("hero", "teaser", "explainer") for l in ("en", "ru", "kk")]
    if a.only:
        films = [f for f in films if f in a.only.split(",")]
    report_path = OUT / "VOICE_TIMING.json"
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    with tempfile.TemporaryDirectory() as t:
        for film in films:
            r = build_demo(a.clips, Path(t)) if film == "demo_en" else \
                build_film(film, a.clips, texts, a.allow_partial, Path(t))
            report[film] = r
            print(f"{film:14s} {r['status']:8s} {r.get('duration_s', '')} {r.get('missing_clips', '')}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    write_manifest(report)


def write_manifest(report: dict) -> None:
    rows = ["# Voiced films", "",
            "Made by `scripts/build_voiced_films.py` from the silent renders in `docs/video/renders/` and one ElevenLabs "
            "speech clip per scene (texts: `docs/video/voiceover_lines.json`). The voice is synthetic and every file "
            "says so in the picture (\"AI voice (ElevenLabs)\") and in its metadata.", "",
            "| File | Status | Length | Silent original | Slowest scene | Size |", "|---|---|---|---|---|---|"]
    for film in ["demo_en"] + [f"{v}_{l}" for v in ("hero", "explainer", "teaser") for l in ("en", "ru", "kk")]:
        r = report.get(film)
        if not r:
            continue
        if r["status"] == "SKIPPED":
            rows.append(f"| `{film}` | not voiced — missing lines {', '.join(r['missing_clips'])} | | | | |")
            continue
        slow = max((s["factor"] for s in r.get("scenes", [])), default=1.0)
        silent = r.get("silent_duration_s", r["duration_s"])
        rows.append(f"| `{film}_voice.mp4` | {r['status']} | {r['duration_s']:.1f} s | {silent:.1f} s | "
                    f"×{slow:.2f} | {r['bytes'] / 1e6:.1f} MB |")
    rows += ["", "Loudness: two-pass EBU R128 normalisation to −16 LUFS; true peak after AAC encoding ≤ −0.6 dBTP.",
             "Subtitles: `<film>_voice.srt` are the films' on-screen subtitles re-timed to the slowed scenes.", ""]
    (OUT / "MANIFEST.md").write_text("\n".join(rows), encoding="utf-8")


if __name__ == "__main__":  # python scripts/build_voiced_films.py --manifest-only rewrites MANIFEST.md
    if sys.argv[1:] == ["--manifest-only"]:
        write_manifest(json.loads((OUT / "VOICE_TIMING.json").read_text(encoding="utf-8")))
        sys.exit(0)
    main()
