"""MIZAN Guard: keeps wording within what the evidence supports.

Four kinds of statement are kept apart:

* ``computed_observation``            - a number computed from the data;
* ``statistical_relationship``        - an association that passed stated tests;
* ``exploratory_hypothesis``          - an idea worth testing;
* ``unverified_physical_explanation`` - a mechanism proposed, not tested here.

Causal wording is admissible only in the last two, and only when the text is
labelled as a hypothesis. A non-significant test may never be worded as proof
of absence. A lag may never be worded as a direction of influence. A status
may never be claimed above the one the evidence record carries.

The guard is deterministic pattern matching: it is a floor, not a referee.
It blocks known overclaims; passing it does not make a statement true.
"""
from __future__ import annotations

import re
from typing import Any

CLAIM_TYPES = ("computed_observation", "statistical_relationship",
               "exploratory_hypothesis", "unverified_physical_explanation")
HYPOTHESIS_TYPES = ("exploratory_hypothesis", "unverified_physical_explanation")
STATUS_ORDER = ["HYPOTHESIS", "OBSERVED", "REPLICATED", "PRACTICALLY_VALIDATED", "TRANSFER_VALIDATED"]

_CAUSAL = [
    r"\bcaus(?:e|es|ed|ing|al|ally|ation)\b", r"\blead(?:s|ing)? to\b", r"\bled to\b",
    r"\bdriv(?:e|es|en|ing)\b", r"\bdue to\b", r"\bbecause(?: of)?\b", r"\bresult(?:s|ed|ing)? in\b",
    r"\bresponsible for\b", r"\bexplain(?:s|ed)? by\b", r"\bis explained by\b", r"\bdetermin(?:es|ed)\b",
    r"\btrigger(?:s|ed)?\b", r"\binduc(?:es|ed)\b", r"\bproduc(?:es|ed) (?:a|an|the)\b",
    r"\bthe effect of\b", r"\bimpact(?:s)? of\b", r"\binfluenc(?:e|es|ed) (?:of|on)\b",
    r"\bforc(?:es|ed|ing)\b", r"\bthanks to\b", r"\bas a result of\b", r"\bso that\b",
    # Russian
    r"вызыва\w*", r"приводит\w* к", r"привел\w* к", r"привод\w* к", r"из-за", r"обусловл\w*",
    r"причин\w*", r"вследствие", r"потому что", r"влия\w* на", r"следстви\w*", r"порожда\w*",
    r"благодаря", r"определя\w*",
]
_PROOF = [r"\bprov(?:e|es|ed|en)\b", r"\bproof\b", r"\bconfirm(?:s|ed)? that\b", r"\bdemonstrat(?:es|ed) that\b",
          r"\bundoubtedly\b", r"\bcertainly\b", r"\bdefinitely\b",
          r"доказыва\w*", r"доказан\w*", r"несомненно", r"однозначно", r"подтвержда\w* что"]
_ABSENCE = [
    r"\bno (?:warming|cooling|trend|change|relationship|link|association|correlation|effect|memory|influence)\b",
    r"\b(?:there is|there was) no\b", r"\bis not (?:warming|changing|increasing|decreasing)\b",
    r"\bdoes not (?:change|exist|warm|depend)\b", r"\babsence of (?:a |any )?(?:trend|warming|relationship|memory)\b",
    r"\bhas not (?:changed|warmed)\b", r"\bunchanged\b", r"\bstable climate\b",
    r"нет (?:потеплени\w+|похолодани\w+|тренд\w*|изменени\w+|связ\w+|зависимост\w+|памят\w+)",
    r"отсутств\w+ (?:тренд\w*|потеплени\w+|связ\w+|памят\w+|изменени\w+)", r"не (?:теплеет|меняется|изменил\w*)",
    # Russian puts the negation after the noun just as often: «потепления нет», «связи нет».
    r"(?:потеплени\w+|похолодани\w+|тренд\w*|изменени\w+|связ\w+|зависимост\w+|памят\w+) нет\b",
]
_LAG_DIRECTION = [
    r"\blag\w*[^.]{0,60}\b(?:shows?|means?|implies|indicates?|establish\w*)[^.]{0,40}\b(?:direction|influence|control|response)",
    r"\bpreced\w+[^.]{0,40}\b(?:therefore|so|hence|thus)\b", r"\bresponds? to\b", r"\breact(?:s|ion)? to\b",
    r"\bleads?,? (?:so|therefore|hence)\b",
    r"лаг\w*[^.]{0,60}(?:показыва\w+|означа\w+|доказыва\w+)[^.]{0,40}(?:направлени\w+|влияни\w+)",
    r"реагиру\w+ на", r"отклик\w* на",
]
_UNIVERSAL = [r"\balways\b", r"\beverywhere\b", r"\bglobal(?:ly)?\b", r"\bin general\b", r"\bnever\b",
              r"всегда", r"везде", r"повсеместно", r"никогда", r"глобальн\w*"]
_STATUS_WORDS = {
    "REPLICATED": [r"\breplicated\b", r"\bindependently (?:verified|confirmed|reproduced)\b",
                   r"независимо (?:подтвержд\w+|воспроизвед\w+)"],
    "PRACTICALLY_VALIDATED": [r"\bvalidated\b", r"\bverified in practice\b", r"\bвалидирован\w*"],
    "TRANSFER_VALIDATED": [r"\btransfer[- ]validated\b", r"\bgeneralis\w+ to other regions\b"],
}
_HYPOTHESIS_LABEL = [r"\bhypothes[ie]s\b", r"\bnot tested\b", r"\buntested\b", r"\bunverified\b",
                     r"гипотез\w*", r"не провер\w*"]


def _find(patterns: list[str], text: str) -> list[str]:
    hits = []
    for pat in patterns:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            hits.append(m.group(0))
    return hits


def check_claim(text: str, claim_type: str, *, status: str = "OBSERVED",
                significant: bool | None = None) -> dict[str, Any]:
    """Return a verdict for one statement.

    ``significant`` is the outcome of the relevant test where one exists
    (None = not applicable). ``allowed`` is False when any blocking rule fires.
    """
    if claim_type not in CLAIM_TYPES:
        raise ValueError(f"unknown claim_type {claim_type!r}")
    if status not in STATUS_ORDER:
        raise ValueError(f"unknown status {status!r}")
    violations: list[dict[str, Any]] = []
    notices: list[dict[str, Any]] = []
    is_hyp = claim_type in HYPOTHESIS_TYPES

    causal = _find(_CAUSAL, text)
    if causal:
        if not is_hyp:
            violations.append({"rule": "CAUSAL_LANGUAGE", "matches": sorted(set(causal)),
                               "message": "Causal wording on a statistical result. A correlation or trend "
                                          "does not identify a cause. Reword as association, or file the "
                                          "mechanism separately as a hypothesis."})
        elif not _find(_HYPOTHESIS_LABEL, text) or status != "HYPOTHESIS":
            violations.append({"rule": "UNLABELLED_HYPOTHESIS", "matches": sorted(set(causal)),
                               "message": "A proposed mechanism must carry status HYPOTHESIS and say in "
                                          "the text that it is untested."})

    proof = _find(_PROOF, text)
    if proof:
        violations.append({"rule": "PROOF_LANGUAGE", "matches": sorted(set(proof)),
                           "message": "Statistical tests on one record do not prove anything; state the "
                                      "estimate, its uncertainty and the test result."})

    absence = _find(_ABSENCE, text)
    if absence and significant is not True:
        violations.append({"rule": "ABSENCE_OF_EVIDENCE", "matches": sorted(set(absence)),
                           "message": "A non-significant result is not evidence of no change. Say that no "
                                      "statistically significant trend/association was detected in this "
                                      "period, and give the confidence interval."})

    lag = _find(_LAG_DIRECTION, text)
    if lag and not (is_hyp and status == "HYPOTHESIS"):
        violations.append({"rule": "LAG_AS_DIRECTION", "matches": sorted(set(lag)),
                           "message": "A lead or lag is a timing statistic. It does not establish which "
                                      "variable influences which."})

    rank = STATUS_ORDER.index(status)
    for claimed, pats in _STATUS_WORDS.items():
        hits = _find(pats, text)
        if hits and STATUS_ORDER.index(claimed) > rank:
            violations.append({"rule": "STATUS_INFLATION", "matches": sorted(set(hits)),
                               "message": f"The text claims {claimed} but the evidence record is {status}."})

    universal = _find(_UNIVERSAL, text)
    if universal:
        notices.append({"rule": "SCOPE", "matches": sorted(set(universal)),
                        "message": "The analysis covers one grid cell and one period; avoid universal wording."})

    allowed = not violations
    label = "HYPOTHESIS — proposed, not tested here" if is_hyp else None
    return {"allowed": allowed, "claim_type": claim_type, "status": status,
            "violations": violations, "notices": notices, "required_label": label,
            "guidance": None if allowed else
            "Blocked. Rewrite as: what was computed, on which data and period, with which test and "
            "uncertainty. Put any mechanism in a separate record with status HYPOTHESIS."}


class GuardViolation(ValueError):
    """Raised when engine-generated text fails its own guard."""


def enforce(text: str, claim_type: str, *, status: str = "OBSERVED",
            significant: bool | None = None) -> str:
    """Return ``text`` unchanged if it passes, otherwise raise. Every sentence
    the engines publish goes through this."""
    verdict = check_claim(text, claim_type, status=status, significant=significant)
    if not verdict["allowed"]:
        rules = ", ".join(v["rule"] for v in verdict["violations"])
        raise GuardViolation(f"guard blocked engine text ({rules}): {text!r}")
    return text
