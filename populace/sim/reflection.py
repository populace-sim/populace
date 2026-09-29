"""The night: going over the day, and what a person takes from it.

Ported from Alive's `reflection.py`. One call per resident who reflects: their
own memories of today, the people in their life, what they already believe,
and what is open between them and anybody. The engine writes the changes, not
the model, and keeps only what the day supports:

* every belief cites memory ids from today, or it is dropped;
* a belief naming somebody must cite something that person was part of;
* feelings move only about people who were in today, by at most three;
* goals are kept, revised or completed, and at most three are carried.

Changed from Alive: every name in the prompt goes through `known_as` (Alive
listed relationships and new faces by raw name), romance is not in v1, and
the weekly review's choices are keep, seek work, quit, leave town and make an
offer (moving out and raising rent belonged to Alive's housing ladder).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .. import words as W
from ..state.resident import Relationship, Resident, stage_for
from .actions import extract_json
from .events import known_as

if TYPE_CHECKING:  # pragma: no cover
    from ..state.town import Town

MAX_DELTA = 3
MAX_BELIEFS = 5
NOTE_CAP = 5
MAX_MEMORIES_REVIEWED = 60
RECAP_CAP = 5

REFLECTION_SYSTEM = """\
You are the part of a person's mind that works over the day after it is done.

You are given one person's own memories of today - only what they personally
saw, did, or were told - and you write what they take away from it. You are not a
narrator and you are not summarising a story: you are one person, in bed, going
over their day.

Two rules that matter more than anything else:

Invent nothing. Every belief you write must rest on memories in the list you were
given, and you must cite their id numbers. If nothing much happened, say that.
A quiet day is a real day.

Keep attribution. If today's memory says somebody TOLD them something, then what
they know is that they were told it - not that it is true. Write it that way:
"Sam says the factory is laying people off", not "the factory is laying people
off". They may be wrong. People usually are.

Beliefs should be things that would still matter in a week: a conclusion about
somebody, a suspicion, a decision, something they have finally admitted to
themselves. Not a recap of events.

A belief about another person must rest on something you actually saw them do
or heard them say. If all you have is a fragment of somebody else's
conversation, what you believe is that you overheard a fragment - write it that
way, with who said it, and do not fill in the rest.

Output JSON only. No prose, no code fence."""

LONGER_VIEW = """

THE LONGER VIEW

It is the end of a week. Once in a while a person stops and looks further than
tomorrow - not because anything happened today, but because a week has gone and
they are still here.

Nobody is stuck here. There is work in town and work in the city, jobs that
end and jobs that start, and people who pack a bag and go. Over a month or two
in a town this size somebody quits, somebody goes, somebody finally asks for
the thing they wanted - and it is made of individual people deciding on
individual Sunday nights.

Most weeks, for most people, the honest answer is still that nothing changes.
But the thing you want long term is the thing you have been carrying while
nothing changed, and a week that ends with it no nearer is information about
the week.

Add one more field, `arc_update`, and it may be exactly one of these:

  {"choice": "keep"}
      This is your life and you are living it. The usual answer.
  {"choice": "seek_work", "workplace": "<a place id>", "reason": "..."}
      You want work, or different work, and there is somewhere that takes
      people on. You will have to ask somebody, to their face, this week.
  {"choice": "quit", "reason": "..."}
      You are done there, and you will have to say so to whoever hired you.
  {"choice": "leave_town", "day": <a day 2 to 7 from now>, "reason": "..."}
      You are going. Name the day. There are people here who should hear it
      from you rather than by noticing you have not been in.
  {"choice": "make_offer", "to": "<id>", "what": "...", "reason": "..."}
      There is something you want to put to somebody, and you have not.

Whatever you choose becomes the thing on your mind - it does not become a fact.
You will still have to go and do it, and it can still come to nothing."""

_WANTS_OUT = ("leave town", "get out of here", "somewhere else", "move away", "leave for good",
              "start over somewhere")


@dataclass
class ReflectionResult:
    resident_id: str
    ok: bool = False
    summary: str = ""
    beliefs: list[dict] = field(default_factory=list)
    relationship_updates: list[dict] = field(default_factory=list)
    goal_update: dict = field(default_factory=dict)
    arc_update: dict = field(default_factory=dict)
    review: bool = False
    rejected: list[str] = field(default_factory=list)
    error: str | None = None


def todays_memories(resident: Resident, day: int) -> list:
    today = [m for m in resident.memory if m.day == day and m.kind in {"observation", "dialogue"}]
    if len(today) > MAX_MEMORIES_REVIEWED:
        kept = sorted(today, key=lambda m: (-m.importance, -m.tick, m.id))[:MAX_MEMORIES_REVIEWED]
        today = sorted(kept, key=lambda m: (m.tick, m.id))
    return today


def _promises(resident: Resident, town: "Town", day: int) -> str:
    lines = []
    for rid in sorted(resident.relationships):
        other = town.residents.get(rid)
        for p in resident.relationships[rid].open_promises():
            who = "you said you would" if p.get("by") == "me" else "they said they would"
            when = int(p.get("by_day", day))
            due = "today" if when == day else ("tomorrow" if when == day + 1 else f"by Day {when}")
            overdue = " - and that day has gone" if when < day else ""
            lines.append(f"  {known_as(other, resident) if other else rid}: {who} {p['what']}, {due}{overdue}")
    return ("OPEN BETWEEN YOU AND SOMEBODY:\n" + "\n".join(lines) + "\n\n") if lines else ""


def _pull_of_the_week(resident: Resident, town: "Town", day: int) -> str:
    """The one thing this person, specifically, has been carrying: out of the
    persona they already have, so the town's spread is characterful."""
    lines = []
    goal = str(resident.persona.get("long_term_goal") or "")
    if W.contains(goal, _WANTS_OUT) or W.contains(goal, [f"leave {town.name}"]):
        weeks = max(1, day // 7)
        lines.append(f"What you want, in your own words, is not in {town.name}. You have wanted it for "
                     f"{weeks} week{'s' if weeks != 1 else ''} of Sundays.")
    if resident.job:
        lines.append("You have work. Keeping it is a choice you make every week, and leaving it is "
                     "a thing you would have to say out loud to whoever took you on.")
    elif resident.persona.get("status") == "between_jobs":
        lines.append("You have no work, and every week without it costs you.")
    return ("\n\nWHERE YOU ARE, SPECIFICALLY\n\n" + "\n\n".join(lines)) if lines else ""


def _longer_view(resident: Resident, town: "Town", day: int, review: bool) -> str:
    if not review:
        return ""
    hires = ", ".join(f"[{pid}] {p.name}" for pid, p in sorted(town.world.places.items())
                      if p.hires and pid in resident.places_known
                      and (not resident.job or resident.job.workplace != pid))
    where = f"\n\nPlaces you know that take people on: {hires}." if hires else ""
    return LONGER_VIEW + _pull_of_the_week(resident, town, day) + where


def build_prompt(resident: Resident, town: "Town", day: int, review: bool = False) -> str:
    memories = todays_memories(resident, day)
    lines = [f"{m.id}: [{m.stamp()}] {m.text}" for m in memories]
    rel_lines = [f"  [{rid}] {known_as(town.residents[rid], resident)} - {rel.label}, currently {rel.sentiment:+d}"
                 for rid, rel in sorted(resident.relationships.items()) if rid in town.residents]
    in_day = {rid for m in memories for rid in m.involved} - {resident.id}
    new_faces = [f"  [{rid}] {known_as(town.residents[rid], resident)}"
                 for rid in sorted(in_day - set(resident.relationships)) if rid in town.residents]
    held = sorted((m for m in resident.memory if m.kind == "belief"), key=lambda m: (-m.importance, -m.total_ticks))
    held_lines = [f"  - {m.text}" for m in held[:12]]
    goals = "\n".join("  - " + g for g in resident.goals_active) or "  - nothing in particular"
    return f"""\
You are {resident.name}, {resident.age}. {resident.persona.get('personality', '')}

What you want, long term: {resident.persona.get('long_term_goal', '')}
What you were trying to do this week:
{goals}

The people in your life and how you felt about them this morning:
{chr(10).join(rel_lines) or '  nobody in particular'}

People who turned up in your day that you had no opinion about yet - if one of
them made an impression, good or bad, say so and they will become somebody you
know:
{chr(10).join(new_faces) or '  nobody new'}

What you already believed before today:
{chr(10).join(held_lines) or '  nothing settled yet'}

Do not write a belief you already hold. If today changed one of them, write the
revised version; if today contradicted one, say so plainly. Otherwise leave them
alone and only write what is new.

{_promises(resident, town, day)}YOUR MEMORIES OF TODAY (day {day}), each with its id:
{chr(10).join(lines) or '  (nothing worth remembering happened)'}

MEMORY_IDS: {[m.id for m in memories]}

Write your reflection:

{{"summary": "at most 50 words, first person, what today was",
  "beliefs": [{{"text": "at most 25 words, something you now hold to be true",
               "importance": 1-10,
               "source_memory_ids": [ids from the list above that this rests on]}}],
  "relationship_updates": [{{"character_id": "id of someone in today's memories",
                            "delta": -3 to +3, "note": "at most 15 words, concrete",
                            "label": null or "what they are to you now, a few words - only when today genuinely changed it"}}],
  "goal_update": {{"action": "keep" or "revise" or "complete", "new_goal": null or "..."}}}}

At most {MAX_BELIEFS} beliefs, and fewer is normal. Only update feelings about
people who actually appear in today's memories, and only when something today
genuinely moved them - most days, most relationships do not change at all.
{_longer_view(resident, town, day, review)}"""


def _grounded(text: str, cited: list, town: "Town") -> str | None:
    """A belief naming somebody must cite something they were part of."""
    cited_people = {rid for m in cited for rid in m.involved}
    cited_text = " ".join(m.text for m in cited)
    for rid in sorted(town.names.find(text)):
        first = town.residents[rid].first_name
        if rid in cited_people or W.contains(cited_text, [first]):
            continue
        return f"names {town.residents[rid].name} but cites nothing they were part of"
    return None


def validate(raw: Any, resident: Resident, town: "Town", day: int) -> ReflectionResult:
    result = ReflectionResult(resident_id=resident.id)
    if not isinstance(raw, dict):
        result.error = "response was not a JSON object"
        return result
    memories = todays_memories(resident, day)
    valid_ids = {m.id for m in memories}
    seen_today = {rid for m in memories if m.kind == "dialogue" or m.importance >= 4
                  for rid in m.involved} - {resident.id}
    result.summary = str(raw.get("summary") or "").strip()[:400]
    for belief in raw.get("beliefs") or []:
        if len(result.beliefs) >= MAX_BELIEFS or not isinstance(belief, dict):
            continue
        text = str(belief.get("text") or "").strip()
        cited = [int(i) for i in belief.get("source_memory_ids") or [] if str(i).lstrip("-").isdigit()]
        kept = [i for i in cited if i in valid_ids]
        if not text:
            continue
        if not kept:
            result.rejected.append(f"belief cites no real memory: {text[:60]!r}")
            continue
        problem = _grounded(text, [m for m in memories if m.id in kept], town)
        if problem:
            result.rejected.append(f"belief {problem}: {text[:60]!r}")
            continue
        try:
            importance = max(1, min(10, int(belief.get("importance", 5))))
        except (TypeError, ValueError):
            importance = 5
        result.beliefs.append({"text": text[:200], "importance": importance,
                               "source_memory_ids": sorted(set(kept))})
    for update in raw.get("relationship_updates") or []:
        if not isinstance(update, dict):
            continue
        rid = str(update.get("character_id") or "")
        if rid not in seen_today:
            result.rejected.append(f"feelings about {rid!r}, who wasn't in today")
            continue
        try:
            delta = int(update.get("delta", 0))
        except (TypeError, ValueError):
            delta = 0
        result.relationship_updates.append({
            "character_id": rid, "delta": max(-MAX_DELTA, min(MAX_DELTA, delta)),
            "note": str(update.get("note") or "").strip()[:120],
            "label": str(update.get("label") or "").strip()[:60] or None})
    goal = raw.get("goal_update")
    if isinstance(goal, dict) and goal.get("action") in {"keep", "revise", "complete"}:
        result.goal_update = {"action": goal["action"],
                              "new_goal": str(goal.get("new_goal") or "").strip()[:200] or None}
    result.ok = bool(result.summary or result.beliefs)
    return result


def apply(result: ReflectionResult, resident: Resident, town: "Town") -> None:
    """The engine writes the changes, not the model."""
    time = town.world.time
    if result.summary:
        resident.remember(time, result.summary, kind="reflection", importance=7,
                          involved=[u["character_id"] for u in result.relationship_updates])
    for belief in result.beliefs:
        resident.remember(time, belief["text"], kind="belief", importance=belief["importance"],
                          source_ids=belief["source_memory_ids"])
    for update in result.relationship_updates:
        rid = update["character_id"]
        rel = resident.relationships.get(rid)
        if rel is None:
            if rid not in town.residents:
                continue
            rel = Relationship(label="somebody from around here", sentiment=0)
            resident.relationships[rid] = rel
        rel.sentiment = max(-10, min(10, rel.sentiment + update["delta"]))
        if update["note"]:
            rel.add_note(update["note"], cap=NOTE_CAP)
        if update.get("label"):
            rel.label = update["label"]
        if abs(update["delta"]) >= 2:
            rel.friction = rel.friction or update["delta"] < 0
    goal = result.goal_update
    if goal.get("action") == "complete" and resident.goals_active:
        resident.goals_active.pop(0)
    if goal.get("action") in {"revise", "complete"} and goal.get("new_goal"):
        resident.goals_active.insert(0, goal["new_goal"])
    del resident.goals_active[3:]
    town.touch(resident.id)


def settle_promises(town: "Town", day: int) -> list[tuple[str, str, bool]]:
    """Judge every promise due today on the record. A money promise is kept if
    what was owed went down; anything else lapses quietly, because an engine
    that scored "I'll come by Sunday" would be scoring the wording."""
    judged = []
    for rid in sorted(town.residents):
        r = town.residents[rid]
        for oid in sorted(r.relationships):
            for p in r.relationships[oid].promises:
                if p.get("status") != "open" or p.get("by") != "me" or int(p.get("by_day", 0)) > day:
                    continue
                owed_when_made = float(p.get("owed_when_made", 0.0) or 0.0)
                if p.get("about") != "money" or owed_when_made <= 0:
                    p["status"] = "lapsed"
                    continue
                owed_now = r.owes_to(oid)
                rent = r.rent or {}
                if rent.get("landlord_id") == oid:
                    owed_now += float(rent.get("owed", 0.0) or 0.0)
                kept = owed_now < owed_when_made
                p["status"] = "kept" if kept else "broken"
                other = town.residents.get(oid)
                if other is not None:
                    for q in other.relationships.get(rid, Relationship("", 0)).promises:
                        if q.get("what") == p.get("what") and q.get("status") == "open":
                            q["status"] = p["status"]
                judged.append((rid, oid, kept))
                town.touch(rid)
    return judged


def settle_stages(resident: Resident, town: "Town") -> None:
    cfg = town.config.trust
    thresholds = tuple(cfg["thresholds"])
    day = town.world.time.day
    for rel in resident.relationships.values():
        rel.stage = stage_for(rel.trust, thresholds)
        moved = rel.recent_trust(day, int(cfg["lately_window_days"]))
        line = int(cfg["lately_threshold"])
        rel.lately = "warmer" if moved >= line else ("cooler" if moved <= -line else None)


def prune(resident: Resident, current_day: int, keep_days: int, beliefs_cap: int) -> int:
    cutoff = current_day - keep_days
    before = len(resident.memory)
    resident.memory = [m for m in resident.memory if m.kind not in {"observation", "dialogue"} or m.day > cutoff]
    for kind, cap in (("belief", beliefs_cap), ("reflection", RECAP_CAP)):
        held = [m for m in resident.memory if m.kind == kind]
        if len(held) > cap:
            keep = {m.id for m in sorted(held, key=lambda m: (-m.importance, -m.total_ticks, m.id))[:cap]}
            resident.memory = [m for m in resident.memory if m.kind != kind or m.id in keep]
    return before - len(resident.memory)


def recap(resident: Resident, day: int) -> str | None:
    """A free, engine-written reflection for somebody the night's cap did not
    reach: their own day, in their own memories, shortened. No beliefs."""
    today = [m for m in todays_memories(resident, day) if m.importance >= 2]
    if not today:
        return None
    heaviest = sorted(today, key=lambda m: (-m.importance, m.tick, m.id))[:4]
    parts = []
    for m in sorted(heaviest, key=lambda m: (m.tick, m.id)):
        text = re.sub(r"\s+", " ", m.text).strip()
        parts.append(text if len(text) <= 90 else text[:87].rsplit(" ", 1)[0] + "...")
    return " ".join(parts)


def mock_state(resident: Resident, town: "Town", day: int, review: bool) -> dict[str, Any]:
    memories = todays_memories(resident, day)
    seen = sorted({rid for m in memories if m.kind == "dialogue" or m.importance >= 4
                   for rid in m.involved} - {resident.id})
    hires = [pid for pid in resident.places_known if town.world.places[pid].hires
             and (not resident.job or resident.job.workplace != pid)]
    return {"review": review, "day": day, "memory_ids": [m.id for m in memories],
            "heavy_ids": [m.id for m in memories if m.importance >= 4], "seen": seen,
            "hires": hires, "has_job": resident.job is not None,
            "between_jobs": resident.persona.get("status") == "between_jobs",
            "circle": list(resident.circle)}


async def reflect_one(resident: Resident, town: "Town", runner, day: int, review: bool) -> ReflectionResult:
    from . import lives

    if not todays_memories(resident, day) and not review:
        return ReflectionResult(resident_id=resident.id, ok=True, review=review)
    response = await runner.call(
        "reflection", [{"type": "text", "text": REFLECTION_SYSTEM}],
        [{"role": "user", "content": build_prompt(resident, town, day, review)}],
        {"char_id": resident.id, "day": day, "tick": town.world.time.tick,
         "mock_state": mock_state(resident, town, day, review)})
    if not response.ok:
        return ReflectionResult(resident_id=resident.id, error=response.error)
    raw = extract_json(response.text)
    if raw is None:
        return ReflectionResult(resident_id=resident.id, error="no JSON in reflection response")
    result = validate(raw, resident, town, day)
    result.review = review
    if review and raw.get("arc_update") is not None:
        try:
            result.arc_update = lives.validate_arc(raw["arc_update"], resident, town)
        except lives.ArcRefused as exc:
            result.rejected.append(f"arc_update: {exc}")
    return result
