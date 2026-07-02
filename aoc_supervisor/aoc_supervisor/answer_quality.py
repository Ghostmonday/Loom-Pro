"""Deterministic answer-informativeness scoring for Intent Forge interrogation.

A world-class interviewer gives credit for substance, not for keystrokes.
This module scores a free-text answer into a confidence credit so that:

- a genuinely informative answer clears the finalize confidence threshold
  (DEFAULT_CONFIDENCE_THRESHOLD = 0.65) in a single pass;
- a rich, specific answer earns more;
- a shrug ("idk", "whatever you think") earns almost nothing, keeping the
  domain below threshold so the engine can come back with a sharper,
  more concrete follow-up instead of silently recording noise.

Scoring is pure and deterministic: same text, same score, no clock, no
randomness, no model call. It is intentionally a heuristic — the goal is
honest bookkeeping, not NLP perfection.
"""

from __future__ import annotations

import re

# Credit levels. WEAK stays below DEFAULT_CONFIDENCE_THRESHOLD (0.65) so a
# weak answer marks the domain "addressed" but not "confident"; SOLID clears
# the threshold in one pass; RICH reflects a specific, decision-dense answer.
WEAK_CREDIT = 0.35
SOLID_CREDIT = 0.70
RICH_CREDIT = 0.85

# Deterministic markers of a non-answer. Matched against the normalized text.
_DEFLECTIONS: tuple[str, ...] = (
    "idk",
    "i don't know",
    "i dont know",
    "dunno",
    "whatever",
    "no idea",
    "not sure",
    "you decide",
    "you choose",
    "up to you",
    "anything",
    "don't care",
    "dont care",
    "doesn't matter",
    "doesnt matter",
    "skip",
    "next",
    "n/a",
    "na",
    "none",
    "nothing",
    "yes",
    "no",
    "ok",
    "okay",
    "sure",
    "fine",
    "good",
)

_STOPWORDS: frozenset[str] = frozenset(
    """a an the and or but if then else of to in on at for with by from as is are was
    were be been being it its this that these those there here just really very
    i we you they he she my our your their me us them do does did doing have has
    had having will would should could can may might must not no yes so too also
    about into over under again more most some any each other than only own same
    please maybe probably think want like need going gonna kind sort stuff thing
    things""".split()
)

_SPECIFICITY_PATTERN = re.compile(
    r"\d|%|"                                  # numbers and percentages
    r"\b(?:must|never|always|only|except)\b|"  # invariant language
    r"\b(?:e\.g\.|i\.e\.|for example|such as)\b|"  # concrete exemplification
    r"[A-Za-z_]+\([)A-Za-z_,* ]*|"             # function-ish tokens
    r"\b[a-z]+_[a-z_]+\b|"                     # snake_case identifiers
    r"\b(?:api|sql|http|json|oauth|postgres|redis|s3|grpc|rest|webhook)\b",
    re.IGNORECASE,
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _content_tokens(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9_']+", text.lower())
    return [token for token in tokens if token not in _STOPWORDS and len(token) > 2]


def is_deflection(text: str) -> bool:
    """True when the answer is a non-answer, regardless of politeness."""
    normalized = _normalize(text)
    if not normalized:
        return True
    stripped = re.sub(r"[^a-z0-9 ]", "", normalized).strip()
    if stripped in _DEFLECTIONS:
        return True
    # Very short answers made entirely of deflection words ("no idea, sorry").
    words = stripped.split()
    if len(words) <= 4 and words and all(
        word in _DEFLECTIONS or word in _STOPWORDS for word in words
    ):
        return True
    return False


def score_answer(text: str) -> float:
    """Score an answer's informativeness as a confidence credit.

    Deterministic tiers:
    - deflection or near-empty            -> WEAK_CREDIT  (0.35)
    - substantive (>= 4 content tokens)   -> SOLID_CREDIT (0.70)
    - substantive AND specific            -> RICH_CREDIT  (0.85)
      (specificity = numbers, invariant language, identifiers, examples,
       or >= 12 content tokens)
    """
    if is_deflection(text):
        return WEAK_CREDIT
    content = _content_tokens(text)
    if len(content) < 4:
        return WEAK_CREDIT
    specific = bool(_SPECIFICITY_PATTERN.search(text)) or len(content) >= 12
    return RICH_CREDIT if specific else SOLID_CREDIT


def credit_confidence(previous: float, answer_text: str) -> float:
    """Fold a new answer's credit into a domain's confidence.

    The domain confidence becomes at least the answer's score, and repeated
    substantive answers compound gently (never past 1.0). Weak answers never
    lower existing confidence.
    """
    score = score_answer(answer_text)
    try:
        prev = float(previous)
    except (TypeError, ValueError):
        prev = 0.0
    if score <= WEAK_CREDIT:
        return max(prev, min(1.0, prev + 0.05), WEAK_CREDIT if prev == 0.0 else prev)
    compounded = prev + (1.0 - prev) * 0.25
    return min(1.0, max(score, compounded))


__all__ = [
    "RICH_CREDIT",
    "SOLID_CREDIT",
    "WEAK_CREDIT",
    "credit_confidence",
    "is_deflection",
    "score_answer",
]
