# Onboarding visual system

The entry experience of EARTH SENSES: splash, language choice, intro, app. It has one
job: show that the same data can tell two opposite stories, and that this tool checks
which one the evidence supports — before the visitor touches a single control.

## Concept

**Earth as a living analytical object.** The globe is not decoration. It is a real
WebGL model of the planet that the camera *investigates*: it starts as the whole
living system, narrows to one 50 km grid cell over Pavlodar, and the numbers appear
beside it as if read off an instrument. Data overlays (coastlines, graticule, the
marker) are drawn from Natural Earth data, not painted.

**Mood:** a quiet mission-control room at night. Credible, unhurried, precise. The
drama comes from one reversal of sign (−0.285 → +0.593), not from effects.

What it is not: no lens flares, no "AI brain" imagery, no glitch, no countdown sounds,
no exaggerated zooms, nothing cartoonish.

## Colour

| Token | Hex | Use |
|---|---|---|
| `--es-space` | `#03050b` | Background; the renderer's clear colour |
| `--es-ink` | `#eef3fb` | Titles, values |
| `--es-ink-2` | `#b8c4d6` | Secondary text, bar labels |
| `--es-muted` | `#7d8aa0` | Captions, hints, source line |
| `--es-glow` | `#7fd6ff` | Data glow: coastlines, marker, checks, focus rings |
| `--es-accent` | `#3987e5` | Primary buttons (same accent as the app) |
| `--es-neg` | `#3987e5` | Negative correlation (same diverging pair as the app's charts) |
| `--es-pos` | `#e66767` | Positive correlation; the strike-through on rejected claims |
| `--es-glass` | `rgba(7,13,27,0.66)` | Panels and cards, with 10–12 px backdrop blur |
| `--es-line` | `rgba(127,214,255,0.16)` | Hairlines and card borders |

Series colours are the app's: precipitation `#3987e5`, relative humidity `#199e70`,
temperature `#d95926`. They were checked for colour-vision-deficiency separation in the
app (dataviz validator). Colour never carries meaning alone: every bar has its signed
value printed beside it, every rejected claim is struck through **and** tagged
"rejected", every check has a symbol.

## Typography

- Family: the app's system stack (Inter, -apple-system, Segoe UI, Roboto …); no web
  font download, so text renders instantly and Cyrillic, including the Kazakh letters
  ә ғ қ ң ө ұ ү һ і, uses well-hinted system glyphs.
- Wordmark: 800 weight, letter-spacing 0.22 em, `white-space: nowrap`,
  `clamp(34px, 6vw, 84px)`.
- Scene titles: 750 weight, `clamp(22px…64px)` by layout, `text-wrap: balance`.
- Numbers: `ui-monospace` with tabular figures, so −0.285 and +0.593 align and do not
  jitter while they animate. Minus is U+2212; Russian and Kazakh use a decimal comma.
- Subtitles: 16–21 px, white on a 42 % black box, at most two lines of 42 characters,
  at most 17 characters per second (tested).

## Motion

| Principle | Rule |
|---|---|
| One clock | Every motion in the intro (camera, text fades, bars, lines) is a function of one time value. Pause freezes everything; capture renders any frame exactly. |
| Ease | Cubic in-out for camera and bars; nothing linear except the slow spin. |
| Camera | Moves last 45 % of a scene, at most 2.4 s. Spin 2–6 °/s. Never more than one camera move per scene. |
| Text | Fades in over 0.6 s with a 10 px rise; fades out over the last 0.45 s of its scene. |
| Data | Lines draw from left to right over the first 60 % of a scene; bars grow from zero; the flip bar starts at the raw value and swings through zero. |
| Splash | Letters of the wordmark resolve from blur one by one (50 ms apart); tagline at 1.3 s; kicker at 2.0 s; motto at 2.6 s. |
| Exits | 0.6 s fade to the app. No wipes. |
| Reduced motion | `prefers-reduced-motion`: no spin, camera moves ≤ 0.4 s, CSS animations off; the intro still advances scene by scene. |

## Earth rendering style

- Photoreal day side (Blue Marble-style texture, 3072 × 1536), warm city lights on the
  night side; the sun comes from the left so a terminator is visible in most framings.
- Thin blue atmospheric rim (Fresnel glow, brighter on the day side).
- Analytical mode: a cool tint (`dataTint` uniform) plus glowing cyan coastlines and a
  faint 30° graticule from Natural Earth 1:110m. Used whenever data is on screen.
- A single marker for the investigated grid cell: core dot, ring, slow pulse, short
  beam out of the surface. Its screen position anchors labels in the intro.
- Sparse, seeded star field (identical in every run and every capture).

## Intro UI rules

1. One idea per scene; one title line; narration as a subtitle line.
2. The globe moves aside (x = −0.24 screen widths) when a panel needs the right half.
3. Panels are glass cards with a small uppercase cyan heading.
4. Every number shown is filled from `facts.json`, computed by the engine. No number is
   typed into a script. Bars may grow or flip; the printed value never counts up — it
   fades in once the bar has settled, so a paused frame cannot show an in-between number.
5. Rejected conclusions appear in quotes, struck through, tagged "rejected", with the
   reason and the number underneath.
6. Source line always available: *NASA POWER (MERRA-2 reanalysis) · Pavlodar grid
   cell · 2001–2024*.
7. Controls stay out of the picture: a thin progress bar segmented by scene, pause,
   replay, subtitles, skip. Keys: Space, R, C, Esc.

## Language switch style

- Its own screen, before any narration, so the intro is never shown in the wrong
  language.
- Three large cards, each label in its own language and script: English, Русский,
  Қазақша; the second line also in that language ("Continue in English",
  "Продолжить на русском", "Қазақ тілінде жалғастыру").
- The heading is shown in all three languages; the selected one is large.
- Number keys 1–3, arrows, Enter; the selected card glows (`--es-glow` ring).
- In the app the switch is a compact segmented control EN | RU | KZ in the header, next
  to an "Intro" button that re-opens the onboarding.

## Cinematic rules for the films

- 16:9, 24 fps for generated footage; the in-app capture renders at the screen's size.
- Start wide, end close: whole planet → region → grid cell → interface.
- Hold every number on screen for at least two seconds after it settles.
- Pause on the sign flip; it is the only dramatic beat.
- Keep the lower fifth calm for subtitles.
- All text and numbers are added in post from the scripts — never generated by a video
  model (see `docs/video/EXTERNAL_VIDEO_PROMPTS.md`).

## Sound and voice-over

**There is no sound in this build.** The in-app intro is silent and shows the narration
as subtitles (stated on screen: "No sound: the narration is shown as subtitles").

For a voiced version: one calm documentary voice per language, about 140 words per
minute in English (the scripts are timed for it); numbers read in full; no music, or
low ambient music ducked 12 dB under the voice. Voice scripts: section 3 of each file in
`docs/video/`. If a synthetic voice is used it must be declared as AI-generated in the
submission.
