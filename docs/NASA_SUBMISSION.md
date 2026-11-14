# NASA Space Apps Challenge 2026 — Submission Package

**Challenge:** Be An Earth System Trend Detective!
**Project:** EARTH SENSES — Interconnected Earth Intelligence

Everything below is in English, as the Project Submission Guide requires. Part A is the text for each field of the
official form. Part B is the same material arranged under the ten headings the team asked for. All numbers come from
the engine's output for the bundled NASA files (`docs/SCIENCE_REVIEW.md`, `docs/EVIDENCE_LEDGER.md`).

## Before you submit — team checklist

| # | Item | State |
|---|---|---|
| 1 | Push `feat/earth-senses-mvp` and open the Draft PR (`docs/HANDOFF.md`) | **TO DO** — could not be done from the build environment |
| 2 | Make the repository **public**: the guide says the final-project link must open without login, permission or registration | **TO DO** — the repository currently asks for credentials |
| 3 | Record the demo: a video of **30 seconds or less**, or **at most 7 slides** including the title slide. A longer demo makes the project ineligible for awards | **TO DO** — script, subtitles and slide outline in `docs/DEMO_SCRIPT.md` |
| 4 | Host the demo at a public link (no login) and paste it into *Link to Project Demo* | **TO DO** |
| 5 | Read the science once as humans (`docs/SCIENCE_REVIEW.md`, 10 minutes) and confirm you stand behind it | **TO DO** — no human review has taken place |
| 6 | Confirm the statement about the origin of the idea in *Use of Super Intelligence* (field A6) | **TO DO** |
| 7 | Fill in team name, members (1–6), local event | **TO DO** |
| 8 | Tick the two checkboxes (terms; originality with all outside resources listed in References) | **TO DO** |
| 9 | Submit before Sunday 15 November, 23:59 local-event time | **TO DO** |

---

# Part A — Official form fields

## A1. Project Name

EARTH SENSES — Interconnected Earth Intelligence

## A2. High-Level Project Summary

EARTH SENSES is a web tool for anyone who wants to know what is changing in the Earth system at a place, and whether
to believe it. Pick a point on the map, choose variables and years, and it reports how fast each variable is
changing, whether the change is statistically significant, and which variables vary together. Then it does what a
careful scientist would do next: it removes the seasonal cycle, corrects for multiple tests and autocorrelation,
repeats the analysis on other periods, checks whether a link survives when a third variable is held fixed, flags
variables that are computed from each other, and lists what the data cannot tell you. In our Pavlodar case the
correlation between precipitation and relative humidity is −0.28 in the raw NASA data and +0.59 once the seasonal
cycle is removed: the raw number was the calendar, not the weather. Every result is an evidence record with its
method, uncertainty, counterevidence and the SHA-256 of the NASA file behind it, and a built-in guard blocks causal
or "proven" wording that such statistics cannot support. The challenge asks for trend detectives; EARTH SENSES
teaches the detective's most important habit, which is to doubt the first answer.

## A3. Link to Project Demo

**TO DO** — public link to a video of 30 seconds or less, or to a deck of at most 7 slides
(see `docs/DEMO_SCRIPT.md`).

## A4. Link to Final Project

<https://github.com/Alishka14/nasa-space-app-2026> (branch `feat/earth-senses-mvp` until the team merges it) —
**TO DO: push the branch and make the repository public.**

## A5. Detailed Project Description

**What it does.** The user opens a map, selects a location (a preset or any point), ticks variables, sets the years
and presses *Investigate*. EARTH SENSES then shows:

- for each variable, the rate of change per year (Theil–Sen slope) with a 95% confidence interval, a significance
  test that accounts for autocorrelation, a false-discovery-corrected q-value and a verdict: *robust trend*,
  *fragile trend* or *no significant trend detected*;
- time series as monthly values, seasonal cycle, anomalies and annual means with the trend line, one panel per
  variable, and a heatmap of the trend over every sub-period, so the user sees at once whether the answer depends on
  the years chosen;
- for each pair of variables, the correlation computed four ways (raw, seasonal cycles alone, deseasonalized,
  detrended), split by season, scanned over lags of ±6 months, and recomputed with each other variable held fixed
  (partial correlation);
- a ⚙ *built-in dependence* flag where one variable is computed from the other (relative humidity is calculated by
  NASA POWER from temperature, specific humidity and pressure), with a check that measures how strong that built-in
  link is;
- a relationship graph in which an edge exists only if it was computed from data; hypotheses can annotate an edge
  but never create one;
- *View Evidence* for every result: claim, evidence, counterevidence, alternatives not excluded, limitations, method,
  parameters, and the source NASA file with its request and hash;
- an evidence timeline (observation → hypothesis → test → counterexample → revision → conclusion), a comparison of
  two regions, and a downloadable report that ends with "what cannot be concluded from these data".

**How it works.** A Python backend (FastAPI, NumPy, SciPy, pandas) retrieves monthly data from the NASA POWER API,
validates it (annual-summary keys separated from months, fill values treated as missing, units read from the
response, complete calendar, correct location), stores the raw response unchanged with a provenance record and its
SHA-256, and runs the analyses. A React + TypeScript interface with MapLibre and Apache ECharts displays only what
the backend returns. No language model takes part in any calculation or in wording any finding: sentences are fixed
templates filled with computed numbers, and each passes a wording guard before it is shown.

**What we found in the demonstration case** (Pavlodar, Kazakhstan, 52.29°N 76.97°E, 2001–2024, MERRA-2 via NASA
POWER):

- *Precipitation and relative humidity.* Raw monthly correlation −0.28. The two seasonal cycles alone give −0.78:
  winters are humid with little precipitation, summers are the reverse. Between monthly anomalies the correlation is
  **+0.59** (95% CI +0.51 to +0.66). It remains +0.59 with temperature held fixed and +0.44 with temperature and
  specific humidity both held fixed, it is +0.58 in the separate 1981–2000 record, and it is absent in winter
  (−0.06) and strongest in summer (+0.70). With every calendar month weighted equally it is +0.37.
- *Temperature and relative humidity.* −0.95 raw, −0.98 from the seasonal cycles alone, −0.32 between anomalies. The
  tool flags this edge as partly built into the definition of relative humidity: rebuilt from temperature and
  specific humidity with a textbook formula, relative humidity matches the NASA values at r = 0.98.
- *Temperature.* No significant trend, and the tool explains why that is not "no warming": the 95% interval runs
  from −0.67 to +0.46 °C per decade.
- *Relative humidity.* p = 0.035, classified as fragile: q = 0.105 after correction, the result flips when any one of
  five years is left out, and the slope has the opposite sign in 1981–2000.

**Benefits.** Students and the public get a trend tool that teaches the habits of a careful analyst. Teachers get a
ready-made lesson on why correlation needs deseasonalizing. Researchers and journalists get results they can trace
to a file hash and rerun.

**Tools and languages.** Python 3.13 (FastAPI, NumPy, SciPy, pandas, statsmodels, pytest), TypeScript, React, Vite,
MapLibre GL JS, Apache ECharts, Natural Earth outlines.

**Honest limits.** One reanalysis grid cell, not station data; all variables come from one model; no independent
observational check; no review by a human scientist yet. Details: `docs/KNOWN_LIMITATIONS.md`.

## A6. Use of Super Intelligence (SI)

SI tools were used and are disclosed here, in the repository README and in the commit metadata.

- **Claude (Anthropic)** wrote the application code, the automated tests, the reproduction of the preliminary
  analysis, the scientific self-audit and the documentation, working from the team's written brief and under the
  team's direction. Commits carry a `Co-Authored-By: Claude` trailer.
- **Gemini (Google)** produced a preliminary exploratory analysis of the Pavlodar data. We treated it as a proposal:
  all sixteen of its numbers were recomputed independently from separately retrieved NASA data
  (`docs/GEMINI_REPRODUCTION.md`), and three interpretations those numbers might suggest were rejected by the
  evidence.
- **No SI takes part in the tool's results.** Every number and every sentence the user sees comes from deterministic
  code and fixed templates. The repository contains no SI-generated data.
- **No SI-generated images, video or audio** are used. Screenshots are captures of the running application. No NASA
  logos or branding are used.
- The project idea, the challenge choice and the methodological principles (MIZAN, BATYR AGA, Ghost Busters and the
  others described in `docs/METHOD_INTEGRATION.md`) came from the team. **TO DO: the team confirms this sentence.**
- The checks described in `docs/SCIENCE_REVIEW.md` were run by an SI system and are a self-audit, not an independent
  scientific validation. Team members are responsible for the submission.

## A7. NASA Data

| NASA resource | How it is used |
|---|---|
| **NASA POWER** (Prediction Of Worldwide Energy Resources), Monthly & Annual API v2.10.0, NASA Langley Research Center — <https://power.larc.nasa.gov/> | Source of every value analysed: monthly `T2M` (air temperature at 2 m), `RH2M` (relative humidity at 2 m), `PRECTOTCORR` (bias-corrected precipitation), `QV2M` (specific humidity at 2 m) for a point, 1981 onward |
| **MERRA-2** (Modern-Era Retrospective analysis for Research and Applications, Version 2), NASA Global Modeling and Assimilation Office | The reanalysis behind those POWER parameters, on a 0.5° × 0.625° grid |
| **NASA POWER methodology documentation** — <https://power.larc.nasa.gov/docs/methodology/meteorology/relative-humidity/> | Establishes that relative humidity is calculated from temperature, specific humidity and pressure, which the tool flags and tests |
| **GPM IMERG** precipitation, requested through NASA POWER as `IMERG_PRECTOT` | Requested as an independent check on precipitation. For the Pavlodar point the service returned its missing-value code for every month of 2001–2024. The response is stored as evidence and the tool refuses to analyse it. **No IMERG result is claimed.** |

Four NASA responses are bundled byte-for-byte, each with a provenance record and SHA-256
(`data/raw/power/`, `data/provenance/`).

## A8. Space Agency Partner Data and Other References

No Space Agency Partner data are used.

Other data: Natural Earth country outlines (public domain) through the `world-atlas` package, for the basemap only.

References

- NASA POWER Project, NASA Langley Research Center. <https://power.larc.nasa.gov/>
- NASA POWER Project. Methodology: Relative Humidity. <https://power.larc.nasa.gov/docs/methodology/meteorology/relative-humidity/>
- Gelaro, R., et al. (2017). The Modern-Era Retrospective Analysis for Research and Applications, Version 2 (MERRA-2). *Journal of Climate* 30, 5419–5454.
- Mann, H. B. (1945). Nonparametric tests against trend. *Econometrica* 13, 245–259.
- Kendall, M. G. (1975). *Rank Correlation Methods.* Griffin.
- Sen, P. K. (1968). Estimates of the regression coefficient based on Kendall's tau. *JASA* 63, 1379–1389.
- Hirsch, R. M., Slack, J. R., Smith, R. A. (1982). Techniques of trend analysis for monthly water quality data. *Water Resources Research* 18, 107–121.
- Hirsch, R. M., Slack, J. R. (1984). A nonparametric trend test for seasonal data with serial dependence. *Water Resources Research* 20, 727–732.
- Hamed, K. H., Rao, A. R. (1998). A modified Mann-Kendall trend test for autocorrelated data. *Journal of Hydrology* 204, 182–196.
- Santer, B. D., et al. (2000). Statistical significance of trends and trend differences in layer-average atmospheric temperature time series. *JGR* 105, 7337–7356.
- Bretherton, C. S., et al. (1999). The effective number of spatial degrees of freedom of a time-varying field. *Journal of Climate* 12, 1990–2009.
- Benjamini, Y., Hochberg, Y. (1995). Controlling the false discovery rate. *JRSS B* 57, 289–300.
- World Meteorological Organization (2008). *Guide to Meteorological Instruments and Methods of Observation*, WMO-No. 8, Annex 4.B.
- Software: NumPy, SciPy, pandas, statsmodels, FastAPI, Uvicorn, pydantic, httpx, pytest, pymannkendall (tests only), React, Vite, TypeScript, MapLibre GL JS, Apache ECharts, world-atlas, topojson-client.
- SI tools: Claude (Anthropic), Gemini (Google) — see A6.

---

# Part B — The ten sections

## 1. Project Description

EARTH SENSES is an open-source web application that investigates trends and relationships in NASA Earth-system data
for any point on Earth and keeps the evidence for every statement it makes. A user chooses a place, variables and a
period; the tool returns rates of change with confidence intervals and significance, the relationships between
variables tested several ways, a graph of those relationships, an evidence record for every result, and an explicit
list of what cannot be concluded. It is built for students, educators, journalists and curious citizens: people who
can read a chart but have no one to tell them when a chart is misleading.

## 2. Problem Statement

Open NASA data and a spreadsheet are enough to produce a trend line or a correlation in minutes. They are also
enough to produce a wrong conclusion in minutes:

- two variables that both follow the seasons correlate strongly even when their year-to-year behaviour is unrelated;
- a "significant" trend can vanish when one year is removed, when several tests are run at once, or when the period
  changes;
- some variables are computed from others, so their correlation is an identity, not a discovery;
- "no significant trend" is routinely read as "nothing is changing";
- a correlation is routinely read as a cause.

AI assistants make this faster, not safer: they produce fluent explanations for numbers nobody checked. The
challenge asks participants to be trend detectives. The missing tool is one that shows not only the clue but also
whether the clue survives cross-examination.

## 3. Proposed Solution

A tool that applies the cross-examination automatically and shows it to the user.

| A detective asks | EARTH SENSES does |
|---|---|
| Is it just the seasons? | Reports each correlation raw, from the seasonal cycles alone, deseasonalized and detrended; decides on the last |
| Is it just luck? | Autocorrelation-aware tests, effective sample sizes, a year-shuffled control, false-discovery correction |
| Is it just this period? | Trend over every sub-period, leave-one-year-out, automatic comparison with the longer record |
| Is it just a third variable? | Partial correlations with each other variable held fixed |
| Is it true by definition? | Flags pairs in which one variable is computed from the other and measures the built-in link |
| What is the evidence? | A record per result: claim, method, uncertainty, counterevidence, alternatives, limitations, NASA file hash |
| What must I not say? | A wording guard blocks causal and "proven" language; every report ends with what cannot be concluded |

**The demonstration.** For Pavlodar, 2001–2024, precipitation and relative humidity correlate at **−0.28** in the raw
monthly data. Removing each variable's average seasonal cycle turns this into **+0.59**. The negative number
described the calendar (winters: high relative humidity and little precipitation; summers: the reverse). The positive number describes the
weather: months that are wetter than usual for the time of year are also more humid than usual. The tool then
qualifies its own result: the link is absent in winter, it weakens to +0.37 when every month is weighted equally, it
survives holding temperature and specific humidity fixed (+0.44), and it is a correlation inside one reanalysis, not
a demonstrated cause.

## 4. NASA Data Sources

| Source | Product | Parameters | Resolution | Period used |
|---|---|---|---|---|
| NASA POWER API v2.10.0 (NASA LaRC), `https://power.larc.nasa.gov/api/temporal/monthly/point` | MERRA-2 reanalysis (NASA GMAO) | `T2M`, `RH2M`, `PRECTOTCORR`, `QV2M` | 0.5° × 0.625° grid cell, monthly means | 1981–2024 (Pavlodar), 2001–2024 (Almaty grid cell) |
| NASA POWER API, parameter `IMERG_PRECTOT` | GPM IMERG | precipitation | — | Requested for Pavlodar 2001–2024; **returned only missing values**; not analysed |

- The data are **model reanalysis** constrained by satellite and conventional observations. They are not direct
  satellite or station measurements, and the tool says so on screen.
- Any other point and any period from 1981 are requested live from NASA POWER when the backend has internet access;
  the response is validated and stored with a provenance record before it is analysed.
- If data cannot be obtained or contain gaps, the tool returns an error. It never substitutes invented values.

## 5. Scientific Methodology

Full description with decision rules: `docs/SCIENCE_METHOD.md`. Self-audit: `docs/SCIENCE_REVIEW.md`.

1. **Data integrity.** Annual-summary keys separated from months; fill values → missing; units from the response;
   calendar completeness; request geometry; SHA-256 re-verified on every read.
2. **Trends.** Theil–Sen slope with 95% CI on day-weighted annual means. Reported p = the larger of the Hamed–Rao
   modified Mann–Kendall p and the AR(1)-adjusted least-squares p. Seasonal Kendall test on monthly values.
   Benjamini–Hochberg across variables. Minimum detectable trend. Verdict `ROBUST_TREND` only if significance also
   survives sub-period and leave-one-year-out checks.
3. **Relationships.** Pearson and Spearman correlation of raw values, seasonal cycles alone, deseasonalized and
   detrended anomalies; effective sample size (Bretherton et al. 1999); year-block permutation control; halves and
   10-year windows; by season; equal-month-weight variant; false-discovery q across pairs; partial correlations.
4. **Lags.** ±6 months, Benjamini–Hochberg across the 13 lags. A lead or lag is reported as timing only.
5. **Derived variables.** Relative humidity is rebuilt from temperature and specific humidity with the Magnus
   formula (nothing fitted) and compared with the NASA values.
6. **Language.** Fixed sentence templates; the MIZAN Guard rejects causal verbs, proof language, "no change"
   conclusions and lag-as-direction. Physical explanations exist only as labelled, untested hypotheses.
7. **Decision rules fixed in advance.** α = 0.05, |r| ≥ 0.2, 2000 permutations with a fixed seed, the same for every
   region.

## 6. Innovation and Impact

- **The product is the doubt.** Most trend tools stop at the chart. EARTH SENSES ships the counterevidence, the
  alternatives it could not exclude and the list of what cannot be concluded as first-class output.
- **Evidence records.** Each result has a deterministic id derived from its method, parameters and data hash, so the
  same inputs always give the same record and anyone can recompute it.
- **A guard against overclaiming** that applies equally to the tool's own sentences, to a human and to an AI.
- **AI proposes, evidence decides.** The project began with an AI-generated analysis; the tool reproduced its
  numbers, kept what the evidence supports and rejected the rest. That workflow is the template we propose for using
  AI in citizen science.
- **Impact.** A classroom can reproduce the Pavlodar reversal in one click and then try its own town. Users leave
  with four transferable habits: remove the seasons, correct for the number of tests, change the period, and
  separate what was observed from what is proposed.

## 7. Technical Architecture

```
NASA POWER API ──► power_client  (fetch · validate · store raw bytes · SHA-256 · provenance record)
                        │
                   normalize     (months vs annual keys · fill values · units · calendar)
                        │
        ┌───────────────┼────────────────┬──────────────┐
     trends        relationships       derived        guard
 (Theil–Sen, MK,  (4-way correlation, (RH rebuilt   (wording rules,
  Hamed–Rao, FDR,  n_eff, permutation, from T and    EN + RU)
  windows, LOO)    lags, partial)      QV)
        └───────────────┼────────────────┴──────────────┘
                   investigate ──► evidence records · relationship graph · change episodes · report
                        │
                   FastAPI  (/api/investigate · /api/compare · /api/evidence/{id} · /api/report · /api/guard/check)
                        │
        React + TypeScript + Vite · MapLibre GL (map) · Apache ECharts (charts)
```

- Backend: Python 3.13, FastAPI, NumPy, SciPy, pandas, statsmodels. Pure functions for the science; the API layer
  contains no statistics.
- Frontend: React 19, TypeScript, Vite 7; offline basemap; colour palette checked for colour-vision deficiency;
  every status has an icon and a label, never colour alone; English interface with Russian labels.
- Tests: 160 automated tests (data traps on real NASA files, statistics cross-checked against `pymannkendall` and
  `statsmodels`, synthetic controls with known answers, guard rules, API contract, golden values).

## 8. Reproducibility and Evidence

```bash
git clone https://github.com/Alishka14/nasa-space-app-2026 && cd nasa-space-app-2026
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements-dev.txt
python scripts/build_provenance.py        # SHA-256 of the four NASA files: must print OK four times
(cd backend && python -m pytest)          # 160 tests
python scripts/science_review.py          # recomputes every number of the science review
(cd frontend && npm ci && npm run build)
EARTH_SENSES_OFFLINE=1 uvicorn earth_senses.api:app --app-dir backend --port 8000   # http://localhost:8000
```

- Raw NASA responses are stored unchanged; every provenance record holds the request URL, retrieval time, API
  version, SHA-256 and validation checks.
- Every evidence record cites the hash of the data it was computed from; `docs/EVIDENCE_LEDGER.md` lists all of them.
- `docs/GEMINI_REPRODUCTION.md`: sixteen numbers from an outside analysis, each reproduced at its reported precision.
- Status ladder: every record is `OBSERVED` or `HYPOTHESIS`. Nothing is labelled as validated by an independent
  party, because nothing has been.

## 9. Known Limitations

- **Reanalysis, one grid cell.** MERRA-2 values for a cell of about 50 km, at the cell's mean elevation; not a
  station, not a city. No homogeneity test of the reanalysis.
- **One model behind all variables.** Relationships between them may be tighter than in nature. No independent
  observational check: IMERG through NASA POWER returned no data for this point.
- **Relative humidity is computed from temperature**, so that relationship is partly built in; the tool flags it.
- **The precipitation–humidity link is seasonal** (absent in winter) and is a correlation, not a cause.
- **Short records.** With 24 years only temperature trends above roughly 1 °C per decade are likely to be detected;
  the trend test is somewhat liberal for strongly persistent series.
- **Linear methods.** Trends are monotonic or linear; partial correlations assume linear relations.
- **Not reviewed by a human scientist.** The science review is a self-audit by the AI system that wrote the code.
- **Live NASA retrieval by the backend was not exercised in the build environment**; the bundled files were fetched
  through a browser and verified by hash.
- Full list: `docs/KNOWN_LIMITATIONS.md`.

## 10. GitHub Repository URL

<https://github.com/Alishka14/nasa-space-app-2026>

Branch `feat/earth-senses-mvp`; Draft pull request into `main` — **TO DO (see the checklist at the top).**

---

## How the project answers the judging criteria

| Criterion | Where to look |
|---|---|
| **Impact** | A reusable habit-forming tool for students and the public; works for any point on Earth from 1981 |
| **Creativity** | Counterevidence, a wording guard and "what cannot be concluded" as product features; AI output treated as a hypothesis to be tested |
| **Validity** | 160 tests; cross-checks against independent libraries; all outside numbers reproduced; self-audit with open items stated |
| **Relevance** | Directly answers the challenge: what is changing, where, how fast, what changes together, and can we trust it |
| **Presentation** | One-click demonstration case; the −0.28 → +0.59 reversal tells the story in ten seconds |
