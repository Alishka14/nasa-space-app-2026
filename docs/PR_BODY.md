# EARTH SENSES MVP — evidence-first trend and relationship investigation (NASA POWER / MERRA-2)

**Draft.** Please do not merge until the team has reviewed it. This branch adds new files only; it does not modify
or delete anything that is already on `main` (if a path existed on both sides, the version on `main` was kept and
ours was added beside it — see the merge commit).

## What this adds

EARTH SENSES for the challenge *Be An Earth System Trend Detective!* — a FastAPI backend and a React interface that
investigate trends and relationships in NASA data for a chosen point and keep an evidence record for every result.

- `backend/earth_senses/` — data validation and provenance (`normalize`, `power_client`), Trend Engine (`trends`),
  Relationship Engine (`relationships`, `derived`), MIZAN Guard (`guard`), Evidence Engine (`evidence`),
  orchestration (`investigate`), report and API.
- `backend/tests/` — 160 automated tests.
- `frontend/` — React + TypeScript + Vite, MapLibre map, ECharts charts.
- `data/` — four raw NASA POWER responses stored byte-for-byte, one provenance record (with SHA-256) each.
- `scripts/` — `build_provenance.py`, `reproduce_gemini.py`, `build_docs.py`, `science_review.py`.
- `docs/` — method, science review, Gemini reproduction, evidence ledger, limitations, demo script, submission text.

## How to check it (about five minutes)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements-dev.txt
python scripts/build_provenance.py            # OK ×4: SHA-256 of the NASA files
(cd backend && python -m pytest)              # 160 passed
(cd frontend && npm ci && npm run build)
EARTH_SENSES_OFFLINE=1 uvicorn earth_senses.api:app --app-dir backend --port 8000
# open http://localhost:8000 → Investigate → "Precipitation ↔ Relative humidity" → View evidence
```

## Verification status

| Check | Result |
|---|---|
| Backend tests, clean environment, `requirements-dev.txt` | **PASS** — 160 passed |
| Backend tests without the optional `pymannkendall` | **PASS** — 151 passed, 9 skipped (reference cross-checks; skipped, not counted as passed) |
| SHA-256 of the four NASA files | **PASS** |
| Frontend production build (`npm ci && npm run build`) | **PASS** |
| Interface in a headless browser: region, time series, relationship, evidence drawer, graph, comparison, report, error banner | **PASS** — inspected, not an automated UI test suite |
| Live request from the backend to NASA | **NOT RUN** — no network route in the build environment; the path is tested with a stubbed transport only |
| Retrieval through Giovanni / GES DISC | **NOT RUN** |
| Review by a human scientist | **NOT DONE** |

## Science in one paragraph

Pavlodar grid cell, 2001–2024. The correlation between precipitation and relative humidity is −0.28 in raw monthly
data and +0.59 once the seasonal cycle is removed; it survives holding temperature and specific humidity fixed
(+0.44), is absent in winter, and remains a correlation inside one reanalysis. Temperature shows no significant
trend, which is not evidence of "no warming". The humidity trend (p = 0.035) is classified as fragile. Relative
humidity is computed by NASA POWER from temperature, so that edge is flagged as partly built into the definition.
Details and open items: `docs/SCIENCE_REVIEW.md` (a self-audit, not an independent validation).

## Not done

- Demo video (≤ 30 s) or slides (≤ 7) and its public link.
- The repository must be public for the submission link.
- A second, independent NASA source (IMERG through NASA POWER returned only missing values for this point).
- Human scientific review.
- Licence for the repository (owner's decision).

## Notes for reviewers

- No secrets, tokens or private code are included. Network access is used only for `power.larc.nasa.gov`.
- AI disclosure: the code, tests and documents in this branch were written by Claude (Anthropic) under the team's
  direction; a preliminary analysis by Gemini was reproduced and checked. No AI model takes part in the tool's
  calculations.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01KCCBh435ACxUgRUjviubtK
