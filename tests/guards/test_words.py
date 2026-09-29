"""The shared whole-word matcher, and the guard that keeps everybody using it.

Ported from Alive, where matching a keyword as a raw substring invented
something false five times over (the list is in `populace/words.py`).

So the rule is enforced rather than remembered. `test_no_raw_substring_keyword_matching`
reads the source of every module and fails if a keyword list is tested with `in`
instead of going through `words.contains`.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

from populace import words as W

REPO = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = REPO / "populace"

# A name that looks like a keyword list: a plural or explicitly-named constant
# whose members are compared against free text.
KEYWORDY = ("WORDS", "PHRASES", "VERBS", "DENIALS", "CUES", "FORBIDDEN", "TERMS")


# -- the matcher itself ----------------------------------------------------


def test_a_keyword_inside_a_longer_word_is_not_a_match():
    for text in ("she was still there", "I distilled it", "wholly idealistic",
                 "registered post", "the hauling crew", "always late"):
        assert not W.contains(text, ("till", "deal", "register", "lin"))


def test_a_keyword_standing_on_its_own_is_a_match():
    assert W.contains("he had his hand in the till", ("till",))
    assert W.contains("the register is forty short", ("register",))
    assert W.contains("Straight up, no deal", ("deal",))


def test_matching_ignores_case_and_punctuation_around_the_word():
    assert W.contains("The Till was short.", ("till",))
    assert W.contains("...took it, obviously", ("took",))


def test_an_owned_word_needs_something_to_own_it():
    """"till" is a whole word in the conjunction too, which is how the second
    live false positive got in."""
    for text in ("nothing moves till you've got the number",
                 "wait till Friday", "we're here till six"):
        assert not W.contains(text, ("till",), owned=True)
    for text in ("he had his hand in the till", "counted the till at closing",
                 "Ana's till came up short", "money out of her till"):
        assert W.contains(text, ("till",), owned=True)


def test_found_reports_which_words_hit():
    assert W.found("he sells nothing and deals with nobody",
                   ("deal", "sells", "pill")) == ["sells"]
    assert W.found("an idealistic dealer", ("deal", "dealer")) == ["dealer"]


def test_an_empty_list_matches_nothing():
    assert not W.contains("anything at all", ())
    assert W.found("anything at all", ()) == []


# -- the guard -------------------------------------------------------------


def _keyword_names(tree: ast.Module) -> set[str]:
    """Module-level constants that are tuples/sets/lists of string literals."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        value = node.value
        if not isinstance(value, (ast.Tuple, ast.Set, ast.List)):
            continue
        if not value.elts or not all(
            isinstance(e, ast.Constant) and isinstance(e.value, str) for e in value.elts
        ):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id.isupper():
                names.add(target.id)
    return names


def _root_name(node: ast.AST) -> str | None:
    while isinstance(node, (ast.Attribute, ast.Subscript)):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _substring_offences(path: pathlib.Path) -> list[str]:
    """Every `<something> in <text>` where the something is a keyword list."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    keyword_lists = {n for n in _keyword_names(tree) if any(k in n for k in KEYWORDY)}
    offences: list[str] = []

    # `any(w in text for w in WORDS)` and `[w for w in WORDS if w in text]`
    for node in ast.walk(tree):
        if not isinstance(node, (ast.GeneratorExp, ast.ListComp, ast.SetComp)):
            continue
        iterated = {
            _root_name(gen.iter) for gen in node.generators
        } & keyword_lists
        if not iterated:
            continue
        for test in ast.walk(node):
            if isinstance(test, ast.Compare) and any(
                isinstance(op, ast.In) for op in test.ops
            ):
                offences.append(
                    f"{path.name}:{test.lineno}: "
                    f"{sorted(iterated)} matched with `in` instead of words.contains"
                )
    # `if TEXT in SOMEWORDS` written the other way round
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare) or not any(
            isinstance(op, ast.In) for op in node.ops
        ):
            continue
        for comparator in node.comparators:
            if _root_name(comparator) in keyword_lists and isinstance(
                node.left, ast.Constant
            ):
                offences.append(
                    f"{path.name}:{node.lineno}: literal tested against a keyword list"
                )
    return offences


def _sources() -> list[pathlib.Path]:
    return sorted(PACKAGE.rglob("*.py"))


def test_no_raw_substring_keyword_matching():
    """No keyword list is ever matched with a bare `in` against free text.

    If this fails, the fix is `populace.words.contains(text, THE_WORDS)` - not an
    exception here. Every previous instance of this pattern shipped a bug that
    put words in somebody's mouth.
    """
    offences: list[str] = []
    for path in _sources():
        offences.extend(_substring_offences(path))
    assert offences == [], "raw substring keyword matching:\n  " + "\n  ".join(offences)


def test_the_guard_can_actually_see_an_offence(tmp_path):
    """A guard nobody has watched fail is not a guard."""
    bad = tmp_path / "bad.py"
    bad.write_text(
        "CRIME_WORDS = (\"stole\", \"took\")\n"
        "def check(text):\n"
        "    return any(w in text for w in CRIME_WORDS)\n"
    , encoding="utf-8")
    assert _substring_offences(bad)

    good = tmp_path / "good.py"
    good.write_text(
        "from populace import words as W\n"
        "CRIME_WORDS = (\"stole\", \"took\")\n"
        "def check(text):\n"
        "    return W.contains(text, CRIME_WORDS)\n"
    , encoding="utf-8")
    assert _substring_offences(good) == []


def test_variants_match_the_common_forms_of_a_word():
    """The PC's retelling said "billing" and "called"; exact whole words missed
    both and reported an injection as left out."""
    from populace import words as W

    assert W.contains("its billing", ["bills"], variants=True)
    assert W.contains("a bill", ["billing"], variants=True)
    assert W.contains("residents called 24 times", ["call"], variants=True)
    assert W.contains("it was restored at ten", ["restore"], variants=True)
    assert W.contains("the line stopped", ["stop"], variants=True)
    assert W.stem("households") == W.stem("household")


def test_variants_stay_whole_words():
    from populace import words as W

    assert not W.contains("billion", ["bill"], variants=True)
    assert not W.contains("recall", ["call"], variants=True)
    assert not W.contains("its billing", ["bills"]), "without variants, still exact"
