# Demo Script and Recording Materials

**Official limits (2026 Project Submission Guide):** the project demo is **either a video of 30 seconds or less or a
deck of at most 7 slides including the title slide**. A longer demo makes the project ineligible for awards. The
link must open without login. Content must be in English; a video in another language needs English subtitles.
Images or video produced by an AI tool need a visible watermark — the materials below use **screen recordings and
screenshots of the running application only**, so no watermark is needed.

Every number below is what the application shows for the bundled NASA files. Do not round differently on screen
and in speech.

## The story in one sentence

> In raw NASA data, precipitation and humidity in Pavlodar move in **opposite** directions (r = −0.28). Remove the
> seasons, and they move **together** (r = +0.59). The first number was the calendar. EARTH SENSES shows which
> number to believe, and keeps the evidence.

What you may say about it, and what you may not:

| Say | Do not say |
|---|---|
| "Months wetter than usual are also more humid than usual." | "Rain causes humidity" / "humidity causes rain" |
| "The raw correlation was produced by the seasonal cycle." | "The raw data were wrong" |
| "It holds from spring to autumn and is absent in winter." | "It always holds" |
| "It survives holding temperature and specific humidity fixed: +0.44." | "We proved the link" |
| "This is one MERRA-2 grid cell, a model reanalysis." | "This is what happens in the city of Pavlodar" |

## Setup (once, 3 minutes)

```bash
source .venv/bin/activate
(cd frontend && npm ci && npm run build)
EARTH_SENSES_OFFLINE=1 uvicorn earth_senses.api:app --app-dir backend --port 8000
```

Open <http://localhost:8000> in Chrome. Window 1920 × 1080, browser zoom 110%, dark theme (default), language EN.
`EARTH_SENSES_OFFLINE=1` serves the bundled, hash-verified NASA files, so the demo does not depend on the network.
Pavlodar, 2001–2024, with temperature, humidity and precipitation ticked is the default state: press **Investigate**
once before recording so the result is cached and appears instantly.

## A. 30-second video

Timing follows the structure recommended in the guide: introduce, name the challenge, title and tagline, the idea,
what comes next. Record the screen once, silently, following the *Screen* column; add the voice-over afterwards.
Total spoken text: about 65 words — roughly 26 seconds at a calm pace. **Check the exported file is 0:30 or shorter.**

| Time | Screen | Voice-over | On-screen caption |
|---|---|---|---|
| 0:00–0:02 | Start screen: map with Pavlodar selected | "We are team ⟨NAME⟩." | Team ⟨NAME⟩ · ⟨city⟩ |
| 0:02–0:05 | Same; cursor moves to **Investigate** | "Our challenge: Earth system trend detective." | Be An Earth System Trend Detective! |
| 0:05–0:10 | Click **Investigate**; trend cards appear | "EARTH SENSES doesn't just find trends. It questions them." | EARTH SENSES — AI proposes. Evidence decides. |
| 0:10–0:16 | Scroll to **Precipitation ↔ Relative humidity**; hold on the four bars | "Raw NASA data: precipitation and humidity move in opposite directions. Minus 0.28." | Raw: r = −0.28 |
| 0:16–0:21 | Same card; cursor moves from the *Raw* bar to the *Deseasonalized* bar | "Remove the seasons and it flips: plus 0.59. The first number was the calendar." | Seasons removed: r = +0.59 |
| 0:21–0:25 | Click **View evidence →**; drawer opens; scroll to *Source NASA data* | "Every result keeps its evidence and its NASA file hash." | Evidence · counterevidence · SHA-256 |
| 0:25–0:30 | Tab **Relationship graph** | "Next: more NASA data, more detectives." | github.com/Alishka14/nasa-space-app-2026 |

Subtitles for this cut: [`docs/demo/subtitles_en.srt`](demo/subtitles_en.srt) (English) and
[`docs/demo/subtitles_ru.srt`](demo/subtitles_ru.srt) (Russian, for a version voiced in Russian — keep the English
file as the burned-in subtitles).

### Shot list for the editor

1. **Start screen** — 2 s static, then cursor travels to the button (3 s).
2. **Click → results** — keep the moment the three trend cards appear (the "no significant trend / fragile" badges
   are visible; do not zoom).
3. **Scroll to the precipitation–humidity card** — one smooth scroll; stop when the title *Precipitation
   (bias-corrected) ↔ Relative humidity (2 m)* is at the top of the window.
4. **Hold on the bar chart** *Correlation as seasonality and trend are removed* — 5 s; optional zoom-in to 160% on
   the four bars.
5. **View evidence** — click, wait for the drawer, scroll once to the SHA-256.
6. **Relationship graph** — click the tab; end frame is the triangle with r = +0.59 on the bottom edge.

Reference frames (captures of the real application): `docs/screenshots/01_investigate.png`,
`08_precipitation_humidity.png`, `02_view_evidence.png`, `03_relationship_graph.png`.

### Recording checklist

- [ ] Exported duration ≤ 0:30 (check the file, not the timeline).
- [ ] English captions readable at 720p; no caption covers the bar chart.
- [ ] Nobody under 18 appears in the video; no NASA logo is added.
- [ ] No AI-generated image, voice or footage. If an AI voice is used for narration, say so in the *Use of Super
      Intelligence* field and add a visible watermark.
- [ ] Uploaded where it opens without login (for example YouTube *Unlisted* or *Public*); link tested in a private
      window.

## A2. Ready-made demo: `docs/video/renders/demo_en.mp4` (29.3 s)

Built only from real material: a screenshot of the splash (3 s), the app's own **Short intro** (16.5 s, rendered
frame by frame from the running app) and three screenshots of the app answering the same question (9.5 s) with
English captions. 1920×1080, silent — every spoken idea is on screen in English.

| Time | Picture | Text on screen |
|---|---|---|
| 0:00–0:03 | Splash: challenge name, EARTH SENSES, tagline, NASA imagery credit | (optional) team name and members |
| 0:03–0:19.5 | Short intro: Same NASA data → −0.285 → +0.593 → seasonality → Evidence before conclusions | the intro's own titles and subtitles |
| 0:19.5–0:22.5 | App: Pavlodar investigated, three variables | In the app: choose a place, variables and years — NASA POWER data |
| 0:22.5–0:26 | App: the precipitation ↔ humidity card | Raw −0.28, seasons removed +0.59 — and not detected in winter |
| 0:26–0:29.3 | App: the evidence drawer | Every result keeps its evidence, counter-evidence and NASA source file |

**Add the team name** (the guide asks for it at 0:00): `TEAM="Team ⟨NAME⟩ · ⟨member names⟩" bash scripts/make_demo.sh`
— it rebuilds the file in about a minute. Without `TEAM` the line is left out rather than invented.

**Publish:** upload `demo_en.mp4` to YouTube as *Unlisted* (or to Vimeo / Google Drive with "anyone with the link"),
open the link in a private browser window to check it plays without login, and paste it into the form. The film is
a screen recording of the app, not generated footage; the AI-use field of the form already says the code and texts
were written with AI assistance.

To re-record the intro films after a change: `node scripts/record_intro.mjs <teaser|explainer|hero> <en|ru|kk>`
with `SCALE=1.5` for 1920×1080, then `python scripts/package_videos.py`.

To show it live instead: open `http://localhost:8000/?intro`, pick a language, choose **Short**, press **Start**.

## B. Seven slides (alternative to the video)

| # | Title | Content | Visual |
|---|---|---|---|
| 1 | **EARTH SENSES — Interconnected Earth Intelligence** | Team name and members · Challenge: *Be An Earth System Trend Detective!* · "AI proposes. Evidence decides." | `01_investigate.png` as background |
| 2 | **The problem: a trend is easy, trusting it is hard** | Seasons fake correlations · one year can make a trend "significant" · some variables are computed from others · "not significant" is read as "no change" | Three short bullets, no chart |
| 3 | **The flip: −0.28 becomes +0.59** | Pavlodar, NASA POWER / MERRA-2, 2001–2024. Raw: −0.28. Seasonal cycles alone: −0.78. Seasons removed: +0.59 (95% CI +0.51 to +0.66) | `08_precipitation_humidity.png`, cropped to the bar chart |
| 4 | **Then it doubts its own answer** | Absent in winter (−0.06), strongest in summer (+0.70) · +0.37 with every month weighted equally · +0.44 with temperature and specific humidity held fixed · same in 1981–2000 (+0.58) | By-season chart and the "held fixed" table |
| 5 | **Every claim keeps its evidence** | Claim · evidence · counterevidence · alternatives · limitations · NASA file SHA-256. Relative humidity flagged as computed from temperature (rebuilt at r = 0.98) | `02_view_evidence.png`, `09_derived_variable_check.png` |
| 6 | **How it works, and how to check us** | NASA POWER API → validation → trend / relationship engines → evidence records → React interface. 160 automated tests. No AI in the calculations. One command reproduces every number | Architecture diagram from `NASA_SUBMISSION.md` §7 |
| 7 | **Limits and next steps** | One reanalysis grid cell; one model; no human scientific review yet. Next: independent satellite and station data, more regions, classroom use | Repository URL |

## C. Live walk-through (about four minutes, for judges or mentors)

| Time | Do | Say |
|---|---|---|
| 0:00 | Start screen with the map. | "The challenge asks for a trend detective. Finding a trend is easy. Knowing whether to believe it is the hard part." |
| 0:15 | Click **Pavlodar**; point at the rectangle on the map. | "Real NASA data: MERRA-2 through the POWER service. A point is really a grid cell about fifty kilometres across, and we show that." |
| 0:30 | **Investigate**. Trend cards. | "Temperature: minus 0.02 degrees per year, not significant. The tool does not say 'no warming'. It says this record could only detect trends above about one degree per decade." |
| 0:55 | Humidity card; heatmap with RH2M selected. | "Humidity looks significant, p = 0.035. After correcting for three tests it is 0.105, it flips if you remove any one of five years, and before 2001 the slope had the opposite sign. Verdict: fragile." |
| 1:25 | **Precipitation ↔ Relative humidity**, the four bars. | "Our main result. Raw: minus 0.28. The two seasonal cycles alone: minus 0.78. Remove the seasons: plus 0.59. The raw number was the calendar." |
| 1:50 | Same card: season chart, then the *held fixed* table. | "And the tool doubts its own answer. Nothing in winter, plus 0.70 in summer. It survives holding temperature fixed." |
| 2:10 | **View evidence →** on that card; scroll the drawer. | "Claim, evidence, counterevidence, alternatives we could not exclude, limitations, and the NASA file with its SHA-256." |
| 2:30 | **Air temperature ↔ Relative humidity**; point at the ⚙ box. | "Minus 0.95 raw, minus 0.32 between anomalies. And a warning: relative humidity is computed from temperature, so part of this is built into the definition." |
| 2:45 | Tick **Specific humidity**, **Investigate**; scroll to *Derived-variable check*. | "With specific humidity added we can measure it: rebuilt from temperature and moisture with a textbook formula, humidity matches NASA's values at 0.98." |
| 3:10 | Tab **Relationship graph**; **Check wording**. | "An edge exists only if it was computed from data. And if anyone, human or AI, writes 'temperature causes humidity to fall, which proves the link', it is blocked." |
| 3:30 | Tab **Evidence timeline**. | "How each interpretation was reached and revised: observation, hypothesis, test, counterexample, revision, conclusion." |
| 3:45 | Tab **Report**; scroll to the end. | "One click gives the full report, ending with what cannot be concluded. AI proposes. Evidence decides." |

Optional 20 seconds: tab **Compare regions**, Pavlodar and Almaty → "opposite signs, neither significant, and the
tool says exactly that; it also warns that this 'Almaty' cell sits at 2,500 metres."

## Questions a judge may ask

| Question | Answer |
|---|---|
| Is this NASA data? | Yes. NASA POWER (Langley) serving MERRA-2 (GMAO). It is a model reanalysis for one grid cell, and the tool says so. |
| Why does the correlation change sign? | Both variables follow the seasons in opposite phase. Subtracting each month's average removes that. What remains is whether wetter-than-usual months are more humid than usual. |
| So rain makes the air humid? | We do not claim that. Both may follow the same air masses. The tool blocks causal wording and lists this under "cannot be concluded". |
| Isn't humidity just temperature in disguise? | Partly, and the tool flags it. But the precipitation–humidity link stays at +0.59 with temperature held fixed and +0.44 with temperature and specific humidity held fixed. |
| Did an AI produce the conclusions? | No. All numbers come from deterministic code on hashed NASA files. AI wrote the code and a first exploratory analysis, which the tool then checked. This is disclosed in the submission. |
| How do you know the statistics are right? | 160 automated tests: cross-checks against `pymannkendall` and `statsmodels`, synthetic series with known answers, and sixteen outside numbers reproduced. No human scientist has reviewed it yet, and we say so. |
| Did you check against satellite precipitation? | We tried. NASA POWER's IMERG parameter returned only missing values for this point. The response is stored, and the tool refuses to analyse it rather than show empty results. |
| Why is "no significant trend" not "no change"? | The confidence interval for temperature runs from −0.67 to +0.46 °C per decade. |
