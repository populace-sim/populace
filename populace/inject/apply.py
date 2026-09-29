"""Injections landing in a running town, one tick at a time.

`apply_due` runs at the top of every tick and applies whatever has fallen due.
Each application changes the world (a place, a price, a problem at somebody's
home, a newcomer) and emits `changed` events at the places where it can be
seen, through the ordinary witness rule; those events carry
`source: inject:<id>`. What cannot be seen at once becomes a notice: posted
at one or more places, noticed once by each person who comes by while it is
up (`notice_pass`, after the tick's moves), written into their own memory as
something they noticed, and able to teach them a new place.

`prompt_lines` gives a resident at most three "what changed" lines, drawn only
from what they have noticed or have at home, plus the services they know of.
Facts, never instructions.

Anything that can no longer apply when its time comes (the place it names has
gone) is refused on the record, not dropped.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from .. import clock
from ..gen.skeleton import resident_id, slug
from ..sim import memory as M
from ..sim.events import Event
from ..state.place import Place, Thing
from ..state.resident import Relationship, Resident, ScheduleEntry, phone_number_for
from . import label, outage_homes, refuse

if TYPE_CHECKING:  # pragma: no cover
    from ..sim.engine import Engine

WHAT_CHANGED_LINES = 3
NOTICE_MEMORY_TICKS = 2 * 48   # how long something noticed stays in the prompt
IMPORTANCE = {"place.new": 5, "place.price": 4, "place.hours": 4, "place.close": 6, "place.reopen": 5,
              "event.outage": 6, "event.weather": 4, "event.notice": 5, "event.arrival": 4,
              "event.letter": 7, "_restore": 5}


def _hhmm_tick(hhmm: str) -> int:
    hours, minutes = (int(x) for x in hhmm.split(":"))
    return (hours * 60 + minutes) // clock.MINUTES_PER_TICK


def _source(inj: dict[str, Any]) -> str:
    return f"inject:{inj['id']}"


def _changed(engine: "Engine", inj: dict[str, Any], place_id: str, text: str,
             only: list[str] | None = None) -> list[str]:
    """A visible change at a place, seen by whoever is there and awake now."""
    world = engine.town.world
    event = Event(kind="changed", day=world.time.day, tick=world.time.tick, location_id=place_id,
                  actor="", actor_name="", detail=text, importance=IMPORTANCE.get(inj["kind"], 4),
                  tags=(inj["kind"], inj["id"]))
    seen = M.witnesses(engine.town, event)
    if only is not None:
        seen = [r for r in seen if r in only]
    engine.emit_seen(event, seen, source=_source(inj))
    return seen


def _post(engine: "Engine", inj: dict[str, Any], places: list[str], text: str, until: int | None,
          seen: list[str], only: list[str] | None = None, reveals: str | None = None,
          reported: dict[str, Any] | None = None) -> None:
    """Something left up for people to notice when they come by."""
    engine.town.world.notices.append({
        "inj": inj["id"], "kind": inj["kind"], "places": sorted(set(places)), "text": text,
        "until": until, "only": sorted(only) if only is not None else None, "reveals": reveals,
        "reported": reported, "seen_by": {rid: engine.town.world.time.total_ticks for rid in seen},
    })
    if reveals:
        _learn_place(engine, reveals, seen)
    if reported:
        _learn_reported(engine.town, reported, seen)


def _learn_reported(town, reported: dict[str, Any], who: list[str]) -> None:
    """They now know somebody at home has got on to the service about it."""
    for rid in who:
        r = town.residents.get(rid)
        if r is None:
            continue
        for p in r.problems:
            if p.get("inj") == reported["inj"] and not p.get("resolved"):
                p["reported"] = dict(reported)
                town.touch(rid)


def report_to_household(engine: "Engine", r: Resident, service: dict[str, Any], said: str | None) -> None:
    """A resident got through to a service about a problem at home: their own
    record says so, and the rest of the household learns it - at once if they
    are at home, when they get in otherwise - so a house does not report the
    same outage three times over without knowing it."""
    town = engine.town
    world = town.world
    open_ = [p for p in r.problems if not p.get("resolved") and p.get("inj")
             and (not service.get("handles") or p.get("kind") in service["handles"])]
    if not open_:
        return
    home = world.places.get(r.home)
    # The household, not the building: a block of flats is many households.
    others = sorted(x for x in (home.residents_of if home else []) if x != r.id
                    and x in town.residents and town.residents[x].household == r.household)
    for inj_id in sorted({p["inj"] for p in open_}):
        kind = next(p.get("kind") for p in open_ if p["inj"] == inj_id)
        info = {"inj": inj_id, "by": r.id, "at": world.time.total_ticks, "service": service["id"],
                "service_name": service["name"], "said": said}
        _learn_reported(town, info, [r.id])
        if not others:
            continue
        text = (f"{r.name} got on to {service['name']} about the {kind}"
                + (f"; they said: \"{said}\"" if said else "") + ".")
        here = [x for x in others if world.location_of(x) == r.home and not town.residents[x].asleep]
        parent = {"id": inj_id, "kind": "_reported"}
        seen = _changed(engine, parent, r.home, text, only=here) if world.location_of(r.id) == r.home else []
        until = next((int(p["until"]) for p in open_ if p["inj"] == inj_id and p.get("until")), None)
        _post(engine, parent, [r.home], text, until, seen, only=others, reported=info)


def _learn_place(engine: "Engine", pid: str, who: list[str]) -> None:
    town = engine.town
    place = town.world.places.get(pid)
    if place is None:
        return
    cap = int(town.config.locality["places_cap"])
    for rid in who:
        if rid not in place.known_by:
            place.known_by.append(rid)
        r = town.residents[rid]
        if pid not in r.places_known:
            r.places_known = (r.places_known + [pid])[-cap:] if len(r.places_known) >= cap else r.places_known + [pid]
        town.touch(rid)


def apply_due(engine: "Engine") -> None:
    world = engine.town.world
    now = world.time.total_ticks
    due = [m for m in world.scheduled if int(m["at"]) <= now]
    if not due:
        return
    world.scheduled = [m for m in world.scheduled if int(m["at"]) > now]
    for inj in sorted(due, key=lambda m: (int(m["at"]), m["id"])):
        try:
            affected = APPLY[inj["kind"]](engine, inj)
        except LookupError as exc:
            refuse(engine.town, inj, f"could not apply at {label(now)}: {exc}")
            engine.telemetry.log_injection({"id": inj["id"], "kind": inj["kind"], "refused": str(exc),
                                            "day": world.time.day, "tick": world.time.tick})
            continue
        record = {"id": inj["id"], "kind": inj["kind"], "params": inj["params"],
                  "day": world.time.day, "tick": world.time.tick, "affected": sorted(affected or [])}
        if not inj["kind"].startswith("_"):
            world.injected.append(record)
        engine.telemetry.log_injection(record)


def expire(engine: "Engine") -> None:
    now = engine.town.world.time.total_ticks
    engine.town.world.notices = [n for n in engine.town.world.notices
                                 if n.get("until") is None or int(n["until"]) > now]


def notice_pass(engine: "Engine") -> None:
    """Whoever is at a place with something posted, awake, notices it once."""
    town = engine.town
    world = town.world
    now = world.time.total_ticks
    for notice in world.notices:
        if notice.get("until") is not None and int(notice["until"]) <= now:
            continue
        fresh = []
        for pid in notice["places"]:
            for rid in world.occupants(pid):
                r = town.residents.get(rid)
                if r is None or r.asleep or rid in notice["seen_by"]:
                    continue
                if notice["only"] is not None and rid not in notice["only"]:
                    continue
                notice["seen_by"][rid] = now
                fresh.append(rid)
                if notice.get("reported"):
                    _learn_reported(town, notice["reported"], [rid])
                event = Event(kind="noticed", day=world.time.day, tick=world.time.tick, location_id=pid,
                              actor=rid, actor_name=r.name, detail=notice["text"],
                              importance=IMPORTANCE.get(notice["kind"], 4), tags=(notice["kind"], notice["inj"]))
                engine.emit_seen(event, [], source=f"inject:{notice['inj']}")
        if fresh and notice.get("reveals"):
            _learn_place(engine, notice["reveals"], fresh)


def prompt_lines(engine: "Engine", r: Resident) -> list[str]:
    """At most three lines of what changed, only what this resident has seen or
    has at home; then the services they know of."""
    town = engine.town
    out = what_changed(town, r)
    services = [s for s in town.services.values() if knows_service(r, s, town)]
    if services:
        out.append("Services you know of: " + "; ".join(_service_line(s, town) for s in services) + ".")
    return out


def news_since(town, r: Resident, since: int) -> bool:
    """Has this resident seen or learned anything new since `since`?"""
    for n in town.world.notices:
        if n["seen_by"].get(r.id, -1) > since:
            return True
    return any((p.get("reported") or {}).get("at", -1) > since for p in r.problems)


def what_changed(town, r: Resident) -> list[str]:
    """The facts a resident has at home or has seen lately: the same lines in
    their decisions and in their conversations."""
    world = town.world
    now = world.time.total_ticks
    lines = []
    for p in r.problems:
        if not p.get("resolved"):
            since = int(p.get("since", now))
            hours = (now - since) * clock.MINUTES_PER_TICK // 60
            how_long = "just now" if hours < 1 else f"{hours} hour{'s' if hours != 1 else ''} now"
            line = (f"At home: {p.get('text') or p.get('kind')} since {label(since)} - {how_long}, "
                    "and it's something you pay for.")
            rep = p.get("reported")
            if rep:
                from ..sim.events import known_as
                who = "You" if rep["by"] == r.id else known_as(town.residents.get(rep["by"]), r)
                line += (f" {who} got on to {rep['service_name']} at {label(int(rep['at']))}"
                         + (f"; they said: \"{rep['said']}\"" if rep.get("said") else "") + ".")
            lines.append(line)
    seen = sorted(((n["seen_by"][r.id], n) for n in world.notices
                   if r.id in n["seen_by"] and now - n["seen_by"][r.id] <= NOTICE_MEMORY_TICKS
                   and n["kind"] not in ("event.outage", "_reported")),
                  key=lambda x: -x[0])
    for when, n in seen:
        where = world.places[n["places"][0]].name if len(n["places"]) == 1 else "around town"
        lines.append(f"Seen at {where}, {label(when)}: {n['text']}")
    return lines[:WHAT_CHANGED_LINES]


def knows_service(r: Resident, service: dict[str, Any], town) -> bool:
    known = service.get("known_by", "everyone")
    if known == "everyone":
        return True
    if isinstance(known, list):
        return r.id in known
    if isinstance(known, dict) and known.get("neighbourhood"):
        return r.neighbourhood == known["neighbourhood"]
    return False


def _service_line(s: dict[str, Any], town) -> str:
    how = " or ".join(s.get("channels") or ["text"])
    hours = f", {s['hours']['open']}-{s['hours']['close']}" if s.get("hours") else ""
    shop = ""
    if s.get("storefront") and s["storefront"] in town.world.places:
        shop = f", counter at {town.world.places[s['storefront']].name}"
    return f"{s['name']} [{s['id']}], {s['purpose']}: {how} them{hours}{shop}"


# -- one function per kind -----------------------------------------------------------


def _place_new(engine, inj):
    town, p = engine.town, inj["params"]
    world = town.world
    pid = p.get("id") or slug(p["name"])
    base, n = pid, 2
    while pid in world.places:
        pid, n = f"{base}_{n}", n + 1
    hours = ({"start": _hhmm_tick(p["hours"]["open"]), "end": _hhmm_tick(p["hours"]["close"])}
             if p.get("hours") else None)
    neighbourhood = p.get("neighbourhood") or next(
        (world.places[a].neighbourhood for a in p.get("announce_at") or [] if a in world.places), "")
    place = Place(id=pid, name=p["name"], kind=p["kind"], description=p.get("description", ""),
                  neighbourhood=neighbourhood, public=bool(p.get("public", True)), open_hours=hours,
                  things=[Thing(slug(t["name"]), t["name"], list(t.get("tags", [])), price=float(t["price"]),
                                satiety=float(t.get("satiety", 0))) for t in p.get("things") or []],
                  owner=p.get("owner"), hires=[p["owner"]] if p.get("owner") else [],
                  introduced_by=inj["id"])
    world.places[pid] = place
    world._reindex()
    announce = list(p.get("announce_at") or sorted(
        q.id for q in world.places.values() if q.public and q.neighbourhood == neighbourhood
        and q.id != pid and not world.is_offtown(q.id)))
    sign = p.get("sign") or f"{p['name']} has opened: a new {p['kind'].replace('_', ' ')}" + (
        f", open {p['hours']['open']}-{p['hours']['close']}" if p.get("hours") else "") + "."
    seen = []
    for where in announce:
        seen += _changed(engine, inj, where, sign)
    _post(engine, inj, announce + [pid], sign, None, seen, reveals=pid)
    return [pid]


def _place_price(engine, inj):
    p, world = inj["params"], engine.town.world
    place = world.places.get(p["place"])
    thing = place.thing_by_name(p["item"]) if place else None
    if thing is None:
        raise LookupError(f"{p['place']} no longer sells {p['item']!r}")
    old, thing.price = thing.price, float(p["price"])
    text = f"New prices at {place.name}: {thing.name} now ${thing.price:.2f} (was ${old:.2f})."
    seen = _changed(engine, inj, place.id, text)
    _post(engine, inj, [place.id], text, world.time.total_ticks + 7 * clock.TICKS_PER_DAY, seen)
    return [place.id]


def _place_hours(engine, inj):
    p, world = inj["params"], engine.town.world
    place = world.places.get(p["place"])
    if place is None:
        raise LookupError(f"{p['place']} is gone")
    place.open_hours = {"start": _hhmm_tick(p["open"]), "end": _hhmm_tick(p["close"])}
    text = f"New hours at {place.name}: open {p['open']}-{p['close']}."
    seen = _changed(engine, inj, place.id, text)
    _post(engine, inj, [place.id], text, world.time.total_ticks + 7 * clock.TICKS_PER_DAY, seen)
    return [place.id]


def _place_close(engine, inj):
    p, world = inj["params"], engine.town.world
    place = world.places.get(p["place"])
    if place is None:
        raise LookupError(f"{p['place']} is gone")
    first, days = world.time.day, int(p["days"])
    place.closed_on = sorted(set(place.closed_on) | set(range(first, first + days)))
    back = first + days
    text = (f"A sign on the door of {place.name}: closed until Day {back}"
            + (f" - {p['reason']}" if p.get("reason") else "") + ".")
    seen = _changed(engine, inj, place.id, text)
    _post(engine, inj, [place.id], text, (back - 1) * clock.TICKS_PER_DAY, seen)
    return [place.id]


def _place_reopen(engine, inj):
    p, world = inj["params"], engine.town.world
    place = world.places.get(p["place"])
    if place is None:
        raise LookupError(f"{p['place']} is gone")
    place.closed_on = [d for d in place.closed_on if d < world.time.day]
    world.notices = [n for n in world.notices if not (n["kind"] == "place.close" and place.id in n["places"])]
    text = f"{place.name} is open again."
    seen = _changed(engine, inj, place.id, text)
    _post(engine, inj, [place.id], text, world.time.total_ticks + 3 * clock.TICKS_PER_DAY, seen)
    return [place.id]


def _outage(engine, inj):
    town, p = engine.town, inj["params"]
    world = town.world
    now = world.time.total_ticks
    until = int(_until_total(p, town))
    service = str(p["service"]).strip()
    affected = []
    for home in outage_homes(p, town):
        people = sorted(world.places[home].residents_of)
        for rid in people:
            r = town.residents[rid]
            r.problems.append({"kind": service, "inj": inj["id"], "since": now, "until": until,
                               "resolved": False, "text": p.get("text") or f"no {service}"})
            town.touch(rid)
            affected.append(rid)
        text = (f"At home: {p['text']}." if p.get("text") else f"The {service} went off at home.")
        seen = _changed(engine, inj, home, text, only=people)
        _post(engine, inj, [home], text, until, seen, only=people)
    world.scheduled.append({"id": f"{inj['id']}-end", "kind": "_restore", "at": until,
                            "params": {"inj": inj["id"], "service": service}})
    return affected


def _restore(engine, inj):
    town, p = engine.town, inj["params"]
    world = town.world
    affected, homes = [], set()
    for r in town.residents.values():
        for problem in r.problems:
            if problem.get("inj") == p["inj"] and not problem.get("resolved"):
                problem["resolved"] = True
                problem["resolved_at"] = world.time.total_ticks
                problem["resolved_by"] = "schedule"
                affected.append(r.id)
                homes.add(r.home)
                town.touch(r.id)
    world.notices = [n for n in world.notices if n["inj"] != p["inj"]]
    parent = {"id": p["inj"], "kind": "_restore"}
    for home in sorted(homes):
        people = sorted(world.places[home].residents_of) if home in world.places else []
        text = f"The {p['service']} came back on at home."
        seen = _changed(engine, parent, home, text, only=people)
        _post(engine, parent, [home], text, world.time.total_ticks + clock.TICKS_PER_DAY, seen, only=people)
    return affected


def _until_total(p, town) -> int:
    from . import parse_at
    return parse_at(p["until"], town)


def _weather(engine, inj):
    town, p = engine.town, inj["params"]
    world = town.world
    until = _until_total(p, town)
    places = sorted(pid for pid in world.places if not world.is_offtown(pid))
    seen = []
    for pid in places:
        if world.occupants(pid):
            seen += _changed(engine, inj, pid, f"The weather: {p['text']}.")
    _post(engine, inj, places, f"The weather: {p['text']}.", until, seen)
    return []


def _notice(engine, inj):
    p, world = inj["params"], engine.town.world
    if p["place"] not in world.places:
        raise LookupError(f"{p['place']} is gone")
    text = f"A notice at {world.places[p['place']].name}: \"{p['text']}\""
    until = _until_total(p, engine.town) if p.get("until") is not None else None
    seen = _changed(engine, inj, p["place"], text)
    _post(engine, inj, [p["place"]], text, until, seen)
    return [p["place"]]


def _letter(engine, inj):
    town, p = engine.town, inj["params"]
    world = town.world
    r = town.residents[p["to"]]
    if p.get("via", "letter") == "text":
        event = Event(kind="noticed", day=world.time.day, tick=world.time.tick,
                      location_id=world.location_of(r.id), actor=r.id, actor_name=r.name,
                      detail=f"A text from {p['from']}: \"{p['text']}\"",
                      importance=IMPORTANCE["event.letter"], tags=(inj["kind"], inj["id"]))
        engine.emit_seen(event, [], source=_source(inj))
        if p.get("problem"):
            r.problems.append({"kind": p["problem"]["kind"], "inj": inj["id"], "since": world.time.total_ticks,
                               "until": None, "resolved": False,
                               "text": p["problem"].get("text") or p["problem"]["kind"]})
            town.touch(r.id)
        return [r.id]
    if p.get("problem"):
        # A letter can bring a problem with it: a wrong bill is something to sort out.
        r.problems.append({"kind": p["problem"]["kind"], "inj": inj["id"], "since": world.time.total_ticks,
                           "until": None, "resolved": False,
                           "text": p["problem"].get("text") or p["problem"]["kind"]})
        town.touch(r.id)
    text = f"A letter from {p['from']}: \"{p['text']}\""
    _post(engine, inj, [r.home], text, None, [], only=[r.id])
    return [r.id]


def _arrival(engine, inj):
    town, p = engine.town, inj["params"]
    world = town.world
    rid = resident_id(len(town.residents) + 1, "", "")
    n = len(town.residents) + 1
    while rid in town.residents:
        n += 1
        rid = resident_id(n, "", "")
    host = town.residents.get(p.get("host") or "")
    home = host.home if host else p["home"]
    hangout = p.get("hangout") or next((q.id for q in sorted(world.places.values(), key=lambda q: q.id)
                                        if q.public and not world.is_offtown(q.id)), home)
    schedule = [ScheduleEntry(0, 14, "sleep", home), ScheduleEntry(14, 16, "eat", home),
                ScheduleEntry(16, 18, "home", home), ScheduleEntry(18, 34, "out", hangout),
                ScheduleEntry(34, 44, "home", home), ScheduleEntry(44, clock.TICKS_PER_DAY, "sleep", home)]
    kinds = town.config.needs["kinds"]
    newcomer = Resident(
        id=rid, name=p["name"], age=int(p["age"]), home=home,
        persona={"gender": p.get("gender", "person"), "descriptor": p["descriptor"],
                 "personality": p.get("personality") or "new in town and finding their feet",
                 "speech_style": p.get("speech_style") or "plain and a little careful",
                 "public_bio": p.get("public_bio") or f"new in town, staying at {world.places[home].name}",
                 "long_term_goal": p.get("long_term_goal") or "settle in", "secret": "",
                 "arrived_day": world.time.day},
        schedule=schedule, needs={k: float(v["start"]) for k, v in kinds.items()},
        money=float(p.get("money", 100)), household=(host.household if host else ""),
        neighbourhood=world.places[home].neighbourhood)
    newcomer.phone["number"] = phone_number_for(town.seed, rid)
    town.residents[rid] = newcomer
    if rid not in world.places[home].residents_of:
        world.places[home].residents_of.append(rid)
    if host:
        for other in [host.id] + [x for x in world.places[home].residents_of if x not in (rid, host.id)]:
            o = town.residents[other]
            newcomer.relationships[other] = Relationship("the people I'm staying with", 3, trust=30, stage=2)
            o.relationships[rid] = Relationship("staying with us", 2, trust=30, stage=2)
            newcomer.names_known[other] = {"day": world.time.day, "how": "said"}
            o.names_known[rid] = {"day": world.time.day, "how": "said"}
            town.touch(other)
    town.reindex_names()
    from ..state import locality
    newcomer.circle = locality.circle(town, newcomer)
    newcomer.places_known = locality.places_known(town, newcomer)
    world.place(rid, home)
    town.touch(rid)
    engine.emit(engine.event("arrive", newcomer), source=_source(inj))
    return [rid]


def _dispatch(engine, inj):
    """Somebody a service sent round, at the customer's home."""
    town, p = engine.town, inj["params"]
    service = town.services.get(p["service"])
    r = town.residents.get(p["resident"])
    if service is None or r is None:
        raise LookupError("the service or the customer is gone")
    fixed = []
    if p.get("fixes", True):
        from ..agents.contact import resolve_problems
        fixed = resolve_problems(r, service, town.world.time.total_ticks, town, p.get("kind"))
        town.touch(r.id)
    text = (f"Somebody from {service['name']} came round"
            + (f" and sorted the {', '.join(fixed)}." if fixed else "."))
    people = sorted(town.world.places[r.home].residents_of) if r.home in town.world.places else [r.id]
    parent = {"id": inj["id"], "kind": "_dispatch"}
    seen = _changed(engine, parent, r.home, text, only=people)
    _post(engine, parent, [r.home], text, town.world.time.total_ticks + clock.TICKS_PER_DAY, seen, only=people)
    return [r.id]


def _register(engine, inj):
    p = dict(inj["params"])
    p.setdefault("channels", ["text"])
    p.setdefault("known_by", "everyone")
    engine.town.services[p["id"]] = p
    return []


APPLY = {
    "place.new": _place_new, "place.price": _place_price, "place.hours": _place_hours,
    "place.close": _place_close, "place.reopen": _place_reopen, "event.outage": _outage,
    "event.weather": _weather, "event.notice": _notice, "event.letter": _letter,
    "event.arrival": _arrival, "service.register": _register, "_restore": _restore,
    "_dispatch": _dispatch,
}
