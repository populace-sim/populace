"""People's own lives: the weekly review, and leaving town.

Ported from Alive's `residents.py`. Once a week, offset per person so a whole
town does not reconsider its life on the same night, a resident's reflection
carries the longer view, and what they choose becomes a stage and a goal - the
thing on their mind, not a fact. They still have to go and do it.

Choices: keep, seek work, quit, leave town, make an offer. Moving out and
raising rent belonged to Alive's housing ladder and are not in v1 (owner's
decision at step 1).

Leaving happens on the day named, from wherever they are, after the morning:
they are seen going by whoever is there, and everybody else finds out by
noticing they have not been in.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

from ..state.resident import Resident
from .events import known_as

if TYPE_CHECKING:  # pragma: no cover
    from ..state.town import Town
    from .engine import Engine

CHOICES = ("keep", "seek_work", "quit", "leave_town", "make_offer")
LEAVE_TICK = 18


class ArcRefused(Exception):
    """The world does not support it: the week is a keep, and nothing is said."""


def review_due(resident: Resident, day: int, every: int) -> bool:
    if day < every:
        return False
    offset = int(hashlib.sha256(f"review|{resident.id}".encode()).hexdigest()[:6], 16) % every
    if (day - offset) % every != 0:
        return False
    return int((resident.arc or {}).get("last_review_day", 0)) < day


def validate_arc(raw: Any, resident: Resident, town: "Town") -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ArcRefused("the review was not an object")
    choice = str(raw.get("choice") or "keep").strip().lower()
    if choice not in CHOICES:
        raise ArcRefused(f"no such choice: {choice!r}")
    reason = str(raw.get("reason") or "").strip()[:200]
    day = town.world.time.day
    out: dict[str, Any] = {"choice": choice, "reason": reason}
    if choice == "keep":
        return out
    if choice == "seek_work":
        where = str(raw.get("workplace") or "").strip()
        place = town.world.places.get(where)
        if place is None or not place.hires:
            raise ArcRefused(f"nobody at {where!r} does the hiring")
        if resident.job and resident.job.workplace == where:
            raise ArcRefused("they already work there")
        out["workplace"] = where
        return out
    if choice == "quit":
        if not resident.job:
            raise ArcRefused("they have no job to leave")
        if not reason:
            raise ArcRefused("nobody walks out of a job for no reason they could name")
        out["workplace"] = resident.job.workplace
        return out
    if choice == "leave_town":
        if not reason:
            raise ArcRefused("no reason given")
        try:
            when = int(raw.get("day", 0))
        except (TypeError, ValueError):
            raise ArcRefused("the day has to be a number") from None
        if not day + 2 <= when <= day + 7:
            raise ArcRefused(f"day {when} is not between {day + 2} and {day + 7}")
        out["day"] = when
        return out
    if choice == "make_offer":
        to = str(raw.get("to") or "").strip()
        if to not in town.residents or to == resident.id:
            raise ArcRefused(f"there is nobody called {to!r}")
        what = str(raw.get("what") or "").strip()[:120]
        if not what:
            raise ArcRefused("an offer of nothing is not an offer")
        out.update(to=to, what=what)
        return out
    raise ArcRefused(f"{choice!r} is not built")


def goal_for(choice: dict[str, Any], resident: Resident, town: "Town") -> str:
    kind = choice["choice"]
    if kind == "seek_work":
        place = town.world.places[choice["workplace"]]
        boss = town.residents.get((place.hires or [None])[0] or "")
        return f"Ask {known_as(boss, resident) if boss else 'whoever does the hiring'} for work at {place.name} this week"
    if kind == "quit":
        place = town.world.places.get(choice.get("workplace", ""))
        return f"Tell them at {place.name if place else 'work'} that I am done"
    if kind == "leave_town":
        return f"Leave town on Day {choice['day']} - and tell the people who should hear it first"
    if kind == "make_offer":
        other = town.residents.get(choice["to"])
        return f"Put it to {known_as(other, resident) if other else 'them'}: {choice['what']}"
    return ""


def apply_arc(choice: dict[str, Any], resident: Resident, town: "Town") -> None:
    arc = dict(resident.arc or {})
    arc["last_review_day"] = town.world.time.day
    if choice["choice"] != "keep":
        arc.update(stage=choice["choice"], since_day=town.world.time.day, detail=choice.get("reason", ""))
    if choice["choice"] == "leave_town":
        arc["leave_day"] = int(choice["day"])
    goal = goal_for(choice, resident, town)
    if goal:
        arc["goal"] = goal
        resident.goals_active = [goal] + [g for g in resident.goals_active if g != goal][:2]
    resident.arc = arc
    town.touch(resident.id)


def check_departures(engine: "Engine") -> None:
    """Anybody whose day has come, after the morning, goes: seen by whoever is there."""
    town = engine.town
    world = town.world
    if world.time.tick < LEAVE_TICK:
        return
    offtown = world.offtown_id()
    for r in list(town.present()):
        leave_day = (r.arc or {}).get("leave_day")
        if leave_day is None or int(leave_day) > world.time.day or offtown is None:
            continue
        engine.emit(engine.event("leave_town", r, detail=(r.arc or {}).get("detail", "")), 8)
        r.away = {"kind": "gone", "since_day": world.time.day, "home": r.home}
        r.arc = {**(r.arc or {}), "stage": "gone", "since_day": world.time.day}
        world.place(r.id, offtown)
        release(town, r)
        town.touch(r.id)


def release(town: "Town", resident: Resident) -> None:
    """Off the rosters. Their file and everybody's memories of them stay."""
    if resident.job:
        place = town.world.places.get(resident.job.workplace)
        if place is not None:
            place.workplace_of = [x for x in place.workplace_of if x != resident.id]
        resident.job = None
    for place in town.world.places.values():
        place.residents_of = [x for x in place.residents_of if x != resident.id]
        if resident.id in place.hires:
            place.hires = [x for x in place.hires if x != resident.id]
        if place.owner == resident.id:
            place.owner = (place.hires or [None])[0]
        for opening in place.openings:
            opening["filled_by"] = [x for x in opening.get("filled_by", []) if x != resident.id]
