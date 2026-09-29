"""How a tick's call budget is spent, and how nobody is starved of it.

New in populace. Alive capped decisions per tick and let dialogue ride on top,
which is how its "cap 5" became 8.3 calls a tick in the only full live log.
Here `scheduler.calls_per_tick` is **every** call in the tick: decisions,
their retries, dialogue lines and phone replies.

* Decisions get `decision_share` of the budget; whatever they leave goes to
  conversations.
* Candidates are ranked by Alive's trigger priorities. Ties rotate with the
  tick, so the same ids do not always win.
* `stale` is a rota: whoever has gone longest without a thought goes first,
  and anybody who has gone `stale_max_days` without one is promoted to `owed`,
  ahead of ordinary staleness.
* `scene` is capped per place per tick, so a busy doorway cannot eat the
  budget.
* Everybody not selected runs their schedule, for free.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .events import Event
from .triggers import CARRYOVER, Trigger, approaches_today, candidate

if TYPE_CHECKING:  # pragma: no cover
    from ..state.town import Town


@dataclass
class Selection:
    decide: list[Trigger] = field(default_factory=list)
    deferred: list[str] = field(default_factory=list)
    candidates: int = 0

    @property
    def names(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for t in self.decide:
            out[t.name] = out.get(t.name, 0) + 1
        return out


def budget(town: "Town") -> tuple[int, int]:
    """(total calls this tick, of which decisions)."""
    cfg = town.config.scheduler
    total = int(cfg["calls_per_tick"])
    decisions = max(1, round(total * float(cfg["decision_share"])))
    return total, min(total, decisions)


def _rotate(town: "Town", rid: str) -> int:
    t = town.world.time
    return int(hashlib.sha256(f"{town.seed}|{t.day}|{t.tick}|{rid}".encode()).hexdigest()[:8], 16)


def select(
    town: "Town",
    last_events: list[Event],
    urgent_now: dict[str, str],
    spoken_today: set[str],
    witnessed: dict[str, list[Event]],
) -> Selection:
    cfg = town.config.scheduler
    _, decision_slots = budget(town)
    cooldown = int(cfg["cooldown_ticks"])
    now = town.world.time.total_ticks
    approaches = approaches_today(spoken_today)
    found: list[Trigger] = []
    for resident in town.present():
        if resident.asleep:
            continue
        hit = candidate(resident, town, last_events, urgent_now, cfg, spoken_today,
                        approaches, witnessed)
        if hit is None:
            continue
        name, about = hit
        fresh = name == "witness" and bool(witnessed.get(resident.id))
        if name != "addressed" and not fresh and now - resident.last_model_tick < cooldown:
            continue
        found.append(Trigger(resident.id, name, about))
    # Stale and owed: longest without a thought first, then a rotating tie-break.
    found.sort(key=lambda t: (t.priority,
                              town.residents[t.resident_id].last_model_tick
                              if t.name in ("stale", "owed") else 0,
                              _rotate(town, t.resident_id)))
    selection = Selection(candidates=len(found))
    scenes_per_place: dict[str, int] = {}
    scene_cap = int(cfg["scene_per_place"])
    for trigger in found:
        if trigger.name == "scene":
            place = town.world.location_of(trigger.resident_id)
            if scenes_per_place.get(place, 0) >= scene_cap:
                continue
            scenes_per_place[place] = scenes_per_place.get(place, 0) + 1
        if len(selection.decide) >= decision_slots:
            selection.deferred.append(trigger.resident_id)
            town.residents[trigger.resident_id].pending_trigger = \
                trigger.name if trigger.name in CARRYOVER else None
            continue
        if trigger.name == "new_face" and trigger.about:
            town.residents[trigger.resident_id].noticed[trigger.about] = town.world.time.day
        town.residents[trigger.resident_id].pending_trigger = None
        selection.decide.append(trigger)
    return selection
