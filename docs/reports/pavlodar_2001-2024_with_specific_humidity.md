# Investigation Report — Pavlodar, Kazakhstan

*EARTH SENSES earth-senses/0.1.0 · generated 2026-11-14T09:48:22+00:00*

- **Location:** 52.29, 76.97 (grid-cell mean elevation 110.97 m)
- **Period:** 2001–2024 · climatological baseline 2001–2024
- **Variables:** Air temperature (2 m) [°C], Relative humidity (2 m) [%], Precipitation (bias-corrected) [mm/day], Specific humidity (2 m) [g/kg]
- **Data hash:** `8bc961f1c7629d528fd3d607e81bf3018939e29e7bba67bddc8db4340146a711` (cache)

## 1. Data provenance

- **Source:** NASA POWER (Prediction Of Worldwide Energy Resources) Monthly & Annual API, NASA Langley Research Center; meteorological parameters from MERRA-2 (NASA GMAO)
  - Request: `https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=T2M,PRECTOTCORR,RH2M&community=AG&longitude=76.97&latitude=52.29&start=2001&end=2024&format=JSON`
  - Retrieved: 2026-11-14T04:58:11.069Z — HTTPS GET issued from a Chrome browser on the team's computer (the build sandbox had no route to power.larc.nasa.gov); SHA-256 computed in the browser on the response body and matched after the body was stored in the repository (byte-identical)
  - Product: POWER Monthly and Annual API v2.10.0, sources MERRA2, POWER
  - Resolution: MERRA-2 native grid, 0.5 deg latitude x 0.625 deg longitude; a point query returns the enclosing grid cell, at the grid cell's mean elevation (per POWER documentation); monthly means (keys YYYY01..YYYY12) plus the API's annual mean (YYYY13)
  - Coverage: 2001-01 to 2024-12 (288 months); missing values: 0 (fill -999.0)
  - SHA-256: `8a65f9e56b005f77eec3783a09903ad2842031590cc0c8084441d92b19f87de6` · validation: VALIDATED
- **Source:** NASA POWER (Prediction Of Worldwide Energy Resources) Monthly & Annual API, NASA Langley Research Center; meteorological parameters from MERRA-2 (NASA GMAO)
  - Request: `https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=QV2M,IMERG_PRECTOT&community=AG&longitude=76.97&latitude=52.29&start=2001&end=2024&format=JSON`
  - Retrieved: 2026-11-14T09:23:59.982Z — HTTPS GET issued from a Chrome browser on the team's computer (the build sandbox had no route to power.larc.nasa.gov); SHA-256 computed in the browser on the response body and matched after the body was stored in the repository (byte-identical)
  - Product: POWER Monthly and Annual API v2.10.0, sources MERRA2
  - Resolution: MERRA-2 native grid, 0.5 deg latitude x 0.625 deg longitude; a point query returns the enclosing grid cell, at the grid cell's mean elevation (per POWER documentation); monthly means (keys YYYY01..YYYY12) plus the API's annual mean (YYYY13)
  - Coverage: 2001-01 to 2024-12 (288 months); missing values: 0 (fill -999.0); also in this file but not used: IMERG_PRECTOT (288 missing)
  - SHA-256: `978b737e26d8e1c4b2b0de4e605b3952934da4fcacb2bc4ac3646055459c768c` · validation: VALIDATED_WITH_MISSING_DATA

Kind of data: model reanalysis (MERRA-2), not a direct satellite or station measurement.

**Warnings**

- variables assembled from 2 verified raw files
- Longer-record check (1981-2024) not available: this request is not in the verified cache and network access is disabled; no data will be invented

## 2. What is changing, and how fast

| Variable | Slope per year (95% CI) | p (autocorrelation-adjusted) | q (FDR) | Verdict |
|---|---|---:|---:|---|
| Air temperature (2 m) | -0.021 (-0.067 to +0.046) °C/year | 0.578 | 0.578 | NO_SIGNIFICANT_TREND_DETECTED |
| Relative humidity (2 m) | +0.164 (+0.007 to +0.293) percentage points/year | 0.035 | 0.112 | FRAGILE_TREND |
| Precipitation (bias-corrected) | +0.005 (-0.004 to +0.015) mm/day per year | 0.264 | 0.352 | NO_SIGNIFICANT_TREND_DETECTED |
| Specific humidity (2 m) | +0.008 (-0.000 to +0.021) g/kg per year | 0.056 | 0.112 | NO_SIGNIFICANT_TREND_DETECTED |

**Air temperature (2 m).** Air temperature (2 m): no statistically significant monotonic trend was detected over 2001-2024 (Theil-Sen slope -0.021 °C/year (95% CI -0.067 to +0.046), autocorrelation-adjusted p = 0.578, q = 0.578). A record of this length and variability would only be likely to show trends larger than about 0.095 °C/year (80% power), so smaller real changes cannot be ruled out.

**Relative humidity (2 m).** Relative humidity (2 m) over 2001-2024: Theil-Sen slope +0.164 percentage points/year (95% CI +0.007 to +0.293), autocorrelation-adjusted p = 0.035, q = 0.112. Some tests indicate a trend, but the result is fragile: not significant after false-discovery correction (q = 0.112); significance depends on single years (2002, 2008, 2017, 2018, 2024).

**Precipitation (bias-corrected).** Precipitation (bias-corrected): no statistically significant monotonic trend was detected over 2001-2024 (Theil-Sen slope +0.005 mm/day per year (95% CI -0.004 to +0.015), autocorrelation-adjusted p = 0.264, q = 0.352). A record of this length and variability would only be likely to show trends larger than about 0.014 mm/day per year (80% power), so smaller real changes cannot be ruled out.

Annual accumulation: mean 325 mm/year; Theil-Sen slope +1.75 mm/year per year (95% CI -1.48 to +5.51, p = 0.286). monthly mean rate (mm/day) x days in each month, summed per year.

**Specific humidity (2 m).** Specific humidity (2 m): no statistically significant monotonic trend was detected over 2001-2024 (Theil-Sen slope +0.008 g/kg per year (95% CI -0.000 to +0.021), autocorrelation-adjusted p = 0.056, q = 0.112). A record of this length and variability would only be likely to show trends larger than about 0.021 g/kg per year (80% power), so smaller real changes cannot be ruled out.

## 3. What varies together

| Pair | raw r | seasonal cycle only | deseasonalized r | detrended r (95% CI) | Status | Lag scan |
|---|---:|---:|---:|---|---|---|
| T2M ↔ PRECTOTCORR | +0.44 | +0.86 | -0.13 | -0.12 (-0.23 to -0.00) | WEAK | INCONCLUSIVE |
| T2M ↔ RH2M | -0.95 | -0.98 | -0.32 | -0.32 (-0.42 to -0.20) | SUPPORTED | LAGGED_ASSOCIATION_DETECTED |
| T2M ↔ QV2M | +0.95 | +0.97 | +0.53 | +0.55 (+0.46 to +0.63) | SUPPORTED | NO_LAGGED_ASSOCIATION_DETECTED |
| PRECTOTCORR ↔ RH2M | -0.28 | -0.78 | +0.59 | +0.59 (+0.51 to +0.66) | SUPPORTED | LAGGED_ASSOCIATION_DETECTED |
| PRECTOTCORR ↔ QV2M | +0.55 | +0.94 | +0.31 | +0.30 (+0.18 to +0.40) | SUPPORTED | LAGGED_ASSOCIATION_DETECTED |
| RH2M ↔ QV2M | -0.84 | -0.91 | +0.39 | +0.36 (+0.24 to +0.46) | SUPPORTED | LAGGED_ASSOCIATION_DETECTED |

**T2M ↔ PRECTOTCORR.** Monthly anomalies of Air temperature (2 m) and Precipitation (bias-corrected) vary in opposite directions over 2001-2024: detrended r = -0.12 (95% CI -0.23 to -0.004, effective n = 283). Raw r = +0.44; the two seasonal cycles alone give r = +0.86. The association is statistically detectable but small.

Lag scan of detrended anomalies, Air temperature (2 m) against Precipitation (bias-corrected), lags -6 to +6 months (13 tests, Benjamini-Hochberg): the largest |r| is at lag -6 (r = -0.14). Some non-zero lags pass an uncorrected test (-6, +6) but none stays significant after correcting for the number of lags tried. Positive lags pair Air temperature (2 m) with later Precipitation (bias-corrected). A lead or lag is a timing statistic only.

**T2M ↔ RH2M.** Monthly anomalies of Air temperature (2 m) and Relative humidity (2 m) vary in opposite directions over 2001-2024: detrended r = -0.32 (95% CI -0.42 to -0.20, effective n = 252). Raw r = -0.95; the two seasonal cycles alone give r = -0.98. The association holds in both halves of the record and against a year-shuffled control.

Lag scan of detrended anomalies, Air temperature (2 m) against Relative humidity (2 m), lags -6 to +6 months (13 tests, Benjamini-Hochberg): the largest |r| is at lag +0 (r = -0.32). Non-zero lags that stay significant after correction: +1 (r = -0.18). Positive lags pair Air temperature (2 m) with later Relative humidity (2 m). A lead or lag is a timing statistic only.

**T2M ↔ QV2M.** Monthly anomalies of Air temperature (2 m) and Specific humidity (2 m) vary in the same direction over 2001-2024: detrended r = +0.55 (95% CI +0.46 to +0.63, effective n = 265). Raw r = +0.95; the two seasonal cycles alone give r = +0.97. The association holds in both halves of the record and against a year-shuffled control.

Lag scan of detrended anomalies, Air temperature (2 m) against Specific humidity (2 m), lags -6 to +6 months (13 tests, Benjamini-Hochberg): the largest |r| is at lag +0 (r = +0.55). No non-zero lag is significant, with or without correction. Positive lags pair Air temperature (2 m) with later Specific humidity (2 m). A lead or lag is a timing statistic only.

**PRECTOTCORR ↔ RH2M.** Monthly anomalies of Precipitation (bias-corrected) and Relative humidity (2 m) vary in the same direction over 2001-2024: detrended r = +0.59 (95% CI +0.51 to +0.66, effective n = 278). Raw r = -0.28; the two seasonal cycles alone give r = -0.78. The association holds in both halves of the record and against a year-shuffled control.

Lag scan of detrended anomalies, Precipitation (bias-corrected) against Relative humidity (2 m), lags -6 to +6 months (13 tests, Benjamini-Hochberg): the largest |r| is at lag +0 (r = +0.59). Non-zero lags that stay significant after correction: +1 (r = +0.33), +2 (r = +0.16), +4 (r = +0.19). Positive lags pair Precipitation (bias-corrected) with later Relative humidity (2 m). A lead or lag is a timing statistic only.

**PRECTOTCORR ↔ QV2M.** Monthly anomalies of Precipitation (bias-corrected) and Specific humidity (2 m) vary in the same direction over 2001-2024: detrended r = +0.30 (95% CI +0.18 to +0.40, effective n = 281). Raw r = +0.55; the two seasonal cycles alone give r = +0.94. The association holds in both halves of the record and against a year-shuffled control.

Lag scan of detrended anomalies, Precipitation (bias-corrected) against Specific humidity (2 m), lags -6 to +6 months (13 tests, Benjamini-Hochberg): the largest |r| is at lag +0 (r = +0.30). Non-zero lags that stay significant after correction: +1 (r = +0.20), +2 (r = +0.20). Positive lags pair Precipitation (bias-corrected) with later Specific humidity (2 m). A lead or lag is a timing statistic only.

**RH2M ↔ QV2M.** Monthly anomalies of Relative humidity (2 m) and Specific humidity (2 m) vary in the same direction over 2001-2024: detrended r = +0.36 (95% CI +0.24 to +0.46, effective n = 242). Raw r = -0.84; the two seasonal cycles alone give r = -0.91. The association holds in both halves of the record and against a year-shuffled control.

Lag scan of detrended anomalies, Relative humidity (2 m) against Specific humidity (2 m), lags -6 to +6 months (13 tests, Benjamini-Hochberg): the largest |r| is at lag +0 (r = +0.36). Non-zero lags that stay significant after correction: +1 (r = +0.23), +2 (r = +0.22). Positive lags pair Relative humidity (2 m) with later Specific humidity (2 m). A lead or lag is a timing statistic only.

## 4. Evidence and counterevidence

### `EV-ae0d4001b558` · OBSERVED · CHECKS_PASSED

Input data checks passed: 288 monthly values per variable for 2001-2024, 0 missing; annual-summary keys (YYYY13) kept apart from months; units taken from the response; values are cache-sourced from 2 raw file(s) whose SHA-256 matches the provenance record.

Evidence:
- calendar complete and identical for all variables: passed.
- YYYY13 annual summaries separated from the 12 calendar months: passed.
- fill value converted to NaN: passed.
- units present in response metadata: passed.
- response geometry matches the request: passed.
- our day-weighted annual means agree with the API's own annual values: passed.

### `EV-d783cf42d80e` · OBSERVED · NO_SIGNIFICANT_TREND_DETECTED

Air temperature (2 m): no statistically significant monotonic trend was detected over 2001-2024 (Theil-Sen slope -0.021 °C/year (95% CI -0.067 to +0.046), autocorrelation-adjusted p = 0.578, q = 0.578). A record of this length and variability would only be likely to show trends larger than about 0.095 °C/year (80% power), so smaller real changes cannot be ruled out.

Evidence:
- Theil-Sen slope -0.021 °C/year (95% CI -0.067 to +0.046) on 24 annual means.
- Classic Mann-Kendall p = 0.413; Hamed-Rao modified p = 0.413; least-squares slope -0.018 with AR(1)-adjusted p = 0.578. The reported p is the larger of the last two.
- Seasonal Kendall test on 288 monthly values: slope -0.005 °C/year, p = 0.725 allowing for dependence between months (p = 0.688 if months are treated as independent).
- Benjamini-Hochberg q = 0.578 across the 4 variables tested together.

Counterevidence:
- Across 55 sub-periods of at least 15 years the slope is positive in 19 and negative in 36; 3 are individually significant.

Alternatives not excluded:
- A step change in the observations assimilated by the reanalysis could appear as a trend.
- Multi-decadal variability can produce a monotonic change inside a short window.

Independent reports of the same quantity:
- trend.T2M.sen_slope_api_annual: reported -0.021, ours -0.0210 (agrees) — Gemini preliminary analysis of NASA POWER for Pavlodar 2001-2024, as relayed in the team brief of 2026-11-14
- trend.T2M.mk_p_api_annual_no_tie_correction: reported 0.427, ours 0.4273 (agrees) — Gemini preliminary analysis of NASA POWER for Pavlodar 2001-2024, as relayed in the team brief of 2026-11-14

### `EV-48a3e7a9a48e` · OBSERVED · FRAGILE_TREND

Relative humidity (2 m) over 2001-2024: Theil-Sen slope +0.164 percentage points/year (95% CI +0.007 to +0.293), autocorrelation-adjusted p = 0.035, q = 0.112. Some tests indicate a trend, but the result is fragile: not significant after false-discovery correction (q = 0.112); significance depends on single years (2002, 2008, 2017, 2018, 2024).

Evidence:
- Theil-Sen slope +0.164 percentage points/year (95% CI +0.007 to +0.293) on 24 annual means.
- Classic Mann-Kendall p = 0.035; Hamed-Rao modified p = 0.035; least-squares slope +0.183 with AR(1)-adjusted p = 0.010. The reported p is the larger of the last two.
- Seasonal Kendall test on 288 monthly values: slope +0.099 percentage points/year, p = 0.016 allowing for dependence between months (p = < 0.001 if months are treated as independent).
- Benjamini-Hochberg q = 0.112 across the 4 variables tested together.

Counterevidence:
- Across 55 sub-periods of at least 15 years the slope is positive in 55 and negative in 0; 12 are individually significant.
- Leaving out any one of the years 2002, 2008, 2017, 2018, 2024 changes whether the classic test is significant (p between 0.051 and 0.102 for those years; 0.035 with all years).

Alternatives not excluded:
- A step change in the observations assimilated by the reanalysis could appear as a trend.
- Multi-decadal variability can produce a monotonic change inside a short window.

Independent reports of the same quantity:
- trend.RH2M.sen_slope_api_annual: reported 0.16, ours 0.1638 (agrees) — Gemini preliminary analysis of NASA POWER for Pavlodar 2001-2024, as relayed in the team brief of 2026-11-14
- trend.RH2M.mk_p_api_annual_no_tie_correction: reported 0.035, ours 0.0350 (agrees) — Gemini preliminary analysis of NASA POWER for Pavlodar 2001-2024, as relayed in the team brief of 2026-11-14
- trend.RH2M.q: reported 0.105, ours 0.1123 (DISAGREES) — Gemini preliminary analysis of NASA POWER for Pavlodar 2001-2024, as relayed in the team brief of 2026-11-14

### `EV-1519275febc4` · OBSERVED · NO_SIGNIFICANT_TREND_DETECTED

Precipitation (bias-corrected): no statistically significant monotonic trend was detected over 2001-2024 (Theil-Sen slope +0.005 mm/day per year (95% CI -0.004 to +0.015), autocorrelation-adjusted p = 0.264, q = 0.352). A record of this length and variability would only be likely to show trends larger than about 0.014 mm/day per year (80% power), so smaller real changes cannot be ruled out.

Evidence:
- Theil-Sen slope +0.005 mm/day per year (95% CI -0.004 to +0.015) on 24 annual means.
- Classic Mann-Kendall p = 0.264; Hamed-Rao modified p = 0.264; least-squares slope +0.007 with AR(1)-adjusted p = 0.147. The reported p is the larger of the last two.
- Seasonal Kendall test on 288 monthly values: slope +0.005 mm/day per year, p = 0.096 allowing for dependence between months (p = 0.069 if months are treated as independent).
- Benjamini-Hochberg q = 0.352 across the 4 variables tested together.

Counterevidence:
- Across 55 sub-periods of at least 15 years the slope is positive in 55 and negative in 0; 2 are individually significant.

Alternatives not excluded:
- A step change in the observations assimilated by the reanalysis could appear as a trend.
- Multi-decadal variability can produce a monotonic change inside a short window.

Independent reports of the same quantity:
- trend.PRECTOTCORR.sen_slope_api_annual: reported 0.005, ours 0.0050 (agrees) — Gemini preliminary analysis of NASA POWER for Pavlodar 2001-2024, as relayed in the team brief of 2026-11-14
- trend.PRECTOTCORR.mk_p_api_annual_no_tie_correction: reported 0.275, ours 0.2751 (agrees) — Gemini preliminary analysis of NASA POWER for Pavlodar 2001-2024, as relayed in the team brief of 2026-11-14

### `EV-7ea7a72be16c` · OBSERVED · NO_SIGNIFICANT_TREND_DETECTED

Specific humidity (2 m): no statistically significant monotonic trend was detected over 2001-2024 (Theil-Sen slope +0.008 g/kg per year (95% CI -0.000 to +0.021), autocorrelation-adjusted p = 0.056, q = 0.112). A record of this length and variability would only be likely to show trends larger than about 0.021 g/kg per year (80% power), so smaller real changes cannot be ruled out.

Evidence:
- Theil-Sen slope +0.008 g/kg per year (95% CI -0.000 to +0.021) on 24 annual means.
- Classic Mann-Kendall p = 0.056; Hamed-Rao modified p = 0.056; least-squares slope +0.014 with AR(1)-adjusted p = 0.053. The reported p is the larger of the last two.
- Seasonal Kendall test on 288 monthly values: slope +0.009 g/kg per year, p = 0.176 allowing for dependence between months (p = 0.068 if months are treated as independent).
- Benjamini-Hochberg q = 0.112 across the 4 variables tested together.

Counterevidence:
- Across 55 sub-periods of at least 15 years the slope is positive in 54 and negative in 1; 3 are individually significant.
- Leaving out any one of the years 2001, 2005, 2007, 2011, 2012, 2014, 2021, 2022 changes whether the classic test is significant (p between 0.039 and 0.045 for those years; 0.056 with all years).

Alternatives not excluded:
- A step change in the observations assimilated by the reanalysis could appear as a trend.
- Multi-decadal variability can produce a monotonic change inside a short window.

### `EV-0d7dbf390eec` · OBSERVED · WEAK

Monthly anomalies of Air temperature (2 m) and Precipitation (bias-corrected) vary in opposite directions over 2001-2024: detrended r = -0.12 (95% CI -0.23 to -0.004, effective n = 283). Raw r = +0.44; the two seasonal cycles alone give r = +0.86. The association is statistically detectable but small.

Evidence:
- Raw monthly series: r = +0.439 (n = 288).
- Seasonal cycles alone (climatology repeated each year): r = +0.860.
- Deseasonalized anomalies (baseline 2001-2024): r = -0.125, naive p = 0.034, autocorrelation-adjusted p = 0.036 (effective n = 282); Spearman rho = -0.158.
- Detrended anomalies: r = -0.121, adjusted p = 0.042.
- Year-shuffled control (2000 permutations): p = 0.011; 95% of shuffled |r| are below 0.097.
- With every calendar month weighted equally (anomalies divided by that month's standard deviation): r = -0.185.
- Partial correlation with Relative humidity (2 m) held fixed statistically: r = +0.085 (95% CI -0.03 to +0.20; r = -0.121 without).
- Partial correlation with Specific humidity (2 m) held fixed statistically: r = -0.354 (95% CI -0.45 to -0.25; r = -0.121 without).
- Partial correlation with Relative humidity (2 m) and Specific humidity (2 m) held fixed statistically: r = +0.003 (95% CI -0.11 to +0.12; r = -0.121 without).

Counterevidence:
- Halves of the record: r = -0.06 (2001-2012) and r = -0.18 (2013-2024); 10-year windows range from -0.21 to -0.06.
- The sign differs between seasons (DJF +0.37, MAM -0.34, JJA -0.32, SON -0.35), so a single all-year statement hides opposite behaviour.

Alternatives not excluded:
- A third factor that varies from month to month (for example the passage of air masses) could move both variables together.
- Both variables come from one model, which may link them more tightly than nature does.

Independent reports of the same quantity:
- corr.T2M-PRECTOTCORR.raw: reported 0.439, ours 0.4393 (agrees) — Gemini preliminary analysis of NASA POWER for Pavlodar 2001-2024, as relayed in the team brief of 2026-11-14
- corr.T2M-PRECTOTCORR.deseasonalized: reported -0.125, ours -0.1250 (agrees) — Gemini preliminary analysis of NASA POWER for Pavlodar 2001-2024, as relayed in the team brief of 2026-11-14

### `EV-6442a74c137c` · OBSERVED · INCONCLUSIVE

Lag scan of detrended anomalies, Air temperature (2 m) against Precipitation (bias-corrected), lags -6 to +6 months (13 tests, Benjamini-Hochberg): the largest |r| is at lag -6 (r = -0.14). Some non-zero lags pass an uncorrected test (-6, +6) but none stays significant after correcting for the number of lags tried. Positive lags pair Air temperature (2 m) with later Precipitation (bias-corrected). A lead or lag is a timing statistic only.

Evidence:
- Lag -2: r = +0.066, q = 0.585.
- Lag -1: r = -0.102, q = 0.280.
- Lag +0: r = -0.121, q = 0.183.
- Lag +1: r = +0.019, q = 0.953.
- Lag +2: r = +0.006, q = 0.953.

Alternatives not excluded:
- Persistence of one variable alone can spread a same-month association onto neighbouring lags.

### `EV-0b4b9d3a2904` · OBSERVED · SUPPORTED

Monthly anomalies of Air temperature (2 m) and Relative humidity (2 m) vary in opposite directions over 2001-2024: detrended r = -0.32 (95% CI -0.42 to -0.20, effective n = 252). Raw r = -0.95; the two seasonal cycles alone give r = -0.98. The association holds in both halves of the record and against a year-shuffled control.

Evidence:
- Raw monthly series: r = -0.945 (n = 288).
- Seasonal cycles alone (climatology repeated each year): r = -0.976.
- Deseasonalized anomalies (baseline 2001-2024): r = -0.316, naive p = < 0.001, autocorrelation-adjusted p = < 0.001 (effective n = 248); Spearman rho = -0.353.
- Detrended anomalies: r = -0.316, adjusted p = < 0.001.
- Year-shuffled control (2000 permutations): p = < 0.001; 95% of shuffled |r| are below 0.097.
- With every calendar month weighted equally (anomalies divided by that month's standard deviation): r = -0.415.
- Partial correlation with Precipitation (bias-corrected) held fixed statistically: r = -0.305 (95% CI -0.41 to -0.19; r = -0.316 without).
- Partial correlation with Specific humidity (2 m) held fixed statistically: r = -0.657 (95% CI -0.72 to -0.58; r = -0.316 without).
- Partial correlation with Precipitation (bias-corrected) and Specific humidity (2 m) held fixed statistically: r = -0.591 (95% CI -0.66 to -0.51; r = -0.316 without).

Counterevidence:
- Relative humidity (2 m) is computed from Air temperature (2 m) (and from Specific humidity (2 m)), so part of this association is built into the definition and is not an independent finding.
- Halves of the record: r = -0.31 (2001-2012) and r = -0.33 (2013-2024); 10-year windows range from -0.40 to -0.27.
- By season: DJF -0.16, MAM -0.58, JJA -0.48, SON -0.35.

Alternatives not excluded:
- A third factor that varies from month to month (for example the passage of air masses) could move both variables together.
- Both variables come from one model, which may link them more tightly than nature does.

Independent reports of the same quantity:
- corr.T2M-RH2M.raw: reported -0.945, ours -0.9451 (agrees) — Gemini preliminary analysis of NASA POWER for Pavlodar 2001-2024, as relayed in the team brief of 2026-11-14
- corr.T2M-RH2M.deseasonalized: reported -0.316, ours -0.3158 (agrees) — Gemini preliminary analysis of NASA POWER for Pavlodar 2001-2024, as relayed in the team brief of 2026-11-14

### `EV-ff59105da47f` · OBSERVED · LAGGED_ASSOCIATION_DETECTED

Lag scan of detrended anomalies, Air temperature (2 m) against Relative humidity (2 m), lags -6 to +6 months (13 tests, Benjamini-Hochberg): the largest |r| is at lag +0 (r = -0.32). Non-zero lags that stay significant after correction: +1 (r = -0.18). Positive lags pair Air temperature (2 m) with later Relative humidity (2 m). A lead or lag is a timing statistic only.

Evidence:
- Lag -2: r = +0.061, q = 0.441.
- Lag -1: r = -0.070, q = 0.432.
- Lag +0: r = -0.316, q = < 0.001.
- Lag +1: r = -0.178, q = 0.030.
- Lag +2: r = -0.032, q = 0.669.

Alternatives not excluded:
- Persistence of one variable alone can spread a same-month association onto neighbouring lags.

Independent reports of the same quantity:
- lag.T2M-RH2M.deseasonalized.+0: reported -0.316, ours -0.3158 (agrees) — Gemini preliminary analysis of NASA POWER for Pavlodar 2001-2024, as relayed in the team brief of 2026-11-14
- lag.T2M-RH2M.deseasonalized.+1: reported -0.185, ours -0.1851 (agrees) — Gemini preliminary analysis of NASA POWER for Pavlodar 2001-2024, as relayed in the team brief of 2026-11-14
- lag.T2M-RH2M.deseasonalized.+2: reported -0.04, ours -0.0447 (agrees) — Gemini preliminary analysis of NASA POWER for Pavlodar 2001-2024, as relayed in the team brief of 2026-11-14

### `EV-15e865232710` · OBSERVED · SUPPORTED

Monthly anomalies of Air temperature (2 m) and Specific humidity (2 m) vary in the same direction over 2001-2024: detrended r = +0.55 (95% CI +0.46 to +0.63, effective n = 265). Raw r = +0.95; the two seasonal cycles alone give r = +0.97. The association holds in both halves of the record and against a year-shuffled control.

Evidence:
- Raw monthly series: r = +0.950 (n = 288).
- Seasonal cycles alone (climatology repeated each year): r = +0.967.
- Deseasonalized anomalies (baseline 2001-2024): r = +0.531, naive p = < 0.001, autocorrelation-adjusted p = < 0.001 (effective n = 262); Spearman rho = +0.658.
- Detrended anomalies: r = +0.549, adjusted p = < 0.001.
- Year-shuffled control (2000 permutations): p = < 0.001; 95% of shuffled |r| are below 0.111.
- With every calendar month weighted equally (anomalies divided by that month's standard deviation): r = +0.674.
- Partial correlation with Precipitation (bias-corrected) held fixed statistically: r = +0.617 (95% CI +0.54 to +0.69; r = +0.549 without).
- Partial correlation with Relative humidity (2 m) held fixed statistically: r = +0.747 (95% CI +0.69 to +0.80; r = +0.549 without).
- Partial correlation with Precipitation (bias-corrected) and Relative humidity (2 m) held fixed statistically: r = +0.745 (95% CI +0.69 to +0.79; r = +0.549 without).

Counterevidence:
- Halves of the record: r = +0.63 (2001-2012) and r = +0.48 (2013-2024); 10-year windows range from +0.48 to +0.64.
- By season: DJF +0.92, MAM +0.75, JJA +0.35, SON +0.71.

Alternatives not excluded:
- A third factor that varies from month to month (for example the passage of air masses) could move both variables together.
- Both variables come from one model, which may link them more tightly than nature does.

### `EV-d1ba081619e9` · OBSERVED · NO_LAGGED_ASSOCIATION_DETECTED

Lag scan of detrended anomalies, Air temperature (2 m) against Specific humidity (2 m), lags -6 to +6 months (13 tests, Benjamini-Hochberg): the largest |r| is at lag +0 (r = +0.55). No non-zero lag is significant, with or without correction. Positive lags pair Air temperature (2 m) with later Specific humidity (2 m). A lead or lag is a timing statistic only.

Evidence:
- Lag -2: r = +0.030, q = 0.874.
- Lag -1: r = +0.068, q = 0.874.
- Lag +0: r = +0.549, q = < 0.001.
- Lag +1: r = +0.029, q = 0.874.
- Lag +2: r = +0.014, q = 0.885.

Alternatives not excluded:
- Persistence of one variable alone can spread a same-month association onto neighbouring lags.

### `EV-4a6e00ea5ffe` · OBSERVED · SUPPORTED

Monthly anomalies of Precipitation (bias-corrected) and Relative humidity (2 m) vary in the same direction over 2001-2024: detrended r = +0.59 (95% CI +0.51 to +0.66, effective n = 278). Raw r = -0.28; the two seasonal cycles alone give r = -0.78. The association holds in both halves of the record and against a year-shuffled control.

Evidence:
- Raw monthly series: r = -0.285 (n = 288).
- Seasonal cycles alone (climatology repeated each year): r = -0.775.
- Deseasonalized anomalies (baseline 2001-2024): r = +0.593, naive p = < 0.001, autocorrelation-adjusted p = < 0.001 (effective n = 274); Spearman rho = +0.534.
- Detrended anomalies: r = +0.590, adjusted p = < 0.001.
- Year-shuffled control (2000 permutations): p = < 0.001; 95% of shuffled |r| are below 0.152.
- With every calendar month weighted equally (anomalies divided by that month's standard deviation): r = +0.367.
- Partial correlation with Air temperature (2 m) held fixed statistically: r = +0.586 (95% CI +0.50 to +0.66; r = +0.590 without).
- Partial correlation with Specific humidity (2 m) held fixed statistically: r = +0.543 (95% CI +0.46 to +0.62; r = +0.590 without).
- Partial correlation with Air temperature (2 m) and Specific humidity (2 m) held fixed statistically: r = +0.440 (95% CI +0.34 to +0.53; r = +0.590 without).

Counterevidence:
- With every calendar month weighted equally the value is +0.37 instead of +0.59: the all-year figure is weighted towards the months with the largest variance.
- Halves of the record: r = +0.52 (2001-2012) and r = +0.64 (2013-2024); 10-year windows range from +0.49 to +0.65.
- The sign differs between seasons (DJF -0.06, MAM +0.54, JJA +0.70, SON +0.64), so a single all-year statement hides opposite behaviour.

Alternatives not excluded:
- A third factor that varies from month to month (for example the passage of air masses) could move both variables together.
- Both variables come from one model, which may link them more tightly than nature does.

Independent reports of the same quantity:
- corr.PRECTOTCORR-RH2M.raw: reported -0.285, ours -0.2850 (agrees) — Gemini preliminary analysis of NASA POWER for Pavlodar 2001-2024, as relayed in the team brief of 2026-11-14
- corr.PRECTOTCORR-RH2M.deseasonalized: reported 0.593, ours 0.5935 (agrees) — Gemini preliminary analysis of NASA POWER for Pavlodar 2001-2024, as relayed in the team brief of 2026-11-14

### `EV-c1fffa61e31b` · OBSERVED · LAGGED_ASSOCIATION_DETECTED

Lag scan of detrended anomalies, Precipitation (bias-corrected) against Relative humidity (2 m), lags -6 to +6 months (13 tests, Benjamini-Hochberg): the largest |r| is at lag +0 (r = +0.59). Non-zero lags that stay significant after correction: +1 (r = +0.33), +2 (r = +0.16), +4 (r = +0.19). Positive lags pair Precipitation (bias-corrected) with later Relative humidity (2 m). A lead or lag is a timing statistic only.

Evidence:
- Lag -2: r = +0.076, q = 0.305.
- Lag -1: r = +0.075, q = 0.305.
- Lag +0: r = +0.590, q = < 0.001.
- Lag +1: r = +0.334, q = < 0.001.
- Lag +2: r = +0.160, q = 0.025.

Alternatives not excluded:
- Persistence of one variable alone can spread a same-month association onto neighbouring lags.

### `EV-ea0465ee11ea` · OBSERVED · SUPPORTED

Monthly anomalies of Precipitation (bias-corrected) and Specific humidity (2 m) vary in the same direction over 2001-2024: detrended r = +0.30 (95% CI +0.18 to +0.40, effective n = 281). Raw r = +0.55; the two seasonal cycles alone give r = +0.94. The association holds in both halves of the record and against a year-shuffled control.

Evidence:
- Raw monthly series: r = +0.551 (n = 288).
- Seasonal cycles alone (climatology repeated each year): r = +0.936.
- Deseasonalized anomalies (baseline 2001-2024): r = +0.308, naive p = < 0.001, autocorrelation-adjusted p = < 0.001 (effective n = 279); Spearman rho = +0.255.
- Detrended anomalies: r = +0.295, adjusted p = < 0.001.
- Year-shuffled control (2000 permutations): p = < 0.001; 95% of shuffled |r| are below 0.133.
- With every calendar month weighted equally (anomalies divided by that month's standard deviation): r = +0.224.
- Partial correlation with Air temperature (2 m) held fixed statistically: r = +0.436 (95% CI +0.34 to +0.53; r = +0.295 without).
- Partial correlation with Relative humidity (2 m) held fixed statistically: r = +0.112 (95% CI -0.004 to +0.22; r = +0.295 without).
- Partial correlation with Air temperature (2 m) and Relative humidity (2 m) held fixed statistically: r = +0.072 (95% CI -0.04 to +0.19; r = +0.295 without).

Counterevidence:
- With every calendar month weighted equally the value is +0.22 instead of +0.31: the all-year figure is weighted towards the months with the largest variance.
- Halves of the record: r = +0.26 (2001-2012) and r = +0.32 (2013-2024); 10-year windows range from +0.20 to +0.32.
- By season: DJF +0.44, MAM +0.07, JJA +0.45, SON +0.08.

Alternatives not excluded:
- A third factor that varies from month to month (for example the passage of air masses) could move both variables together.
- Both variables come from one model, which may link them more tightly than nature does.

### `EV-ad099bfaf654` · OBSERVED · LAGGED_ASSOCIATION_DETECTED

Lag scan of detrended anomalies, Precipitation (bias-corrected) against Specific humidity (2 m), lags -6 to +6 months (13 tests, Benjamini-Hochberg): the largest |r| is at lag +0 (r = +0.30). Non-zero lags that stay significant after correction: +1 (r = +0.20), +2 (r = +0.20). Positive lags pair Precipitation (bias-corrected) with later Specific humidity (2 m). A lead or lag is a timing statistic only.

Evidence:
- Lag -2: r = +0.068, q = 0.481.
- Lag -1: r = +0.077, q = 0.481.
- Lag +0: r = +0.295, q = < 0.001.
- Lag +1: r = +0.205, q = 0.004.
- Lag +2: r = +0.195, q = 0.005.

Alternatives not excluded:
- Persistence of one variable alone can spread a same-month association onto neighbouring lags.

### `EV-face3dbd4c54` · OBSERVED · SUPPORTED

Monthly anomalies of Relative humidity (2 m) and Specific humidity (2 m) vary in the same direction over 2001-2024: detrended r = +0.36 (95% CI +0.24 to +0.46, effective n = 242). Raw r = -0.84; the two seasonal cycles alone give r = -0.91. The association holds in both halves of the record and against a year-shuffled control.

Evidence:
- Raw monthly series: r = -0.844 (n = 288).
- Seasonal cycles alone (climatology repeated each year): r = -0.912.
- Deseasonalized anomalies (baseline 2001-2024): r = +0.388, naive p = < 0.001, autocorrelation-adjusted p = < 0.001 (effective n = 231); Spearman rho = +0.266.
- Detrended anomalies: r = +0.358, adjusted p = < 0.001.
- Year-shuffled control (2000 permutations): p = < 0.001; 95% of shuffled |r| are below 0.145.
- With every calendar month weighted equally (anomalies divided by that month's standard deviation): r = +0.174.
- Partial correlation with Air temperature (2 m) held fixed statistically: r = +0.670 (95% CI +0.59 to +0.74; r = +0.358 without).
- Partial correlation with Precipitation (bias-corrected) held fixed statistically: r = +0.239 (95% CI +0.12 to +0.35; r = +0.358 without).
- Partial correlation with Air temperature (2 m) and Precipitation (bias-corrected) held fixed statistically: r = +0.569 (95% CI +0.48 to +0.65; r = +0.358 without).

Counterevidence:
- Relative humidity (2 m) is computed from Specific humidity (2 m) (and from Air temperature (2 m)), so part of this association is built into the definition and is not an independent finding.
- With every calendar month weighted equally the value is +0.17 instead of +0.39: the all-year figure is weighted towards the months with the largest variance.
- Halves of the record: r = +0.23 (2001-2012) and r = +0.44 (2013-2024); 10-year windows range from +0.22 to +0.43.
- By season: DJF +0.01, MAM +0.05, JJA +0.65, SON +0.28.

Alternatives not excluded:
- A third factor that varies from month to month (for example the passage of air masses) could move both variables together.
- Both variables come from one model, which may link them more tightly than nature does.

### `EV-9c4725d1e4f4` · OBSERVED · LAGGED_ASSOCIATION_DETECTED

Lag scan of detrended anomalies, Relative humidity (2 m) against Specific humidity (2 m), lags -6 to +6 months (13 tests, Benjamini-Hochberg): the largest |r| is at lag +0 (r = +0.36). Non-zero lags that stay significant after correction: +1 (r = +0.23), +2 (r = +0.22). Positive lags pair Relative humidity (2 m) with later Specific humidity (2 m). A lead or lag is a timing statistic only.

Evidence:
- Lag -2: r = +0.143, q = 0.086.
- Lag -1: r = +0.131, q = 0.111.
- Lag +0: r = +0.358, q = < 0.001.
- Lag +1: r = +0.230, q = 0.002.
- Lag +2: r = +0.215, q = 0.003.

Alternatives not excluded:
- Persistence of one variable alone can spread a same-month association onto neighbouring lags.

### `EV-ce4d336760f4` · OBSERVED · DERIVED_VARIABLE_CONFIRMED

Relative humidity (2 m) is a derived quantity in these data. Rebuilt from monthly Air temperature (2 m) and Specific humidity (2 m) with a textbook formula and no fitting, it matches the RH2M values in the file at r = +0.982 (mean absolute difference 2.60 percentage points); for detrended anomalies r = +0.767. A linear combination of the temperature and specific-humidity anomalies reproduces 50% of the variance of the relative-humidity anomalies (R2 by season: DJF 0.19, MAM 0.87, JJA 0.98, SON 0.69).

Evidence:
- Reconstruction against the file: r = +0.982, mean difference -0.59 percentage points, mean absolute difference 2.60.
- Fit of anomalies, all months: -1.23 percentage points per deg C and +6.10 per g/kg, R2 = 0.504.

Counterevidence:
- The match is weakest in DJF (R2 = 0.19); the reconstruction uses monthly means and a constant pressure, so the mismatch there is not evidence of independent information in RH2M.

Alternatives not excluded:
- The remaining mismatch may come from averaging (the mean of a ratio is not the ratio of the means) or from pressure changes; neither was tested.

## 5. Hypotheses — proposed, not tested here

These are possible explanations. They are not findings.

- `EV-5522e986bbfb` (T2M ↔ PRECTOTCORR): Hypothesis (untested here): in the warm season wet months are cloudier and evaporation cools the surface, while in winter mild air masses are also the moist ones, which would reverse the sign. A test: analyse seasons separately and add cloud amount or surface solar radiation.
- `EV-73905de10d27` (T2M ↔ RH2M): Hypothesis (untested here): for a fixed amount of water vapour, warmer air is further from saturation, so relative humidity is lower in warmer-than-usual months. A test: add specific humidity (QV2M), the moisture content itself, and compare how it and relative humidity each co-vary with temperature.
- `EV-3eb24d6b4573` (PRECTOTCORR ↔ RH2M): Hypothesis (untested here): wetter-than-usual months bring moister air and wetter soil, and both raise near-surface humidity; humidity staying high in the following month would fit soil-moisture memory. A test: add surface soil wetness (GWETTOP) and check whether it carries the one-month lag.

## 6. What cannot be concluded from these data

- Stability of Air temperature (2 m) cannot be concluded: the 95% interval of its slope runs from -0.067 to +0.046 °C/year, which includes change in either direction.
- A lasting trend in Relative humidity (2 m) cannot be concluded: not significant after false-discovery correction (q = 0.112); significance depends on single years (2002, 2008, 2017, 2018, 2024).
- Stability of Precipitation (bias-corrected) cannot be concluded: the 95% interval of its slope runs from -0.004 to +0.015 mm/day per year, which includes change in either direction.
- Stability of Specific humidity (2 m) cannot be concluded: the 95% interval of its slope runs from -0.000 to +0.021 g/kg per year, which includes change in either direction.
- A cause-and-effect link between Air temperature (2 m) and Precipitation (bias-corrected) cannot be concluded from co-variation of anomalies, however strong.
- A cause-and-effect link between Air temperature (2 m) and Relative humidity (2 m) cannot be concluded from co-variation of anomalies, however strong.
- That Air temperature (2 m) and Relative humidity (2 m) are linked by a separate physical process cannot be concluded from their correlation: the second is computed from the first, so part of the association is built into the definition.
- A cause-and-effect link between Air temperature (2 m) and Specific humidity (2 m) cannot be concluded from co-variation of anomalies, however strong.
- A cause-and-effect link between Precipitation (bias-corrected) and Relative humidity (2 m) cannot be concluded from co-variation of anomalies, however strong.
- A cause-and-effect link between Precipitation (bias-corrected) and Specific humidity (2 m) cannot be concluded from co-variation of anomalies, however strong.
- A cause-and-effect link between Relative humidity (2 m) and Specific humidity (2 m) cannot be concluded from co-variation of anomalies, however strong.
- That Specific humidity (2 m) and Relative humidity (2 m) are linked by a separate physical process cannot be concluded from their correlation: the second is computed from the first, so part of the association is built into the definition.
- Which variable influences which cannot be read from a lead or lag.
- That the atmosphere has or lacks 'memory' cannot be concluded from monthly correlation coefficients at a few lags.
- Nothing can be said about years outside 2001-2024 from this analysis alone.
- Values at a particular station or city inside the grid cell cannot be inferred, least of all where the terrain is uneven.
- That the same holds in other places cannot be concluded: one grid cell was analysed.

## 7. Limitations

- One MERRA-2 grid cell (about 0.5 x 0.625 degrees) at the cell's mean elevation: it describes the cell, not a station or a city.
- MERRA-2 is a model reanalysis. Changes in the observations it assimilates can create steps that look like trends; no homogeneity test is applied here.
- Only monotonic (Theil-Sen / Mann-Kendall) and linear trends are tested.
- Correlations describe co-variation of monthly anomalies. They do not identify causes, and a lead or lag is a timing statistic only.
- Results hold for the stated period; other periods can and do give different answers.

## 8. How to reproduce

Decision rules fixed in advance: alpha = 0.05; primary trend test: larger p of Hamed-Rao modified Mann-Kendall and AR(1)-adjusted least squares, on annual means (both must reject); Benjamini-Hochberg within each declared family; lag scan ±6 months; 2000 year-block permutations, seed 20261114.

```bash
pip install -r backend/requirements.txt
python scripts/build_provenance.py      # re-verifies the SHA-256 of every raw NASA file
python scripts/reproduce_gemini.py      # recomputes the Pavlodar case
```

No language model takes part in any computation in this report.
