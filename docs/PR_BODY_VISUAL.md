## Visual module: 3D Earth onboarding, intro films in English / Русский / Қазақша

Adds a first-visit onboarding to EARTH SENSES. The analysis engine is unchanged apart from one MIZAN Guard rule for
Russian word order. Developed in `RakamakadoN/earth-senses` and brought here as its own commits, with authorship
kept. The MVP already in `main` is not added again.

### What it adds

- **3D Earth** (three.js, WebGL). It shows day and night, city lights, the atmosphere, coastlines and the Pavlodar
  grid cell. Without WebGL it falls back to a labelled 2D globe.
- **Splash → language (English / Русский / Қазақша) → intro → app.**
  - Language and "intro seen" are remembered.
  - **▶ Intro** in the header replays the onboarding, and **EN · RU · KZ** switches the language.
  - Esc or **Skip** leaves at any time.
- **Intro in three lengths:** Short 16.5 s, Explainer 45 s, Full film 59.5 s. Every number comes from the
  engine, for example precipitation ↔ humidity −0.285 raw and +0.593 with the seasonal cycle removed.
  `backend/tests/test_09_intro_content.py` fails if the numbers drift.
- **Films:** `docs/video/renders/`, 1920×1080 H.264. They are screen captures of the running app, not generated
  footage. There are nine intro films (3 lengths × 3 languages) and `demo_en.mp4` (30 s or less) for the NASA form.
  Scripts, storyboards, SRT subtitles, final narration texts with pronunciation, and prompts for external
  generators are in `docs/video/`.
- **Earth imagery: NASA Earth Observatory.** The images are Blue Marble: Next Generation and Earth at Night 2012.
  They are byte-identical to the files in NASA's WorldWind repository, with SHA-256 pinned and tested. The credit
  appears on the splash screen and in every film. Details: `docs/visual/ASSETS_AND_LICENSES.md`.

### Checks

- `cd backend && python -m pytest` — see the result in the PR comment / description update.
- Frontend build passes. In the browser flow, 16 of 16 steps pass with no console errors.
- All 20 scenes were checked in each language at 1280×720, 1440×900, 1024×768 and 390×844: no text overlaps and
  nothing is clipped.
- Skip and Replay have names, are reachable with Tab, show a visible focus ring and work with Enter and Esc.

### Not done

- The Russian and Kazakh texts have not been reviewed by native speakers.
- There is no voice-over: the films are silent and show the narration as subtitles.
- A public video link for the NASA form still has to be created: upload `demo_en.mp4`.
- The NASA images were not compared with NASA Visible Earth's own copies, because those servers are blocked from
  the build environment.

Draft — please review before merging. Merge with **Create a merge commit**, not squash or rebase.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01KCCBh435ACxUgRUjviubtK
