"""Every name a resident reads has been through the funnel.

In Alive "nobody knows your name until you give it" was fixed five times, each
fix correct and each leaving the next place untouched: the dialogue prompt,
the memory it was built from, ten sections of the decision prompt, an event's
detail string. Two checks here: a static one over the prompt builders, and a
sweep that builds every resident's prompt in a generated town and looks for any
name the reader was never given.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
BUILDERS = [REPO / "populace" / "prompt" / "blocks.py", REPO / "populace" / "sim" / "phone.py"]
# `.name` may be read directly only off these: a place, a thing, the reader
# themselves, the town. Anything else is a person and goes through known_as.
ALLOWED = re.compile(r"^(place|thing|t|resident|town|world\.places\[.*\]|town\.world\.places\[.*\])$")


def offences(path: pathlib.Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "name":
            base = ast.unparse(node.value)
            if not ALLOWED.match(base):
                found.append(f"{path.name}:{node.lineno}: {base}.name")
    return found


def test_no_person_is_named_outside_the_funnel():
    found = [o for path in BUILDERS for o in offences(path)]
    assert found == [], "\n".join(found)


def test_the_guard_can_see_an_offence(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text("def f(other):\n    return f'{other.name} is here'\n", encoding="utf-8")
    assert offences(bad)


DESCRIPTION = "a suburb of 200 people with a strip mall, a school and a factory"


def _suburb(path):
    import asyncio
    from populace.gen.generate import generate

    town, _ = asyncio.run(generate(DESCRIPTION, path, seed=7))
    return town


@pytest.fixture(scope="module")
def suburb(tmp_path_factory):
    return _suburb(tmp_path_factory.mktemp("t") / "t")


def _tokens(text: str) -> list[str]:
    return [t for t in re.split(r"[^\w]+|_", text.lower()) if t]


def stranger_leaks(town) -> list[str]:
    """Seat the town in crowds of eight at its public places, build every
    reader's decision prompt and a dialogue prompt with a stranger, and look
    for any stranger's given and family name side by side in any form: a
    display name, or an id like `mariama_boateng`. The first live day found the
    model reading names out of ids; a sweep of display names alone missed it."""
    from populace.prompt.blocks import build_decision_prompt
    from populace.sim.dialogue import ConversationResult, speaker_prompt

    public = sorted(pid for pid, p in town.world.places.items() if p.public)
    ids = sorted(town.residents)
    for n, rid in enumerate(ids):
        town.world.place(rid, public[(n // 8) % len(public)])
    leaks = []
    for rid in ids:
        r = town.residents[rid]
        here = town.world.location_of(rid)
        strangers = [o for o in town.world.occupants(here) if o != rid and not r.knows_name(o)]
        system, messages, _ = build_decision_prompt(r, town, [])
        texts = [system[1]["text"], messages[0]["content"]]
        if strangers:
            other = town.residents[strangers[0]]
            texts.append(speaker_prompt(r, other, town, ConversationResult(rid, other.id, here)))
        tokens = _tokens("\n".join(texts))
        pairs = set(zip(tokens, tokens[1:]))
        for sid in strangers:
            given, *_, family = _tokens(town.residents[sid].name)
            if (given, family) in pairs:
                leaks.append(f"{rid} reads {town.residents[sid].name}")
    return leaks


def test_no_prompt_in_a_whole_town_names_a_stranger(suburb):
    leaks = stranger_leaks(suburb)
    assert leaks == [], "\n".join(leaks[:10])


def test_the_sweep_catches_names_carried_in_ids(tmp_path, monkeypatch):
    """Populace's first scheme, and Alive's: ids made from names."""
    from populace.gen import skeleton

    monkeypatch.setattr(skeleton, "resident_id", lambda n, given, family: skeleton.slug(f"{given}_{family}"))
    leaks = stranger_leaks(_suburb(tmp_path / "old"))
    assert leaks, "the sweep never fired on name-built ids"


def test_ids_say_nothing_about_the_person(suburb):
    for rid, r in suburb.residents.items():
        assert re.fullmatch(r"r\d{3,}", rid), rid
