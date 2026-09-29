"""Deals: the moment a line stops being talk and moves the world.

Ported from Alive's `deals.py`, twelve of its twenty-six: hire, fire, quit,
loan, repay, promise, gift, gift_accept, number, invite, accept, introduce.
Every deal is checked against the world before it happens: the standing to
make it, the means to keep it, both people in the room. The line stands either
way, because they did say it.

**One change: a deal that does not hold up tells the speaker.** In Alive it was
dropped and logged, so a shopkeeper who "hired" somebody with no job going
never learned that nothing happened. Here the reason goes into the speaker's
own memory as a refusal, the same way any other action that cannot happen does.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from ..state.resident import Job, Resident, clear_work_blocks, set_work_block
from . import economy as E
from .events import known_as

if TYPE_CHECKING:  # pragma: no cover
    from .engine import Engine

Handler = Callable[["Engine", Resident, Resident, dict[str, Any], int], "str | None"]
_REGISTRY: dict[str, Handler] = {}
MONEY_WORDS = ("pay", "pays", "paid", "owe", "owes", "owed", "rent", "dollar", "dollars", "cash")


def deal(kind: str) -> Callable[[Handler], Handler]:
    def register(fn: Handler) -> Handler:
        _REGISTRY[kind] = fn
        return fn
    return register


def kinds() -> list[str]:
    return sorted(_REGISTRY)


def apply_all(engine: "Engine", result) -> list[dict[str, Any]]:
    """Whatever a finished conversation carried, in the order it was said, one
    of each kind per speaker: nobody is hired twice in one exchange."""
    outcomes = []
    done: set[tuple[str, str, str]] = set()
    for entry in result.deals:
        payload = entry.get("deal") or {}
        key = (str(entry.get("speaker")), str(payload.get("kind") or ""),
               str(payload.get("what") or "") if payload.get("kind") == "promise" else "")
        if key in done:
            continue
        done.add(key)
        outcomes.append(apply_one(engine, result, entry.get("speaker"), payload,
                                  int(entry.get("line_no", 0))))
    return outcomes


def apply_one(engine: "Engine", result, speaker_id, raw, line_no: int) -> dict[str, Any]:
    town = engine.town
    payload = dict(raw) if isinstance(raw, dict) else {}
    kind = str(payload.get("kind") or "").strip().lower()
    other_id = result.target if speaker_id == result.initiator else result.initiator
    outcome = {"kind": kind, "speaker": speaker_id, "other": other_id, "ok": False, "reason": ""}
    if payload.get("accept") is False:
        outcome.update(ok=True, reason="declined", declined=True)
        return outcome
    handler = _REGISTRY.get(kind)
    speaker = town.residents.get(speaker_id)
    other = town.residents.get(other_id)
    if speaker is None or other is None:
        outcome["reason"] = "one of them is not a person here"
    elif handler is None:
        outcome["reason"] = f"there is no such thing as a {kind!r} deal"
    else:
        try:
            reason = handler(engine, speaker, other, payload, line_no)
        except Exception as exc:  # a bad deal must never break a tick
            reason = f"{type(exc).__name__}: {exc}"
        outcome["ok"] = reason is None
        outcome["reason"] = reason or ""
    if not outcome["ok"] and speaker is not None:
        from .actions import Action
        engine._refuse(speaker, Action(kind or "deal"), outcome["reason"])
    for rid in (speaker_id, other_id):
        if rid in town.residents:
            town.touch(rid)
    return outcome


def _name(who: Resident, viewer: Resident) -> str:
    return known_as(who, viewer)


@deal("hire")
def _hire(engine, speaker, other, payload, line_no):
    """You run the place, there is work going, and the terms are the opening's:
    a hire cannot invent its own wage."""
    world = engine.town.world
    title = str(payload.get("title") or "").strip()
    found = None
    for pid in sorted(world.places):
        place = world.places[pid]
        if speaker.id not in place.hires:
            continue
        opening = place.opening(title or None) or (place.opening(None) if title else None)
        if opening is not None:
            found = (place, opening)
            break
    if found is None:
        return "I have no work going" + (f" called {title!r}" if title else "")
    if other.job is not None:
        return f"{_name(other, speaker)} already has a job; that would have to end first"
    place, opening = found
    start_today = str(payload.get("start") or "tomorrow").lower() == "today"
    job = Job(title=str(opening["title"]), workplace=place.id,
              wage_per_tick=float(opening["wage_per_tick"]), shift_start=int(opening["shift"]["start"]),
              shift_end=int(opening["shift"]["end"]), days=list(opening.get("days", [0, 1, 2, 3, 4])),
              employer_id=speaker.id, start_day=world.time.day + (0 if start_today else 1),
              hired_day=world.time.day)
    other.job = job
    set_work_block(other, place.id, job.shift_start, job.shift_end)
    other.routine_days = sorted(job.days)
    other.persona["status"] = "worker"
    opening.setdefault("filled_by", []).append(other.id)
    place.workplace_of = sorted(set(place.workplace_of) | {other.id})
    engine.emit(engine.event("hired", speaker, target=other.id, location_id=place.id, detail=(
        f"{job.title}, ${job.wage_per_tick:.2f} the half hour, {job.shift_label()}, "
        f"from {'today' if start_today else 'tomorrow'}")))
    return None


@deal("fire")
def _fire(engine, speaker, other, payload, line_no):
    job = other.job
    if job is None:
        return f"{_name(other, speaker)} does not work for anybody"
    place = engine.town.world.places.get(job.workplace)
    if place is None or speaker.id not in place.hires:
        return f"{_name(other, speaker)} does not work for me"
    _leave_job(other, place)
    engine.emit(engine.event("fired", speaker, target=other.id))
    return None


@deal("quit")
def _quit(engine, speaker, other, payload, line_no):
    """Said to the person who pays you, or it is only said."""
    job = speaker.job
    if job is None:
        return "I do not work for anybody"
    place = engine.town.world.places.get(job.workplace)
    if place is None or other.id not in place.hires:
        return f"{_name(other, speaker)} is not who I answer to"
    _leave_job(speaker, place)
    arc = dict(speaker.arc or {})
    if arc.get("stage") == "quit":
        goal = arc.get("goal")
        arc.update(stage="done", goal="", detail="")
        speaker.goals_active = [g for g in speaker.goals_active if g != goal]
    speaker.arc = arc
    engine.emit(engine.event("quit", speaker, target=other.id, location_id=place.id, detail=job.title))
    return None


def _leave_job(resident: Resident, place) -> None:
    clear_work_blocks(resident)
    resident.job = None
    resident.routine_days = None
    resident.off_schedule = []
    resident.persona["status"] = "between_jobs"
    for opening in place.openings:
        if resident.id in opening.get("filled_by", []):
            opening["filled_by"].remove(resident.id)
    place.workplace_of = [r for r in place.workplace_of if r != resident.id]


@deal("loan")
def _loan(engine, speaker, other, payload, line_no):
    config = engine.config
    try:
        amount = round(float(payload.get("amount", 0)), 2)
    except (TypeError, ValueError):
        return "a loan needs an amount"
    if amount < 1:
        return "that is not worth lending anybody"
    cap = E.loan_cap(speaker, other.id, config)
    if cap <= 0:
        return f"I would not put money in {_name(other, speaker)}'s hand yet"
    amount = min(amount, cap)
    if speaker.money - amount < float(config.economy["loan_min_reserve"]):
        return "I have not got it to lend"
    time = engine.town.world.time
    try:
        days = int(payload.get("due_in_days", config.economy["loan_default_due_days"]))
    except (TypeError, ValueError):
        days = int(config.economy["loan_default_due_days"])
    due = time.day + max(1, min(14, days))
    speaker.money = round(speaker.money - amount, 2)
    other.money = round(other.money + amount, 2)
    E.add_obligation(other, speaker, "loan", amount, time.day, due_day=due)
    engine.emit(engine.event("loan", speaker, target=other.id, amount=amount, detail=f"Due back Day {due}."))
    return None


@deal("repay")
def _repay(engine, speaker, other, payload, line_no):
    """They hand you money against what they owe you, and you take it. Asserted
    by the creditor; the money and the memory belong to the one paying."""
    offer = engine.offers.get(other.id) or {}
    offered = offer.get("money") if offer.get("to") == speaker.id else None
    if not offered:
        return f"{_name(other, speaker)} did not offer anything this half hour"
    rent = other.rent or {}
    is_landlord = rent.get("landlord_id") == speaker.id
    arrears = float(rent.get("owed", 0.0)) if is_landlord else 0.0
    owed = other.owes_to(speaker.id)
    if owed + arrears <= 0:
        return f"{_name(other, speaker)} owes me nothing"
    amount = round(min(float(offered), other.money, owed + arrears), 2)
    if amount < 1:
        return "there was nothing there to hand over"
    today = engine.town.world.time.day
    late = any(e.get("to") == speaker.id and int(e.get("due_day") or today) < today
               for e in other.obligations.get("owes", []))
    other.money = round(other.money - amount, 2)
    speaker.money = round(speaker.money + amount, 2)
    left = round(amount - E.settle(other, speaker, amount), 2)
    if left > 0 and arrears > 0:
        rent["owed"] = round(arrears - left, 2)
    still = round(other.owes_to(speaker.id) + (float(rent.get("owed", 0.0)) if is_landlord else 0.0), 2)
    engine.emit(engine.event("repay", other, target=speaker.id, amount=amount,
                             detail="That clears it." if still <= 0.009 else f"Still owe ${still:.0f}.",
                             tags=("late",) if late else ()))
    return None


def _about_money(what: str) -> bool:
    from .. import words as W
    return "$" in what or W.contains(what, MONEY_WORDS)


@deal("promise")
def _promise(engine, speaker, other, payload, line_no):
    """In both heads, judged at the end of the day it was due, on the record."""
    what = str(payload.get("what") or "").strip()[:120]
    if not what:
        return "a promise has to be about something"
    by = str(payload.get("by") or "me").lower()
    by = by if by in {"me", "them"} else "me"
    try:
        in_days = max(1, min(14, int(payload.get("in_days", 2))))
    except (TypeError, ValueError):
        in_days = 2
    time = engine.town.world.time
    promiser, promisee = (speaker, other) if by == "me" else (other, speaker)
    entry = {"what": what, "made_day": time.day, "by_day": time.day + in_days, "status": "open",
             "about": "money" if _about_money(what) else "other"}
    rent = promiser.rent or {}
    owed_when_made = promiser.owes_to(promisee.id) + (
        float(rent.get("owed", 0.0) or 0.0) if rent.get("landlord_id") == promisee.id else 0.0)
    promiser.relationship_with(promisee.id).add_promise({**entry, "by": "me", "owed_when_made": owed_when_made})
    promisee.relationship_with(promiser.id).add_promise({**entry, "by": "them", "owed_when_made": owed_when_made})
    engine.emit(engine.event("promise", promiser, target=promisee.id, detail=f"{what} - by Day {entry['by_day']}"))
    return None


@deal("gift")
def _gift(engine, speaker, other, payload, line_no):
    try:
        money = round(float(payload.get("money", 0) or 0), 2)
    except (TypeError, ValueError):
        money = 0.0
    if money <= 0:
        return "a gift has to be something"
    if speaker.money < money:
        return "I have not got it"
    speaker.money = round(speaker.money - money, 2)
    other.money = round(other.money + money, 2)
    engine.emit(engine.event("gift", speaker, target=other.id, amount=money, detail=f"${money:.0f}"))
    return None


@deal("gift_accept")
def _gift_accept(engine, speaker, other, payload, line_no):
    """They offered you something and you are taking it: it lands when your
    own reply takes it."""
    offer = engine.offers.get(other.id) or {}
    money = offer.get("money") if offer.get("to") == speaker.id else None
    if not money:
        return f"{_name(other, speaker)} has not offered me anything"
    return _gift(engine, other, speaker, {"money": money}, line_no)


@deal("number")
def _number(engine, speaker, other, payload, line_no):
    stage = speaker.trust_stage(other.id, tuple(engine.config.trust["thresholds"]))
    if stage < int(engine.config.trust["number_min_stage"]):
        return f"I would not hand {_name(other, speaker)} my number yet"
    from . import phone as PH
    PH.exchange_numbers(speaker, other)
    speaker.relationship_with(other.id).number_shared = True
    engine.emit(engine.event("number", speaker, target=other.id))
    return None


@deal("invite")
def _invite(engine, speaker, other, payload, line_no):
    world = engine.town.world
    where = str(payload.get("where") or "").strip()
    if where not in world.places or not world.places[where].public:
        return f"there is no {where or 'such place'} to meet at"
    try:
        in_ticks = max(1, min(24, int(payload.get("in_ticks", 4))))
    except (TypeError, ValueError):
        in_ticks = 4
    engine.meetups.append({"who": sorted((speaker.id, other.id)), "where": where,
                           "at": world.time.total_ticks + in_ticks, "asked_by": speaker.id,
                           "accepted": False})
    engine.emit(engine.event("invite", speaker, target=other.id,
                             detail=f"meet at {world.places[where].name}"))
    return None


@deal("accept")
def _accept(engine, speaker, other, payload, line_no):
    pair = sorted((speaker.id, other.id))
    for meetup in engine.meetups:
        if meetup["who"] == pair and not meetup["accepted"]:
            meetup["accepted"] = True
            engine.emit(engine.event("accept", speaker, target=other.id,
                                     detail=engine.town.world.places[meetup["where"]].name))
            return None
    return f"{_name(other, speaker)} has not asked me anywhere"


@deal("introduce")
def _introduce(engine, speaker, other, payload, line_no):
    town = engine.town
    third_id = str(payload.get("to") or "").strip()
    third = town.residents.get(third_id)
    if third is None or third_id in {speaker.id, other.id}:
        return "there is nobody to introduce them to"
    if speaker.trust_stage(other.id, tuple(engine.config.trust["thresholds"])) < \
            int(engine.config.trust["introduce_min_stage"]):
        return f"I would not put my name on {_name(other, speaker)}"
    if not speaker.has_met(third_id):
        return f"I do not know {_name(third, speaker)}"
    world = town.world
    present = third_id in world.occupants(world.location_of(speaker.id))
    for a, b in ((other, third), (third, other)):
        rel = a.relationship_with(b.id)
        rel.add_note(f"{speaker.name} introduced us." if present else f"{speaker.name} says I should talk to them.")
        if present:
            rel.met_day = rel.met_day or world.time.day
            a.learn_name(b.id, world.time.day, how="introduced")
        town.touch(a.id)
    if present:
        speaker.learn_name(other.id, world.time.day, how="introduced")
        speaker.learn_name(third_id, world.time.day, how="introduced")
    engine.emit(engine.event("introduced", speaker, target=other.id,
                             detail=third.name if present else "", force_private=not present))
    return None
