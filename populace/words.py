"""One place that decides whether a keyword appears in a piece of text.

Ported verbatim from Alive, where matching a keyword as a raw substring
invented something false at least five separate times: "an hour" inside the
wage "five an hour" refused a complete hire, a short first name inside a longer
word rejected a valid description, and "till" inside "still" turned a man
paying back a round into a man confessing to robbing a register.

The rule is enforced rather than remembered: keyword lists go through
`contains` or `matcher`, and `tests/guards/test_words.py` fails the build if a
raw substring membership test against a keyword list appears anywhere.

Whole words are necessary and not always sufficient. "till" is a whole word in
"nothing moves till you've got the number", where it is the conjunction and not
a cash drawer, so an ambiguous noun also wants `owned`: something has to own it
before it counts.
"""

from __future__ import annotations

import re
from functools import lru_cache

# Words that can own the noun after them. The conjunction "till" never takes
# one; the cash drawer nearly always does.
DETERMINERS = (
    "the", "a", "an", "that", "this", "these", "those",
    "his", "her", "their", "my", "your", "our", "its",
)


SUFFIXES = ("ings", "ing", "ers", "er", "ed", "es", "s")


def stem(word: str) -> str:
    """A crude root for matching a word's common forms: "billing", "bills" and
    "bill" share one, as do "called" and "calls". Not linguistics; enough that
    a narrator's "billing" is heard as the facts' "bills"."""
    w = word.lower()
    for suffix in SUFFIXES:
        if w.endswith(suffix) and len(w) - len(suffix) >= 3:
            w = w[: -len(suffix)]
            break
    if len(w) >= 4 and w[-1] == w[-2] and w[-1] not in "lsz":
        w = w[:-1]                      # "stopp" -> "stop", but keep "bill", "pass"
    if w.endswith("e") and len(w) >= 4:
        w = w[:-1]                      # "restore" and "restoring" meet at "restor"
    return w


def _variant_body(word: str) -> str:
    root = stem(word)
    roots = sorted({re.escape(root), re.escape(root) + re.escape(root[-1])}, key=len, reverse=True)
    return rf"(?:{'|'.join(roots)})(?:e|ings|ing|ers|er|ed|es|s|d)?"


@lru_cache(maxsize=256)
def matcher(words: tuple[str, ...], owned: bool = False, variants: bool = False) -> re.Pattern[str]:
    """A compiled whole-word matcher for a keyword list.

    `owned` additionally requires a determiner or a possessive immediately
    before the word - "the till", "the shop's float" - which is what separates a
    cash drawer from the conjunction.

    `variants` also matches a word's common forms - "bill" finds "bills" and
    "billing", "call" finds "called" - still as whole words, so "bill" never
    finds "billion" and "call" never finds "recall".
    """
    if not words:
        return re.compile(r"(?!)")  # matches nothing
    if variants:
        body = "|".join(_variant_body(w) for w in words)
    else:
        body = "|".join(re.escape(w) for w in words)
    if not owned:
        return re.compile(rf"\b(?:{body})\b", re.IGNORECASE)
    owners = "|".join(re.escape(d) for d in DETERMINERS)
    return re.compile(
        rf"(?:\b(?:{owners})\b|\w+['’]s)\s+\b(?:{body})\b", re.IGNORECASE
    )


def contains(text: str, words, owned: bool = False, variants: bool = False) -> bool:
    """Does any of `words` appear in `text` as a whole word (or, with
    `variants`, in one of its common forms)?"""
    if not text:
        return False
    return matcher(tuple(words), owned, variants).search(text) is not None


def found(text: str, words, owned: bool = False, variants: bool = False) -> list[str]:
    """Which of `words` appear in `text` as whole words, in list order."""
    if not text:
        return []
    return [w for w in words if matcher((w,), owned, variants).search(text)]
