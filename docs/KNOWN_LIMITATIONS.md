# Known Limitations

What is not done, what was not run, and what the results cannot support. Nothing here is hidden elsewhere.

## Not done

| Item | State | What it needs |
|---|---|---|
| **A second, independent NASA source** | **NOT DONE** | The 2026 Project Submission Guide requires "at least one NASA data or resource" for Global Award eligibility; NASA POWER / MERRA-2 meets that. What is missing is a cross-check against a different product. Tried: (1) `IMERG_PRECTOT` through NASA POWER — the service accepted the parameter and returned its missing-value code for all 288 months at Pavlodar (file stored as evidence); (2) the Giovanni time-series service behind the Resources-tab Hydrology tool — access from the build environment was not permitted, **NOT RUN**. Next step for the team: download GPM IMERG monthly precipitation or GLDAS-2.1 for the Pavlodar point from Giovanni / GES DISC with an Earthdata login, store it with provenance, and compare. |
| **Push to `Alishka14/nasa-space-app-2026`, Draft PR** | **NOT DONE** | The build session's GitHub credential has no access to the repository (it does not appear in the session's repository list, the connector refuses it, and `git ls-remote` asks for a username). The branch `feat/earth-senses-mvp` exists locally with no common history with the remote; the remote's content was not seen. Commands for publishing from a team member's computer, without force-push and without touching `main`, are in `HANDOFF.md`; the Draft PR text is in `PR_BODY.md`. |
| **Repository must be public at submission** | **TEAM** | The Project Submission Guide requires the "Link to Final Project" to open without login or permission. The repository currently asks for credentials. |
| Live retrieval from NASA by the backend | **NOT RUN** | `PowerStore._fetch_live` is implemented and tested with a stubbed HTTP transport only (good answer, HTTP errors, network failure, truncated or mismatched body); the build sandbox had no route to `power.larc.nasa.gov`. The four bundled files were fetched through a browser and verified by SHA-256. The first live run should be watched. |
| Variables beyond `T2M`, `RH2M`, `PRECTOTCORR`, `QV2M` | **NOT VERIFIED** | Five more POWER parameters are selectable and marked as unverified: no real response for them was parsed in this build. `QV2M` is verified for Pavlodar 2001–2024 only; its 1981–2000 values are not bundled, so the longer-record check is skipped (with a warning) when it is selected. |
| Demo video (≤ 30 s) or slides (≤ 7), public demo link | **NOT DONE** | Script, slide outline, subtitles and shot list are in `DEMO_SCRIPT.md`; recording is the team's. |
| Human scientific review | **NOT DONE** | All checks so far were made by AI systems and automated tests. `SCIENCE_REVIEW.md` is a self-audit, not an independent validation. |
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
4. **Short records, low power.** With 24 annual values, only temperature trends above roughly 0.95 °C per decade would
   be likely to be detected. Non-significance here says little about whether change is occurring.
5. **Residual false positives under persistence.** On trend-free AR(1) noise with 24 points (3000 simulations), the
   primary trend rule rejects in about 3.7% of cases at φ = 0, 7.5% at φ = 0.3, 12% at φ = 0.6 and 14% at φ = 0.7
   (nominal 5%). The Hamed–Rao correction scans every lag up to n − 1, so one noisy high-lag autocorrelation can
   move its p-value slightly. The detrended annual
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
12. **Relative humidity is not an independent variable.** NASA POWER computes `RH2M` from MERRA-2 pressure,
    temperature and specific humidity. The temperature–humidity association (−0.32 between anomalies) is partly an
    identity. The derived-variable check quantifies this only approximately: it is linear and uses monthly means, and
    it reproduces 98% of the anomaly variance in summer but 19% in winter, for reasons that were not tested.
13. **The precipitation–humidity link is seasonal.** The all-year +0.59 is weighted towards months with large
    variance: with every calendar month weighted equally it is +0.37, and in winter (DJF) it is −0.06. It should be
    described as a spring-to-autumn association.
14. **Partial correlations are linear and descriptive.** "Held fixed" means regressed out linearly. A non-linear
    dependence on the control variable is only partly removed, and no causal ordering is implied.
15. **Replication is narrow.** "Replicated" marks individual numbers that two AI systems each obtained from a
    separately retrieved copy of the same NASA product. The comparison was not blind, and Gemini's trend method had to
    be inferred by trying seven variants. No record as a whole, and no interpretation, is above `OBSERVED`, and no
    human has reviewed them.

## Engineering limits

- Results are cached in memory per backend process; evidence ids can always be recomputed, but
  `GET /api/evidence/{id}` only knows investigations run since the process started.
- A requested period is served from bundled files when they cover it, including by joining files along time or
  across variables; otherwise the whole request is made live. Partial overlap is not merged with a live request.
- With four or more variables the investigation takes several seconds (2000 permutations per pair).
- The frontend bundle is a single 2.6 MB file; no code splitting.
- The map uses bundled Natural Earth outlines at 1:110 m, sufficient for choosing a point, not for navigation.
- Python 3.13 and the pinned library versions in `backend/requirements.txt` are the only tested environment.
