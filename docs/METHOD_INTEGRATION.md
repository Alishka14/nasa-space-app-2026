# Method Integration

Which of the team's engineering methodologies were applied in EARTH SENSES, where, and what was deliberately left out.

**Rule followed.** Principles were adapted; code was not copied. Most of the methodology repositories carry no licence
file, which means all rights are reserved by their authors, so only ideas were taken and re-implemented for this
domain. Authorship of each methodology stays with its authors.

## What was reviewed

| Repository | Reviewed in this build | Licence found | Used |
|---|---|---|---|
| `airtrio-security-lab/mizan-methodology` | README, `docs/METHODOLOGY.md`, schemas (commit `be21a79`) | none | principles |
| `airtrio-security-lab/batyr-aga-skill` | README (`31ed3da`) | none | principles |
| `airtrio-security-lab/git-senses` | README, schema list (`6757819`) | none | principles |
| `airtrio-security-lab/diyaz-method` | README (`97a39a1`) | none | principles |
| `airtrio-security-lab/modus-flow` | README (`11bca71`) | none | principle |
| `airtrio-security-lab/skill-scrap` | README, which holds only a title (`fe3521d`) | none | principle as described in the brief |
| `RakamakadoN/ghost-busters-skill` | README, `SKILL.md` outline (`1f64b8d`) | MIT | principles |
| `RakamakadoN/diyaz-forge-skill` | README (`43ca80c`) | MIT | principle |
| `RakamakadoN/pavlodar-pulse` | README, `NOTICE.md` (`935c523`) | custom notice, no open licence | nothing |
| `RakamakadoN/ghost-busters-pro` | **not reviewed** | — | nothing |
| `RakamakadoN/agent-smith-swarm` | **not reviewed** | — | nothing |
| `airtrio-security-lab/pavlodar-hub-academy` | **not reviewed** | — | nothing |

The last three were not opened in this session. Nothing in this project depends on them.

## How each was applied

### MIZAN + BURHAN — is a claim trustworthy?

| Principle | Implementation |
|---|---|
| Claim → Evidence → Counterevidence → Alternatives → Verdict | The fields of every `EvidenceRecord` (`evidence.py`); shown in View Evidence and in the report |
| Status ladder HYPOTHESIS → OBSERVED → REPLICATED → … | `STATUS_ORDER` in `guard.py`; the engine can assign only the first two |
| REPLICATED needs an independent assessor or independently obtained artifact | `attach_independent_reports`: a value is marked replicated only when a registered external value agrees; one disagreement blocks it; the record as a whole stays OBSERVED |
| A passing test is not universal proof | `PROOF_LANGUAGE` and `ABSENCE_OF_EVIDENCE` rules; "what cannot be concluded" in every investigation |
| Separate observation, supported relation, hypothesis, unverified explanation | Four `claim_type` values; causal wording admitted only in labelled hypotheses |

Not taken: MIZAN's benefit/harm registers and ATHAR lineage tracing, which have no counterpart in a climate-statistics
tool. `PRACTICALLY_VALIDATED` and `TRANSFER_VALIDATED` are defined but nothing in this project has earned them.

### BATYR AGA — AI proposes; evidence decides; humans remain accountable

| Principle | Implementation |
|---|---|
| AI proposes | Gemini's preliminary analysis is treated as a proposal and stored as an *independent report*, not as a result |
| Evidence decides | Results come only from deterministic code on hashed data; no language model in the computation path |
| Humans remain accountable | Every record with replicated values states that both assessors are AI systems and that human review is required |
| Independent roles | See "Independence" below |

### Git Senses — a research series has a history

`EarthChangeEpisode` (`build_episodes` in `investigate.py`): Observation → Hypothesis → Test → Counterexample →
Revision → Conclusion for each trend and relationship, with the data version (hash), evidence ids and the reason for
each revision. Shown in the Evidence Timeline. Method changes made during development are logged in
`SCIENCE_METHOD.md` §9. Not implemented: persisting episodes across runs and data versions (they are rebuilt per
investigation).

### MODUS FLOW — knowledge provenance graph

The relationship graph (`build_graph`): every edge carries the id of the evidence record it was computed from, which
carries the data hash, which resolves to a provenance record and a raw NASA file. Hypotheses annotate edges and cannot
create them.

### DIYAZ METHOD — staged, evidence-driven engineering

| Stage | What happened here |
|---|---|
| DISCOVER | Preflight: event rules, repository access, NASA API reachability, the Resources tab |
| MODEL | Data traps and decision rules written down before the engines |
| DECOMPOSE | Separate modules for ingestion, trends, relationships, guard, evidence |
| EXECUTE | Small commits per module |
| CHALLENGE | Synthetic negative controls; cross-checks against other libraries; a separate verification agent |
| VERIFY | 146 tests; rendered interface inspected screen by screen |
| GOVERN | Guard on all published text; statuses that cannot be self-assigned |
| EVOLVE | Method revisions recorded with their trigger (`SCIENCE_METHOD.md` §9) |

### Ghost Busters — bugs that never crash

| Ghost named in the brief | Trap | Test |
|---|---|---|
| HTTP 200 with incomplete data | calendar-completeness and parameter checks before caching | `test_http_200_with_missing_months_is_rejected` |
| False zeros / fill values | declared fill → NaN; analysis refused on gaps | `test_fill_value_becomes_nan_and_is_counted` |
| Mismatched dates | identical calendar required; alignment checked before correlating | `test_misaligned_calendars_are_refused` |
| Hidden units | units only from the response; mismatch is a hard error | `test_units_come_from_the_response…` |
| Wrong climatological baseline | baseline explicit, recorded, minimum length enforced | `test_climatology_needs_enough_years…` |
| False statistical significance | effective sample size, two-test rule, FDR, permutation control | `test_autocorrelation_inflates…`, `test_bh_controls_false_discoveries…` |
| Cache not matching the region | SHA-256 and geometry re-verified on every load | `test_cache_file_swapped_for_another_region_is_detected` |
| Chart showing other data than the API | API values compared with the raw file; chart layers must rebuild the raw series | `test_series_in_the_response_are_the_values_in_the_raw_nasa_file` |

Ghosts found by hunting, not on the list: the `times` block that changes the raw hash on every request; the grid-cell
elevation that makes "Almaty" a mountain cell; a Hamed–Rao correction that made the test *more* liberal; interface
panels that silently collapsed to zero height (found only by looking at the rendered page).

Found in the FINAL DELIVERY audit (`SCIENCE_REVIEW.md`), none of which raised an error before: a derived variable
(`RH2M`) presented as if it were independent of its input; a NASA parameter (`IMERG_PRECTOT`) that returns HTTP 200,
valid units and nothing but fill values; a data-check sentence that counted gaps of variables nobody had requested;
an all-year correlation carried by the high-variance months; a test module that failed at import, not at a test, when
an optional package was absent; graph labels that covered each other once a fourth variable was selected.

### Skill Scrap — record reusable methods without overstating them

Recorded as candidate methods, each observed once in this project and therefore not claimed as transferable:

1. *Hash-verified transfer through a browser* when a build sandbox cannot reach a data source: compute SHA-256 where
   the bytes arrive, move the body, re-hash, and compare chunk hashes to localise any difference.
2. *Identify an unstated method by enumeration*: compute every standard variant, publish the whole table including
   the non-matching rows.
3. *Let the guard fail the build*: route the engine's own sentences through the same wording rules as outside text.
4. *Characterisation tests for a known weakness*: a test that pins the residual false-positive rate documents the
   limitation and fails if someone changes it unknowingly.

### Diyaz Forge

One principle carried over: pure domain logic → deterministic tests → thin service → interface. The API layer
(`api.py`) contains no statistics.

## Independence — stated honestly

| Check | Who | Independent of the engine's author? |
|---|---|---|
| Original numbers | Gemini | Yes: other model family, separate data retrieval, no shared code |
| Reproduction and engines | Claude | — (author) |
| Library cross-checks | `pymannkendall`, `statsmodels` | Yes for the algorithms covered |
| Separate recomputation and review | a second Claude agent that wrote its own code before seeing ours, then reviewed code and wording | **Partly**: separate context and code, but the same model family, so it does not count as independent under MIZAN rule 10. It found no numerical disagreement, one medium issue (a match tolerance wider than rounding, which hid that the tie-corrected test gives 0.274 where Gemini reported 0.275), four low ones and fifteen overstated or unclear sentences; all confirmed items were fixed (`SCIENCE_METHOD.md` §9, `GEMINI_REPRODUCTION.md`) |
| FINAL DELIVERY science review (`SCIENCE_REVIEW.md`) | Claude (the engine's author) | **No.** A self-audit with stated, reproducible tests. It restricted interpretations and added checks; it raised no status |
| Human scientific review | — | **Not done** |
