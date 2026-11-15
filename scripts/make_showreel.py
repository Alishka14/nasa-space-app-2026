#!/usr/bin/env python3
"""Showreel: a full walkthrough of EARTH SENSES on one real example (~106 s, 1920x1080, English titles).

    python scripts/make_showreel.py [out.mp4] [--voice DIR]

Built only from real material: the app's own intro film (docs/video/renders/hero_en.mp4, screen recording),
screenshots of the running app, and the synthesised music bed (docs/video/music/earth_senses_bed.mp3).
Chapter cards carry the explanation as on-screen text. With --voice DIR, clips DIR/sr_<n>.mp3 (one per
chapter, optional) are placed at the start of their chapter and the picture label says "AI voice".
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERO = ROOT / "docs/video/renders/hero_en.mp4"
MUSIC = ROOT / "docs/video/music/earth_senses_bed.mp3"
STILLS = ROOT / "docs/video/demo_stills"
VSHOTS = ROOT / "docs/visual/screenshots"
FONT_B = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
FONT_R = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"
FPS = 24
W, H = 1920, 1080

# (chapter label, title, body, [footage...]); footage = ("hero", start, dur) | ("still", path, dur, label)
WT = ROOT / "docs/video/walkthrough_stills"   # real screens of the running app (Pavlodar, 2001–2024)
CHAPTERS = [
    ("", "EARTH SENSES", "A full walkthrough, on one real example\n\nalishkaTeam · Ali & Diyaz\nNASA Space Apps Challenge 2026 · Be An Earth System Trend Detective!", 4.5, []),
    ("The challenge", "How do air, water and heat\nchange together?",
     "Our question: do rain and humidity move together\nin Pavlodar, Kazakhstan?", 3.5, [("hero", 6.6, 5.4)]),
    ("How we built it", "A hypothesis is not a result.",
     "Gemini gave a first exploratory analysis. We rebuilt every\nnumber in our own engine on NASA POWER (MERRA-2) data:\n180 automated tests, nothing estimated by an AI.", 4.0, [("hero", 13.0, 5.0)]),
    ("Step 1 · Set up", "Choose a place, variables and years.",
     "Example: Pavlodar · air temperature, relative humidity,\nprecipitation · 2001–2024 (288 months).", 3.0,
     [("still", WT / "w01_setup.jpg", 4.0, "Pick a place on the map, tick the variables, choose the years — Investigate")]),
    ("Step 2 · Trends", "Every variable: a trend, an interval, a verdict.",
     "Temperature −0.021 °C/yr: no significant trend.\nHumidity +0.164 points/yr: p = 0.035, but q = 0.105 after correction → fragile.", 3.5,
     [("still", WT / "w02_results.jpg", 4.5, "Each card shows the Theil–Sen slope, its 95% interval, p, q (FDR) and the verdict"),
      ("still", WT / "w03_trend_fragile.jpg", 4.0, "Humidity: “Fragile — not established”, not a headline")]),
    ("Step 3 · Relationships", "Rain and humidity: the sign flips.",
     "Raw monthly values: r = −0.285. The seasonal cycles alone give −0.775.\nSeasons removed: r = +0.593. By season: winter −0.06, summer +0.70.", 3.5,
     [("still", WT / "w04_relationship_card.jpg", 5.0, "The raw negative value was the calendar; the anomalies move together")]),
    ("Step 4 · Evidence", "Every number opens its evidence.",
     "Evidence, counter-evidence, alternatives not excluded,\nmethod, uncertainty, limitations and the NASA source file.", 3.0,
     [("still", WT / "w05_evidence.jpg", 5.0, "View evidence: everything behind one claim")]),
    ("Step 5 · Relationship graph", "An edge only where data support it.",
     "Seasons removed: rain ↔ humidity +0.59, temperature ↔ humidity −0.32,\ntemperature ↔ rain −0.12 (weak). Hypotheses annotate edges, never create them.", 3.0,
     [("still", WT / "w06_graph.jpg", 4.5, "Edges carry the deseasonalised correlation and its status")]),
    ("Step 6 · Evidence timeline", "How each conclusion was reached and revised.",
     "Observation → hypothesis → test → counter-example → revision → conclusion.", 2.5,
     [("still", WT / "w07_timeline.jpg", 4.0, "Every step cites the evidence it rests on")]),
    ("Step 7 · Compare regions", "Same years, same method, another place.",
     "Pavlodar vs Almaty: temperature trends with opposite signs —\nand neither is statistically significant.", 2.5,
     [("still", WT / "w08_compare.jpg", 4.5, "Differences in elevation are stated next to the comparison")]),
    ("Step 8 · Report", "A report you can share.",
     "Markdown with data provenance: the NASA POWER request,\nretrieval time and SHA-256 fingerprint of every file.", 2.5,
     [("still", WT / "w09_report.jpg", 4.0, "Download .md — every number is traceable")]),
    ("Guardrails", "Say only what the data support.",
     "Correlation is not causation. “No warming” is not a valid conclusion here;\n“humidity is rising” is a fragile result.", 3.5, [("hero", 48.0, 6.5)]),
    ("For everyone", "A real NASA Earth, in three languages.",
     "3D globe with NASA imagery, intro films and narration\nin English, Russian and Kazakh.", 3.0,
     [("still", VSHOTS / "02_language_en.jpg", 2.2, "Choose a language"),
      ("still", VSHOTS / "11_intro_flip_kk.jpg", 2.2, "The intro in Kazakh")]),
    ("", "AI proposes. Evidence decides.",
     "alishkaTeam · Ali & Diyaz\ngithub.com/Alishka14/nasa-space-app-2026\n\nData: NASA POWER (MERRA-2) · Earth imagery: NASA Earth Observatory", 5.0, []),
]


def run(cmd: list[str]) -> None:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"failed: {' '.join(cmd[:8])}\n{p.stderr[-1500:]}")


def dur(p: Path) -> float:
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 str(p)], capture_output=True, text=True).stdout)


def enc(dst: Path) -> list[str]:
    return ["-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
            "-an", str(dst)]


def fades(d: float) -> str:
    return f"fade=t=in:st=0:d=0.35,fade=t=out:st={d - 0.35:.2f}:d=0.35"


def card(tmp: Path, bg: Path, i: int, label: str, title: str, body: str, d: float) -> Path:
    files = {}
    for k, v in (("label", label), ("title", title), ("body", body)):
        f = tmp / f"c{i}_{k}.txt"
        f.write_text(v, encoding="utf-8")
        files[k] = f
    big = title in ("EARTH SENSES",)
    tsize = 120 if big else 64
    vf = ["crop=iw:ih*0.55:0:0", f"scale={W}:{H}", "boxblur=24:2", "eq=brightness=-0.30:saturation=0.85"]  # top of the globe only: no titles
    if label:
        vf.append(f"drawtext=fontfile={FONT_B}:textfile={files['label']}:fontsize=30:fontcolor=0x7dd3fc:x=160:y=300")
    vf.append(f"drawtext=fontfile={FONT_B}:textfile={files['title']}:fontsize={tsize}:fontcolor=white:"
              f"line_spacing=14:x=160:y={360 if label else 330}")
    nlines = title.count("\n") + 1
    ybody = (360 if label else 330) + nlines * (tsize + 18) + 40
    vf.append(f"drawtext=fontfile={FONT_R}:textfile={files['body']}:fontsize=38:fontcolor=0xd1d5db:"
              f"line_spacing=16:x=160:y={ybody}")
    vf.append(fades(d))
    dst = tmp / f"seg{i:02d}_0.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-t", f"{d}", "-i", str(bg), "-vf", ",".join(vf)] + enc(dst))
    return dst


def footage(tmp: Path, i: int, j: int, item: tuple, chapter: str) -> Path:
    dst = tmp / f"seg{i:02d}_{j + 1}.mp4"
    lab = tmp / f"f{i}_{j}.txt"
    if item[0] == "hero":
        _, ss, d = item
        lab.write_text(chapter, encoding="utf-8")
        vf = [f"scale={W}:{H}",
              f"drawtext=fontfile={FONT_B}:textfile={lab}:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.55:"
              f"boxborderw=12:x=40:y=36", fades(d)]
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{ss}", "-t", f"{d}", "-i", str(HERO), "-vf", ",".join(vf)] + enc(dst))
    else:
        _, path, d, caption = item
        lab.write_text(f"{chapter}  ·  {caption}", encoding="utf-8")
        vf = [f"scale={W}:{H}:force_original_aspect_ratio=decrease",
              f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x05070d",
              f"drawtext=fontfile={FONT_B}:textfile={lab}:fontsize=30:fontcolor=white:box=1:boxcolor=black@0.7:"
              f"boxborderw=16:x=(w-text_w)/2:y=h-110", fades(d)]
        run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-t", f"{d}", "-i", str(path), "-vf", ",".join(vf)] + enc(dst))
    return dst


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = Path(args[0]) if args else ROOT / "docs/video/renders/showreel_walkthrough_en.mp4"
    voice = Path(sys.argv[sys.argv.index("--voice") + 1]) if "--voice" in sys.argv else None
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        bg = tmp / "bg.png"
        run(["ffmpeg", "-y", "-v", "error", "-ss", "0.15", "-i", str(HERO), "-frames:v", "1", str(bg)])
        segs, starts, t0 = [], [], 0.0
        for i, (label, title, body, d, items) in enumerate(CHAPTERS):
            starts.append(t0)
            segs.append(card(tmp, bg, i, label, title, body, d))
            t0 += d
            for j, it in enumerate(items):
                segs.append(footage(tmp, i, j, it, label))
                t0 += it[2]
        lst = tmp / "list.txt"
        lst.write_text("".join(f"file '{s}'\n" for s in segs))
        video = tmp / "video.mp4"
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(video)])
        total = dur(video)
        # audio: music bed (ducked under voice if any), two-pass to -18 LUFS (music only -20)
        inputs = ["-stream_loop", "-1", "-i", str(MUSIC)]
        clips = []
        if voice:
            for i, s in enumerate(starts):
                c = voice / f"sr_{i}.mp3"
                if c.exists():
                    clips.append((c, s + 0.4))
        fc = [f"[0:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,aformat=channel_layouts=stereo,"
              f"loudnorm=I=-30:TP=-6,afade=t=in:d=1.5,afade=t=out:st={total - 3:.3f}:d=3[mu]"]
        if clips:
            for k, (c, s) in enumerate(clips, start=1):
                inputs += ["-i", str(c)]
                ms = int(s * 1000)
                fc.append(f"[{k}:a]aformat=channel_layouts=stereo,adelay={ms}|{ms}[v{k}]")
            vo = "".join(f"[v{k}]" for k in range(1, len(clips) + 1))
            fc.append(f"{vo}amix=inputs={len(clips)}:normalize=0:duration=longest,apad,atrim=0:{total:.3f},asplit=2[va][vb]")
            fc.append("[mu][vb]sidechaincompress=threshold=0.02:ratio=6:attack=20:release=450[md]")
            fc.append("[va][md]amix=inputs=2:normalize=0:duration=first[mix]")
            target = -16
        else:
            fc.append("[mu]anull[mix]")
            target = -20
        raw = tmp / "mix.wav"
        run(["ffmpeg", "-y", "-v", "error"] + inputs + ["-filter_complex", ";".join(fc), "-map", "[mix]",
                                                         "-t", f"{total:.3f}", str(raw)])
        meas = subprocess.run(["ffmpeg", "-i", str(raw), "-af", f"loudnorm=I={target}:TP=-1.5:print_format=json",
                               "-f", "null", "-"], capture_output=True, text=True).stderr
        m = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
        ln = (f"loudnorm=I={target}:TP=-1.5:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
              f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}")
        label = ["-vf", f"drawtext=fontfile={FONT_B}:text='AI voice (ElevenLabs)':fontsize=22:fontcolor=white@0.78:"
                        f"box=1:boxcolor=black@0.45:boxborderw=8:x=w-text_w-28:y=24"] if clips else []
        vcodec = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p"] if clips else ["-c:v", "copy"]
        out.parent.mkdir(parents=True, exist_ok=True)
        run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-i", str(raw)] + label +
            ["-map", "0:v", "-map", "1:a", "-af", ln] + vcodec +
            ["-c:a", "aac", "-b:a", "160k", "-t", f"{total:.3f}", "-movflags", "+faststart",
             "-metadata", "title=EARTH SENSES — full walkthrough (showreel)",
             "-metadata", "comment=Real material only: screen recording of the in-app intro and screenshots of the "
                          "running app. Music synthesised by scripts/synth_music_bed.py. "
                          + ("Narration: synthetic ElevenLabs voice (AI). " if clips else "No voice-over. ")
                          + "Data: NASA POWER (MERRA-2). Earth imagery: NASA Earth Observatory. Team: alishkaTeam.",
             str(out)])
        (out.with_suffix(".chapters.json")).write_text(json.dumps(
            [{"chapter": c[0] or c[1], "start_s": round(s, 2)} for c, s in zip(CHAPTERS, starts)], indent=1),
            encoding="utf-8")
        print(f"{out}: {dur(out):.1f} s, voice clips: {len(clips)}")


if __name__ == "__main__":
    main()
