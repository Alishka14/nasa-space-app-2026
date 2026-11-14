# Science Method

How EARTH SENSES turns a NASA response into conclusions. Everything here is implemented in `backend/earth_senses/`
and exercised by `backend/tests/`. The decision rules were fixed before the results they judge; where a rule was
changed during development, the change and its reason are recorded in §9.

## 1. Data

**Source.** NASA POWER Monthly & Annual API (`/api/temporal/monthly/point`), community `AG`. The meteorological
parameters come from MERRA-2 (Gelaro et al. 2017), a model reanalysis on a 0.5° × 0.625° grid. A "point" request
returns the grid cell that contains the point, at the cell's mean elevation (third coordinate of the response).
These are model values constrained by observations, not station or direct satellite measurements, and the tool says
so wherever the data are shown.

**Storage.** The response body is written byte-for-byte to `data/raw/power/` and never edited. A Data Provenance
Record (`data/provenance/`) holds the source, the exact request, retrieval time and method, variables and units,
spatial and temporal resolution, coverage, missing-value counts, product version, SHA-256 and validation status.
Derived tables live separately in `data/normalized/`.

**Two hashes.** The response contains a `times` block with server timings that change on every request, so identical
data yield different raw hashes. We store the raw-byte SHA-256 and a second SHA-256 over the data, units, geometry and
period only.

**Validation on every use** (`normalize.py`, `power_client.py`). A response, fresh or cached, is rejected if:

| Check | Why |
|---|---|
| body empty, not JSON, or without parameters | HTTP 200 does not mean data arrived |
| a requested parameter or any calendar month is absent | partial responses must not be analysed |
| variables do not share one calendar | misaligned months silently change correlations |
| a time key is not `YYYY01`–`YYYY12` or `YYYY13` | unknown structure |
| `header.fill_value` or a parameter's units are absent | missing data and units are never assumed |
| geometry or period differ from the request | a cache entry must describe the region it is used for |
| the file's SHA-256 differs from its provenance record | corruption or substitution |

Keys ending in `13` are the API's annual means. They are kept apart and never enter a monthly series. Values equal
to the declared fill value (−999) become missing; an investigation with missing months is refused, because gap
handling is not implemented.

**Units.** Units are read from the response. For the three verified variables a mismatch with the expected unit is a
hard error. `PRECTOTCORR` is a mean rate in mm/day: monthly totals are rate × the real number of days in that month,
annual totals are their sum. Trends are reported separately, and never mixed, as °C per year, percentage points per
year, mm/day per year (intensity) and mm/year per year (accumulation).

**Annual and seasonal means** weight each month by its length. Computed this way they agree with the API's own annual
values to within two-decimal rounding (≤ 0.005), which doubles as a check that months and annual summaries were not
confused. A season needs all three months; DJF of year Y uses December of Y−1 and is dropped when that month is absent.

## 2. Anomalies

The climatological baseline is the mean of each calendar month over stated baseline years (default: the analysed
period; at least 10 years per calendar month). The baseline is part of every evidence record's parameters.

- **Deseasonalized anomaly** = value − baseline mean of its calendar month.
- **Detrended anomaly** = deseasonalized anomaly − its least-squares line.

## 3. Trend Engine (`trends.py`)

Computed on annual means (one value per year), so the seasonal cycle cannot leak into the test.

| Quantity | Method |
|---|---|
| Rate of change | Theil–Sen slope (Sen 1968) with a 95% rank-based confidence interval |
| Classic test | Mann–Kendall with tie and continuity corrections (Mann 1945; Kendall 1975) |
| Autocorrelation-aware rank test | Hamed & Rao (1998) variance correction, clipped so it can only widen the variance |
| Autocorrelation-aware parametric test | Least squares with the AR(1) effective sample size n_eff = n(1 − r₁)/(1 + r₁) (Santer et al. 2000) |
| **Primary p-value** | **the larger of the two autocorrelation-aware p-values** — both must reject |
| Monthly cross-check | Seasonal Kendall test and seasonal slope (Hirsch et al. 1982) with the between-month covariance term (Hirsch & Slack 1984) |
| Multiple testing | Benjamini–Hochberg (1995) q-values across the variables analysed together; a separate family for the seasonal tests |
| Power | Minimum trend detectable with 80% power, from the AR(1)-adjusted standard error of the slope |
| Period sensitivity | Slope and test for every sub-period of at least 15 years (20 for records of 40+ years) |
| Single-year influence | Leave-one-year-out |
| Longer context | The same trend over 1981 to the end year, when those data can be obtained |

**Verdicts.**

- `ROBUST_TREND`: primary p < 0.05 **and** q < 0.05 **and** the confidence interval excludes zero **and** no single
  year's removal changes significance.
- `FRAGILE_TREND`: at least one test gives p < 0.05, but one of the conditions above fails. The reasons are listed.
- `NO_SIGNIFICANT_TREND_DETECTED`: otherwise. The statement always gives the confidence interval and the minimum
  detectable trend, and never says that there is no change.

Our implementations are checked against an independent library (`pymannkendall`) and `statsmodels` in the tests:
S, variance, p-value, slope, seasonal test, covariance term, Hamed–Rao (unclipped) and Benjamini–Hochberg all agree.

## 4. Relationship Engine (`relationships.py`)

Each pair of variables is correlated four ways, shown side by side and never merged:

1. **raw** monthly values;
2. **seasonal cycles alone** — each series replaced by its repeating climatology, which shows how much of the raw
   value the calendar produces by itself;
3. **deseasonalized** anomalies;
4. **detrended** anomalies (the basis of the verdict).

**Inference.** Pearson r with Spearman's ρ alongside. Because monthly anomalies are autocorrelated, p-values and the
confidence interval use the effective sample size n_eff = n(1 − r₁ₓr₁ᵧ)/(1 + r₁ₓr₁ᵧ) (Bretherton et al. 1999). The
naive p-value is shown for comparison.

**Negative control.** Whole years of one series are shuffled against the other (2000 permutations, fixed seed). This
keeps each series' within-year structure and destroys only the year-to-year pairing. A real association must stand out
from that null distribution.

**Stability.** Correlation in each half of the record and in sliding 10-year windows. **Seasons.** Correlation within
DJF, MAM, JJA and SON; a sign that differs between seasons is reported as counterevidence to any all-year statement.

**Status of an edge** (thresholds α = 0.05 and |r| ≥ 0.2, set in advance):

| Status | Condition |
|---|---|
| `SUPPORTED` | adjusted p < α, permutation p < α, same sign in both halves, |r| ≥ 0.2 |
| `WEAK` | as above but |r| < 0.2 |
| `INCONCLUSIVE` | only one of the two tests passes, or the sign differs between the halves |
| `NOT_SUPPORTED` | neither test passes |

**Equal weight for every calendar month.** Anomalies are also divided by the standard deviation of their own
calendar month and correlated again. In a continental climate summer precipitation varies far more than winter
precipitation, so a pooled coefficient is weighted towards summer. If the equal-weight value is below three quarters
of the pooled one, a counterevidence line says so (Pavlodar precipitation–humidity: +0.59 pooled, +0.37 with equal
weights, −0.06 in winter).

**False discovery across pairs.** The adjusted p-values of all pairs in one investigation form a family;
Benjamini–Hochberg q is reported per pair (`q_across_pairs`). The status is still decided per pair; if a detectable
pair has q ≥ α a warning is raised.

**Partial correlation** (`partial_correlation`). For each pair and each other selected variable (and all others
together), both series are regressed on the control series and the residuals are correlated; each control costs one
degree of freedom on top of the autocorrelation adjustment. This answers one question only: does the association
remain when the other series is held fixed statistically? It assumes linear relations and is still a correlation.

### 4a. Derived variables (`derived.py`, `catalog.DERIVED`)

Some "variables" are computed from others. NASA POWER calculates relative humidity (`RH2M`) from MERRA-2 pressure,
temperature and specific humidity, over water only (POWER methodology, *Relative Humidity*). A correlation between
`RH2M` and `T2M` or `QV2M` is therefore partly built into the definition. The engine:

1. flags every pair in which one variable is computed from the other (⚙ *built-in dependence*) in the pair card,
   the graph edge, the evidence record's counterevidence, the episode timeline and the list of what cannot be
   concluded;
2. when `T2M`, `QV2M` and `RH2M` are all selected, rebuilds relative humidity from monthly temperature and specific
   humidity with the Magnus formula over water (WMO-No. 8 coefficients) at a constant standard-atmosphere pressure for
   the grid cell's elevation — nothing is fitted — and reports its agreement with the `RH2M` values in the file;
3. reports how much of the variance of the `RH2M` anomalies a linear combination of the `T2M` and `QV2M` anomalies
   reproduces, overall and by season.

The reconstruction is approximate on purpose (monthly means, constant pressure, a different saturation formula from
POWER's); its mismatch is reported and is not treated as evidence of independent information.

## 5. Lag analysis

r(k) = corr(x[t], y[t+k]) for k = −6…+6 on detrended anomalies. **k > 0 pairs x with later y.** Each lag loses |k|
months. The thirteen lags form one family: q-values come from Benjamini–Hochberg on the autocorrelation-adjusted
p-values. If some non-zero lag passes an uncorrected test but none survives correction, the lag verdict is
`INCONCLUSIVE`.

A lead or lag is a timing statistic. It does not show which variable influences which, and persistence of one series
alone can spread a same-month association onto neighbouring lags. Monthly means cannot resolve anything faster than a
month. The engine's text and the guard both enforce this.

## 6. Region comparison

Both places are analysed over the same years. Reported: each place's trend, the trend of the difference series
(which tests whether the places are drifting apart), and the correlation of their detrended monthly anomalies.
`OPPOSITE_SIGNIFICANT_TRENDS` requires both trends to be significant with opposite signs; opposite signs without
significance are labelled as exactly that.

## 7. MIZAN Guard (`guard.py`)

Statements are of four kinds: computed observation, statistical relationship, exploratory hypothesis, unverified
physical explanation. The guard is deterministic pattern matching in English and Russian:

| Rule | Blocks |
|---|---|
| `CAUSAL_LANGUAGE` | causes, leads to, drives, due to, because of, determines… on a statistical result |
| `UNLABELLED_HYPOTHESIS` | a mechanism not marked as an untested hypothesis with status `HYPOTHESIS` |
| `PROOF_LANGUAGE` | proves, confirms that, certainly… |
| `ABSENCE_OF_EVIDENCE` | "no warming", "no trend", "has not changed" for a non-significant result |
| `LAG_AS_DIRECTION` | a lag presented as direction of influence; "responds to" |
| `STATUS_INFLATION` | "replicated", "validated" above the record's actual status |

Every sentence the engines publish is passed through the guard when the evidence record is created; a violation
raises an error instead of producing output. The same check is exposed as `POST /api/guard/check` for text written by
people or by a language model. The guard is a floor: it blocks known overclaims, and passing it does not make a
statement true.

## 8. Evidence Engine (`evidence.py`)

Each conclusion is a record with: `id, claim, claim_type, region, period, variables, method, parameters, data_hash,
result, uncertainty, status, supporting_evidence, counterevidence, alternatives, limitations, verdict`.

- The `id` is a hash of claim type, region, period, variables, method, parameters and data hash. Same inputs, same id.
- `data_hash` identifies the raw files (by SHA-256) and the slice used.
- **Status** follows the MIZAN ladder. A record is `OBSERVED` or `HYPOTHESIS`; the engine cannot assign anything
  higher. Replication is tracked per value: a number is listed under `replicated_values` only when a value registered
  in `data/independent_reports/` — reported by a different assessor from separately obtained data — matches ours
  within its stated tolerance for the same place, period and quantity. One disagreeing report for a record blocks
  it. The record itself stays `OBSERVED`, because its claim contains more than the replicated numbers.
- **Relationship graph.** Nodes are variables. An edge exists only if a relationship record was computed, and carries
  that record's id. Hypotheses can annotate an edge; they cannot create one.
- **EarthChangeEpisode.** For each trend and relationship the path Observation → Hypothesis → Test → Counterexample →
  Revision → Conclusion is stored with the data hash and the reason for any revision.

## 9. Changes made during development, and why

| Change | Trigger | Effect on real results |
|---|---|---|
| Hamed–Rao variance factor clipped at ≥ 1 | On the 1981–2024 precipitation record the unclipped factor was 0.48, making the "corrected" test more liberal than the classic one | None on verdicts |
| Primary p = larger of Hamed–Rao and AR(1)-adjusted least squares | Synthetic control (3000 simulations, n = 24): on trend-free AR(1) noise Hamed–Rao alone rejects in 12% of cases at φ = 0.3 and 29% at φ = 0.7 instead of 5%; the combined rule in 7.5% and 14% | Temperature p 0.413 → 0.578; verdicts unchanged |
| Seasonal correlations: lag-1 autocorrelation from consecutive months only | Independent review: a season subset jumps from February to December, and those array neighbours were being treated as lag 1 | By-season adjusted p-values only; no verdict uses them |
| Fill value matched exactly | Independent review: values within about 0.01 of −999 were also treated as missing | None on these files |
| Replication tracked per value, records stay `OBSERVED` | A record's claim contains more than the replicated numbers | Status labels only |
| "Stability cannot be concluded…" sentence split by verdict | The sentence wrongly said the humidity interval included both signs | Wording only |
| ⚙ built-in dependence flag and derived-variable check | Science review: `RH2M` is computed from temperature, yet the temperature–humidity edge was shown as an ordinary association | Numbers unchanged; interpretation restricted |
| Partial correlations | Science review: no way to ask whether an association survives a third variable | New numbers only |
| `q_across_pairs` | Science review: pair tests were not corrected across pairs | No status changed |
| Equal-month-weight correlation | Science review: the all-year precipitation–humidity value is weighted towards high-variance months | New counterevidence line |
| A variable that is entirely missing is stored as evidence and refused | Real NASA response: `IMERG_PRECTOT` came back as −999 in every month for Pavlodar | None |
| Variables may be assembled from several verified files | `QV2M` was retrieved separately from the first three variables | Data hash of the default case unchanged |

## 10. What the method does not do

No homogeneity (change-point) testing of the reanalysis; no non-linear trend models; no gap filling; no spatial
aggregation beyond one grid cell; no physical attribution. See `KNOWN_LIMITATIONS.md`.

## References

- Benjamini, Y., Hochberg, Y. (1995). Controlling the false discovery rate. *J. R. Stat. Soc. B* 57, 289–300.
- Bretherton, C. S., et al. (1999). The effective number of spatial degrees of freedom of a time-varying field. *J. Climate* 12, 1990–2009.
- Gelaro, R., et al. (2017). The Modern-Era Retrospective Analysis for Research and Applications, Version 2 (MERRA-2). *J. Climate* 30, 5419–5454.
- Hamed, K. H., Rao, A. R. (1998). A modified Mann-Kendall trend test for autocorrelated data. *J. Hydrol.* 204, 182–196.
- Hirsch, R. M., Slack, J. R., Smith, R. A. (1982). Techniques of trend analysis for monthly water quality data. *Water Resour. Res.* 18, 107–121.
- Hirsch, R. M., Slack, J. R. (1984). A nonparametric trend test for seasonal data with serial dependence. *Water Resour. Res.* 20, 727–732.
- Kendall, M. G. (1975). *Rank Correlation Methods.* Griffin, London.
- Mann, H. B. (1945). Nonparametric tests against trend. *Econometrica* 13, 245–259.
- NASA POWER Project. Methodology: Relative Humidity. <https://power.larc.nasa.gov/docs/methodology/meteorology/relative-humidity/>
- Santer, B. D., et al. (2000). Statistical significance of trends and trend differences in layer-average atmospheric temperature time series. *J. Geophys. Res.* 105, 7337–7356.
- World Meteorological Organization (2008). *Guide to Meteorological Instruments and Methods of Observation*, WMO-No. 8, Annex 4.B (saturation vapour pressure formulae).
- Sen, P. K. (1968). Estimates of the regression coefficient based on Kendall's tau. *J. Am. Stat. Assoc.* 63, 1379–1389.
