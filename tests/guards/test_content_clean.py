"""populace ships none of Alive's world.

The brief is a repository clean of any game-specific content. Code was ported
from Alive function by function, and a ported docstring or example is exactly
where a resident's name would slip through, so this reads every file that
ships and fails on any of Alive's proper nouns.

The names themselves are not written here: the guard holds the first 16 hex
digits of each one's SHA-256 (single words and two-word names, case as
written), and hashes every word and every pair of adjacent words it reads.
"""

from __future__ import annotations

import hashlib
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[2]
SHIPPED = ("populace", "tests", "examples", "demo")
EXEMPT = {pathlib.Path(__file__).resolve()}

# Alive's setting, its residents' names, its places and its client, hashed.
FORBIDDEN = frozenset((
    "6135934f23d475bb",
    "983ea566852da4d9",
    "b48cde19e3b69408",
    "3ba5f6b575cd33e1",
    "51a70b09f4ac9589",
    "67085d681b2970f9",
    "d94af4ddf389f0d3",
    "95d5798c5815192d",
    "cb0d804cddaaa7d9",
    "2ddbedcf3fd4a461",
    "4bd76ef1a6bf8651",
    "23dd2e21a1bd47c8",
    "e3f395cb87ee4f8b",
    "6136ce1b6ce6fd78",
    "8ead7a2567d2a4b1",
    "f1d122510dbba1fe",
    "bee11462fe2d380c",
    "632561cb71d33e1e",
    "076bfa5c84399fe7",
    "ca82e4bdbf0d9464",
    "dcf77c4f64726cb4",
    "2b8ae95c6e03d742",
    "412666a8d238b719",
    "91f5c51e92a2ff52",
    "8eb6bf3ef2c6f6ce",
    "957cafedcf90e0e7",
    "2a02b2443f7985d8",
))
WORD = re.compile(r"\b\w+\b")


def digest(name: str) -> str:
    return hashlib.sha256(name.encode("utf-8")).hexdigest()[:16]


def _shipped_files() -> list[pathlib.Path]:
    out = []
    for top in SHIPPED:
        base = REPO / top
        if base.exists():
            out += [p for p in base.rglob("*") if p.is_file()
                    and p.suffix in {".py", ".json", ".md", ".txt"}
                    and p.resolve() not in EXEMPT]
    return sorted(out)


def offences_in(text: str, forbidden: frozenset[str] = FORBIDDEN) -> list[str]:
    words = WORD.findall(text)
    candidates = set(words) | {f"{a} {b}" for a, b in zip(words, words[1:])}
    return sorted(c for c in candidates if digest(c) in forbidden)


def test_nothing_that_ships_names_alive():
    found = []
    for path in _shipped_files():
        hits = offences_in(path.read_text(encoding="utf-8", errors="replace"))
        if hits:
            found.append(f"{path.relative_to(REPO)}: {', '.join(hits)}")
    assert found == [], "Alive's content in files that ship:\n  " + "\n  ".join(found)


def test_the_list_is_all_there():
    assert len(FORBIDDEN) == 27


def test_the_guard_can_actually_see_an_offence():
    planted = frozenset({digest("Zebulon"), digest("Grey Heron")})
    text = "She works at the Grey Heron on Zebulon Lane."
    assert offences_in(text, planted) == ["Grey Heron", "Zebulon"]
    assert offences_in("Zebulonian soup at the grey heron.", planted) == []
