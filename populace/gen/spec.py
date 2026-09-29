"""From a sentence to a town spec.

`parse_description` reads a description like "a suburb of 200 people with a
strip mall, a school and a factory" by keyword rules: it is deterministic,
free, and needs no model. `spec_from_model` asks the model for the same JSON
and falls back to the rules whenever the answer does not validate, so a bad
reply can never produce a town the rules would not.

Whatever the description leaves out, a town of that size still needs:
somewhere to buy food, somewhere to eat out, a park, and past a size a school,
a clinic and so on (`per_capita` in `data/place_kinds.json`). Those are added,
and the spec says which were asked for and which were added.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from dataclasses import asdict, dataclass, field
from typing import Any

from .. import words as W
from . import data as D

MIN_POPULATION = 5
MAX_POPULATION = 500

NUMBER_WORDS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "twelve": 12, "twenty": 20, "thirty": 30,
    "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    "hundred": 100,
}
# What a place is called when no number is given.
SIZE_WORDS = {
    "hamlet": 30, "village": 60, "neighbourhood": 120, "neighborhood": 120,
    "town": 150, "suburb": 200, "estate": 150, "city": 300,
}
PEOPLE_WORDS = r"(?:people|residents|inhabitants|souls|persons|folks?)"


class SpecError(ValueError):
    pass


@dataclass
class TownSpec:
    name: str
    seed: int
    description: str
    population: int
    places: list[dict[str, Any]] = field(default_factory=list)  # {kind, count, asked}
    culture_mix: dict[str, float] = field(default_factory=dict)
    employment_rate: float = 0.74
    commute_share: float = 0.3
    source: str = "rules"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "TownSpec":
        return TownSpec(
            name=str(d["name"]), seed=int(d["seed"]), description=str(d.get("description", "")),
            population=int(d["population"]), places=[dict(p) for p in d.get("places", [])],
            culture_mix=dict(d.get("culture_mix", {})),
            employment_rate=float(d.get("employment_rate", 0.74)),
            commute_share=float(d.get("commute_share", 0.3)),
            source=str(d.get("source", "rules")),
        )

    def count(self, kind: str) -> int:
        return sum(int(p["count"]) for p in self.places if p["kind"] == kind)

    def validate(self) -> list[str]:
        problems = []
        known = D.kinds()
        if not MIN_POPULATION <= self.population <= MAX_POPULATION:
            problems.append(f"population {self.population} is outside "
                            f"{MIN_POPULATION}..{MAX_POPULATION}")
        for p in self.places:
            if p.get("kind") not in known or known[p["kind"]].get("residential"):
                problems.append(f"unknown or residential place kind {p.get('kind')!r}")
            if not 0 < int(p.get("count", 0)) <= 20:
                problems.append(f"{p.get('kind')}: count {p.get('count')} is not 1..20")
        if not self.count("grocery") and not self.count("convenience_store"):
            problems.append("a town needs somewhere to buy food")
        if abs(sum(self.culture_mix.values()) - 1.0) > 0.01:
            problems.append("culture mix does not sum to 1")
        return problems


def _rng(seed: int, text: str) -> random.Random:
    digest = hashlib.sha256(f"{seed}|{text.strip().lower()}".encode()).hexdigest()
    return random.Random(int(digest[:16], 16))


def _number(token: str) -> int | None:
    token = token.lower().replace(",", "")
    if token.isdigit():
        return int(token)
    return NUMBER_WORDS.get(token)


def read_population(text: str) -> int | None:
    """The first number of people the text names, or a size word's default."""
    m = re.search(rf"\b(\d[\d,]*)\s+{PEOPLE_WORDS}\b", text, re.IGNORECASE) or \
        re.search(r"\b(?:of|with|about|around|roughly|population)\s+(\d[\d,]*)\b", text, re.IGNORECASE)
    if m:
        return int(m.group(1).replace(",", ""))
    m = re.search(rf"\b({'|'.join(NUMBER_WORDS)})\s+(?:hundred\s+)?{PEOPLE_WORDS}\b", text,
                  re.IGNORECASE)
    if m:
        n = _number(m.group(1)) or 0
        return n * 100 if "hundred" in m.group(0).lower() and n < 100 else n
    for word, size in SIZE_WORDS.items():
        if W.contains(text, [word]):
            return size
    return None


def read_name(text: str) -> str | None:
    m = re.search(r"\b(?:called|named)\s+((?:[A-Z][\w'-]*)(?:\s+[A-Z][\w'-]*){0,2})", text)
    return m.group(1).strip() if m else None


def _count_before(text: str, alias: str) -> int:
    m = re.search(rf"\b(\d+|{'|'.join(NUMBER_WORDS)})\s+(?:[a-z-]+\s+)?{re.escape(alias)}\b",
                  text, re.IGNORECASE)
    if m:
        n = _number(m.group(1))
        return max(1, min(20, n or 1))
    return 1


def read_places(text: str) -> dict[str, int]:
    """Kinds the text asks for, with counts. Composites expand to their parts."""
    asked: dict[str, int] = {}
    lowered = text.lower()
    for phrase, parts in D.composites().items():
        if W.contains(lowered, [phrase]):
            for kind in parts:
                asked[kind] = max(asked.get(kind, 0), 1)
            lowered = re.sub(rf"\b{re.escape(phrase)}\b", " ", lowered)
    for kind, spec in D.kinds().items():
        if spec.get("residential"):
            continue
        # Longest alias first, so "high school" is read before "school".
        for alias in sorted(spec.get("aliases", []), key=len, reverse=True):
            if W.contains(lowered, [alias]):
                asked[kind] = max(asked.get(kind, 0), _count_before(lowered, alias))
                lowered = re.sub(rf"\b{re.escape(alias)}\b", " ", lowered)
                break
    return asked


def add_what_a_town_needs(population: int, asked: dict[str, int]) -> dict[str, int]:
    """Kinds a town of this size has whether or not anybody mentioned them."""
    out = dict(asked)
    for kind, spec in D.kinds().items():
        rule = spec.get("per_capita")
        if not rule or population < int(rule["min_population"]):
            continue
        wanted = max(1, population // int(rule["per"]))
        out[kind] = max(out.get(kind, 0), wanted)
    return out


def parse_description(description: str, seed: int = 0,
                      overrides: dict[str, Any] | None = None) -> TownSpec:
    overrides = dict(overrides or {})
    rng = _rng(seed, description)
    population = int(overrides.pop("population", None) or read_population(description) or 100)
    population = max(MIN_POPULATION, min(MAX_POPULATION, population))
    name = overrides.pop("name", None) or read_name(description) or \
        rng.choice(D.load("geography")["town_names"])
    asked = read_places(description)
    wanted = add_what_a_town_needs(population, asked)
    places = [{"kind": k, "count": int(wanted[k]), "asked": k in asked} for k in sorted(wanted)]
    mix = overrides.pop("culture_mix", None) or D.load("households")["culture_mix_default"]
    total = float(sum(mix.values()))
    spec = TownSpec(
        name=str(name), seed=int(seed), description=description, population=population,
        places=places, culture_mix={k: v / total for k, v in sorted(mix.items())},
        source="rules",
    )
    for key, value in overrides.items():
        if not hasattr(spec, key):
            raise SpecError(f"unknown override {key!r}")
        setattr(spec, key, value)
    problems = spec.validate()
    if problems:
        raise SpecError("; ".join(problems))
    return spec


# -- the model path -----------------------------------------------------------------

SPEC_SYSTEM = """\
You read a one-line description of a town and say what is in it, as JSON.

Reply with one JSON object and nothing else:
{"name": the town's name if the description gives one, else null,
 "population": how many people live there, a whole number,
 "places": [{"kind": one of the kinds listed below, "count": how many}]}

Only list places the description mentions or clearly implies. Use only these
kinds: @KINDS@"""


def spec_prompt(description: str) -> tuple[list[dict], list[dict]]:
    kinds = ", ".join(k for k, v in sorted(D.kinds().items())
                      if not v.get("residential") and k != "offtown")
    system = [{"type": "text", "text": SPEC_SYSTEM.replace("@KINDS@", kinds)}]
    return system, [{"role": "user", "content": f"Description: {description}"}]


def merge_model_answer(rules: TownSpec, answer: dict[str, Any]) -> TownSpec | None:
    """The model's reading on top of the rules', or None if it does not hold up."""
    try:
        population = int(answer.get("population") or rules.population)
        asked: dict[str, int] = {}
        for p in answer.get("places") or []:
            kind = str(p.get("kind"))
            if kind not in D.kinds() or D.kinds()[kind].get("residential") or kind == "offtown":
                return None
            asked[kind] = max(asked.get(kind, 0), max(1, min(20, int(p.get("count", 1)))))
    except (TypeError, ValueError):
        return None
    population = max(MIN_POPULATION, min(MAX_POPULATION, population))
    wanted = add_what_a_town_needs(population, asked)
    spec = TownSpec(
        name=str(answer.get("name") or rules.name), seed=rules.seed,
        description=rules.description, population=population,
        places=[{"kind": k, "count": int(wanted[k]), "asked": k in asked} for k in sorted(wanted)],
        culture_mix=rules.culture_mix, source="model",
    )
    return None if spec.validate() else spec


async def spec_from_model(description: str, seed: int, runner,
                          overrides: dict[str, Any] | None = None) -> TownSpec:
    from ..sim.actions import extract_json

    rules = parse_description(description, seed, overrides)
    if overrides and any(k in overrides for k in ("population", "places")):
        return rules  # the caller said; the model is not asked to second-guess it
    system, messages = spec_prompt(description)
    result = await runner.call("town_spec", system, messages, {
        "char_id": "_town", "mock_state": {"rules_spec": rules.to_dict()}, "mock_no_garbage": True,
    })
    if not result.ok:
        return rules
    answer = extract_json(result.text)
    merged = merge_model_answer(rules, answer) if isinstance(answer, dict) else None
    if merged is None:
        return rules
    if overrides and overrides.get("name"):
        merged.name = str(overrides["name"])
    return merged


def _register_mock() -> None:
    from ..providers.mock import handler

    @handler("town_spec")
    def _mock_town_spec(rng, state, meta):
        rules = state.get("rules_spec") or {}
        return json.dumps({
            "name": None, "population": rules.get("population"),
            "places": [{"kind": p["kind"], "count": p["count"]}
                       for p in rules.get("places", []) if p.get("asked")],
        })


_register_mock()
