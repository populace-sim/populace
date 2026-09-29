"""Dropping things into a running town: places, events, notices, services.

    from populace.inject import inject
    inject(town, {"kind": "place.close", "at": "Day 2 07:00",
                  "params": {"place": "diner", "days": 3, "reason": "a burst pipe"}})

or from the command line, dry run by default:

    populace inject towns/x --file schedule.json [--write]

An injection is something somebody could perceive. It never touches a mind:
nobody is told how to feel, what to believe or what to do, and nothing is
written into anybody's memory directly. It becomes events through the ordinary
witness rule, and a notice that people who come by later notice once. What a
resident then does about it is up to them.

Validation refuses, out loud and on the record: an unknown kind, an unknown
place or resident, a time already past, a closure longer than two weeks, a
duplicate, any free text naming a resident, and any text or field that reaches
into a mind ("you feel", "everyone knows", a `beliefs` field). Every refusal
is kept in the world's `refused` list with its reason.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import TYPE_CHECKING, Any

from .. import clock, words as W

if TYPE_CHECKING:  # pragma: no cover
    from ..state.town import Town

KINDS = {
    "place.new": "a new place opens: name, kind, hours, things for sale",
    "place.price": "a price changes at a place",
    "place.hours": "a place's opening hours change",
    "place.close": "a place shuts for up to fourteen days, with a reason on the door",
    "place.reopen": "a shut place opens again",
    "event.outage": "a service goes off at some homes until a time",
    "event.weather": "weather everybody out and about can see",
    "event.notice": "a notice posted at a place",
    "event.arrival": "a newcomer arrives in town",
    "event.letter": "a letter or a text reaches one resident",
    "service.register": "an outside service residents may contact",
}
MAX_CLOSE_DAYS = 14
# Phrases that reach into a mind rather than describe the world.
MIND_PHRASES = (
    "you feel", "you think", "you believe", "you remember", "you decide", "you want",
    "you know", "you are angry", "you are sad", "you are happy", "you love", "you hate",
    "everyone feels", "everybody feels", "everyone knows", "everybody knows", "everyone thinks",
    "everybody thinks", "people feel", "residents feel", "makes you feel", "make you feel",
    "will want to", "will decide", "should feel",
)
MIND_KEYS = {"memory", "memories", "belief", "beliefs", "sentiment", "trust", "mood", "feelings",
             "goal", "goals", "relationship", "relationships", "intent", "decision"}
TEXT_KEYS = ("text", "reason", "sign", "name", "description", "purpose", "from", "descriptor")


class InjectionRefused(ValueError):
    pass


def parse_at(at: Any, town: "Town") -> int:
    """`"now"`, `"Day 2 07:00"`, or `{"day": 2, "time": "07:00"}`, as a total tick."""
    now = town.world.time.total_ticks
    if at in (None, "now"):
        return now
    if isinstance(at, dict):
        day, hhmm = at.get("day"), str(at.get("time", "00:00"))
    else:
        m = re.fullmatch(r"\s*Day\s+(\d+)\s+(\d{1,2}:\d{2})\s*", str(at))
        if not m:
            raise InjectionRefused(f"'at' must be \"now\", \"Day N HH:MM\" or {{day, time}}; got {at!r}")
        day, hhmm = m.group(1), m.group(2)
    try:
        hours, minutes = (int(x) for x in hhmm.split(":"))
        day = int(day)
    except (TypeError, ValueError):
        raise InjectionRefused(f"cannot read the time {at!r}") from None
    if day < 1 or not (0 <= hours < 24 and 0 <= minutes < 60):
        raise InjectionRefused(f"no such time: {at!r}")
    return (day - 1) * clock.TICKS_PER_DAY + (hours * 60 + minutes) // clock.MINUTES_PER_TICK


def label(total: int) -> str:
    day, tick = divmod(total, clock.TICKS_PER_DAY)
    return f"Day {day + 1} {clock.tick_to_hhmm(tick)}"


def injection_id(kind: str, at: int, params: dict[str, Any]) -> str:
    body = json.dumps({"kind": kind, "at": at, "params": params}, sort_keys=True, default=str)
    return "i" + hashlib.sha256(body.encode()).hexdigest()[:10]


def _texts(params: Any) -> list[str]:
    out = []
    if isinstance(params, dict):
        for k, v in params.items():
            if isinstance(v, str) and k in TEXT_KEYS:
                out.append(v)
            elif isinstance(v, (dict, list)):
                out += _texts(v)
    elif isinstance(params, list):
        for v in params:
            out += _texts(v)
    return out


def _keys(params: Any) -> set[str]:
    if isinstance(params, dict):
        return set(params) | set().union(*(_keys(v) for v in params.values())) if params else set()
    if isinstance(params, list):
        return set().union(*(_keys(v) for v in params)) if params else set()
    return set()


def _place(town: "Town", pid: Any, what: str = "place") -> str:
    if not isinstance(pid, str) or pid not in town.world.places:
        raise InjectionRefused(f"there is no {what} {pid!r}")
    return pid


def validate(raw: Any, town: "Town") -> dict[str, Any]:
    """A clean injection record, or InjectionRefused with the reason."""
    if not isinstance(raw, dict):
        raise InjectionRefused("an injection is an object with 'kind', 'at' and 'params'")
    kind = raw.get("kind")
    if kind not in KINDS:
        raise InjectionRefused(f"no such kind {kind!r}; the kinds are {', '.join(KINDS)}")
    params = raw.get("params") or {}
    if not isinstance(params, dict):
        raise InjectionRefused("'params' must be an object")
    at = parse_at(raw.get("at", "now"), town)
    if at < town.world.time.total_ticks:
        raise InjectionRefused(f"{label(at)} has already passed; it is {label(town.world.time.total_ticks)}")
    touched = sorted(_keys(params) & MIND_KEYS)
    if touched:
        raise InjectionRefused(f"an injection cannot set {', '.join(touched)}: it changes the world, never a mind")
    for text in _texts(params):
        if W.contains(text, MIND_PHRASES):
            raise InjectionRefused(f"{text!r} reaches into a mind ({', '.join(W.found(text, MIND_PHRASES))}); "
                                   "describe what can be seen or read instead")
        named = [r.name for r in town.residents.values() if re.search(rf"\b{re.escape(r.name)}\b", text)]
        if named:
            raise InjectionRefused(f"{text!r} names {', '.join(named)}; refer to residents by id "
                                   "in the fields meant for it, so nobody learns a name they were not given")
    _check(kind, params, at, town)
    record = {"id": injection_id(kind, at, params), "kind": kind, "at": at, "params": params}
    known = {m["id"] for m in town.world.scheduled + town.world.injected if "id" in m}
    if record["id"] in known:
        raise InjectionRefused(f"this exact injection is already in the town ({record['id']})")
    return record


def _until(params: dict[str, Any], town: "Town", at: int, required: bool) -> int | None:
    if params.get("until") is None:
        if required:
            raise InjectionRefused("'until' is required")
        return None
    until = parse_at(params["until"], town)
    if until <= at:
        raise InjectionRefused(f"'until' ({label(until)}) must come after 'at' ({label(at)})")
    return until


def _check(kind: str, p: dict[str, Any], at: int, town: "Town") -> None:
    world = town.world
    if kind == "place.new":
        if not str(p.get("name") or "").strip() or not str(p.get("kind") or "").strip():
            raise InjectionRefused("a new place needs a 'name' and a 'kind'")
        if any(pl.name == p["name"] for pl in world.places.values()):
            raise InjectionRefused(f"there is already a place called {p['name']!r}")
        for pid in p.get("announce_at") or []:
            _place(town, pid, "place to announce it at")
        if p.get("owner") is not None and p["owner"] not in town.residents:
            raise InjectionRefused(f"there is no resident {p['owner']!r} to own it")
        for thing in p.get("things") or []:
            if not isinstance(thing, dict) or not thing.get("name") or float(thing.get("price", -1)) < 0:
                raise InjectionRefused(f"a thing for sale needs a 'name' and a 'price': {thing!r}")
    elif kind == "place.price":
        pid = _place(town, p.get("place"))
        if world.places[pid].thing_by_name(str(p.get("item") or "")) is None:
            raise InjectionRefused(f"{world.places[pid].name} sells no {p.get('item')!r}")
        if float(p.get("price", -1)) < 0:
            raise InjectionRefused("'price' must be zero or more")
    elif kind == "place.hours":
        _place(town, p.get("place"))
        for key in ("open", "close"):
            if not re.fullmatch(r"\d{1,2}:\d{2}", str(p.get(key) or "")):
                raise InjectionRefused(f"'{key}' must be HH:MM")
    elif kind == "place.close":
        _place(town, p.get("place"))
        days = p.get("days")
        if not isinstance(days, int) or not 1 <= days <= MAX_CLOSE_DAYS:
            raise InjectionRefused(f"'days' must be a whole number from 1 to {MAX_CLOSE_DAYS}")
    elif kind == "place.reopen":
        _place(town, p.get("place"))
    elif kind == "event.outage":
        if not str(p.get("service") or "").strip():
            raise InjectionRefused("an outage needs the 'service' that went off, e.g. \"internet\"")
        _until(p, town, at, required=True)
        homes = outage_homes(p, town)
        if not homes:
            raise InjectionRefused("the outage reaches no homes: give 'homes', a 'street' or a 'neighbourhood'")
    elif kind == "event.weather":
        if not str(p.get("text") or "").strip():
            raise InjectionRefused("weather needs a 'text', e.g. \"heavy rain\"")
        _until(p, town, at, required=True)
    elif kind == "event.notice":
        _place(town, p.get("place"))
        if not str(p.get("text") or "").strip():
            raise InjectionRefused("a notice needs its 'text'")
        _until(p, town, at, required=False)
    elif kind == "event.arrival":
        for key in ("name", "descriptor"):
            if not str(p.get(key) or "").strip():
                raise InjectionRefused(f"a newcomer needs a '{key}'")
        if not isinstance(p.get("age"), int) or not 13 <= p["age"] <= 100:
            raise InjectionRefused("a newcomer's 'age' must be a whole number from 13 to 100")
        if any(r.name == p["name"] for r in town.residents.values()):
            raise InjectionRefused(f"somebody called {p['name']!r} already lives here")
        host = p.get("host")
        if host is not None and host not in town.residents:
            raise InjectionRefused(f"there is no resident {host!r} to stay with")
        if host is None:
            _place(town, p.get("home"), "home")
        if p.get("hangout") is not None:
            _place(town, p["hangout"], "place to spend the day")
    elif kind == "event.letter":
        if p.get("to") not in town.residents:
            raise InjectionRefused(f"there is no resident {p.get('to')!r} to send it to")
        if p.get("via", "letter") not in ("letter", "text"):
            raise InjectionRefused("'via' is \"letter\" or \"text\"")
        if not str(p.get("text") or "").strip() or not str(p.get("from") or "").strip():
            raise InjectionRefused("a letter needs a 'from' and a 'text'")
        if p.get("problem") is not None and (not isinstance(p["problem"], dict) or not p["problem"].get("kind")):
            raise InjectionRefused("a letter's 'problem' needs a 'kind', e.g. {\"kind\": \"billing\"}")
    elif kind == "service.register":
        sid = str(p.get("id") or "")
        if not re.fullmatch(r"[a-z][a-z0-9_]{1,30}", sid):
            raise InjectionRefused("a service needs an 'id' of lower-case letters, digits and underscores")
        if sid in town.services or sid in world.places or sid in town.residents:
            raise InjectionRefused(f"the id {sid!r} is already taken")
        if not str(p.get("name") or "").strip() or not str(p.get("purpose") or "").strip():
            raise InjectionRefused("a service needs a 'name' and a 'purpose'")
        if p.get("storefront") is not None:
            # A counter may be a place an earlier injection is about to open.
            coming = {(m["params"].get("id") or ""): int(m["at"]) for m in world.scheduled
                      if m["kind"] == "place.new"}
            if not (p["storefront"] in coming and coming[p["storefront"]] <= at):
                _place(town, p["storefront"], "storefront")
        known = p.get("known_by", "everyone")
        if isinstance(known, list):
            unknown = [x for x in known if x not in town.residents]
            if unknown:
                raise InjectionRefused(f"'known_by' names residents who do not exist: {unknown}")


def outage_homes(p: dict[str, Any], town: "Town") -> list[str]:
    places = town.world.places
    if p.get("homes"):
        for pid in p["homes"]:
            _place(town, pid, "home")
        return sorted(p["homes"])
    if p.get("street"):
        return sorted(pid for pid, pl in places.items() if not pl.public and pl.street == p["street"]
                      and pl.residents_of)
    if p.get("neighbourhood"):
        return sorted(pid for pid, pl in places.items() if not pl.public
                      and pl.neighbourhood == p["neighbourhood"] and pl.residents_of)
    return []


def refuse(town: "Town", raw: Any, reason: str) -> None:
    town.world.refused.append({"at": town.world.time.total_ticks, "raw": raw, "reason": reason})


def inject(town: "Town", raw: Any) -> dict[str, Any]:
    """Validate and schedule one injection; refused ones are recorded and raised."""
    try:
        record = validate(raw, town)
    except InjectionRefused as exc:
        refuse(town, raw, str(exc))
        raise
    town.world.scheduled.append(record)
    return record


def inject_many(town: "Town", raws: list[Any]) -> tuple[list[dict[str, Any]], list[tuple[Any, str]]]:
    done, refused = [], []
    for raw in raws:
        try:
            done.append(inject(town, raw))
        except InjectionRefused as exc:
            refused.append((raw, str(exc)))
    return done, refused
