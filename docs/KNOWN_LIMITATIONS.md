# Known Limitations

What is not done, what was not run, and what the results cannot support. Nothing here is hidden elsewhere.

## Not done

| Item | State | What it needs |
|---|---|---|
| **A NASA source from the challenge's Resources tab** | **NOT DONE** | The tab lists Giovanni, Hydrology Time Series, AppEEARS and NOAA Climate Data Online. NASA POWER is not listed. The Hydrology Time Series tool now delivers data through the Giovanni time-series service (`api.giovanni.earthdata.nasa.gov`), which serves GLDAS-2.1, MERRA-2 and IMERG point series. The build session could not read that host. Next step: retrieve GLDAS-2.1 `Tair_f_inst` and `Rainf_f_tavg` for the Pavlodar point, store them with provenance, add a `giovanni_client` beside `power_client`, and compare the two sources. |
| **Push to `Alishka14/nasa-space-app-2026`, pull request** | **NOT DONE** | The build session's GitHub credential had no access to the repository. The branch `feat/earth-senses-mvp` exists locally with no common history with the remote, so it must be rebased onto the remote default branch before a pull request can be opened. The remote's current content was not seen. |
| Live retrieval from NASA by the backend | **NOT RUN** | `PowerStore._fetch_live` is implemented and its validation path is tested, but the build sandbox had no route to `power.larc.nasa.gov`; the three bundled files were fetched through a browser and verified by SHA-256. First live run should be watched. |
| Variables beyond `T2M`, `RH2M`, `PRECTOTCORR` | **NOT VERIFIED** | Six more POWER parameters are selectable and marked as unverified: no real response for them was parsed in this build. |
| Demo video, public demo link | **NOT DONE** | |
| Human scientific review | **NOT DONE** | All checks so far were made by AI systems and automated tests. |
| Russian interface | **PARTIAL** | Labels are translated; findings are generated in English only. |
| Episodes persisted across runs | **NOT DONE** | Evidence Timeline is rebuilt per investigation. |
| Automated interface tests | **NOT DONE** | The interface was built, type-checked and inspected in a headless browser screen by screen; there is no automated UI test suite. |
| Licence for this repository | **NOT DECIDED** | Owner's decision. |

## Scientific limits

1. **Reanalysis, not observation.** MERRA-2 is a model constrained by observations. Changes in the assimilated
   observing system can produce steps that look like trends. No change-point or homogeneity test is applied.
2. **One grid cell.** About 0.5° × 0.625°, at the cell's mean elevation. For Pavlodar that elevation is 111 m; for the
   Almaty point it is 2478 m, far above the city, so that cell must not be read as "Almaty". Nothing is aggregated
   over an area.
3. **No ground truth.** Nothing was compared with station records. Agreement between Gemini and this engine shows
   that the arithmetic is right, not that MERRA-2 is.
4. **Short records, low power.** With 24 annual values, only temperature trends above roughly 0.9 °C per decade would
   be likely to be detected. Non-significance here says little about whether change is occurring.
5. **Residual false positives under strong persistence.** On trend-free AR(1) noise with φ = 0.7 and 24 points, the
   primary trend rule still rejects in about 11% of cases (nominal 5%); at φ = 0.3 about 6%. The detrended annual
   series used here have lag-1 autocorrelations between −0.12 and +0.08, where this is not a concern, but the rule would be
   too liberal for strongly persistent series.
6. **Monotonic and linear trends only.** Accelerations, reversals and step changes are not modelled; the sub-period
   heatmap is the only guard against them.
7. **Correlation of monthly anomalies.** Both variables of every pair come from the same model, which may couple them
   more tightly than nature does. A third factor can move both. No causal method is applied, and none is claimed.
8. **Lags.** Monthly resolution; neighbouring lags are not independent tests; persistence of one series spreads a
   same-month association to other lags. Lag results are timing statistics.
9. **Thresholds are conventions.** α = 0.05 and |r| ≥ 0.2 separate the status labels. Results near a threshold
   (for example temperature–precipitation, r = −0.12, upper confidence limit −0.004) should be read as borderline.
10. **Relative humidity near saturation.** January and February values sit at about 94–97% with little variance,
    which limits any winter correlation involving humidity whatever the underlying physics.
11. **The guard is pattern matching.** It blocks listed overclaims in English and Russian. A determined writer can
    phrase a causal claim it does not recognise; passing the guard is not validation.
12. **Replication is narrow.** "Replicated" marks individual numbers that two AI systems obtained independently from
    NASA data. No record as a whole, and no interpretation, is above `OBSERVED`, and no human has reviewed them.

## Engineering limits

- Results are cached in memory per backend process; evidence ids can always be recomputed, but
  `GET /api/evidence/{id}` only knows investigations run since the process started.
- A requested period is served from bundled files when they cover it, including by joining two files; otherwise the
  whole period is requested live. Partial overlap is not merged with a live request.
- The frontend bundle is a single 2.6 MB file; no code splitting.
- The map uses bundled Natural Earth outlines at 1:110 m, sufficient for choosing a point, not for navigation.
- Python 3.13 and the pinned library versions in `backend/requirements.txt` are the only tested environment.
