"""System block 1 (who you are) and the user message (what is happening now).

Ported from Alive's `observe.py`: `character_block`, `dynamic_block` with its
trim loop, `build_decision_prompt`. Two changes carry the whole difference
between a block and a town:

* **PEOPLE YOU KNOW and PLACES YOU KNOW** come from the resident's own circle
  and places known, not from a roster of everybody.
* **Every other person is named through `known_as` or `as_seen_by`.** In Alive
  the rule "nobody knows your name until you give it" had to be fixed in five
  separate places before it held; here there is no other way to render a
  person, and `tests/guards/test_prompt_name_funnel.py` walks this file's AST
  to keep it so.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..clock import WEEKDAYS, tick_to_hhmm
from ..sim.events import as_seen_by, known_as
from ..sim.memory import ObservationContext, retrieve
from ..state.resident import Memory, Resident, stage_words
from . import rules

if TYPE_CHECKING:  # pragma: no cover
    from ..state.town import Town

CACHE_CONTROL = {"type": "ephemeral"}


def present_to(town: "Town", resident: Resident) -> list[str]:
    """Everybody else in the same place, awake or not. The off-town place is
    where nobody can see anybody."""
    here = town.world.location_of(resident.id)
    if town.world.is_offtown(here):
        return []
    return [r for r in town.world.occupants(here) if r != resident.id]


def shared_block(town: "Town") -> str:
    """System block 0: the same bytes for every resident in the town."""
    cached = getattr(town, "_rules_text", None)
    if cached is None:
        cached = rules.world_rules(
            str(town.config.prompt.get("profile") or "frontier"), town.name,
            str(town.spec.get("description", "")), town.config.needs)
        town._rules_text = cached
    return cached


def _place_line(town: "Town", pid: str) -> str:
    place = town.world.places[pid]
    days = "" if place.open_days is None else " (" + ", ".join(
        WEEKDAYS[d][:3] for d in sorted(place.open_days)) + ")"
    line = f"  [{pid}] {place.name} - {place.hours_label()}{days}"
    sale = place.for_sale()
    if sale:
        line += "; sells " + ", ".join(f"{t.name} ${t.price:.0f}" for t in sale[:5])
    return line


BREAK_WAYS = {
    "prompt": ("get on to them straight away - it's what you pay them for",
               ("organised", "organized", "practical", "no-nonsense", "blunt", "impatient", "sharp",
                "direct", "brisk", "efficient", "demanding", "busy", "driven", "restless")),
    "patient": ("give it a few hours to come back before you chase it",
                ("patient", "calm", "easy-going", "easygoing", "laid-back", "gentle", "unhurried",
                 "placid", "relaxed", "steady", "mild")),
    "social": ("ask the neighbours first whether it's just you, then get on to them",
               ("sociable", "chatty", "friendly", "warm", "talkative", "neighbourly", "outgoing",
                "gregarious", "nosy")),
    "put_up": ("tend to put up with it rather than make a fuss",
               ("proud", "stubborn", "reserved", "shy", "frugal", "stoic", "wary", "private")),
}
# When a persona says nothing either way: most people chase it, fewer wait or
# ask around, a few put up with it.
BREAK_WEIGHTS = (("prompt", 45), ("patient", 25), ("social", 25), ("put_up", 5))


def when_things_break(resident: Resident) -> str:
    """How this person deals with something they pay for going wrong, read off
    the persona they already have, so a town's response comes out characterful
    rather than uniform. A disposition, not an instruction."""
    import hashlib

    from .. import words as W

    p = resident.persona
    text = f"{p.get('personality', '')} {p.get('speech_style', '')}"
    hits = [k for k, (_, words) in BREAK_WAYS.items() if W.contains(text, words)]
    roll = int(hashlib.sha256(f"break|{resident.id}".encode()).hexdigest()[:8], 16)
    # Putting up with it is the unusual choice: only when nothing else in the
    # persona leans another way, and then only for some of them.
    if "put_up" in hits and (len(hits) > 1 or roll % 3):
        hits.remove("put_up")
    if hits:
        way = hits[roll % len(hits)]
    else:
        point, way = roll % 100, "prompt"
        for name, weight in BREAK_WEIGHTS:
            if point < weight:
                way = name
                break
            point -= weight
    return f"When something you pay for stops working, you {BREAK_WAYS[way][0]}."


def character_block(resident: Resident, town: "Town") -> str:
    """System block 1: this resident only. Changes at night, on a hire, on a new goal."""
    p = resident.persona
    world = town.world
    lines = [
        f"YOU ARE {resident.name.upper()}, {resident.age}.",
        "",
        f"Personality: {p.get('personality', '')}",
        f"How you talk: {p.get('speech_style', '')}",
        when_things_break(resident),
    ]
    if p.get("signature_phrases"):
        lines.append("Things that sound like you (touchstones, not scripts - vary them): "
                     + "; ".join(f'"{x}"' for x in p["signature_phrases"]))
    if p.get("forbidden_phrases"):
        lines.append("Words and phrases that are NOT yours - never say: "
                     + "; ".join(f'"{x}"' for x in p["forbidden_phrases"]))
    lines += [
        f"Background: {p.get('backstory', '')}",
        "",
        f"Something you keep to yourself: {p.get('secret') or 'nothing in particular'}",
        "You do not volunteer that. It comes out only if you are cornered, or if you "
        "decide - in the moment, for a reason - to tell someone.",
        "",
        f"What you want, long term: {p.get('long_term_goal', '')}",
    ]
    if resident.goals_active:
        lines.append("What you're trying to do right now:")
        lines += [f"  - {g}" for g in resident.goals_active]
    lines.append("")

    household = world.households.get(resident.household, {})
    kids = household.get("dependents", [])
    if kids:
        lines.append("At home with you, too young to be out on their own much: "
                     + ", ".join(f"{d['name'].split()[0]} ({d['age']})" for d in kids) + ".")
    job = resident.job
    if job:
        boss = town.residents.get(job.employer_id) if job.employer_id else None
        where = "in the city" if world.is_offtown(job.workplace) else f"at [{job.workplace}]"
        days = ", ".join(WEEKDAYS[d][:3] for d in sorted(job.days))
        lines.append(
            f"Work: {job.title} {where}"
            + (f" for {known_as(boss, resident)}" if boss else "")
            + f", {job.shift_label()} on {days}, ${job.wage_per_tick:.2f} per half hour worked.")
    else:
        lines.append(f"Work: none right now ({str(p.get('status', '')).replace('_', ' ')}).")
    for pid in sorted(world.places):
        place = world.places[pid]
        if resident.id not in place.hires:
            continue
        free = [o for o in place.openings if int(o.get("slots", 1)) > len(o.get("filled_by", []))]
        if free:
            offers = "; ".join(
                f"{o['title']}, ${float(o['wage_per_tick']):.2f} the half hour, "
                f"{tick_to_hhmm(int(o['shift']['start']))}-{tick_to_hhmm(int(o['shift']['end']))}"
                for o in free)
            lines.append(f"You could use, at [{pid}]: {offers}.")
    lines.append(f"Home: [{resident.home}] {world.places[resident.home].name}")
    if resident.rent:
        landlord = town.residents.get(resident.rent["landlord_id"])
        lines.append(
            f"Rent: ${resident.rent['amount']:.0f} a week to "
            f"{known_as(landlord, resident) if landlord else 'your landlord'}, due every "
            f"{WEEKDAYS[int(resident.rent['due_weekday'])]}.")
    lines.append("")

    lines.append("An ordinary working day for you:" if resident.off_schedule
                 else "An ordinary day for you:")
    for e in sorted(resident.schedule, key=lambda e: e.start_tick):
        lines.append(f"  {tick_to_hhmm(e.start_tick)}-{tick_to_hhmm(e.end_tick)} "
                     f"{e.activity} at [{e.location_id}]")
    if resident.off_schedule and resident.routine_days is not None:
        off = [WEEKDAYS[d][:3] for d in range(7) if d not in resident.routine_days]
        lines.append(f"On {', '.join(off)} the day is your own.")
    lines.append("")

    tastes = p.get("tastes") or {}
    if tastes.get("likes"):
        lines.append("Things you like: " + ", ".join(tastes["likes"]) + ".")
    if tastes.get("dislikes"):
        lines.append("Things you have no time for: " + ", ".join(tastes["dislikes"]) + ".")
    from ..sim.gossip import disposition_words
    lines.append(f"With news: {disposition_words(resident)}")
    tells = p.get("tells") or {}
    if tells.get("warm") or tells.get("cold"):
        lines.append("It shows, without you saying so:")
        if tells.get("warm"):
            lines.append(f"  when you have warmed to somebody - {tells['warm']}")
        if tells.get("cold"):
            lines.append(f"  when you have gone off somebody - {tells['cold']}")
    lines.append("")

    lines.append("PLACES YOU KNOW")
    lines += [_place_line(town, pid) for pid in resident.places_known if pid in world.places]
    lines.append("")

    lines.append("PEOPLE YOU KNOW, and how you feel about them (-10 to +10):")
    numbers = (resident.phone or {}).get("contacts", {})
    for rid in sorted(set(resident.circle) | set(resident.relationships)):
        other = town.residents.get(rid)
        if other is None:
            continue
        rel = resident.relationships.get(rid)
        has_number = ", you have their number" if rid in numbers else ""
        if rel:
            lately = f" (lately {rel.lately})" if rel.lately else ""
            lines.append(f"  [{rid}] {known_as(other, resident)} - {rel.label}, "
                         f"{rel.sentiment:+d}, {stage_words(rel.stage)}{lately}{has_number}")
            for note in rel.notes:
                lines.append(f"      {as_seen_by(note, resident, town)}")
        else:
            lines.append(f"  [{rid}] {known_as(other, resident)} - you know them to say "
                         f"hello to{has_number}")
    lines.append("")

    open_items: list[str] = []
    for rid in sorted(resident.relationships):
        other = town.residents.get(rid)
        who = known_as(other, resident) if other else "somebody"
        for promise in resident.relationships[rid].open_promises():
            said = "You told them you would" if promise.get("by") == "me" else f"{who} said they would"
            open_items.append(f"  {said} {promise['what']} - by Day {int(promise.get('by_day', 0))}")
    if open_items:
        lines.append("Open, and on your mind:")
        lines += open_items
        lines.append("")

    beliefs = [m for m in resident.memory if m.kind == "belief"]
    if beliefs:
        lines.append("What you've come to believe:")
        for m in sorted(beliefs, key=lambda m: (-m.importance, m.id))[:8]:
            lines.append(f"  - {as_seen_by(m.text, resident, town)}")
        lines.append("")
    recaps = [m for m in resident.memory if m.kind == "reflection"]
    if recaps:
        lines.append("How the last few days went:")
        for m in sorted(recaps, key=lambda m: -m.total_ticks)[:2]:
            lines.append(f"  - Day {m.day}: {as_seen_by(m.text, resident, town)}")
        lines.append("")
    return as_seen_by("\n".join(lines), resident, town)


def _memory_lines(memories: list[Memory]) -> list[str]:
    return [f"  [{m.stamp()}] {m.text}" for m in memories]


def needs_line(resident: Resident, town: "Town") -> str:
    parts = [f"{name.capitalize()} {resident.needs.get(name, 0.0):.0f}/100."
             for name in town.config.needs["kinds"]]
    return " ".join(parts) + f" You have ${resident.money:.2f}."


def dynamic_block(
    resident: Resident,
    town: "Town",
    memories: list[Memory],
    local_lines: list[str],
    budget_tokens: int = 1000,
    attention: list[str] | None = None,
    extra_lines: list[str] | None = None,
) -> tuple[str, bool]:
    """The user message: everything that changes. Returns (text, truncated)."""
    world = town.world
    time = world.time
    here = world.location_of(resident.id)
    place = world.places[here]
    open_now = world.is_open(here)
    head = [
        f"{time.label()}.",
        f"You are at {place.name} [{here}]" + ("" if open_now else " - it's closed right now") + ".",
    ]
    others = present_to(town, resident)
    if others:
        head.append("With you right now:")
        for rid in others:
            other = town.residents[rid]
            rel = resident.relationships.get(rid)
            feel = f", you feel {rel.sentiment:+d} about them" if rel else ""
            head.append(f"  [{rid}] {known_as(other, resident)} "
                        f"({'asleep' if other.asleep else 'here'}{feel})")
    else:
        head.append("There is nobody else here.")
    sale = place.for_sale()
    if sale and open_now:
        head.append("For sale here: " + ", ".join(f"{t.name} (${t.price:.0f})" for t in sale))

    unread = [(o, m) for o, msgs in (resident.phone or {}).get("threads", {}).items()
              for m in msgs if m.get("to") == resident.id and not m.get("read")]
    if unread:
        who = sorted({known_as(town.residents[o], resident) if o in town.residents
                      else o.split(":", 1)[-1] for o, _ in unread})
        head.append(f"Your phone has messages you have not answered: {', '.join(who)}.")

    head.append("")
    head.append(needs_line(resident, town))
    if resident.job is None:
        head.append("You have no job. There is no shift for you to go to, and asking "
                    "somebody who hires is the only way that changes.")
    elif resident.job.works_on(time.weekday_index) and 0 < resident.job.shift_start - time.tick <= 2:
        where = "in the city" if world.is_offtown(resident.job.workplace) \
            else f"at {world.places[resident.job.workplace].name}"
        head.append(f"Your shift {where} starts at {tick_to_hhmm(resident.job.shift_start)}.")
    if resident.rent and float(resident.rent.get("owed", 0)) > 0:
        landlord = town.residents.get(resident.rent["landlord_id"])
        head.append(f"You are ${float(resident.rent['owed']):.0f} behind on the rent to "
                    f"{known_as(landlord, resident) if landlord else 'your landlord'}.")
    elif resident.rent:
        days = (int(resident.rent["due_weekday"]) - time.weekday_index) % 7
        if days <= 1:
            when = "today" if days == 0 else "tomorrow"
            head.append(f"Rent of ${resident.rent['amount']:.0f} is due {when}.")
    owes = resident.obligations.get("owes", [])
    if owes:
        head.append("You owe: " + "; ".join(
            f"{known_as(town.residents[o['to']], resident) if o.get('to') in town.residents else 'somebody'} "
            f"${float(o.get('amount', 0)):.0f}" + (f", due Day {o['due_day']}" if o.get("due_day") else "")
            for o in owes[:4]) + ".")
    owed = resident.obligations.get("owed", [])
    if owed:
        head.append("Owed to you: " + "; ".join(
            f"{known_as(town.residents[o['from']], resident) if o.get('from') in town.residents else 'somebody'} "
            f"${float(o.get('amount', 0)):.0f}"
            + (f", due Day {o['due_day']}" + (" - that day has gone" if time.day > int(o["due_day"]) else "")
               if o.get("due_day") else "")
            for o in owed[:4]) + ".")
    hands = sorted(rid for rid, r in town.residents.items()
                   if r.job and r.job.employer_id == resident.id)
    if hands:
        head.append("On your books:")
        for rid in hands:
            job = town.residents[rid].job
            missed = f" Missed {job.no_shows} shift{'s' if job.no_shows != 1 else ''} this week." \
                if job.no_shows else ""
            head.append(f"  {known_as(town.residents[rid], resident)} - {job.title}, "
                        f"{job.shift_label()}.{missed}")

    hearsay = [(rid, e) for rid in sorted(resident.told_about) for e in resident.told_about[rid]
               if e.get("by") != resident.id and rid != resident.id]
    if hearsay:
        head.append("")
        head.append("What people have said about others, where you could hear it:")
        for rid, e in sorted(hearsay, key=lambda h: (h[1].get("day", 0), h[1].get("tick", 0)))[-6:]:
            about = town.residents.get(rid)
            teller = town.residents.get(e.get("by", ""))
            mouth = known_as(teller, resident) if teller else "somebody"
            said = f"you heard {mouth} say" if e.get("how") == "overheard" else f"{mouth} told you"
            head.append(f"  - about {known_as(about, resident) if about else 'somebody'}, Day "
                        f"{e.get('day')} {tick_to_hhmm(int(e.get('tick', 0)))}: {said} "
                        f"\"{as_seen_by(str(e.get('claim', '')), resident, town)}\"")
        head.append("  That is what was said. You did not see any of it, and the person "
                    "who said it may be right, wrong, or lying.")
    covered = resident.todays_threads(time.day)
    if covered:
        head.append("")
        head.append("Already discussed today (covered ground - do not re-raise unless "
                    "something new happened since):")
        for t in covered[-6:]:
            other = town.residents.get(t["other"])
            head.append(f"  - with {known_as(other, resident) if other else 'somebody'} at "
                        f"{tick_to_hhmm(t['tick'])}: {as_seen_by(t['topic'], resident, town)} -> "
                        f"{as_seen_by(t['outcome'], resident, town)}")
    for line in extra_lines or []:
        head.append(as_seen_by(line, resident, town))
    if local_lines:
        head.append("")
        head.append("In the last half hour, here:")
        head.extend(f"  {as_seen_by(line, resident, town)}" for line in local_lines)

    entry = resident.scheduled_entry(time.tick, time.weekday_index)
    tail = [""]
    if attention:
        tail.append("Your eye keeps going to " + ", ".join(attention) + ". "
                    "Whatever is between you, it is on your mind right now.")
    tail.append(f"On an ordinary day you'd be doing: {entry.activity} at [{entry.location_id}].")
    if resident.intent:
        tail.append(f"You had decided to: {resident.intent.action}"
                    + (f" {resident.intent.target}" if resident.intent.target else ""))
    tail += ["", "What do you do for the next half hour? Reply with the JSON object only."]

    kept = list(memories)
    truncated = False
    while True:
        mem = (["", "What's on your mind (oldest first):"]
               + [as_seen_by(line, resident, town) for line in _memory_lines(kept)]) if kept else []
        text = "\n".join(head + mem + tail)
        if len(text) // 4 <= budget_tokens or not kept:
            return text, truncated
        droppable = kept[:-3] if len(kept) > 3 else kept
        kept.remove(min(droppable, key=lambda m: (m.importance, m.total_ticks, m.id)))
        truncated = True


def build_decision_prompt(
    resident: Resident,
    town: "Town",
    local_lines: list[str],
    trigger: str | None = None,
    salient: set[str] | None = None,
    extra_lines: list[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    """(system_blocks, messages, truncated) for one decision call."""
    world = town.world
    here = world.location_of(resident.id)
    entry = resident.scheduled_entry(world.time.tick, world.time.weekday_index)
    present = present_to(town, resident)
    ctx = ObservationContext(location_id=here, present_ids=present,
                             keywords=[entry.activity] + resident.goals_active + local_lines)
    memories = retrieve(resident, ctx, cap=int(town.config.memory["retrieval_cap"]),
                        now_ticks=world.time.total_ticks, weights=town.config.memory)
    attention = []
    if trigger == "goal" and salient:
        attention = [known_as(town.residents[r], resident) for r in present if r in salient]
    text, truncated = dynamic_block(
        resident, town, memories, local_lines,
        budget_tokens=int(town.config.prompt["dynamic_budget_tokens"]),
        attention=attention, extra_lines=extra_lines)
    system = [
        {"type": "text", "text": shared_block(town), "cache_control": CACHE_CONTROL},
        {"type": "text", "text": character_block(resident, town), "cache_control": CACHE_CONTROL},
    ]
    return system, [{"role": "user", "content": text}], truncated
