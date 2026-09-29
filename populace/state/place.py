"""Places, the things in them, and the world that holds both.

Ported from Alive's `world.py`, without the tables for one particular street that were
re-applied to every world on load. Changes:

* A place has a `kind` (from `data/place_kinds.json`), a `neighbourhood`, and
  `public` (whether anybody may walk in).
* `World` keeps an occupancy index beside `positions`, so "who is here" does
  not scan every resident on every call.
* The off-town place (a job in the city, a bus that has left) is where nobody
  can see or hear anybody, exactly as Alive's `offblock` was.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..clock import GameTime, tick_to_hhmm

SCHEMA_VERSION = 1
OFFTOWN_KIND = "offtown"


class WorldError(Exception):
    """Malformed world data, or an illegal change to the world."""


@dataclass
class Thing:
    """Something in a place: a thing for sale, a fixture, a notice on a door."""

    id: str
    name: str
    tags: list[str] = field(default_factory=list)
    price: float | None = None
    satiety: float = 0.0
    # Ground truth for things that work or do not. Whoever is `responsible`
    # always has the true state in front of them.
    state: str | None = None
    responsible: str | None = None
    stock: int | None = None  # None: never runs out
    kind: str = ""
    text: str = ""  # a notice or a letter
    addressed_to: str | None = None

    @staticmethod
    def from_dict(d: dict) -> "Thing":
        return Thing(
            id=d["id"], name=d["name"], tags=list(d.get("tags", [])), price=d.get("price"),
            satiety=float(d.get("satiety", 0.0)), state=d.get("state"),
            responsible=d.get("responsible"), stock=d.get("stock"), kind=d.get("kind", ""),
            text=d.get("text", ""), addressed_to=d.get("addressed_to"),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "tags": sorted(self.tags), "price": self.price,
            "satiety": self.satiety, "state": self.state, "responsible": self.responsible,
            "stock": self.stock, "kind": self.kind, "text": self.text,
            "addressed_to": self.addressed_to,
        }


@dataclass
class Place:
    id: str
    name: str
    kind: str
    description: str
    neighbourhood: str = ""
    # An address, for homes: which street and where along it. Neighbours are
    # people a few doors apart on the same street, or in the same building.
    street: str = ""
    number: int = 0
    # Anybody may walk in. A house is not public; a shop, a park or a school gate is.
    public: bool = True
    open_hours: dict[str, int] | None = None  # {"start", "end"} in ticks; None = always
    open_days: list[int] | None = None  # weekday indices; None = every day
    things: list[Thing] = field(default_factory=list)
    owner: str | None = None
    # Who may take somebody on here or let them go.
    hires: list[str] = field(default_factory=list)
    # {"title", "wage_per_tick", "shift": {start, end}, "days", "slots", "filled_by"}
    openings: list[dict[str, Any]] = field(default_factory=list)
    residents_of: list[str] = field(default_factory=list)
    workplace_of: list[str] = field(default_factory=list)
    closed_on: list[int] = field(default_factory=list)  # days it did not open
    # A place dropped in by an injection is known only to those who have seen
    # it; the nightly rebuild of places known must not hand it to everybody.
    introduced_by: str | None = None
    known_by: list[str] = field(default_factory=list)

    def is_open(self, tick: int, day: int | None = None, weekday_index: int | None = None) -> bool:
        if day is not None and day in self.closed_on:
            return False
        if weekday_index is not None and self.open_days is not None \
                and weekday_index not in self.open_days:
            return False
        if self.open_hours is None:
            return True
        start, end = self.open_hours["start"], self.open_hours["end"]
        if start <= end:
            return start <= tick < end
        return tick >= start or tick < end  # open across midnight

    def hours_label(self) -> str:
        if self.open_hours is None:
            return "always open"
        return f"{tick_to_hhmm(self.open_hours['start'])}-{tick_to_hhmm(self.open_hours['end'])}"

    def opening(self, title: str | None = None) -> dict[str, Any] | None:
        for opening in self.openings:
            free = int(opening.get("slots", 1)) - len(opening.get("filled_by", []))
            if free <= 0:
                continue
            if title and title.strip().lower() != str(opening.get("title", "")).lower():
                continue
            return opening
        return None

    def thing_by_name(self, name: str) -> Thing | None:
        needle = (name or "").strip().lower()
        if not needle:
            return None
        for thing in self.things:
            if thing.id.lower() == needle or thing.name.lower() == needle:
                return thing
        return None

    def for_sale(self) -> list[Thing]:
        return [t for t in self.things if t.price is not None]

    @staticmethod
    def from_dict(d: dict) -> "Place":
        return Place(
            id=d["id"], name=d["name"], kind=d["kind"], description=d.get("description", ""),
            neighbourhood=d.get("neighbourhood", ""), street=d.get("street", ""),
            number=int(d.get("number", 0)), public=bool(d.get("public", True)),
            open_hours=d.get("open_hours"),
            open_days=[int(x) for x in d["open_days"]] if d.get("open_days") is not None else None,
            things=[Thing.from_dict(t) for t in d.get("things", [])],
            owner=d.get("owner"), hires=list(d.get("hires", [])),
            openings=[dict(o) for o in d.get("openings", [])],
            residents_of=list(d.get("residents_of", [])),
            workplace_of=list(d.get("workplace_of", [])),
            closed_on=[int(x) for x in d.get("closed_on", [])],
            introduced_by=d.get("introduced_by"), known_by=list(d.get("known_by", [])),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "kind": self.kind,
            "description": self.description, "neighbourhood": self.neighbourhood,
            "street": self.street, "number": self.number,
            "public": self.public, "open_hours": self.open_hours, "open_days": self.open_days,
            "things": [t.to_dict() for t in self.things], "owner": self.owner,
            "hires": sorted(self.hires), "openings": [dict(o) for o in self.openings],
            "residents_of": sorted(self.residents_of), "workplace_of": sorted(self.workplace_of),
            "closed_on": sorted(self.closed_on),
            **({"introduced_by": self.introduced_by, "known_by": sorted(self.known_by)}
               if self.introduced_by else {}),
        }


@dataclass
class World:
    time: GameTime
    places: dict[str, Place]
    positions: dict[str, str]  # resident id -> place id
    seed: int = 0
    public_log: list[dict[str, Any]] = field(default_factory=list)
    # Injected changes queued for a later tick. Each one is something somebody
    # could perceive; none of them touches a mind.
    scheduled: list[dict[str, Any]] = field(default_factory=list)
    # Injections applied and refused, for the record; what is posted where for
    # people to notice when they come by; and outside services (step 4).
    injected: list[dict[str, Any]] = field(default_factory=list)
    refused: list[dict[str, Any]] = field(default_factory=list)
    notices: list[dict[str, Any]] = field(default_factory=list)
    services: dict[str, dict[str, Any]] = field(default_factory=dict)
    # {id: {"kind", "home", "members": [resident ids], "dependents": [{"name",
    # "age", "relation"}]}}. Dependents are young children who live with a
    # household and are not simulated.
    households: dict[str, dict[str, Any]] = field(default_factory=dict)
    schema_version: int = SCHEMA_VERSION
    _by_place: dict[str, set[str]] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self._reindex()

    def _reindex(self) -> None:
        self._by_place = {}
        for rid, pid in self.positions.items():
            self._by_place.setdefault(pid, set()).add(rid)

    # -- queries --------------------------------------------------------------

    def place_by_id(self, place_id: str) -> Place:
        try:
            return self.places[place_id]
        except KeyError:
            raise WorldError(f"unknown place: {place_id}") from None

    def occupants(self, place_id: str) -> list[str]:
        """Resident ids at a place, sorted for determinism."""
        return sorted(self._by_place.get(place_id, ()))

    def location_of(self, resident_id: str) -> str:
        try:
            return self.positions[resident_id]
        except KeyError:
            raise WorldError(f"resident not placed: {resident_id}") from None

    def offtown_id(self) -> str | None:
        for pid in sorted(self.places):
            if self.places[pid].kind == OFFTOWN_KIND:
                return pid
        return None

    def is_offtown(self, place_id: str | None) -> bool:
        place = self.places.get(place_id) if place_id else None
        return place is not None and place.kind == OFFTOWN_KIND

    def is_open(self, place_id: str) -> bool:
        return self.place_by_id(place_id).is_open(
            self.time.tick, self.time.day, self.time.weekday_index)

    def destinations(self) -> list[str]:
        return sorted(pid for pid, p in self.places.items() if p.kind != OFFTOWN_KIND)

    # -- mutation ----------------------------------------------------------------

    def place(self, resident_id: str, place_id: str) -> None:
        if place_id not in self.places:
            raise WorldError(f"unknown place: {place_id}")
        old = self.positions.get(resident_id)
        if old is not None:
            self._by_place.get(old, set()).discard(resident_id)
        self.positions[resident_id] = place_id
        self._by_place.setdefault(place_id, set()).add(resident_id)

    def remove(self, resident_id: str) -> None:
        old = self.positions.pop(resident_id, None)
        if old is not None:
            self._by_place.get(old, set()).discard(resident_id)

    def log_public(self, event: dict[str, Any]) -> None:
        self.public_log.append(event)

    def clear_public_log(self) -> None:
        self.public_log = []

    # -- serialisation --------------------------------------------------------------

    @staticmethod
    def from_dict(d: dict) -> "World":
        return World(
            schema_version=int(d.get("schema_version", SCHEMA_VERSION)),
            seed=int(d.get("seed", 0)),
            time=GameTime.from_dict(d["time"]),
            places={p["id"]: Place.from_dict(p) for p in d["places"]},
            positions=dict(d.get("positions", {})),
            public_log=list(d.get("public_log", [])),
            scheduled=[dict(m) for m in d.get("scheduled", [])],
            injected=[dict(m) for m in d.get("injected", [])],
            refused=[dict(m) for m in d.get("refused", [])],
            notices=[dict(m) for m in d.get("notices", [])],
            services={k: dict(v) for k, v in (d.get("services") or {}).items()},
            households={k: dict(v) for k, v in (d.get("households") or {}).items()},
        )

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version, "seed": self.seed,
            "time": self.time.to_dict(),
            "places": [self.places[k].to_dict() for k in sorted(self.places)],
            "positions": {k: self.positions[k] for k in sorted(self.positions)},
            "public_log": list(self.public_log),
            "scheduled": [dict(m) for m in self.scheduled],
            "injected": [dict(m) for m in self.injected],
            "refused": [dict(m) for m in self.refused],
            "notices": [dict(m) for m in self.notices],
            "services": {k: self.services[k] for k in sorted(self.services)},
            "households": {k: self.households[k] for k in sorted(self.households)},
        }

    def validate(self) -> list[str]:
        problems = []
        for rid, pid in sorted(self.positions.items()):
            if pid not in self.places:
                problems.append(f"{rid} is at unknown place {pid!r}")
        for place in self.places.values():
            hours = place.open_hours
            if hours is not None and not (0 <= hours["start"] <= 48 and 0 <= hours["end"] <= 48):
                problems.append(f"{place.id}: open hours out of range {hours}")
        return problems
