# Preview notes — onboarding and intro

All images in [`screenshots/`](screenshots/) are captures of the running application with the NASA Earth textures (`EARTH_SENSES_OFFLINE=1`,
built frontend served by the backend), taken in headless Chrome with **software WebGL (SwiftShader)** at 1440 × 900
(mobile: 390 × 844). Nothing is mocked up or generated. On a laptop with a real GPU the globe is the same scene, drawn
faster and with smoother edges.

## Screenshot index

| File | What it shows | Where in the flow |
|---|---|---|
| `01_splash_en.jpg` | Splash: wordmark, tagline, the Earth rising from below, NASA imagery credit | First seconds of a first visit |
| `02_language_en.jpg` · `03_language_ru.jpg` · `04_language_kk.jpg` | Language screen: three cards in their own names, intro length chips, globe turned to Kazakhstan | After the splash |
| `05_intro_place_en.jpg` | Explainer, scene 1: Pavlodar marker and coordinates | Intro, 0–6.5 s |
| `06_intro_raw_and_cycles_en.jpg` | Explainer, scene 2→3: raw −0.285 and the seasonal cycles alone −0.775 | Intro, 13–19.5 s |
| `07_intro_flip_en.jpg` | Short intro: −0.285 → +0.593 once the seasonal cycle is removed | Short intro, 4–9 s |
| `08_intro_temperature_humidity_en.jpg` | Temperature ↔ humidity −0.945 → −0.316, with the note that relative humidity is computed partly from temperature | Explainer, 19.5–28 s |
| `09_intro_checks_en.jpg` | "Before any conclusion": the six checks, incl. winter −0.06 / summer +0.70 and correlation ≠ causation | Explainer, 28–35 s |
| `10_intro_rejected_claims_en.jpg` | "No warming" and "Humidity is rising" struck through, with the reasons | Explainer, 35–40.5 s |
| `11_intro_flip_kk.jpg` | The same flip in Kazakh (decimal comma, Kazakh labels) | Full film, Kazakh |
| `12_intro_end_kk.jpg` | Last scene, as recorded in the film (in the app a button opens the app here) | Full film, Kazakh, end |
| `13_app_header_kk.jpg` | Main app in Kazakh: **EN · RU · KZ** switch and **▶ Intro** in the header | After the intro |
| `14_fallback_2d.jpg` | No-WebGL fallback: a labelled 2D dotted globe instead of the 3D one | `?earth=2d` or no WebGL |
| `15_mobile_kk.jpg` | Splash and language screen on a phone-sized screen | 390 × 844 |

Numbers in the intro come from `frontend/src/onboarding/content/facts.json`, which `scripts/build_intro_assets.py`
computes with the same engine as the app; `backend/tests/test_09_intro_content.py` fails if they drift. While a bar
grows, only the bar moves; the number appears when the bar has settled, so a paused frame never shows an in-between
value.

## See it yourself

```
http://localhost:8000/?intro              full onboarding, as on a first visit
http://localhost:8000/?intro=language     straight to the language screen
http://localhost:8000/?nointro            skip it
http://localhost:8000/?intro&lang=kk      first visit with Kazakh preselected
http://localhost:8000/?intro&earth=2d     the fallback globe
```

Keys during the intro: **Space** pause · **R** replay · **C** subtitles on/off · **Esc** skip to the app.
On the language screen: **1 / 2 / 3** or arrows to choose, **Enter** to start.

## Presenting it to judges (about one minute)

1. Open `/?intro`. While the splash runs: *"This is a real 3D Earth drawn live in the browser, not a video."*
2. On the language screen press **3** (Қазақша) to show it is built for the region, then **1** for English; choose
   **Short** and press **Enter**.
3. During the flip: *"Raw NASA data say precipitation and humidity move in opposite directions, −0.285. Remove the
   seasonal cycle and they move together, +0.593. The first number described the calendar."*
4. When the app opens, press **Investigate** and scroll to *Precipitation ↔ Relative humidity* — the same
   values, rounded there to two decimals (−0.28, +0.59).
5. **▶ Intro** in the header replays it; **EN · RU · KZ** switches the whole interface.

Say: "a relationship that survives removing the seasons", "one model grid cell", "correlation, not cause".
Do not say: "we proved rain causes humidity", "there is no warming", "humidity is definitely rising".

**If the projector laptop has no WebGL** the 2D fallback appears with a note; the story and numbers are the same.
**If there is no time**, press **Esc** — the app opens immediately. The splash and intro are skipped automatically
on every later visit.

## Known caveats visible in the preview

- Software rendering in these captures makes the coastlines slightly soft and the motion less smooth than on a GPU.
- The Russian and Kazakh texts have not yet been reviewed by native speakers.
- The intro is silent; the narration is shown as subtitles.
- Earth imagery is NASA's (Blue Marble: Next Generation, Earth at Night 2012), credited on the splash screen and in
  every film; provenance in [`ASSETS_AND_LICENSES.md`](ASSETS_AND_LICENSES.md).
