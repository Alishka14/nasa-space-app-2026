# NASA Space Apps Challenge 2026 — Submission Text

Draft text for the project page. Field names follow recent Space Apps submission forms; check them against the 2026
form before pasting. Items marked **TO DO** must be completed by the team.

---

**Challenge:** Be An Earth System Trend Detective!

**Project name:** EARTH SENSES — Interconnected Earth Intelligence

**Team:** **TO DO** (team name, members, local event)

## High-level summary

EARTH SENSES is a web tool that lets anyone pick a place on Earth, choose Earth-science variables and a period, and
find out what is changing, how fast, and whether the change is statistically significant. It goes one step further
than a trend calculator: it shows which variables change together, tests whether that link survives once the seasonal
cycle and trends are removed, checks whether a conclusion survives a different period, and lists what the data
cannot tell you. Every result is stored as an evidence record with the method, the uncertainty, the counterevidence
and the SHA-256 of the NASA file it came from. A built-in guard blocks causal or "proven" wording that statistics on
one record cannot support. The aim is to turn users into careful data detectives, not just chart readers.

## Links

- Project demo: **TO DO**
- Final project (repository): <https://github.com/Alishka14/nasa-space-app-2026> — **TO DO: branch not pushed yet**

## Detailed project description

**What it does.** The user opens a map, selects a location (a preset or any point), ticks variables, sets the years and
presses *Investigate*. The tool then shows:

- for each variable, the rate of change per year (Theil–Sen slope) with a 95% confidence interval, a significance test
  that accounts for autocorrelation, a false-discovery-corrected q-value, and a verdict: robust trend, fragile trend,
  or no significant trend detected;
- time series as monthly values, seasonal cycle, anomalies and annual means with the trend line, one panel per
  variable;
- a heatmap of the trend over every sub-period, so the user sees at once whether the answer depends on the years
  chosen;
- for each pair of variables, the correlation computed four ways (raw, seasonal cycles alone, deseasonalized,
  detrended), split by season, and scanned over lags of ±6 months with correction for multiple testing;
- a relationship graph in which an edge exists only if it was computed from data;
- *View Evidence* for every result: claim, evidence, counterevidence, alternatives not excluded, limitations, method,
  parameters, and the source NASA data with its request and hash;
- an evidence timeline showing how each interpretation was reached and revised;
- a comparison of two regions over the same years, including whether they are drifting apart;
- a downloadable report that ends with "what cannot be concluded from these data".

Plain-language definitions accompany every variable, and two bundled cases (Pavlodar and an Almaty grid cell) work
without an internet connection as demonstrations.

**How it works.** A Python backend (FastAPI, NumPy, SciPy, pandas) retrieves monthly data, validates it (annual
summary keys separated from months, declared fill values treated as missing, units read from the response, complete
calendar, correct location), stores the raw response unchanged with a provenance record, and runs the analyses:
Theil–Sen, Mann–Kendall with the Hamed–Rao correction, least squares with an AR(1) effective sample size, seasonal
Kendall, Benjamini–Hochberg, effective-sample-size correlation tests, a year-block permutation control, and
sensitivity analyses. A React + TypeScript interface with MapLibre and ECharts displays only what the backend
returns. 129 automated tests cover the data traps, cross-check the statistics against independent libraries, and run
synthetic controls with known answers.

**What we found in our demonstration case** (Pavlodar, Kazakhstan, 2001–2024, MERRA-2):

- The raw correlation between temperature and relative humidity is −0.95, but the seasonal cycles alone give −0.98;
  between monthly anomalies it is −0.32.
- Precipitation and humidity correlate at −0.28 in raw data and +0.59 once the seasonal cycle is removed.
- Temperature and precipitation anomalies correlate at +0.37 in winter and −0.32 in summer; the all-year value of
  −0.12 hides the reversal.
- Temperature shows no significant trend, and the tool explains why that is not evidence of "no warming": the 95%
  interval is −0.67 to +0.46 °C per decade.
- Relative humidity shows p = 0.035, which the tool classifies as fragile: q = 0.105 after correction, the result
  depends on single years, and it vanishes over 1981–2024.

**Benefits.** Students and members of the public get a trend tool that teaches the habits of a careful analyst:
remove the seasonal cycle, correct for multiple tests, try another period, and separate what was observed from what
is merely proposed. Researchers and journalists get results they can trace to a file hash.

**Tools and languages.** Python 3.13 (FastAPI, NumPy, SciPy, pandas, statsmodels, pytest), TypeScript, React, Vite,
MapLibre GL JS, Apache ECharts, Natural Earth outlines.

**What is not finished.** Data retrieval through a tool listed in the challenge's Resources tab; a public demo;
verification of variables beyond the three used; review by a human scientist. See `docs/KNOWN_LIMITATIONS.md`.

## NASA data

| Resource | How it is used |
|---|---|
| **NASA POWER** Monthly & Annual API v2.10.0, NASA Langley Research Center — <https://power.larc.nasa.gov/> | Source of all data analysed so far: monthly `T2M`, `RH2M`, `PRECTOTCORR` for a point, 1981 onward |
| **MERRA-2** (Modern-Era Retrospective analysis for Research and Applications, Version 2), NASA GMAO | The reanalysis behind those POWER parameters; named in the challenge text |
| **Hydrology Time Series / Giovanni** (GES DISC) — listed in the challenge Resources | **Not used yet.** Planned second source (GLDAS-2.1) for cross-checking. **TO DO before submission if the team wants to claim a Resources-tab source** |

Three responses are bundled in the repository byte-for-byte with their SHA-256 and a provenance record each.

## Space Agency Partner and other data

- Natural Earth (public domain) country outlines via the `world-atlas` package, for the basemap only.
- No Space Agency Partner data are used.

## Use of artificial intelligence

AI tools were used and are disclosed here:

- **Gemini** produced a preliminary exploratory analysis of the Pavlodar data. We treated it as a proposal and
  reproduced every number independently (`docs/GEMINI_REPRODUCTION.md`).
- **Claude** (Anthropic) wrote the application code, the tests, the independent reproduction and the documentation
  under the team's direction, and ran a separate verification pass.
- **No AI model takes part in the tool's calculations or in producing its findings.** All numbers and all sentences
  shown to the user come from deterministic code and fixed templates.
- No AI-generated images, video, audio or NASA branding are used.
- Team members are responsible for the submission and should review the science before it is submitted.
  **TO DO: confirm this review has taken place.**

## References

- NASA POWER Project, NASA Langley Research Center. <https://power.larc.nasa.gov/>
- Gelaro, R., et al. (2017). The Modern-Era Retrospective Analysis for Research and Applications, Version 2 (MERRA-2). *Journal of Climate* 30, 5419–5454.
- Mann, H. B. (1945). Nonparametric tests against trend. *Econometrica* 13, 245–259.
- Sen, P. K. (1968). Estimates of the regression coefficient based on Kendall's tau. *JASA* 63, 1379–1389.
- Hirsch, R. M., Slack, J. R., Smith, R. A. (1982). Techniques of trend analysis for monthly water quality data. *Water Resources Research* 18, 107–121.
- Hirsch, R. M., Slack, J. R. (1984). A nonparametric trend test for seasonal data with serial dependence. *Water Resources Research* 20, 727–732.
- Hamed, K. H., Rao, A. R. (1998). A modified Mann-Kendall trend test for autocorrelated data. *Journal of Hydrology* 204, 182–196.
- Santer, B. D., et al. (2000). Statistical significance of trends and trend differences in layer-average atmospheric temperature time series. *JGR* 105, 7337–7356.
- Bretherton, C. S., et al. (1999). The effective number of spatial degrees of freedom of a time-varying field. *Journal of Climate* 12, 1990–2009.
- Benjamini, Y., Hochberg, Y. (1995). Controlling the false discovery rate. *JRSS B* 57, 289–300.
- Software: NumPy, SciPy, pandas, statsmodels, FastAPI, React, Vite, MapLibre GL JS, Apache ECharts, pymannkendall (tests only), world-atlas / Natural Earth.
