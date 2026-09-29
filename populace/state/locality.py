"""Who each resident knows about, and which places they have reason to go.

New in populace. Alive put every resident in every prompt and gave everybody
everybody's name, which is true of nineteen people in two buildings and false
of two hundred in a town (and costs about 8,000 tokens a call at that size).

A resident's **circle** is ranked by how close the tie is and capped:

    household                         3 + 10  (always first)
    a relationship                    |sentiment| + 1 + 5
    a coworker                        2
    a neighbour (same building, or
      a few doors along the street)   1
    anybody met since                 1

Only the circle gets names at the start (`how: "always"`), because only the
circle has been living beside them. Everybody else is a description until a
name is said in front of them, which is Alive's rule unchanged.

**Places known** are home, work, every place in their ordinary days, the public
places of their own neighbourhood, and then one of each other kind in town,
nearest neighbourhood first, up to the cap.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from .place import OFFTOWN_KIND

if TYPE_CHECKING:  # pragma: no cover
    from .resident import Resident
    from .town import Town

NEAR_DOORS = 4


def _tiebreak(seed: int, a: str, b: str) -> int:
    return int(hashlib.sha256(f"{seed}|{a}|{b}".encode()).hexdigest()[:8], 16)


def _neighbours(town: "Town", resident: "Resident") -> set[str]:
    home = town.world.places.get(resident.home)
    if home is None:
        return set()
    near_homes = {home.id}
    if home.street:
        for place in town.world.places.values():
            if place.street == home.street and not place.public \
                    and abs(place.number - home.number) <= NEAR_DOORS:
                near_homes.add(place.id)
    out: set[str] = set()
    for pid in near_homes:
        out.update(town.world.places[pid].residents_of)
    out.discard(resident.id)
    return out


def circle_scores(town: "Town", resident: "Resident") -> dict[str, float]:
    scores: dict[str, float] = {}

    def add(rid: str, score: float) -> None:
        if rid != resident.id and rid in town.residents:
            scores[rid] = max(scores.get(rid, 0.0), score)

    for other in town.residents.values():
        if resident.household and other.household == resident.household:
            add(other.id, 13.0)
    for rid, rel in resident.relationships.items():
        add(rid, abs(rel.sentiment) + 6.0)
    if resident.job and not town.world.is_offtown(resident.job.workplace):
        for rid in town.world.places[resident.job.workplace].workplace_of:
            add(rid, 2.0)
    for rid in _neighbours(town, resident):
        add(rid, 1.0)
    for rid in resident.names_known:
        add(rid, 1.0)
    return scores


def circle(town: "Town", resident: "Resident") -> list[str]:
    cap = int(town.config.locality["people_cap"])
    scores = circle_scores(town, resident)
    ranked = sorted(scores, key=lambda rid: (-scores[rid], _tiebreak(town.seed, resident.id, rid)))
    return sorted(ranked[:cap])


def places_known(town: "Town", resident: "Resident") -> list[str]:
    cap = int(town.config.locality["places_cap"])
    places = town.world.places
    chosen: list[str] = []

    def add(pid: str | None) -> None:
        if pid and pid in places and pid not in chosen and places[pid].kind != OFFTOWN_KIND:
            place = places[pid]
            if place.introduced_by and resident.id not in place.known_by:
                return  # dropped in by an injection, and not seen yet
            chosen.append(pid)

    add(resident.home)
    if resident.job:
        add(resident.job.workplace)
    for day in (resident.schedule, resident.off_schedule):
        for entry in day:
            add(entry.location_id)
    own = sorted(p.id for p in places.values()
                 if p.public and p.neighbourhood == resident.neighbourhood)
    for pid in own:
        if len(chosen) >= cap:
            break
        add(pid)
    kinds_known = {places[p].kind for p in chosen}
    others = sorted(
        (p for p in places.values() if p.public and p.kind not in kinds_known
         and p.kind != OFFTOWN_KIND),
        key=lambda p: (p.neighbourhood != resident.neighbourhood,
                       _tiebreak(town.seed, resident.id, p.id)),
    )
    for place in others:
        if len(chosen) >= cap:
            break
        if place.kind in kinds_known:
            continue
        add(place.id)
        kinds_known.add(place.kind)
    return chosen[:max(cap, 1)]


def refresh(town: "Town") -> None:
    """Recompute every resident's circle and places. Cheap; runs nightly."""
    for resident in town.residents.values():
        new_circle = circle(town, resident)
        new_places = places_known(town, resident)
        if new_circle != resident.circle or new_places != resident.places_known:
            resident.circle = new_circle
            resident.places_known = new_places
            town.touch(resident.id)


def seed_acquaintance(town: "Town") -> None:
    """At generation only: the circle holds each other's names and faces.

    Never on load. In Alive, seeding on every load gave a newcomer who arrived
    mid-game every name in the place when the save came back.
    """
    for resident in town.residents.values():
        for rid in resident.circle:
            resident.names_known.setdefault(rid, {"day": 0, "how": "always"})
            resident.noticed.setdefault(rid, 0)
        town.touch(resident.id)
