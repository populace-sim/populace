"""Who is worth a model call this tick.

Ported from Alive's `triggers.py`: the priority order, edge-triggered needs
with a hysteresis re-arm, money owed by somebody standing in front of you,
salient people, staleness. Two changes for a town rather than a street, both
because at 200 residents the old rule would fire in every shop every tick:

* `new_face` is for people who **arrived** (an injected newcomer), not for
  everybody you have not met. In a town, most people are strangers, and a
  stranger buying bread is not an event.
* `scene` fires when somebody **you know** arrives or leaves where you are,
  not when anybody does.

The addressed check comes before the phone check. In Alive the phone came
first despite the comment saying otherwise, so somebody spoken to while
holding an unread text answered the text instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..state.resident import Resident
from .events import Event

if TYPE_CHECKING:  # pragma: no cover
    from ..state.town import Town

PRIORITY = {
    "addressed": 1,
    "witness": 2,
    "phone": 3,
    "business": 4,
    "new_face": 5,
    "need": 6,
    # Somebody who has gone `stale_max_days` without a thought outranks the
    # routine reasons below. Without this a 200-person town spent 85 of its
    # 120 daily decisions on people watching family come home, and after four
    # days 89 residents had never thought at all.
    "owed": 7,
    "scene": 8,
    "goal": 9,
    "stale": 10,
}
WITNESS_IMPORTANCE = 7
CARRYOVER = {"addressed", "witness", "phone", "business", "scene", "need", "goal"}
BUSINESS_TO_TARGET = {"rent_missed", "no_show", "debt_overdue", "fired", "quit"}
BUSINESS_TO_ACTOR = {"date"}


@dataclass(frozen=True)
class Trigger:
    resident_id: str
    name: str
    about: str | None = None

    @property
    def priority(self) -> int:
        return PRIORITY[self.name]


def check_urgent(resident: Resident, needs_config: dict, town: "Town") -> str | None:
    """Edge-detect a need crossing into urgency; mutates the re-arm flags."""
    hyst = float(needs_config.get("hysteresis", 10.0))
    fired: str | None = None
    for name, need in needs_config["kinds"].items():
        value = float(resident.needs.get(name, 0.0))
        armed = resident.urgent_armed.get(name, True)
        if "urgent_above" in need:
            line = float(need["urgent_above"])
            if value >= line and armed:
                resident.urgent_armed[name] = False
                fired = fired or name
            elif value < line - hyst:
                resident.urgent_armed[name] = True
        else:
            line = float(need["urgent_below"])
            if value <= line and armed:
                resident.urgent_armed[name] = False
                fired = fired or name
            elif value > line + hyst:
                resident.urgent_armed[name] = True
    rent = resident.rent
    if rent:
        days_to_due = (int(rent["due_weekday"]) - town.world.time.weekday_index) % 7
        due = float(rent["amount"]) + float(rent.get("owed", 0))
        short = resident.money < due
        if short and days_to_due <= 1 and resident.urgent_armed.get("cash", True):
            resident.urgent_armed["cash"] = False
            fired = fired or "cash"
        elif not short or days_to_due > 1:
            resident.urgent_armed["cash"] = True
    return fired


def salient_ids(resident: Resident, today: int | None = None) -> set[str]:
    """People this resident would react to seeing: strong feeling, friction,
    somebody from today's heavier moments."""
    ids = {rid for rid, rel in resident.relationships.items()
           if rel.friction or abs(rel.sentiment) >= 3}
    if today is not None:
        for m in resident.memory:
            if m.day == today and m.importance >= 6:
                ids.update(m.involved)
    ids.discard(resident.id)
    return ids


def pair_key(a: str, b: str) -> str:
    return "|".join(sorted((a, b)))


def present_awake(town: "Town", resident: Resident) -> list[str]:
    here = town.world.location_of(resident.id)
    if town.world.is_offtown(here):
        return []
    return [r for r in town.world.occupants(here)
            if r != resident.id and not town.residents[r].asleep]


def _debtor_present(resident: Resident, town: "Town", spoken_today: set[str]) -> str | None:
    """Somebody standing in front of me with unfinished business, not yet raised
    today: they owe me, or they work for me and keep missing shifts."""
    for rid in present_awake(town, resident):
        if pair_key(resident.id, rid) in spoken_today:
            continue
        other = town.residents[rid]
        rent = other.rent or {}
        owes_rent = rent.get("landlord_id") == resident.id and float(rent.get("owed", 0) or 0) > 0
        absent = bool(other.job and other.job.employer_id == resident.id and other.job.no_shows >= 2)
        if owes_rent or absent or resident.owed_by(rid) > 0:
            return rid
    return None


def _new_face(resident: Resident, town: "Town", approaches: dict[str, int], cap: int) -> str | None:
    """A newcomer to town, here, whom I have not clocked yet."""
    for rid in present_awake(town, resident):
        other = town.residents[rid]
        if other.persona.get("arrived_day") is None:
            continue
        if resident.has_met(rid) or rid in resident.noticed or approaches.get(rid, 0) >= cap:
            continue
        return rid
    return None


def candidate(
    resident: Resident,
    town: "Town",
    last_events: list[Event],
    urgent_now: dict[str, str],
    scheduler_cfg: dict,
    spoken_today: set[str],
    approaches: dict[str, int],
    witnessed: dict[str, list[Event]],
) -> tuple[str, str | None] | None:
    """The single highest-priority reason to spend a call on this resident."""
    if resident.pending_trigger:
        return resident.pending_trigger, None
    world = town.world
    here = world.location_of(resident.id)
    for event in last_events:
        if event.kind in {"conversation", "woken"} and event.target == resident.id:
            return "addressed", event.actor
    for event in witnessed.get(resident.id, ()):
        if event.actor != resident.id and event.base_importance >= WITNESS_IMPORTANCE:
            return "witness", event.actor
    threads = (resident.phone or {}).get("threads", {})
    if any(m.get("to") == resident.id and not m.get("read") for msgs in threads.values() for m in msgs):
        return "phone", None
    for event in last_events:
        if event.kind in BUSINESS_TO_TARGET and event.target == resident.id:
            return "business", event.actor
        if event.kind in BUSINESS_TO_ACTOR and event.actor == resident.id:
            return "business", event.target
    debtor = _debtor_present(resident, town, spoken_today)
    if debtor is not None:
        return "business", debtor
    face = _new_face(resident, town, approaches, int(scheduler_cfg["new_face_max_per_day"]))
    if face is not None:
        return "new_face", face
    for event in last_events:
        if event.kind in {"arrive", "depart"} and event.location_id == here \
                and event.actor != resident.id and event.actor in resident.relationships \
                and town.residents[event.actor].household != resident.household:
            return "scene", event.actor
    if resident.id in urgent_now:
        return "need", None
    from .. import clock

    since = world.time.total_ticks - resident.last_model_tick
    if since >= int(scheduler_cfg["stale_max_days"]) * clock.TICKS_PER_DAY:
        return "owed", None
    salient = set(present_awake(town, resident)) & salient_ids(resident, world.time.day)
    if salient:
        return "goal", sorted(salient)[0]
    company = bool(present_awake(town, resident))
    entry = resident.scheduled_entry(world.time.tick, world.time.weekday_index)
    free_time = entry.activity in {"leisure", "errand"}
    threshold = int(scheduler_cfg["staleness_ticks"]) if (company or free_time) \
        else int(scheduler_cfg["staleness_ticks_idle"])
    if since >= threshold:
        return "stale", None
    return None


def approaches_today(spoken_today: set[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for key in spoken_today:
        for rid in key.split("|"):
            counts[rid] = counts.get(rid, 0) + 1
    return counts
