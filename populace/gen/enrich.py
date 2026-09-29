"""Persona prose: who somebody is, how they talk, what they hide.

The skeleton gives each resident a name, an age, a household, a job, a home,
their ties and what they look like. This writes the rest, five residents per
`chargen` call, from exactly those facts:

    personality, speech_style, backstory, public_bio, secret, long_term_goal,
    current_goals, tastes {likes, dislikes}, tells {warm, cold},
    signature_phrases, forbidden_phrases, gossip

Every answer is validated before it is kept: required keys and types, length
limits, a gossip disposition from the known three, no capitalised name that is
not somebody in the batch or their own ties, and no public bio that gives away
the person's own secret (Alive's `leak_check`). A batch that fails is asked
once more; a person who fails twice is filled from templates and marked
`source: template`, and the report counts them.

Each finished batch is cached under `<town>/cache/enrich/`, so generating a
200-person town on a laptop can be stopped and resumed without paying for a
batch twice.

In mock mode the same prompt goes through the same runner and the mock answers
from `data/personas.json`, so the validator and the cache run for free.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import random
import re
from pathlib import Path
from typing import Any

from .. import words as W
from ..providers.mock import handler
from ..sim.actions import extract_json
from ..sim.events import leak_check
from ..state.town import Town
from . import data as D

DISPOSITIONS = ("talker", "confider", "keeper")
REQUIRED = {
    "personality": (str, 12, 300),
    "speech_style": (str, 8, 240),
    "backstory": (str, 20, 600),
    "public_bio": (str, 12, 300),
    "secret": (str, 12, 300),
    "long_term_goal": (str, 8, 240),
}

ENRICH_SYSTEM = """\
You write short character sheets for ordinary people who live in a small town.
Each person is a resident of a life simulation: another model will play them,
so what you write has to be specific enough to act on.

Write from the facts you are given and never contradict them: name, age, job,
household, where they live, and the people they know. Ordinary lives only: work,
money, family, neighbours, health, small ambitions and small shames. No crime
bosses, no celebrities, no real places or brands. A secret is something human
that would matter to one or two people if it came out.

The only people you may name are the people listed in this request. Do not
invent other named people.

Reply with one JSON object and nothing else:
{"people": [{"id": the id you were given,
  "personality": two sentences on how they behave, especially under pressure,
  "speech_style": one or two sentences on how they talk,
  "backstory": two or three sentences,
  "public_bio": one sentence anybody in town could say about them,
  "secret": one sentence,
  "long_term_goal": one sentence,
  "current_goals": one or two short things they are trying to do this week,
  "tastes": {"likes": three to five short things, "dislikes": two or three},
  "tells": {"warm": what they do when they like you, "cold": what they do when they do not},
  "signature_phrases": three short phrases they really say,
  "forbidden_phrases": three phrases they would never say,
  "gossip": "talker" (passes news on freely) | "confider" (tells one trusted person) | "keeper" (keeps things to themself)}]}"""


def batch_payload(town: Town, ids: list[str]) -> dict[str, Any]:
    people = []
    for rid in ids:
        r = town.residents[rid]
        hh = town.world.households.get(r.household, {})
        home = town.world.places[r.home]
        job = r.job
        work = town.world.places[job.workplace].name if job else None
        people.append({
            "id": rid, "name": r.name, "age": r.age,
            "gender": r.persona.get("gender"),
            "status": r.persona.get("status"),
            "job": f"{job.title} at {work}" if job else None,
            "home": f"{home.name}, {'a flat in a shared building' if home.kind == 'apartment_building' else 'a house'}",
            "household": [
                {"name": town.residents[m].name, "relation": r.relationships[m].label}
                for m in hh.get("members", []) if m != rid and m in r.relationships
            ] + [{"name": d["name"], "relation": f"child, age {d['age']}"} for d in hh.get("dependents", [])],
            "knows": [
                {"name": town.residents[o].name, "relation": rel.label,
                 "feeling": "warm" if rel.sentiment >= 3 else "cool" if rel.sentiment <= -1 else "neutral"}
                for o, rel in sorted(r.relationships.items())
                if town.residents[o].household != r.household
            ][:6],
            "looks": r.persona.get("descriptor", ""),
        })
    return {"town": {"name": town.name, "description": town.spec.get("description", "")},
            "people": people}


def _allowed_names(town: Town, ids: list[str]) -> set[str]:
    allowed: set[str] = set()
    for rid in ids:
        r = town.residents[rid]
        allowed.update(r.name.split())
        for oid in r.relationships:
            allowed.update(town.residents[oid].name.split())
        for d in town.world.households.get(r.household, {}).get("dependents", []):
            allowed.update(d["name"].split())
    return allowed


def _as_list(value: Any) -> Any:
    """A sentence where a list belongs becomes a list, not a refusal."""
    if isinstance(value, str):
        parts = [p.strip(" .;") for p in re.split(r";|\n|,(?![^()]*\))", value) if p.strip(" .;")]
        return parts or [value]
    return value


def normalise_sheet(sheet: Any) -> Any:
    """Forgive shape, never content. A small model writes `current_goals` as one
    sentence, or `likes` as a comma-separated string; that is the same answer
    in the wrong container, and refusing it threw away ten good sheets in the
    first live run."""
    if not isinstance(sheet, dict):
        return sheet
    out = dict(sheet)
    if isinstance(out.get("current_goals"), str):
        out["current_goals"] = [out["current_goals"].strip()]
    for key in ("signature_phrases", "forbidden_phrases"):
        out[key] = _as_list(out.get(key))
    tastes = out.get("tastes")
    if isinstance(tastes, dict):
        out["tastes"] = {k: _as_list(v) for k, v in tastes.items()}
    if isinstance(out.get("gossip"), str):
        out["gossip"] = out["gossip"].strip().lower()
    return out


def validate_person(town: Town, rid: str, sheet: Any, allowed: set[str]) -> list[str]:
    """Problems with one person's sheet; an empty list means keep it."""
    if not isinstance(sheet, dict):
        return ["not an object"]
    problems = []
    for key, (kind, lo, hi) in REQUIRED.items():
        value = sheet.get(key)
        if not isinstance(value, kind) or not lo <= len(value.strip()) <= hi:
            problems.append(f"{key} missing or the wrong length")
    for key in ("signature_phrases", "forbidden_phrases"):
        value = sheet.get(key)
        if not isinstance(value, list) or not 2 <= len(value) <= 6 \
                or not all(isinstance(v, str) and 0 < len(v) <= 60 for v in value):
            problems.append(f"{key} must be two to six short phrases")
    goals = sheet.get("current_goals")
    if not isinstance(goals, list) or not 1 <= len(goals) <= 3 \
            or not all(isinstance(g, str) and 3 <= len(g) <= 160 for g in goals):
        problems.append("current_goals must be one to three short goals")
    tastes = sheet.get("tastes")
    if not isinstance(tastes, dict) or not isinstance(tastes.get("likes"), list) \
            or not isinstance(tastes.get("dislikes"), list):
        problems.append("tastes must have likes and dislikes lists")
    tells = sheet.get("tells")
    if not isinstance(tells, dict) or not isinstance(tells.get("warm"), str) \
            or not isinstance(tells.get("cold"), str):
        problems.append("tells must have warm and cold")
    if sheet.get("gossip") not in DISPOSITIONS:
        problems.append("gossip must be talker, confider or keeper")
    for key in REQUIRED:
        sentences = [x.strip().lower() for x in re.split(r"(?<=[.!?])\s+", str(sheet.get(key, "")))
                     if x.strip()]
        if len(sentences) != len(set(sentences)):
            problems.append(f"{key} says the same sentence twice")
    if problems:
        return problems
    # Names: every capitalised word that is somebody in this town must be
    # somebody this person actually knows of.
    prose = " ".join(str(sheet.get(k, "")) for k in REQUIRED)
    for rid_named in town.names.find(prose):
        named = town.residents[rid_named]
        if not set(named.name.split()) & allowed:
            problems.append(f"names {named.name}, who is nobody they know")
    if leak_check(sheet["public_bio"], {rid: sheet["secret"]}):
        problems.append("the public bio gives away the secret")
    return problems


def apply_sheet(town: Town, rid: str, sheet: dict[str, Any], source: str) -> None:
    r = town.residents[rid]
    for key in REQUIRED:
        r.persona[key] = sheet[key].strip()
    r.persona["tastes"] = {"likes": [str(x) for x in sheet["tastes"]["likes"]][:5],
                           "dislikes": [str(x) for x in sheet["tastes"]["dislikes"]][:3]}
    r.persona["tells"] = {"warm": sheet["tells"]["warm"], "cold": sheet["tells"]["cold"]}
    r.persona["signature_phrases"] = [str(x) for x in sheet["signature_phrases"]][:3]
    r.persona["forbidden_phrases"] = [str(x) for x in sheet["forbidden_phrases"]][:5]
    r.persona["gossip"] = sheet["gossip"]
    r.persona["source"] = source
    r.goals_active = [str(g) for g in sheet["current_goals"]][:2]
    town.touch(rid)


# -- templates: the mock's answer, and the fallback for a person who fails twice ----


GROUP_OF_STATUS = {
    "pupil": "pupil", "student": "student", "worker": "worker", "retired": "retired",
    "between_jobs": "home", "homemaker": "home", "carer": "home", "unable_to_work": "home",
}
_SLOT = re.compile(r"{(\w+)}")


def group_of(resident) -> str:
    return GROUP_OF_STATUS.get(resident.persona.get("status", ""), "worker")


def slots_for(town: Town, rid: str, rng: random.Random) -> dict[str, str]:
    """What a template may mention about this person's own life."""
    r = town.residents[rid]
    first = lambda oid: town.residents[oid].name.split()[0]
    by_label: dict[str, list[str]] = {}
    for oid, rel in sorted(r.relationships.items()):
        by_label.setdefault(rel.label, []).append(oid)

    def pick(*labels: str) -> str | None:
        pool = [oid for label in labels for oid in by_label.get(label, [])]
        return first(rng.choice(pool)) if pool else None

    slots: dict[str, str | None] = {
        "partner": pick("wife", "husband", "partner"),
        "boss": pick("boss"),
        "coworker": pick("coworker", "works for me"),
        "friend": pick("old friend", "friend", "drinking buddy", "school friend"),
        "neighbour": pick("neighbour"),
        "relative": pick("cousin", "sister", "brother", "sibling", "mum", "dad", "parent",
                         "son", "daughter", "child"),
        "landlord": pick("landlord"),
        "parent": next((label for label in ("mum", "dad", "parent") if label in by_label), None),
        "town": town.name,
        "street": town.world.places[r.home].street or None,
        "weekday": rng.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]),
        "amount": str(rng.choice([40, 60, 80, 120, 150, 200, 300, 450, 600, 900, 1200])),
        "years": str(rng.randint(2, 25)),
    }
    kids = [d["name"].split()[0] for d in town.world.households.get(r.household, {}).get("dependents", [])]
    kids += [first(o) for o in by_label.get("son", []) + by_label.get("daughter", []) + by_label.get("child", [])]
    slots["kid"] = rng.choice(kids) if kids else None
    if r.job:
        place = town.world.places[r.job.workplace]
        offtown = town.world.is_offtown(r.job.workplace)
        slots["workplace"] = "work" if offtown else place.name
        slots["job"] = r.job.title
        slots["job_phrase"] = f"work as a {r.job.title}" if offtown else f"a job at {place.name}"
    school = next((town.world.places[e.location_id].name for e in r.schedule
                   if e.activity == "school" and not town.world.is_offtown(e.location_id)), None)
    slots["school"] = school or "school"
    return {k: v for k, v in slots.items() if v}


def fill(rng: random.Random, pool: list[str], slots: dict[str, str]) -> str:
    """A template from the pool whose every slot this person can fill.

    Every pool holds at least one template whose slots anybody has, so the
    last resort should never be reached. If it is, the slot is left visible as
    "[name]" rather than papered over, and a test looks for exactly that.
    """
    usable = [t for t in pool if set(_SLOT.findall(t)) <= set(slots)]
    if usable:
        return rng.choice(usable).format(**slots)
    return rng.choice(pool).format_map(_Missing(slots))


class _Missing(dict):
    def __missing__(self, key):
        return f"[{key}]"


def template_sheet(town: Town, rid: str, rng: random.Random) -> dict[str, Any]:
    """A complete sheet from the bundled pools, fitted to this person's life:
    a pupil gets a pupil's backstory, secret and wants; a retired person a
    retired person's; and the slots are their own ties, work and children."""
    P = D.load("personas")
    G = P["grouped"]
    r = town.residents[rid]
    group = group_of(r)
    slots = slots_for(town, rid, rng)
    status = r.persona.get("status")
    street = slots.get("street", "their street")
    job = r.job
    if status == "retired":
        bio = f"{r.name} is retired and has lived on {street} for years."
    elif status == "pupil":
        bio = f"{r.name} goes to {slots['school']} and lives on {street}."
    elif status == "student":
        bio = f"{r.name} is studying in the city and lives on {street}."
    elif job:
        article = "an" if job.title[:1].lower() in "aeiou" else "a"
        if town.world.is_offtown(job.workplace):
            where = "" if "city" in job.title else " in the city"
        else:
            where = f" at {town.world.places[job.workplace].name}"
        bio = f"{r.name} works as {article} {job.title}{where}."
    elif status == "between_jobs":
        bio = f"{r.name} lives on {street} and is between jobs."
    elif status == "carer":
        bio = f"{r.name} lives on {street} and looks after family full time."
    elif status == "homemaker":
        bio = f"{r.name} lives on {street} and runs a busy household."
    else:
        bio = f"{r.name} lives on {street} and doesn't work at the moment."
    if r.rent and r.money < r.rent["amount"]:
        goals = ["Find the rent before it is due."]
    else:
        goals = [fill(rng, G["weekly"][group], slots)]
    personality = rng.sample(P["personality"], 2)
    pupil = group == "pupil"
    return {
        "personality": " ".join(personality),
        "speech_style": rng.choice(P["speech_style"]),
        "backstory": fill(rng, G["backstory"][group], slots),
        "public_bio": bio,
        "secret": fill(rng, G["secret"][group], slots),
        "long_term_goal": fill(rng, G["long_term_goal"][group], slots),
        "current_goals": goals,
        "tastes": {"likes": rng.sample(P["likes_pupil"] if pupil else P["likes"], 4),
                   "dislikes": rng.sample(P["dislikes_pupil"] if pupil else P["dislikes"], 2)},
        "tells": {"warm": rng.choice(P["tells_warm"]), "cold": rng.choice(P["tells_cold"])},
        "signature_phrases": rng.sample(P["signature_phrases"], 3),
        "forbidden_phrases": rng.sample(P["forbidden_pool"], 4),
        "gossip": rng.choices(DISPOSITIONS, [0.25, 0.55, 0.2])[0],
    }


def _person_rng(town: Town, rid: str, salt: str = "") -> random.Random:
    return random.Random(int(hashlib.sha256(f"{town.seed}|persona|{rid}|{salt}".encode()).hexdigest()[:12], 16))


# The mock reads the batch from its mock_state and answers with templates. The
# town itself is not in the call, so the mock gets what it needs passed in.
_MOCK_TOWNS: dict[str, Town] = {}


@handler("chargen")
def _mock_chargen(rng, state, meta):
    town = _MOCK_TOWNS.get(state.get("town_key", ""))
    if town is None:
        return {"people": []}
    # A retry is told what was wrong, so it answers differently.
    salt = "" if meta.get("attempt", 1) == 1 else f"retry{meta['attempt']}"
    return {"people": [dict(template_sheet(town, rid, _person_rng(town, rid, salt)), id=rid)
                       for rid in state.get("ids", [])]}


def _norm_text(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower().rstrip("."))


def _clash(a: dict[str, Any], b: dict[str, Any]) -> str | None:
    for key in ("secret", "long_term_goal"):
        if _norm_text(a.get(key)) == _norm_text(b.get(key)):
            return key.replace("_", " ")
    shared = {_norm_text(x) for x in a.get("signature_phrases", [])} & \
        {_norm_text(x) for x in b.get("signature_phrases", [])}
    if len(shared) >= 2:
        return "catchphrases"
    return None


def variety_cap(population: int) -> int:
    """How many residents may share one secret, goal or weekly goal."""
    return max(2, -(-population * 2 // 100))


def repeated(town: Town) -> dict[str, list[tuple[str, int]]]:
    """Texts held by more residents than the cap allows, per field."""
    cap = variety_cap(len(town.residents))
    out: dict[str, list[tuple[str, int]]] = {}
    fields = {
        "secret": lambda r: r.persona.get("secret"),
        "long_term_goal": lambda r: r.persona.get("long_term_goal"),
        "weekly goal": lambda r: (r.goals_active or [""])[0],
        "catchphrases": lambda r: " | ".join(sorted(r.persona.get("signature_phrases", []))),
    }
    for name, get in fields.items():
        counts: dict[str, int] = {}
        for r in town.residents.values():
            text = _norm_text(get(r))
            if text:
                counts[text] = counts.get(text, 0) + 1
        over = sorted(((t, n) for t, n in counts.items() if n > cap), key=lambda x: -x[1])
        if over:
            out[name] = over
    return out


def enforce_variety(town: Town) -> int:
    """Redraw, from the person's own pool, any text more of the town shares
    than the cap allows. Deterministic: ids in order, first come keeps it."""
    cap = variety_cap(len(town.residents))
    P = D.load("personas")
    redrawn = 0
    for key, pool_name in (("secret", "secret"), ("long_term_goal", "long_term_goal"),
                           ("weekly", "weekly"), ("phrases", None)):
        counts: dict[str, int] = {}
        for rid in sorted(town.residents):
            r = town.residents[rid]
            current = (r.goals_active or [""])[0] if key == "weekly" else \
                " | ".join(sorted(r.persona.get("signature_phrases", []))) if key == "phrases" else \
                r.persona.get(key, "")
            text = _norm_text(current)
            if counts.get(text, 0) < cap:
                counts[text] = counts.get(text, 0) + 1
                continue
            rng = _person_rng(town, rid, f"variety-{key}")
            for attempt in range(40):
                if key == "phrases":
                    candidate = rng.sample(P["signature_phrases"], 3)
                    text = _norm_text(" | ".join(sorted(candidate)))
                else:
                    candidate = fill(rng, P["grouped"][pool_name][group_of(r)], slots_for(town, rid, rng))
                    text = _norm_text(candidate)
                if counts.get(text, 0) < cap:
                    break
            counts[text] = counts.get(text, 0) + 1
            if key == "phrases":
                r.persona["signature_phrases"] = candidate
            elif key == "weekly":
                r.goals_active = [candidate] + r.goals_active[1:]
            else:
                r.persona[key] = candidate
            r.persona.setdefault("redrawn", []).append(key)
            town.touch(rid)
            redrawn += 1
    return redrawn


# -- the pass --------------------------------------------------------------------------


def _cache_key(town: Town, ids: list[str], mock: bool) -> str:
    key = json.dumps([town.seed, town.name, town.spec.get("description"), ids, mock])
    return hashlib.sha256(key.encode()).hexdigest()[:16]


async def enrich(town: Town, runner, cache_dir: Path | None = None,
                 on_batch=None) -> dict[str, int]:
    """Fill every resident's persona. Returns counts by source."""
    size = int(town.config.gen["enrich_batch"])
    ids = sorted(town.residents)
    batches = [ids[i:i + size] for i in range(0, len(ids), size)]
    town_key = f"{town.seed}|{town.name}"
    _MOCK_TOWNS[town_key] = town
    counts = {"model": 0, "template": 0, "cached": 0, "mock": 0, "redrawn_for_variety": 0}
    system = [{"type": "text", "text": ENRICH_SYSTEM}]

    async def one(index: int, batch: list[str]) -> None:
        path = cache_dir / f"{_cache_key(town, batch, runner.mock)}.json" if cache_dir else None
        if path and path.exists():
            cached = json.loads(path.read_text(encoding="utf-8"))
            for rid, (sheet, source) in cached.items():
                apply_sheet(town, rid, sheet, source)
            counts["cached"] += len(cached)
            if on_batch:
                on_batch(index, len(batches))
            return
        allowed = _allowed_names(town, batch)
        payload = batch_payload(town, batch)
        todo = list(batch)
        kept: dict[str, tuple[dict[str, Any], str]] = {}
        messages = [{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]
        for attempt in (1, 2):
            if not todo:
                break
            result = await runner.call("chargen", system, messages, {
                "char_id": f"_batch{index}", "attempt": attempt, "mock_no_garbage": True,
                "mock_state": {"town_key": town_key, "ids": todo},
            })
            answer = extract_json(result.text) if result.ok else None
            people = answer.get("people") if isinstance(answer, dict) else None
            by_id = {p.get("id"): normalise_sheet(p) for p in people or [] if isinstance(p, dict)}
            still: dict[str, list[str]] = {}
            for rid in todo:
                sheet = by_id.get(rid)
                problems = ["missing from the reply"] if sheet is None else \
                    validate_person(town, rid, sheet, allowed)
                if problems:
                    still[rid] = problems
                else:
                    kept[rid] = (sheet, "mock" if runner.mock else "model")
            # Within one batch: two people with the same secret or goal, or
            # sharing catchphrases, is one person written twice. The later id
            # is refused and asked again.
            for rid in sorted(kept):
                if rid not in batch or kept[rid][1] == "template":
                    continue
                for other in sorted(kept):
                    if other >= rid or other not in batch:
                        continue
                    clash = _clash(kept[rid][0], kept[other][0])
                    if clash:
                        still[rid] = [f"repeats {other}'s {clash}; write this person differently"]
                        del kept[rid]
                        break
            todo = list(still)
            # The retry says what was wrong. Sending the same prompt again to a
            # server that decodes deterministically gets the same answer back,
            # which is what the first live run did.
            if todo:
                refused = "\n".join(f"- {rid}: {'; '.join(p)}" for rid, p in still.items())
                messages = messages + [
                    {"role": "assistant", "content": result.text or "(no reply)"},
                    {"role": "user", "content": (
                        "These sheets could not be used:\n" + refused + "\n\nReply with one JSON "
                        'object {"people": [...]} containing corrected sheets for exactly those '
                        "ids, and nothing else.")},
                ]
        for rid in todo:
            kept[rid] = (template_sheet(town, rid, _person_rng(town, rid, "fallback")), "template")
        for rid, (sheet, source) in kept.items():
            apply_sheet(town, rid, sheet, source)
            counts[source] += 1
        # Only answers that passed are cached. A template stand-in is not an
        # answer: caching it would lock that batch out of the model for good.
        if path and len(kept) == len(batch) and all(src != "template" for _, src in kept.values()):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(kept, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        if on_batch:
            on_batch(index, len(batches))

    # Bounded by the runner's own concurrency; applied in batch order.
    await asyncio.gather(*(one(i, b) for i, b in enumerate(batches)))
    _MOCK_TOWNS.pop(town_key, None)
    counts["redrawn_for_variety"] = enforce_variety(town)
    return counts
