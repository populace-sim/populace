"""The night: promises judged, reflection within a cap, free recaps for the rest.

New in populace. Alive reflected for every resident every night, which at 200
residents on a laptop is most of an hour. Here `reflection.nightly_cap` sets
how many real reflections a night buys (None means everybody). Who gets one is
a rota: tonight's weekly reviews and anybody who talked to somebody today come
first, then whoever has gone longest without one. Everybody else who had a day
gets a recap the engine writes from their own memories, for free and without
beliefs, so nobody's week is a blank.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from . import lives
from . import reflection as R

if TYPE_CHECKING:  # pragma: no cover
    from .engine import Engine


async def night(engine: "Engine", day: int) -> None:
    town = engine.town
    cfg = town.config.reflection
    for promiser, promisee, kept in R.settle_promises(town, day):
        r = town.residents[promiser]
        engine.emit(engine.event("promise_kept" if kept else "promise_broken", r, target=promisee))

    present = [r for r in town.present()]
    every = int(cfg["review_every_days"])
    reviewing = {r.id for r in present if lives.review_due(r, day, every)}

    def rank(r):
        today = R.todays_memories(r, day)
        talked = any(m.kind == "dialogue" for m in today)
        weight = sum(m.importance for m in today)
        last = int((r.arc or {}).get("last_reflection_day", 0))
        return (r.id not in reviewing, not talked, last, -weight, r.id)

    cap = cfg.get("nightly_cap")
    had_a_day = [r for r in present if R.todays_memories(r, day) or r.id in reviewing]
    chosen = sorted(had_a_day, key=rank)
    if cap is not None:
        chosen = chosen[: int(cap)]
    chosen_ids = {r.id for r in chosen}
    results = await asyncio.gather(*(R.reflect_one(r, town, engine.runner, day, r.id in reviewing)
                                     for r in sorted(chosen, key=lambda r: r.id)))
    reflected = rejected = arcs = 0
    failed: set[str] = set()
    for result in sorted(results, key=lambda x: x.resident_id):
        r = town.residents[result.resident_id]
        if not result.ok:
            # A garbled or failed call: the resident falls back to the free
            # recap below and keeps their place at the front of the rota.
            failed.add(r.id)
            continue
        R.apply(result, r, town)
        reflected += 1
        if result.arc_update:
            lives.apply_arc(result.arc_update, r, town)
            arcs += result.arc_update.get("choice") != "keep"
        rejected += len(result.rejected)
        r.arc = {**(r.arc or {}), "last_reflection_day": day}
        if r.id in reviewing:
            r.arc["last_review_day"] = day
        town.touch(r.id)
    recapped = 0
    for r in had_a_day:
        if r.id in chosen_ids and r.id not in failed:
            continue
        text = R.recap(r, day)
        if text:
            r.remember(town.world.time, text, kind="reflection", importance=3)
            recapped += 1
            town.touch(r.id)
    for r in town.residents.values():
        R.settle_stages(r, town)
        R.prune(r, day, int(cfg["prune_after_days"]), int(cfg["beliefs_cap"]))
    engine.telemetry.log_tick({
        "kind": "night", "day": day, "reflected": reflected, "recapped": recapped,
        "reviews": len(reviewing & chosen_ids), "life_changes": arcs, "rejected": rejected,
        "errors": sum(1 for x in results if x.error), "failed": len(failed),
    })
    engine.night_report = {"reflected": reflected, "recapped": recapped, "life_changes": arcs,
                           "rejected": rejected, "failed": len(failed)}
