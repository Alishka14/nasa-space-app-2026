# Language flow

Screens: `frontend/src/onboarding/LanguageSelect.tsx`; gate: `frontend/src/Root.tsx`;
storage: `frontend/src/onboarding/storage.ts`. Screenshots: `screenshots/02_language_en.jpg`, `03_language_ru.jpg`, `04_language_kk.jpg`.

## Flow

```
first visit ──► splash ──► language ──► intro (chosen length) ──► app
                    │            │              │
                    └── Esc / Skip intro ───────┴──────────────► app
returning visit (intro seen) ─────────────────────────────────► app
app header "▶ Intro" ──────► language (current language preselected) ──► intro ──► app
```

## The language screen

- Three cards, labels native: **English**, **Русский**, **Қазақша**; under each, the
  call to action in that same language.
- Heading in all three languages; the one for the selected language is large.
- Selecting a card switches every text on the screen immediately and is saved at once.
- Intro length chips: Short ≈ 17 s, Explainer ≈ 45 s (default), Full film ≈ 60 s; the
  durations are computed from the scripts.
- Keys: `1` `2` `3` or arrows to choose, `Enter` to start, `Esc` to skip to the app.
- A note says the choice is stored on this device and can be changed in the header.

## What is remembered (localStorage)

| Key | Value | Effect |
|---|---|---|
| `earth-senses.lang` | `en` / `ru` / `kk` | Language of the onboarding and of the app on the next visit |
| `earth-senses.intro-seen` | `1` (intro version) | Returning visitors go straight to the app. Bumping `INTRO_VERSION` shows a changed intro once more |
| `earth-senses.intro-variant` | `teaser` / `explainer` / `hero` | Preselected length |

If storage is unavailable (private mode, blocked), everything still works for the
session; nothing is remembered.

**Decision for a returning visitor:** the intro is *not* forced again — judges reload
often. The app header has a language switch (EN | RU | KZ) and an "▶ Intro" button that
re-opens the onboarding at the language screen, with the previous language marked
("Last time you chose this language").

URL switches for demos and tests: `?intro` (always show from the splash),
`?intro=language`, `?nointro`, `?lang=kk`, `?capture&variant=hero&lang=ru`.

## i18n structure

| Part | Where | Languages | Coverage |
|---|---|---|---|
| Onboarding interface (56 strings) | `frontend/src/locales/{en,ru,kk}.json` | en, ru, kk | 100 % in all three |
| Intro films (3 variants, 20 scenes) | `frontend/src/onboarding/content/intro-scripts.json` | en, ru, kk per scene | 100 % |
| Numbers in any text | `{fact_key}` placeholders filled from `facts.json` | all | formatted per language |
| App interface (82 keys) | `frontend/src/i18n.ts` | en, ru (original table), kk (separate `KK` table) | 100 % (82/82) |
| Findings produced by the engine | backend | English only | unchanged; the app says so |

The existing English–Russian table was not rewritten: Kazakh was added as a separate
table, and a missing Kazakh key would fall back to English. `<html lang>` follows the
choice, so screen readers and hyphenation use the right language.

Tests (`backend/tests/test_09_intro_content.py`): identical keys and placeholders in all
three locale files; every scene present in all three languages; Kazakh lines are not
copies of the Russian ones; the app's Kazakh table covers every key.

## Limits

- **The MIZAN Guard has English and Russian rules only.** The English and Russian intro
  lines are checked automatically; the Kazakh lines are not. A Russian rule was added in
  this change (the word order «потепления нет»).
- **The Kazakh and Russian texts have not been reviewed by a native speaker.** They were
  written carefully, with the Kazakh letters and established terms (маусымдылық —
  seasonality, жауын-шашын — precipitation, салыстырмалы ылғалдылық — relative
  humidity, себептілік — causality), but a review before submission is advised.
