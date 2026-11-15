"""The onboarding intro may only show what the engine computed, in wording the
MIZAN Guard accepts. Checks the facts, the series, the scripts in three
languages, the interface strings and the generated video documents.
REAL data: facts are recomputed from the bundled NASA files.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from build_intro_assets import compute  # noqa: E402
from build_video_docs import MAX_CPS, cues_for, max_cps  # noqa: E402
from intro_content import (LANGS, PLACEHOLDER, fact_text, fill, format_number, load_facts,  # noqa: E402
                           load_locale, load_scripts, strip_quotes)
from earth_senses.guard import check_claim  # noqa: E402

FACTS = load_facts()
SCRIPTS = load_scripts()
SERIES = json.loads((ROOT / "frontend/src/onboarding/content/series.json").read_text(encoding="utf-8"))
NEGATION = re.compile(r"\b(?:not|never|no|does not|isn't|mistake)\b|≠|\bне\b|\bнельзя\b|\bемес\b|шатастырма", re.I)


@pytest.fixture(scope="module")
def recomputed():
    return compute()


def scenes():
    for v in SCRIPTS["variants"]:
        for s in v["scenes"]:
            yield v, s


# ---- numbers ------------------------------------------------------------------------------------

def test_stored_facts_match_the_engine(recomputed):
    facts, series = recomputed
    assert facts["source"]["data_hash"] == FACTS["source"]["data_hash"]
    for k, f in FACTS.items():
        if k == "source":
            continue
        assert fact_text(FACTS, k, "en") == fact_text(facts, k, "en"), k
        assert f["value"] == pytest.approx(facts[k]["value"], abs=1e-9), k
    assert series == SERIES


def test_the_numbers_named_in_the_brief():
    shown = {k: fact_text(FACTS, k, "en") for k in ("p_rh_raw", "p_rh_deseason", "t_rh_raw", "t_rh_deseason")}
    assert shown == {"p_rh_raw": "−0.285", "p_rh_deseason": "+0.593",
                     "t_rh_raw": "−0.945", "t_rh_deseason": "−0.316"}
    assert FACTS["source"]["verdicts"] == {"T2M": "NO_SIGNIFICANT_TREND_DETECTED", "RH2M": "FRAGILE_TREND",
                                           "PRECTOTCORR-RH2M": "SUPPORTED"}
    # "no warming" is wrong because the interval includes warming
    assert FACTS["t_trend_ci_low"]["value"] < 0 < FACTS["t_trend_ci_high"]["value"]


def test_series_reproduce_the_two_correlations_shown_on_screen():
    p, rh = SERIES["PRECTOTCORR"], SERIES["RH2M"]
    assert len(SERIES["months"]) == 288 and SERIES["months"][0] == "2001-01" and SERIES["months"][-1] == "2024-12"
    assert np.corrcoef(p["raw"], rh["raw"])[0, 1] == pytest.approx(FACTS["p_rh_raw"]["value"], abs=5e-4)
    assert np.corrcoef(p["anomaly"], rh["anomaly"])[0, 1] == pytest.approx(FACTS["p_rh_deseason"]["value"], abs=5e-4)


def test_number_format_per_language():
    assert format_number(-0.2849, 3, True, "en") == "−0.285"
    assert format_number(0.59349, 3, True, "ru") == "+0,593"
    assert format_number(0.105, 3, False, "kk") == "0,105"
    assert format_number(-0.0001, 2, True, "en") == "0.00"          # no "−0.00"
    assert format_number(5, 0, False, "en") == "5"


# ---- scripts ------------------------------------------------------------------------------------

def test_three_variants_within_their_target_lengths():
    ids = [v["id"] for v in SCRIPTS["variants"]]
    assert ids == ["hero", "explainer", "teaser"]
    for v in SCRIPTS["variants"]:
        total = sum(s["dur"] for s in v["scenes"])
        lo, hi = v["target"]
        assert lo <= total <= hi, (v["id"], total)
    assert sum(s["dur"] for s in SCRIPTS["variants"][2]["scenes"]) <= 30   # usable as the 30-second submission demo


def test_every_scene_exists_in_three_languages_and_every_placeholder_is_a_fact():
    for v, s in scenes():
        for field in ("title", "vo"):
            assert set(s[field]) == set(LANGS), (s["id"], field)
            for lang in LANGS:
                text = s[field][lang].strip()
                assert text, (s["id"], field, lang)
                for key in PLACEHOLDER.findall(text):
                    assert key in FACTS and key != "source", (s["id"], key)
                assert "{" not in fill(text, FACTS, lang), (s["id"], lang)
        # Kazakh is not a copy of the Russian text
        assert s["vo"]["kk"] != s["vo"]["ru"] or s["vo"]["kk"].startswith("EARTH"), s["id"]
        assert s["vo"]["kk"] == s["vo"]["kk"].strip()


def test_the_main_story_is_in_every_variant_and_language():
    for v in SCRIPTS["variants"]:
        for lang in LANGS:
            text = " ".join(fill(s["vo"][lang] + " " + s["title"][lang], FACTS, lang) for s in v["scenes"])
            assert fact_text(FACTS, "p_rh_raw", lang) in text, (v["id"], lang)
            assert fact_text(FACTS, "p_rh_deseason", lang) in text, (v["id"], lang)


def test_subtitles_are_readable():
    for v in SCRIPTS["variants"]:
        for lang in LANGS:
            cues = cues_for(v, lang, FACTS)
            assert max_cps(cues) <= MAX_CPS, (v["id"], lang, max_cps(cues))
            for _a, _b, text in cues:
                assert all(len(line) <= 48 for line in text.split("\n")), (v["id"], lang, text)
                assert text.count("\n") <= 1, (v["id"], lang, text)


@pytest.mark.parametrize("lang", ["en", "ru"])
def test_every_line_passes_the_mizan_guard(lang):
    """Kazakh is not covered: the guard has English and Russian rules only (see LANGUAGE_FLOW.md)."""
    for _v, s in scenes():
        for field in ("title", "vo"):
            text, quotes = strip_quotes(fill(s[field][lang], FACTS, lang))
            verdict = check_claim(text, "statistical_relationship")
            if s["guard"] == "statistical":
                assert verdict["allowed"], (s["id"], field, lang, text, verdict["violations"])
            else:   # a statement about the method: only negated causal wording is allowed
                rules = {x["rule"] for x in verdict["violations"]}
                assert rules <= {"CAUSAL_LANGUAGE", "PROOF_LANGUAGE"}, (s["id"], rules)
                if rules:
                    assert NEGATION.search(text), (s["id"], field, lang, text)
            # quoted claims are the rejected ones; "no warming" must be caught by the guard
            for q in quotes:
                if re.search(r"warming|потеплени", q, re.I):
                    assert not check_claim(q, "statistical_relationship")["allowed"], q


def test_forbidden_conclusions_never_appear_unquoted():
    forbidden = [r"\bproven\b", r"\bproves?\b", r"доказан", r"дәлелденді", r"no memory", r"нет памяти",
                 r"definitely", r"однозначно", r"\bcauses\b"]
    for _v, s in scenes():
        for lang in LANGS:
            text, _ = strip_quotes(fill(s["vo"][lang] + " " + s["title"][lang], FACTS, lang))
            for pat in forbidden:
                assert not re.search(pat, text, re.I), (s["id"], lang, pat, text)


# ---- interface strings ---------------------------------------------------------------------------

def test_locales_have_the_same_keys_and_placeholders():
    loc = {l: load_locale(l) for l in LANGS}
    assert set(loc["en"]) == set(loc["ru"]) == set(loc["kk"])
    for k in loc["en"]:
        ph = {l: sorted(PLACEHOLDER.findall(loc[l][k])) for l in LANGS}
        assert ph["en"] == ph["ru"] == ph["kk"], (k, ph)
        for key in ph["en"]:
            assert key in FACTS or key == "n", (k, key)
    assert [loc[l]["meta.languageName"] for l in LANGS] == ["English", "Русский", "Қазақша"]


def test_main_app_has_a_complete_kazakh_table():
    src = (ROOT / "frontend/src/i18n.ts").read_text(encoding="utf-8")
    keys = re.findall(r"^  (\w+): \{ en:", src, re.M)
    kk_block = src[src.index("const KK"):src.index("export const tr")]
    kk_keys = re.findall(r"^  (\w+): '", kk_block, re.M)
    assert set(kk_keys) == set(keys)


# ---- generated documents are current -------------------------------------------------------------

def test_video_documents_are_generated_from_the_current_scripts():
    docs = ROOT / "docs" / "video"
    for v in SCRIPTS["variants"]:
        for lang in LANGS:
            md = (docs / f"{v['file']}_{lang.upper()}.md").read_text(encoding="utf-8")
            for s in v["scenes"]:
                assert fill(s["vo"][lang], FACTS, lang) in md, (v["id"], lang, s["id"])
            srt = (docs / "subtitles" / f"{v['id']}_{lang}.srt").read_text(encoding="utf-8")
            assert srt.count("-->") == len(cues_for(v, lang, FACTS))
    for name in ("VIDEO_MASTER_PLAN.md", "EXTERNAL_VIDEO_PROMPTS.md"):
        assert (docs / name).stat().st_size > 2000


def test_guard_catches_russian_negation_after_the_noun():
    """Added with the intro: «потепления нет» is as common as «нет потепления»."""
    for text in ("Потепления нет.", "Нет потепления.", "Связи нет.", "Тренда нет за этот период."):
        verdict = check_claim(text, "statistical_relationship")
        assert not verdict["allowed"] and verdict["violations"][0]["rule"] == "ABSENCE_OF_EVIDENCE", text
    assert check_claim("Зимой связь не обнаруживается (r = −0,06).", "statistical_relationship")["allowed"]
