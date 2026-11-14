"""Generate the video documents from intro-scripts.json (the same file the app plays).

Writes:
  docs/video/{HERO,EXPLAINER,TEASER}_{EN,RU,KK}.md   (9 scripts with storyboard, VO, on-screen text, subtitles)
  docs/video/subtitles/{variant}_{lang}.srt           (9 subtitle files)
  docs/video/VIDEO_MASTER_PLAN.md
  docs/video/EXTERNAL_VIDEO_PROMPTS.md

Run from the repository root:  python scripts/build_video_docs.py
"""
from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from intro_content import LANGS, ROOT, fill, load_facts, load_locale, load_scripts  # noqa: E402

OUT = ROOT / "docs" / "video"
SUBS = OUT / "subtitles"
MAX_LINE = 42
MAX_CPS = 17.0          # subtitle reading speed ceiling (characters per second)

H = {  # localized headings
    "en": dict(variant="Variant", language="Language", duration="Duration", target="Target length", audience="Audience",
               concept="1. Short concept", storyboard="2. Scene-by-scene storyboard", vo="3. Voiceover script",
               onscreen="4. On-screen text", subs="5. Subtitles", est="6. Estimated duration", tone="7. Tone direction",
               prompt="8. Prompt for an external video generator", scene="Scene", time="Time", shot="Shot",
               camera="Camera", text="On-screen text", srtfile="Subtitle file", reading="Reading speed",
               chars="characters per second, maximum", generated="Generated from", noaudio=(
                   "No audio track exists yet. The in-app intro shows this narration as subtitles; record the voice-over "
                   "from section 3 if a sound version is needed."),
               numbers="Every number above is filled from facts.json, which is computed by the engine from the NASA files.",
               see="Shot-by-shot prompts, constraints and sync notes are in",
               wordsec="words", seconds="s"),
    "ru": dict(variant="Вариант", language="Язык", duration="Длительность", target="Целевая длина", audience="Аудитория",
               concept="1. Краткая концепция", storyboard="2. Покадровая раскадровка", vo="3. Текст диктора",
               onscreen="4. Текст на экране", subs="5. Субтитры", est="6. Оценка длительности", tone="7. Тон и подача",
               prompt="8. Промпт для внешнего видеогенератора", scene="Сцена", time="Время", shot="Кадр",
               camera="Камера", text="Текст на экране", srtfile="Файл субтитров", reading="Скорость чтения",
               chars="символов в секунду, максимум", generated="Сгенерировано из", noaudio=(
                   "Звуковой дорожки пока нет. Встроенное вступление показывает этот текст субтитрами; если нужна "
                   "озвученная версия, запишите голос по разделу 3."),
               numbers="Все числа подставлены из facts.json, который движок вычисляет по файлам NASA.",
               see="Покадровые промпты, ограничения и синхронизация — в файле",
               wordsec="слов", seconds="с",
               shotnote="Описание кадров — на английском: это рабочие заметки для монтажа и видеогенератора."),
    "kk": dict(variant="Нұсқа", language="Тіл", duration="Ұзақтығы", target="Мақсатты ұзақтық", audience="Аудитория",
               concept="1. Қысқа тұжырымдама", storyboard="2. Сахналық раскадровка", vo="3. Диктор мәтіні",
               onscreen="4. Экрандағы мәтін", subs="5. Субтитрлер", est="6. Болжамды ұзақтық", tone="7. Үн мен ырғақ",
               prompt="8. Сыртқы бейне генераторына арналған промпт", scene="Сахна", time="Уақыт", shot="Кадр",
               camera="Камера", text="Экрандағы мәтін", srtfile="Субтитр файлы", reading="Оқу жылдамдығы",
               chars="секундына таңба, ең көбі", generated="Мына файлдан жасалған", noaudio=(
                   "Дыбыс жолағы әзірге жоқ. Қосымшадағы кіріспе бұл мәтінді субтитрмен көрсетеді; дыбыстық нұсқа "
                   "қажет болса, 3-бөлім бойынша дауыс жазыңыз."),
               numbers="Барлық сандар facts.json файлынан алынған; оны есептеу жүйесі NASA файлдарынан есептейді.",
               see="Кадрлық промпттар, шектеулер және синхрондау мына файлда",
               wordsec="сөз", seconds="с",
               shotnote="Кадр сипаттамасы ағылшын тілінде: бұл монтаж бен бейне генераторына арналған жұмыс жазбалары."),
}
LANG_NAME = {"en": "English", "ru": "Русский", "kk": "Қазақша"}
VISUAL_EN = {"earth": "Earth from space", "layers": "Data layers over the globe", "focus": "Focus on the grid cell",
             "series-raw": "Raw time series", "corr": "Correlation bars", "corr-flip": "Correlation flips sign",
             "title": "Title over the globe", "checks": "Evidence checklist", "claims": "Rejected conclusions",
             "enter": "Transition into the app"}


def ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def mmss(seconds: float) -> str:
    return f"{int(seconds) // 60}:{seconds % 60:04.1f}"


def split_cues(text: str) -> list[str]:
    """Sentences, then clauses, so that no cue is longer than two subtitle lines."""
    parts = [p.strip() for p in re.split(r"(?<=[.!?…])\s+", text) if p.strip()]
    out: list[str] = []
    for p in parts:
        if len(p) <= 2 * MAX_LINE:
            out.append(p)
            continue
        chunks, cur = [], ""
        for piece in re.split(r"(?<=[,:;—])\s+", p):
            if cur and len(cur) + 1 + len(piece) > 2 * MAX_LINE:
                chunks.append(cur)
                cur = piece
            else:
                cur = (cur + " " + piece).strip()
        if cur:
            chunks.append(cur)
        out.extend(chunks)
    return out


def wrap2(text: str) -> str:
    lines = textwrap.wrap(text, MAX_LINE, break_long_words=False, break_on_hyphens=False)
    if len(lines) <= 2:
        return "\n".join(lines)
    mid = len(text) // 2
    cut = text.rfind(" ", 0, mid + 10)
    return text[:cut] + "\n" + text[cut + 1:]


def cues_for(variant: dict, lang: str, facts: dict) -> list[tuple[float, float, str]]:
    cues, t0 = [], 0.0
    for s in variant["scenes"]:
        vo = fill(s["vo"][lang], facts, lang)
        parts = split_cues(vo)
        start, end = t0 + 0.25, t0 + s["dur"] - 0.2
        total = sum(len(p) for p in parts)
        cur = start
        for p in parts:
            span = (end - start) * len(p) / total
            cues.append((cur, cur + span, wrap2(p)))
            cur += span
        t0 += s["dur"]
    return cues


def srt(cues: list[tuple[float, float, str]]) -> str:
    return "".join(f"{i}\n{ts(a)} --> {ts(b)}\n{t}\n\n" for i, (a, b, t) in enumerate(cues, 1))


def max_cps(cues) -> float:
    return max(len(t.replace("\n", " ")) / (b - a) for a, b, t in cues)


def variant_doc(v: dict, lang: str, facts: dict) -> tuple[str, str]:
    h = H[lang]
    loc = load_locale(lang)
    total = sum(s["dur"] for s in v["scenes"])
    cues = cues_for(v, lang, facts)
    words = sum(len(fill(s["vo"][lang], facts, lang).split()) for s in v["scenes"])
    name = loc[f"lang.variant.{v['id']}"]
    srt_name = f"subtitles/{v['id']}_{lang}.srt"
    L = [f"# EARTH SENSES — {name} ({v['file']}_{lang.upper()})", "",
         f"> {h['generated']} `frontend/src/onboarding/content/intro-scripts.json` · `scripts/build_video_docs.py`. "
         f"{h['numbers']}", "",
         f"| | |", "|---|---|",
         f"| {h['variant']} | {v['file']} — {name} |",
         f"| {h['language']} | {LANG_NAME[lang]} |",
         f"| {h['duration']} | {total:.1f} {h['seconds']} |",
         f"| {h['target']} | {v['target'][0]}–{v['target'][1]} {h['seconds']} |",
         f"| {h['audience']} | {v['audience'][lang]} |", "",
         f"## {h['concept']}", "", v["concept"][lang], "",
         f"## {h['storyboard']}", "",
         *([h["shotnote"], ""] if h.get("shotnote") else []),
         f"| # | {h['time']} | {h['shot']} | {h['camera']} | {h['text']} |", "|---|---|---|---|---|"]
    t0 = 0.0
    for i, s in enumerate(v["scenes"], 1):
        cam = s.get("camera", {})
        cam_txt = f"{cam.get('lat', '')}°, {cam.get('lon', '')}° · d {cam.get('dist', '')}" if cam else "—"
        L.append(f"| {i} | {mmss(t0)}–{mmss(t0 + s['dur'])} | {VISUAL_EN[s['visual']]}: {s['prompt']} | {cam_txt} | "
                 f"{fill(s['title'][lang], facts, lang)} |")
        t0 += s["dur"]
    L += ["", f"## {h['vo']}", "", h["noaudio"], ""]
    t0 = 0.0
    for s in v["scenes"]:
        L.append(f"**[{mmss(t0)}]** {fill(s['vo'][lang], facts, lang)}  ")
        t0 += s["dur"]
    L += ["", f"## {h['onscreen']}", ""]
    for s in v["scenes"]:
        L.append(f"- {fill(s['title'][lang], facts, lang)}")
    widgets = {s["widget"]["type"] for s in v["scenes"] if s.get("widget")}
    if "checks" in widgets:
        L.append("- " + loc["checks.title"] + ": " + "; ".join(fill(loc[k], facts, lang) for k in (
            "checks.seasons", "checks.tests", "checks.periods", "checks.winter", "checks.causation", "checks.scope")))
    if "claims" in widgets:
        L.append(f"- {loc['claims.warming']} — {fill(loc['claims.warmingWhy'], facts, lang)}")
        L.append(f"- {loc['claims.humidity']} — {fill(loc['claims.humidityWhy'], facts, lang)}")
    L.append(f"- {loc['intro.source']}")
    L += ["", f"## {h['subs']}", "", f"{h['srtfile']}: [`{srt_name}`]({srt_name})", "", "```srt", srt(cues).rstrip(), "```", "",
          f"## {h['est']}", "",
          f"- {total:.1f} {h['seconds']} · {len(v['scenes'])} · {words} {h['wordsec']}",
          f"- {h['reading']}: {max_cps(cues):.1f} {h['chars']} ({MAX_CPS:.0f})", "",
          f"## {h['tone']}", "", v["tone"][lang], "",
          f"## {h['prompt']}", "",
          f"{h['see']} [`EXTERNAL_VIDEO_PROMPTS.md`](EXTERNAL_VIDEO_PROMPTS.md#{v['id']}).", ""]
    return "\n".join(L), srt(cues)


GLOBAL_STYLE = (
    "Cinematic scientific visualisation, NASA mission-control mood. Photoreal Earth from space against a deep black "
    "sky with sparse sharp stars; day side lit from the left, night side with warm city lights, thin blue atmospheric "
    "rim. Cool cyan data overlays (thin coastlines, faint latitude-longitude grid). Slow, steady camera moves with eased "
    "starts and stops; no shake, no lens flares, no fast cuts. Colour: near-black navy background, white and cyan "
    "accents, blue for negative values, red for positive values. 16:9, 24 fps.")
NEGATIVE = (
    "No text, numbers, letters, logos or flags rendered by the generator (all text is added in post); no NASA logo or "
    "insignia; no people or faces; no fire, storms, disasters or apocalyptic imagery; no glowing 'AI brain' imagery; "
    "no cartoon style; no invented charts; no fictional satellites with labels; no cities zoomed to street level; "
    "no changes to the shape of continents.")


def prompts_doc(scripts: dict, facts: dict) -> str:
    L = ["# External video generation prompts", "",
         "> Generated by `scripts/build_video_docs.py` from `intro-scripts.json`. For tools such as Gemini (Veo) or "
         "other text-to-video generators. **No video was generated for this repository.**", "",
         "## Rules that apply to every variant", "",
         "1. **The generator makes pictures only.** Every word and every number is added in post-production from the "
         "on-screen text in the script files (`HERO_EN.md` …). Generators misspell text and invent digits; a wrong "
         "correlation on screen would defeat the purpose of the project.",
         "2. **Numbers come from `facts.json` only:** " + ", ".join(
             f"{k} = {fill('{' + k + '}', facts, 'en')}" for k in ("p_rh_raw", "p_rh_cycles", "p_rh_deseason",
                                                                  "t_rh_raw", "t_rh_deseason")) + ".",
         "3. **Charts are not generated.** For the correlation and time-series shots, capture the real in-app frames "
         "(`?capture&variant=…&lang=…`, see `docs/video/VIDEO_MASTER_PLAN.md`) and use the generated footage only as "
         "background plates.",
         "4. **Disclosure.** The NASA Space Apps rules require AI-generated images and video to carry a visible "
         "watermark and to be declared in the *Use of Super Intelligence* field.",
         "5. **Length.** The submission demo must be 30 seconds or less. Only the Teaser (and a trimmed Explainer) "
         "fits; the Hero film is for presentations.", "",
         "## Global style prompt", "", "```text", GLOBAL_STYLE, "```", "",
         "## Negative prompt / constraints", "", "```text", NEGATIVE, "```", ""]
    for v in scripts["variants"]:
        total = sum(s["dur"] for s in v["scenes"])
        L += [f'<a id="{v["id"]}"></a>', "", f"## {v['file'].title()} — {total:.1f} s (target {v['target'][0]}–{v['target'][1]} s)", "",
              v["concept"]["en"], "", "### Visual generation prompt (whole film)", "", "```text",
              GLOBAL_STYLE + " Story: " + " Then ".join(
                  re.sub(r"[−+]?\d+\.\d+", "[value added in post]", s["prompt"]).rstrip(".") for s in v["scenes"]) + ".",
              "```", "", "### Shot-by-shot prompts and timing", "",
              "| Shot | Time | Length | Prompt (pictures only) | Text added in post (EN) |", "|---|---|---|---|---|"]
        t0 = 0.0
        for i, s in enumerate(v["scenes"], 1):
            pic = re.sub(r"[−+]?\d+\.\d+", "[value in post]", s["prompt"])
            L.append(f"| {i} | {mmss(t0)} | {s['dur']:.1f} s | {pic} | {fill(s['title']['en'], facts, 'en')} |")
            t0 += s["dur"]
        L += ["", "### Subtitle overlay notes", "",
              "- Use the SRT files in `docs/video/subtitles/` (`" + v["id"] + "_en.srt`, `_ru.srt`, `_kk.srt`); white, "
              "sentence case, bottom centre, at most two lines of 42 characters, black 40% box behind the text.",
              "- Keep the lower fifth of every generated shot calm (no bright clouds or city lights) so the subtitles stay legible.",
              "- Numbers on screen use the language's own format: −0.285 (en), −0,285 (ru, kk).", "",
              "### Voice-over sync notes", "",
              "- One scene = one VO block; each block starts 0.25 s after the cut and ends 0.2 s before the next.",
              "- Pause about half a second after the line that states the second correlation; the flip is the point of the film.",
              "- Read numbers as 'minus zero point two eight five' (en), 'минус ноль целых двести восемьдесят пять тысячных' "
              "or the shorter 'минус ноль двести восемьдесят пять' (ru), 'минус нөл бүтін мыңнан екі жүз сексен бес' (kk).",
              "- No music is specified. If music is added: ambient, low, no beat drops; duck it 12 dB under the voice.", ""]
    return "\n".join(L)


def probe(path: Path) -> str:
    """'16.5 s | 1280×720, 24 fps' from ffprobe, or '—' when ffprobe is not installed."""
    import json as _json
    import shutil
    import subprocess
    if not shutil.which("ffprobe"):
        return "— | —"
    out = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", "-show_format",
                          str(path)], capture_output=True, text=True, check=False).stdout
    try:
        info = _json.loads(out)
        v = next(st for st in info["streams"] if st["codec_type"] == "video")
        num, den = (int(x) for x in v["r_frame_rate"].split("/"))
        return f"{float(info['format']['duration']):.1f} s | {v['width']}×{v['height']}, {num / den:g} fps"
    except (ValueError, KeyError, StopIteration):
        return "— | —"


def master_plan(scripts: dict, facts: dict, stats: dict) -> str:
    L = ["# Video master plan — EARTH SENSES intro", "",
         "> Generated by `scripts/build_video_docs.py`. The in-app intro, these documents and the subtitles are produced "
         "from one file, `frontend/src/onboarding/content/intro-scripts.json`; the numbers from `facts.json`, which "
         "`scripts/build_intro_assets.py` computes with the engine from the hash-verified NASA files.", "",
         "## What exists", "",
         "| | State |", "|---|---|",
         "| In-app intro (3 variants × 3 languages), motion graphics over the real WebGL Earth | **Built** — the primary experience |",
         "| Scripts, storyboards, on-screen text, subtitles for all 9 versions | **Built** (this folder) |",
         "| Recorded video files | Only if listed under *Recorded files* below. A recording is a screen capture of the in-app intro, not generated footage |",
         "| Voice-over audio | **Not recorded.** The scripts in section 3 of each file are ready for recording |",
         "| Generated (AI) video | **Not made.** Prompts are in `EXTERNAL_VIDEO_PROMPTS.md` |",
         "| Native-speaker review of the Kazakh and Russian texts | **Not done** |", "",
         "## The nine versions", "",
         "| Variant | Purpose | Length | EN | RU | KK |", "|---|---|---|---|---|---|"]
    for v in scripts["variants"]:
        total = sum(s["dur"] for s in v["scenes"])
        cells = " | ".join(f"[{v['file']}_{l.upper()}]({v['file']}_{l.upper()}.md) · {stats[(v['id'], l)]:.1f} cps"
                           for l in LANGS)
        L.append(f"| {v['file'].title()} | {v['audience']['en']} | {total:.1f} s | {cells} |")
    L += ["", "cps = the highest subtitle reading speed in that version (ceiling 17 characters per second).", "",
          "## Story every version keeps", "",
          "1. Earth as one interconnected system.",
          "2. Data can mislead when read naively.",
          f"3. Seasonality changes the relationship: precipitation–humidity {fill('{p_rh_raw}', facts, 'en')} raw, "
          f"{fill('{p_rh_deseason}', facts, 'en')} with the seasonal cycle removed (Pavlodar grid cell, 2001–2024).",
          "4. EARTH SENSES checks the evidence (seasonality, autocorrelation, multiple tests, other periods).",
          "5. Correlation is not causation.",
          "6. Uncertainty and limits are kept: “no warming” is not supported; “humidity is rising” is fragile.",
          "7. The viewer enters the application.", "",
          "## What the films must not say", "",
          "- that a causal relation is proven;", "- that there is no warming;", "- that humidity is definitely rising;",
          "- that the atmosphere has no memory;", "- anything about a city or region beyond one MERRA-2 grid cell.", "",
          "Checked automatically: `backend/tests/test_09_intro_content.py` runs every English and Russian line through "
          "the MIZAN Guard (Kazakh is not covered by the guard), checks every number against the engine, every "
          "placeholder, every duration and every reading speed.", "",
          "## How to record a version from the app", "",
          "```bash",
          "EARTH_SENSES_OFFLINE=1 uvicorn earth_senses.api:app --app-dir backend --port 8000",
          "# open http://localhost:8000/?capture&variant=teaser&lang=en  (no controls, clock driven by window.__esIntro.seek)",
          "node scripts/record_intro.mjs teaser en        # frame-exact capture -> docs/video/renders/teaser_en.mp4",
          "```", "",
          "Live playback (with controls): <http://localhost:8000/?intro>. Choose the language and the length on the "
          "second screen. Keys: Space pause, R replay, C subtitles, Esc skip.", "",
          "## Recorded files", ""]
    renders = sorted((OUT / "renders").glob("*.mp4")) if (OUT / "renders").exists() else []
    if renders:
        L += ["Frame-exact screen captures of the running application made with `scripts/record_intro.mjs` "
              "(headless Chrome, software WebGL, H.264, **silent** — the narration is on screen). They are not "
              "generated footage and not a finished edit: no voice, no music, no team title card.", "",
              "| File | Length | Picture | Size |", "|---|---|---|---|"]
        L += [f"| [`renders/{p.name}`](renders/{p.name}) | {probe(p)} | {p.stat().st_size / 1e6:.1f} MB |"
              for p in renders]
    else:
        L.append("None yet.")
    L += ["", "---", "", "**Кратко по-русски.** Три варианта (Hero ≈ 60 с, Explainer ≈ 45 с, Teaser ≈ 17 с) на трёх "
          "языках. Все тексты, субтитры и встроенное вступление берутся из одного файла; числа — из `facts.json`, "
          "посчитанного движком. Озвучка и сгенерированное видео не сделаны; промпты — в `EXTERNAL_VIDEO_PROMPTS.md`."]
    return "\n".join(L)


def main() -> int:
    facts = load_facts()
    scripts = load_scripts()
    SUBS.mkdir(parents=True, exist_ok=True)
    stats = {}
    for v in scripts["variants"]:
        for lang in LANGS:
            md, s = variant_doc(v, lang, facts)
            (OUT / f"{v['file']}_{lang.upper()}.md").write_text(md + "\n", encoding="utf-8")
            (SUBS / f"{v['id']}_{lang}.srt").write_text(s, encoding="utf-8")
            stats[(v["id"], lang)] = max_cps(cues_for(v, lang, facts))
    (OUT / "EXTERNAL_VIDEO_PROMPTS.md").write_text(prompts_doc(scripts, facts) + "\n", encoding="utf-8")
    (OUT / "VIDEO_MASTER_PLAN.md").write_text(master_plan(scripts, facts, stats) + "\n", encoding="utf-8")
    for (vid, lang), cps in sorted(stats.items()):
        print(f"{vid:10s} {lang}  max {cps:4.1f} cps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
