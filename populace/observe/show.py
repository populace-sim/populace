"""`populace show`: a readable listing of a generated town.

For the hand-off after generation: does this read like a town somebody could
live in? Places with their hours and staff, a sample of households, full
sheets for a sample of residents, and the shape of the social graph.
"""

from __future__ import annotations

import random
from collections import Counter

from ..clock import WEEKDAYS, tick_to_hhmm
from ..state.place import OFFTOWN_KIND
from ..state.town import Town


def _days(days: list[int] | None) -> str:
    if days is None or len(days) == 7:
        return "every day"
    if sorted(days) == [0, 1, 2, 3, 4]:
        return "Mon-Fri"
    return ", ".join(WEEKDAYS[d][:3] for d in sorted(days))


def _day_line(town: Town, schedule) -> str:
    parts = []
    for e in schedule:
        where = town.world.places[e.location_id].name
        parts.append(f"{tick_to_hhmm(e.start_tick)}-{tick_to_hhmm(e.end_tick)} {e.activity} ({where})")
    return "; ".join(parts)


def summary(town: Town, generation: dict | None = None) -> str:
    R = list(town.residents.values())
    hh = town.world.households
    lines = [f"# {town.name}", "", f"_{town.spec.get('description', '')}_", ""]
    deps = sum(len(h.get("dependents", [])) for h in hh.values())
    lines.append(f"- {len(R)} residents in {len(hh)} households, plus {deps} young children "
                 "who live with them and are not simulated")
    for nb in town.spec.get("neighbourhoods", []):
        lines.append(f"- {nb['name']}: {', '.join(nb['streets'])}")
    status = Counter(r.persona.get("status", "?") for r in R)
    lines.append("- " + ", ".join(f"{n} {k.replace('_', ' ')}" for k, n in status.most_common()))
    local = sum(1 for r in R if r.job and not town.world.is_offtown(r.job.workplace))
    commute = sum(1 for r in R if r.job and town.world.is_offtown(r.job.workplace))
    lines.append(f"- {local} work in town, {commute} commute to the city")
    if generation:
        src = generation.get("persona_sources", {})
        lines.append(f"- persona prose: " + ", ".join(f"{v} {k}" for k, v in src.items() if v))
    return "\n".join(lines)


def places_table(town: Town) -> str:
    lines = ["## Places", "", "| place | kind | hours | days | staff | runs it | hand short |",
             "|---|---|---|---|---|---|---|"]
    for p in sorted(town.world.places.values(), key=lambda p: (p.kind, p.name)):
        if not p.public:
            continue
        boss = ", ".join(town.residents[h].name for h in p.hires) or "-"
        short = ", ".join(f"{o['title']} x{o['slots'] - len(o['filled_by'])}" for o in p.openings
                          if o["slots"] > len(o["filled_by"])) or "-"
        lines.append(f"| {p.name} | {p.kind.replace('_', ' ')} | {p.hours_label()} | "
                     f"{_days(p.open_days)} | {len(p.workplace_of)} | {boss} | {short} |")
    homes = [p for p in town.world.places.values() if not p.public and p.kind != OFFTOWN_KIND]
    kinds = Counter(p.kind for p in homes)
    lines += ["", f"Homes: {kinds.get('house', 0)} houses and "
                  f"{kinds.get('apartment_building', 0)} apartment buildings."]
    return "\n".join(lines)


def households_sample(town: Town, n: int, rng: random.Random) -> str:
    lines = ["## A sample of households", ""]
    hids = sorted(town.world.households)
    for hid in sorted(rng.sample(hids, min(n, len(hids)))):
        h = town.world.households[hid]
        home = town.world.places[h["home"]]
        members = []
        for rid in h["members"]:
            r = town.residents[rid]
            job = f"{r.job.title}" + ("" if town.world.is_offtown(r.job.workplace)
                                      else f" at {town.world.places[r.job.workplace].name}") \
                if r.job else r.persona.get("status", "").replace("_", " ")
            members.append(f"{r.name} ({r.age}, {job})")
        kids = [f"{d['name'].split()[0]} ({d['age']})" for d in h.get("dependents", [])]
        payer = next((town.residents[m] for m in h["members"] if town.residents[m].rent), None)
        rent = (f"; rent ${payer.rent['amount']:.0f} a week to "
                f"{town.residents[payer.rent['landlord_id']].name}" if payer else "; they own it")
        lines.append(f"- **{home.name}** ({h['kind'].replace('_', ' ')}): " + ", ".join(members)
                     + (f"; children {', '.join(kids)}" if kids else "") + rent)
    return "\n".join(lines)


def resident_sheet(town: Town, rid: str) -> str:
    r = town.residents[rid]
    p = r.persona
    home = town.world.places[r.home]
    lines = [f"### {r.name}, {r.age}", ""]
    lines.append(f"*{p.get('descriptor', '')}* (what a stranger sees)")
    lines.append("")
    if r.job:
        where = "the city" if town.world.is_offtown(r.job.workplace) else town.world.places[r.job.workplace].name
        lines.append(f"- **Work:** {r.job.title}, {where}, {r.job.shift_label()} {_days(r.job.days)}, "
                     f"${r.job.wage_per_tick * 2:.2f} an hour"
                     + (f", answers to {town.residents[r.job.employer_id].name}" if r.job.employer_id else ""))
    else:
        lines.append(f"- **Work:** none ({p.get('status', '').replace('_', ' ')})")
    lines.append(f"- **Home:** {home.name}; ${r.money:.0f} on hand"
                 + (f"; rent ${r.rent['amount']:.0f} due {WEEKDAYS[r.rent['due_weekday']]}s"
                    if r.rent else ""))
    for key, label in (("personality", "Personality"), ("speech_style", "Talks"),
                       ("backstory", "Backstory"), ("public_bio", "What people say"),
                       ("secret", "Secret"), ("long_term_goal", "Wants")):
        lines.append(f"- **{label}:** {p.get(key, '')}")
    lines.append(f"- **This week:** {'; '.join(r.goals_active)}")
    tastes = p.get("tastes", {})
    lines.append(f"- **Likes / dislikes:** {', '.join(tastes.get('likes', []))} / "
                 f"{', '.join(tastes.get('dislikes', []))}")
    lines.append(f"- **Says:** {', '.join(repr(x) for x in p.get('signature_phrases', []))}; "
                 f"never: {', '.join(repr(x) for x in p.get('forbidden_phrases', []))}")
    lines.append(f"- **With news:** {p.get('gossip')}; persona written by {p.get('source')}")
    ties = sorted(r.relationships.items(), key=lambda kv: -abs(kv[1].sentiment))
    lines.append("- **Knows:** " + "; ".join(
        f"{town.residents[o].name} ({rel.label}, {rel.sentiment:+d}{', friction' if rel.friction else ''})"
        for o, rel in ties))
    lines.append(f"- **Circle:** {len(r.circle)} people; knows {len(r.places_known)} places: "
                 + ", ".join(town.world.places[pid].name for pid in r.places_known))
    lines.append(f"- **A working day:** {_day_line(town, r.schedule)}")
    if r.off_schedule:
        lines.append(f"- **A day off:** {_day_line(town, r.off_schedule)}")
    return "\n".join(lines)


def graph_shape(town: Town) -> str:
    R = list(town.residents.values())
    degree = Counter(len(r.relationships) for r in R)
    friction = sum(1 for r in R for rel in r.relationships.values() if rel.friction)
    labels = Counter(rel.label for r in R for rel in r.relationships.values())
    circles = [len(r.circle) for r in R]
    lines = ["## The social graph", ""]
    lines.append("| ties per resident | residents |")
    lines.append("|---|---|")
    for k in sorted(degree):
        lines.append(f"| {k} | {degree[k]} |")
    lines.append("")
    lines.append(f"- {sum(degree[k] * k for k in degree)} directed ties, {friction} with friction")
    lines.append("- labels: " + ", ".join(f"{k} {v}" for k, v in labels.most_common(12)))
    lines.append(f"- circle size: min {min(circles)}, median {sorted(circles)[len(circles) // 2]}, "
                 f"max {max(circles)} (cap {town.config.locality['people_cap']})")
    return "\n".join(lines)


def render(town: Town, residents: int = 10, households: int = 8, seed: int = 0,
           generation: dict | None = None, only: str | None = None) -> str:
    if only:
        from .names import NameBook
        rid = NameBook.of(town).find(only)
        if rid is None:
            raise SystemExit(f"no resident is called or numbered {only!r}")
        return resident_sheet(town, rid)
    rng = random.Random(seed)
    sample = sorted(rng.sample(sorted(town.residents), min(residents, len(town.residents))))
    parts = [summary(town, generation), places_table(town), households_sample(town, households, rng),
             "## Ten residents, in full" if residents == 10 else f"## {residents} residents, in full"]
    parts += [resident_sheet(town, rid) for rid in sample]
    parts.append(graph_shape(town))
    return "\n\n".join(parts) + "\n"
