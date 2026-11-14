"""Shared helpers for the intro content: load facts and scripts, fill placeholders.

The formatting rules mirror frontend/src/onboarding/i18n.ts (formatNumber):
U+2212 minus sign, '+' for positive signed values, decimal comma for ru and kk.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "frontend" / "src" / "onboarding" / "content"
LOCALES = ROOT / "frontend" / "src" / "locales"
LANGS = ("en", "ru", "kk")
PLACEHOLDER = re.compile(r"\{([a-z0-9_]+)\}", re.I)


def load_facts() -> dict:
    return json.loads((CONTENT / "facts.json").read_text(encoding="utf-8"))


def load_scripts() -> dict:
    return json.loads((CONTENT / "intro-scripts.json").read_text(encoding="utf-8"))


def load_locale(lang: str) -> dict:
    return json.loads((LOCALES / f"{lang}.json").read_text(encoding="utf-8"))


def format_number(value: float, digits: int, signed: bool, lang: str) -> str:
    body = f"{abs(value):.{digits}f}"
    if lang != "en":
        body = body.replace(".", ",")
    if value < 0 and float(f"{abs(value):.{digits}f}") != 0:
        return "−" + body
    return ("+" + body) if (signed and value > 0) else body


def fact_text(facts: dict, key: str, lang: str) -> str:
    f = facts[key]
    return format_number(f["value"], f["digits"], f["signed"], lang)


def fill(text: str, facts: dict, lang: str, params: dict | None = None) -> str:
    params = params or {}

    def repl(m: re.Match) -> str:
        k = m.group(1)
        if k in params:
            return str(params[k])
        if k in facts and k != "source":
            return fact_text(facts, k, lang)
        return m.group(0)

    return PLACEHOLDER.sub(repl, text)


QUOTED = re.compile(r"[«“\"]([^»”\"]+)[»”\"]")


def strip_quotes(text: str) -> tuple[str, list[str]]:
    """Remove quoted (rejected) claims; return the remaining text and the quotes."""
    quotes = QUOTED.findall(text)
    return QUOTED.sub("…", text), quotes
