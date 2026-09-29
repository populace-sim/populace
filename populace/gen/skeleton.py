"""From a spec to a town: places, households, jobs, routines and ties.

Fully procedural and seeded: the same spec always builds the same town, and no
model is involved. Persona prose (who somebody is, how they talk, what they
hide) is written afterwards by `enrich.py`; this module leaves the persona with
only what can be seen from across a street.

The order matters and is the whole algorithm:

1. neighbourhoods and their streets
2. households, drawn from templates until the population is reached; children
   under the simulated age are the household's dependents, not residents
3. homes along the streets, a share of them in apartment buildings
4. public places of the kinds the spec asks for, with hours, prices and roles
5. jobs: owners and hirers first, then staff, then commuters; a slot nobody
   fills is an opening, which is somebody's chance to be hired later
6. routines: an ordinary working (or school) day and a day off, tiled
7. ties: household, coworkers, neighbours, landlords, a few across town
8. money, rent, phones, what they look like, and where they are at dawn
"""

from __future__ import annotations

import hashlib
import random
import re
import unicodedata
from typing import Any

from .. import clock
from ..clock import GameTime
from ..config import Config
from ..state.place import OFFTOWN_KIND, Place, Thing, World
from ..state.resident import (
    Job, Relationship, Resident, ScheduleEntry, phone_number_for, tile,
)
from ..state.town import Town
from . import data as D
from .spec import TownSpec

WEEKDAYS = [0, 1, 2, 3, 4]
ALL_DAYS = [0, 1, 2, 3, 4, 5, 6]
SUNDAY = 6
START_TICK = 12  # the town starts at six in the morning on a Monday
LEISURE_KINDS = ("park", "cafe", "bar", "community_center", "library")
FOOD_KINDS = ("diner", "cafe", "grocery", "bakery", "convenience_store")
ERRAND_KINDS = ("grocery", "convenience_store", "bakery", "pharmacy", "post_office")


def resident_id(n: int, given: str, family: str) -> str:
    """A resident's id says nothing about them: `r017`. Every prompt shows ids in
    square brackets, and an id made from a name hands a stranger's name to the
    reader; the first live day found the model greeting strangers that way.
    Names come back for people through `populace.observe.names`."""
    return f"r{n:03d}"


def slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _rng(spec: TownSpec, salt: str = "") -> random.Random:
    key = f"{spec.seed}|{spec.name}|{spec.population}|{spec.description}|{salt}"
    return random.Random(int(hashlib.sha256(key.encode()).hexdigest()[:16], 16))


def _weighted(rng: random.Random, weights: dict[str, float]) -> str:
    keys = sorted(weights)
    return rng.choices(keys, [weights[k] for k in keys])[0]


class Builder:
    def __init__(self, spec: TownSpec, config: Config):
        self.spec = spec
        self.config = config
        self.rng = _rng(spec)
        self.geo = D.load("geography")
        self.hh = D.load("households")
        self.routines = D.load("routines")
        self.kinds = D.kinds()
        self.places: dict[str, Place] = {}
        self.residents: dict[str, Resident] = {}
        self.households: dict[str, dict[str, Any]] = {}
        self.meta: dict[str, dict[str, Any]] = {}  # per resident, build-time only
        self.neighbourhoods: list[dict[str, Any]] = []
        self.full_names: set[str] = set()

    # -- 1. neighbourhoods and streets ------------------------------------------------

    def make_neighbourhoods(self) -> None:
        k = max(1, min(6, round(self.spec.population / 70)))
        names = list(self.geo["neighbourhood_names"])
        stems = list(self.geo["street_stems"])
        self.rng.shuffle(names)
        self.rng.shuffle(stems)
        for i in range(k):
            streets = []
            for _ in range(2):
                stem = stems.pop()
                streets.append({"stem": stem,
                                "name": f"{stem} {self.rng.choice(self.geo['street_suffixes'])}",
                                "next": 1 + 2 * self.rng.randint(0, 3)})
            self.neighbourhoods.append({"id": slug(names[i % len(names)]) + (f"_{i}" if i >= len(names) else ""),
                                        "name": names[i % len(names)], "streets": streets})

    # -- 2. households -------------------------------------------------------------------

    def _name(self, culture: str, gender: str, family: str | None) -> tuple[str, str]:
        pool = D.names(culture)
        key = {"woman": "given_f", "man": "given_m"}.get(gender) or self.rng.choice(["given_f", "given_m"])
        # First names tell people apart, for readers and for the check on names
        # said without being given: draw from the least-used ones in the pool.
        used = self.__dict__.setdefault("given_used", {})
        fewest = min(used.get(g, 0) for g in pool[key])
        fresh = [g for g in pool[key] if used.get(g, 0) == fewest]
        for attempt in range(60):
            # A household's surname is fixed; if every fresh first name is taken
            # with it, fall back to the whole pool.
            given = self.rng.choice(fresh if attempt < 20 else pool[key])
            fam = family or self.rng.choice(pool["family"])
            full = f"{given} {fam}"
            if full not in self.full_names:
                self.full_names.add(full)
                used[given] = used.get(given, 0) + 1
                return given, fam
        raise RuntimeError("ran out of distinct names; add names to data/names")

    def _gender(self) -> str:
        r = self.rng.random()
        return "nonbinary" if r < 0.03 else ("woman" if r < 0.515 else "man")

    def make_households(self) -> None:
        templates = self.hh["templates"]
        ages = self.hh["ages"]
        min_age = int(self.hh["simulated_min_age"])
        simulated = 0
        index = 0
        while simulated < self.spec.population:
            index += 1
            template = self.rng.choices(templates, [t["weight"] for t in templates])[0]
            culture = _weighted(self.rng, self.spec.culture_mix)
            family = self.rng.choice(D.names(culture)["family"])
            hid = f"h{index:03d}"
            members: list[str] = []
            dependents: list[dict[str, Any]] = []
            roles: dict[str, str] = {}
            parent_ages: list[int] = []
            for band, role in template["members"]:
                lo, hi = ages[band]
                if role == "child" and parent_ages:
                    hi = min(hi, min(parent_ages) - 18)
                    lo = min(lo, hi)
                age = self.rng.randint(lo, max(lo, hi))
                if role in ("parent", "partner") and parent_ages:
                    # The second of a couple is about the first one's age.
                    age = max(ages[band][0], min(ages[band][1], parent_ages[0] + self.rng.randint(-6, 6)))
                gender = self._gender()
                own_family = family
                own_culture = culture
                if role == "flatmate" or (role == "partner" and self.rng.random() < 0.3):
                    own_culture = _weighted(self.rng, self.spec.culture_mix)
                    own_family = None
                given, fam = self._name(own_culture, gender, own_family)
                if role in ("parent", "partner", "self", "flatmate"):
                    parent_ages.append(age)
                if age < min_age:
                    dependents.append({"name": f"{given} {fam}", "age": age, "gender": gender,
                                       "relation": "child"})
                    continue
                if simulated >= self.spec.population:
                    break
                rid = resident_id(len(self.residents) + 1, given, fam)
                self.residents[rid] = Resident(
                    id=rid, name=f"{given} {fam}", age=age, home="", persona={"gender": gender},
                    schedule=[], needs={}, money=0.0, household=hid,
                )
                self.meta[rid] = {"culture": own_culture, "role": role, "gender": gender}
                members.append(rid)
                roles[rid] = role
                simulated += 1
            if not members:
                continue
            self.households[hid] = {"kind": template["kind"], "home": "", "members": members,
                                    "dependents": dependents, "roles": roles}

    # -- 3. homes --------------------------------------------------------------------------

    def _address(self, nb: dict[str, Any]) -> tuple[dict[str, Any], int]:
        street = min(nb["streets"], key=lambda s: s["next"])
        number = street["next"]
        street["next"] += 2 if self.rng.random() < 0.8 else 4
        return street, number

    def make_homes(self) -> None:
        hids = sorted(self.households)
        self.rng.shuffle(hids)
        share = float(self.hh["apartment_share"])
        in_blocks = hids[: int(len(hids) * share)]
        in_houses = hids[len(in_blocks):]
        nbs = self.neighbourhoods
        # Apartment buildings, filled to a drawn size.
        building: Place | None = None
        room = 0
        kind = self.kinds["apartment_building"]
        for i, hid in enumerate(in_blocks):
            if building is None or room == 0:
                nb = nbs[i % len(nbs)]
                street, number = self._address(nb)
                name = self._fill(self.rng.choice(kind["name_templates"]), street=street, family=None)
                pid = slug(f"{street['name']}_{number}")
                building = Place(pid, name, "apartment_building", self.rng.choice(kind["description"]),
                                 neighbourhood=nb["id"], street=street["name"], number=number,
                                 public=False)
                self.places[pid] = building
                room = self.rng.randint(*kind["units"])
            self._move_in(hid, building)
            room -= 1
        house = self.kinds["house"]
        for i, hid in enumerate(in_houses):
            nb = nbs[i % len(nbs)]
            street, number = self._address(nb)
            pid = slug(f"{street['name']}_{number}")
            place = Place(pid, f"{number} {street['name']}", "house",
                          self.rng.choice(house["description"]), neighbourhood=nb["id"],
                          street=street["name"], number=number, public=False)
            self.places[pid] = place
            self._move_in(hid, place)

    def _move_in(self, hid: str, place: Place) -> None:
        self.households[hid]["home"] = place.id
        for rid in self.households[hid]["members"]:
            r = self.residents[rid]
            r.home = place.id
            r.neighbourhood = place.neighbourhood
            place.residents_of.append(rid)

    # -- 4. public places --------------------------------------------------------------------

    def _fill(self, template: str, street: dict[str, Any] | None, family: str | None) -> str:
        fam = family or self.rng.choice(D.names(_weighted(self.rng, self.spec.culture_mix))["family"])
        return template.format(street_name=(street or {}).get("stem", "Main"),
                               family=fam, town=self.spec.name, number="")

    def make_public_places(self) -> None:
        order = []
        for p in self.spec.places:
            order += [p["kind"]] * int(p["count"])
        used_names: set[str] = set()
        for i, kind_name in enumerate(order):
            kind = self.kinds[kind_name]
            nb = self.neighbourhoods[i % len(self.neighbourhoods)]
            street = nb["streets"][0]
            n = sum(1 for p in self.places.values() if p.kind == kind_name) + 1
            pid = f"{kind_name}_{n}" if order.count(kind_name) > 1 else kind_name
            hours = kind.get("hours")
            place = Place(
                pid, "", kind_name, self.rng.choice(kind["description"]), neighbourhood=nb["id"],
                street=street["name"], public=bool(kind.get("public", True)),
                open_hours={"start": hours[0], "end": hours[1]} if hours else None,
                open_days=list(kind["days"]) if kind.get("days") and len(kind["days"]) < 7 else None,
                things=[Thing(slug(s["name"]), s["name"], list(s["tags"]), price=float(s["price"]),
                              satiety=float(s["satiety"])) for s in kind.get("sells", [])],
            )
            place.openings = self._roles_for(kind)
            self.places[pid] = place
            self.meta[f"place:{pid}"] = {"template": self.rng.choice(kind["name_templates"]),
                                         "street": street, "used_names": used_names}
        city = Place("city", "the city", OFFTOWN_KIND, self.kinds["offtown"]["description"][0],
                     public=False)
        self.places["city"] = city

    def _roles_for(self, kind: dict[str, Any]) -> list[dict[str, Any]]:
        scale = min(1.0, self.spec.population / 200)
        roles = []
        for role in kind.get("roles", []):
            lo, hi = role["slots"]
            n = self.rng.randint(lo, hi)
            if hi > 2:
                n = max(lo, round(n * scale))
            if n <= 0:
                continue
            wage = round(role["wage_per_tick"] * self.rng.uniform(0.92, 1.1), 2)
            roles.append({"title": role["title"], "wage_per_tick": wage,
                          "shift": dict(role["shift"]), "days": list(role["days"]), "slots": n,
                          "filled_by": [], "hires": bool(role["hires"]),
                          "owner": bool(role["owner"]), "min_age": int(role["min_age"]),
                          "uniform": role.get("uniform", "")})
        return roles

    def name_public_places(self) -> None:
        for pid, place in sorted(self.places.items()):
            info = self.meta.get(f"place:{pid}")
            if not info:
                continue
            owner = self.residents.get(place.owner) if place.owner else None
            family = owner.name.split()[-1] if owner else None
            name = self._fill(info["template"], info["street"], family)
            used = info["used_names"]
            templates = list(self.kinds[place.kind]["name_templates"])
            tries = 0
            while name in used and tries < 10:
                name = self._fill(self.rng.choice(templates), info["street"], None)
                tries += 1
            if name in used:
                name = f"{name} ({place.street})"
            used.add(name)
            place.name = name

    # -- 5. jobs -------------------------------------------------------------------------------

    def make_jobs(self) -> None:
        adults = [r for r in self.residents.values() if r.age >= 18]
        workers, students = [], []
        for r in sorted(adults, key=lambda r: r.id):
            m = self.meta[r.id]
            if r.age >= 67:
                m["status"] = "retired" if self.rng.random() > 0.08 else "worker"
            elif r.age <= 21 and self.rng.random() < 0.45:
                m["status"] = "student"
            elif self.rng.random() < self.spec.employment_rate:
                m["status"] = "worker"
            else:
                # Not working is several different lives, and only one of them
                # is looking for work.
                weights = dict(self.hh["not_working"])
                if not self.households[r.household]["dependents"]:
                    weights["homemaker"] *= 0.3
                m["status"] = _weighted(self.rng, weights)
            if m["status"] == "worker":
                workers.append(r)
            elif m["status"] == "student":
                students.append(r)
        for r in self.residents.values():
            if r.age < 18:
                self.meta[r.id]["status"] = "pupil"
        self.rng.shuffle(workers)
        slots = []
        for pid, place in sorted(self.places.items()):
            for opening in place.openings:
                slots.append((pid, opening))
        # Owners and hirers first, from the oldest eligible workers.
        lead = [(pid, o) for pid, o in slots if o["owner"] or o["hires"]]
        staff = [(pid, o) for pid, o in slots if not (o["owner"] or o["hires"])]
        pool = sorted(workers, key=lambda r: -r.age)
        taken: set[str] = set()
        for pid, opening in lead:
            for r in pool:
                if r.id in taken or r.age < opening["min_age"]:
                    continue
                self._hire(r, pid, opening, employer=None)
                taken.add(r.id)
                break
        # Staff: a share of workers commute; the rest take local slots in turn.
        remaining = [r for r in workers if r.id not in taken]
        commuters = set(r.id for r in remaining
                        if self.rng.random() < self.spec.commute_share)
        self.rng.shuffle(staff)
        local = [r for r in remaining if r.id not in commuters]
        held = float(self.hh["held_open_probability"])
        for pid, opening in staff:
            # Some places are a hand short: that is a job somebody can ask for.
            keep_open = 1 if opening["slots"] >= 2 and self.rng.random() < held else 0
            while len(opening["filled_by"]) < opening["slots"] - keep_open and local:
                candidate = next((r for r in local if r.age >= opening["min_age"]), None)
                if candidate is None:
                    break
                local.remove(candidate)
                self._hire(candidate, pid, opening, employer=self._hirer(pid))
                taken.add(candidate.id)
        for r in remaining:
            if r.id not in taken:
                job = self.rng.choice(self.geo["commuter_jobs"])
                r.job = Job(job["title"], "city", round(job["wage_per_tick"] * self.rng.uniform(0.9, 1.15), 2),
                            job["shift"][0], job["shift"][1], days=list(WEEKDAYS))
                self.meta[r.id]["uniform"] = job.get("uniform", "")
        for place in self.places.values():
            for opening in place.openings:
                opening.pop("owner", None)
                opening.pop("hires", None)
                opening.pop("uniform", None)

    def _hirer(self, pid: str) -> str | None:
        place = self.places[pid]
        return place.hires[0] if place.hires else None

    def _hire(self, r: Resident, pid: str, opening: dict[str, Any], employer: str | None) -> None:
        place = self.places[pid]
        r.job = Job(opening["title"], pid, float(opening["wage_per_tick"]),
                    int(opening["shift"]["start"]), int(opening["shift"]["end"]),
                    days=list(opening["days"]), employer_id=employer)
        opening["filled_by"].append(r.id)
        place.workplace_of.append(r.id)
        if opening.get("owner") and place.owner is None:
            place.owner = r.id
        if opening.get("hires"):
            place.hires.append(r.id)
        self.meta[r.id]["uniform"] = opening.get("uniform", "")

    # -- 6. routines -----------------------------------------------------------------------------

    def _open_for(self, place: Place, start: int, end: int, days: list[int]) -> bool:
        """Open for the whole of [start, end) on every one of these weekdays."""
        return all(place.is_open(t, None, d) for d in days for t in range(start, end))

    def _near(self, r: Resident, kinds: tuple[str, ...], adult_only: bool = False,
              window: tuple[int, int] | None = None, days: list[int] | None = None) -> str | None:
        """A place of one of these kinds, own neighbourhood first, open for the
        whole window on every day the routine applies. None if nowhere is:
        a routine never sends anybody to a door that is locked."""
        options = [p for p in self.places.values() if p.kind in kinds and p.public
                   and not (adult_only and p.kind == "bar" and r.age < 21)]
        if window is not None:
            options = [p for p in options if self._open_for(p, window[0], window[1], days or ALL_DAYS)]
        if not options:
            return None
        own = [p for p in options if p.neighbourhood == r.neighbourhood]
        choice = sorted(own or options, key=lambda p: p.id)
        return choice[int(hashlib.sha256(f"{r.id}|{','.join(kinds)}".encode()).hexdigest(), 16) % len(choice)].id

    def _block(self, start: int, end: int, activity: str, where: str) -> dict[str, Any]:
        return {"start_tick": start, "end_tick": end, "activity": activity, "location_id": where}

    def _free_day(self, r: Resident, wake: int, bed: int, rng: random.Random,
                  days: list[int]) -> list[dict[str, Any]]:
        home = r.home
        blocks = [self._block(0, wake, "sleep", home), self._block(wake, wake + 1, "eat", home)]
        cursor = wake + 2
        start = max(cursor, rng.randint(19, 23))
        errand = self._near(r, ERRAND_KINDS, window=(start, start + 2), days=days)
        if errand:
            blocks.append(self._block(start, start + 2, "errand", errand))
            cursor = start + 2
        blocks.append(self._block(max(cursor, 25), max(cursor, 25) + 1, "eat", home))
        cursor = max(cursor, 25) + 2
        if rng.random() < 0.65:
            start = max(cursor, rng.randint(27, 31))
            end = min(start + rng.randint(2, 4), 37)
            leisure = self._near(r, LEISURE_KINDS, adult_only=True, window=(start, end), days=days) \
                if end > start else None
            if leisure:
                blocks.append(self._block(start, end, "leisure", leisure))
        blocks.append(self._block(37, 38, "eat", home))
        blocks.append(self._block(bed, clock.TICKS_PER_DAY, "sleep", home))
        return blocks

    def _church(self, r: Resident, blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        church = self._near(r, ("church",), window=(20, 23), days=[SUNDAY])
        if not church:
            return blocks
        kept = [b for b in blocks if b["end_tick"] <= 20 or b["start_tick"] >= 23]
        return kept + [self._block(20, 23, "leisure", church)]

    def make_routines(self) -> None:
        R = self.routines
        for rid in sorted(self.residents):
            r = self.residents[rid]
            rng = random.Random(int(hashlib.sha256(f"{self.spec.seed}|routine|{rid}".encode()).hexdigest()[:12], 16))
            status = self.meta[rid]["status"]
            bed = rng.randint(*R["bedtime"])
            churchgoer = rng.random() < R["churchgoer_probability"]
            if status in ("worker",) and r.job:
                s, e = r.job.shift_start, r.job.shift_end
                work_days = sorted(r.job.days)
                off_days = [d for d in ALL_DAYS if d not in work_days]
                wake = max(8, s - R["wake_before_shift"])
                work_bed = min(clock.TICKS_PER_DAY, max(bed, e + R["late_bedtime_after_shift"]))
                blocks = [self._block(0, wake, "sleep", r.home),
                          self._block(wake, wake + 1, "eat", r.home),
                          self._block(s, e, "work", r.job.workplace)]
                if e - s >= 12:
                    lunch = s + (e - s) // 2
                    where = r.job.workplace
                    if rng.random() < R["lunch_out_probability"] and not self.places[where].kind == OFFTOWN_KIND:
                        where = self._near(r, FOOD_KINDS, window=(lunch, lunch + 1), days=work_days) or where
                    blocks = [b for b in blocks if b["activity"] != "work"] + [
                        self._block(s, lunch, "work", r.job.workplace),
                        self._block(lunch, lunch + 1, "eat", where),
                        self._block(lunch + 1, e, "work", r.job.workplace)]
                if e <= 38:
                    evening = e
                    if rng.random() < R["evening_out_probability"]:
                        out = self._near(r, LEISURE_KINDS, adult_only=True, window=(e + 1, e + 3),
                                         days=work_days)
                        if out:
                            blocks.append(self._block(e + 1, e + 3, "leisure", out))
                            evening = e + 3
                    dinner = max(evening + 1, 37)
                    if dinner < work_bed:
                        blocks.append(self._block(dinner, dinner + 1, "eat", r.home))
                if work_bed < clock.TICKS_PER_DAY:
                    blocks.append(self._block(work_bed, clock.TICKS_PER_DAY, "sleep", r.home))
                r.schedule = _entries(tile(blocks, r.home))
                r.routine_days = work_days
                if off_days:
                    off = self._free_day(r, rng.randint(*R["wake_free_day"]), bed, rng, off_days)
                    if churchgoer and SUNDAY in off_days:
                        off = self._church(r, off) if off_days == [SUNDAY] else off
                    r.off_schedule = _entries(tile(off, r.home))
            elif status in ("pupil", "student"):
                school = self._near(r, ("school",)) if status == "pupil" else None
                where = school or "city"
                start, end = R["student_hours"]
                blocks = [self._block(0, start - 2, "sleep", r.home),
                          self._block(start - 2, start - 1, "eat", r.home),
                          self._block(start, end, "school", where),
                          self._block(37, 38, "eat", r.home),
                          self._block(bed, clock.TICKS_PER_DAY, "sleep", r.home)]
                if rng.random() < 0.4:
                    hangout = self._near(r, ("park", "cafe", "community_center", "library"),
                                         window=(end + 1, end + 3), days=list(WEEKDAYS))
                    if hangout:
                        blocks.append(self._block(end + 1, end + 3, "leisure", hangout))
                r.schedule = _entries(tile(blocks, r.home))
                r.routine_days = list(WEEKDAYS)
                r.off_schedule = _entries(tile(self._free_day(r, rng.randint(17, 20), bed, rng, [5, 6]),
                                               r.home))
            else:
                wake = rng.randint(*(R["retired_wake"] if status == "retired" else R["wake_free_day"]))
                days = [0, 1, 2, 3, 4, 5] if churchgoer else list(ALL_DAYS)
                day = self._free_day(r, wake, bed, rng, days)
                r.schedule = _entries(tile(day, r.home))
                r.routine_days = days if churchgoer else None
                if churchgoer:
                    sunday = self._free_day(r, wake, bed, rng, [SUNDAY])
                    r.off_schedule = _entries(tile(self._church(r, sunday), r.home))

    # -- 7. ties ---------------------------------------------------------------------------------

    def _tie(self, a: str, b: str, label_ab: str, label_ba: str, sentiment: int,
             friction: bool = False, trust: int | None = None) -> None:
        if a == b or b in self.residents[a].relationships:
            return
        drift = self.rng.randint(-2, 2)
        for x, y, label, sent in ((a, b, label_ab, sentiment), (b, a, label_ba, sentiment + drift)):
            sent = max(-10, min(10, sent))
            t = trust if trust is not None else max(0, min(100, 20 + 5 * sent))
            self.residents[x].relationships[y] = Relationship(label=label, sentiment=sent,
                                                              friction=friction, trust=t)

    def _kin_label(self, rid: str, relation: str) -> str:
        g = self.meta[rid]["gender"]
        words = {"partner": ("wife", "husband", "partner"), "child": ("daughter", "son", "child"),
                 "parent": ("mum", "dad", "parent"), "sibling": ("sister", "brother", "sibling")}[relation]
        if relation == "partner" and self.rng.random() < 0.4:
            return "partner"
        return words[0] if g == "woman" else (words[1] if g == "man" else words[2])

    def make_ties(self) -> None:
        rng = self.rng
        for hid, hh in sorted(self.households.items()):
            members = hh["members"]
            roles = hh["roles"]
            for i, a in enumerate(members):
                for b in members[i + 1:]:
                    ra, rb = roles[a], roles[b]
                    sentiment = rng.randint(2, 7)
                    friction = rng.random() < 0.18
                    trust = rng.randint(45, 80)
                    if ra == rb == "partner" or {ra, rb} == {"parent"}:
                        self._tie(a, b, self._kin_label(b, "partner"), self._kin_label(a, "partner"),
                                  sentiment, friction, trust)
                    elif ra == "parent" and rb == "child":
                        self._tie(a, b, self._kin_label(b, "child"), self._kin_label(a, "parent"),
                                  sentiment, friction, trust)
                    elif ra == "child" and rb == "parent":
                        self._tie(a, b, self._kin_label(b, "parent"), self._kin_label(a, "child"),
                                  sentiment, friction, trust)
                    elif ra == rb == "child":
                        self._tie(a, b, self._kin_label(b, "sibling"), self._kin_label(a, "sibling"),
                                  sentiment, friction, trust)
                    else:
                        self._tie(a, b, "flatmate", "flatmate", rng.randint(-1, 5),
                                  rng.random() < 0.25)
        # Coworkers: everybody in a small place, two or three each in a big one.
        for pid, place in sorted(self.places.items()):
            staff = sorted(place.workplace_of)
            boss = set(place.hires)
            for a in staff:
                others = [b for b in staff if b != a]
                picks = others if len(staff) <= 5 else rng.sample(others, min(len(others), rng.randint(2, 3)))
                for b in picks:
                    if a in boss and b not in boss:
                        self._tie(a, b, "works for me", "boss", rng.randint(-1, 4), rng.random() < 0.15)
                    elif b in boss and a not in boss:
                        self._tie(a, b, "boss", "works for me", rng.randint(-2, 4), rng.random() < 0.15)
                    else:
                        self._tie(a, b, "coworker", "coworker", rng.randint(-2, 5), rng.random() < 0.12)
        # Neighbours: the same building, or a few doors along.
        homes = sorted((p for p in self.places.values() if not p.public and p.kind != OFFTOWN_KIND),
                       key=lambda p: (p.street, p.number))
        for p in homes:
            adults = [rid for rid in p.residents_of if self.residents[rid].age >= 18]
            near = [q for q in homes if q.street == p.street and q.id != p.id and abs(q.number - p.number) <= 4]
            pool = [rid for q in near for rid in q.residents_of if self.residents[rid].age >= 18]
            if p.kind == "apartment_building":
                pool += [rid for rid in adults]
            for a in adults:
                candidates = [b for b in pool if b != a and self.residents[b].household != self.residents[a].household]
                for b in rng.sample(candidates, min(len(candidates), rng.randint(1, 2))):
                    self._tie(a, b, "neighbour", "neighbour", rng.randint(-3, 4), rng.random() < 0.15)
        # A few ties across town, and friends at school.
        everyone = sorted(self.residents)
        labels = [("old friend", "old friend", 2, 6), ("cousin", "cousin", 0, 6),
                  ("ex", "ex", -3, 2), ("friend", "friend", 1, 5),
                  ("drinking buddy", "drinking buddy", 1, 5), ("old colleague", "old colleague", 0, 4)]
        for a in everyone:
            r = self.residents[a]
            if r.age < 18:
                peers = [b for b in everyone if b != a and self.residents[b].age < 20
                         and self.residents[b].household != r.household]
                for b in rng.sample(peers, min(len(peers), rng.randint(1, 3))):
                    self._tie(a, b, "school friend", "school friend", rng.randint(0, 6), rng.random() < 0.15)
                continue
            if len(r.relationships) >= 7:
                continue
            others = [b for b in everyone if self.residents[b].age >= 18
                      and self.residents[b].household != r.household]
            for b in rng.sample(others, min(len(others), rng.randint(1, 2))):
                la, lb, lo, hi = rng.choice(labels)
                self._tie(a, b, la, lb, rng.randint(lo, hi), la == "ex" or rng.random() < 0.12)

    # -- 8. money, rent, phones, looks, dawn ---------------------------------------------------------

    def make_money_and_rent(self) -> None:
        rng = self.rng
        for rid in sorted(self.residents):
            r = self.residents[rid]
            status = self.meta[rid]["status"]
            if r.job:
                weekly = r.job.wage_per_tick * (r.job.shift_end - r.job.shift_start) * len(r.job.days)
                r.money = round(weekly * rng.uniform(0.3, 1.8))
            elif status == "retired":
                r.money = float(rng.randint(120, 600))
            elif status in ("pupil", "student"):
                r.money = float(rng.randint(5, 60))
            else:
                r.money = float(rng.randint(20, 180))
        # Landlords: older residents who own their own home.
        candidates = sorted((r for r in self.residents.values() if r.age >= 45 and r.job is not None
                             or r.age >= 60), key=lambda r: r.id)
        rng.shuffle(candidates)
        landlords = candidates[: max(1, len(candidates) // 12)] if candidates else []
        renter_share = float(self.hh["renter_share_of_houses"])
        due = {l.id: rng.randint(0, 6) for l in landlords}
        for hid, hh in sorted(self.households.items()):
            home = self.places[hh["home"]]
            renting = home.kind == "apartment_building" or rng.random() < renter_share
            adults = [rid for rid in hh["members"] if self.residents[rid].age >= 18]
            if not renting or not adults or not landlords:
                continue
            payer = max(adults, key=lambda rid: (self.residents[rid].money, rid))
            # One landlord per building: every flat in a block pays the same
            # person. Nobody is their own household's landlord.
            start = int(hashlib.sha256(home.id.encode()).hexdigest(), 16) % len(landlords)
            ring = landlords[start:] + landlords[:start]
            landlord = next((l for l in ring if l.household != hid and l.home != home.id), None)
            if landlord is None:
                continue
            base = 150 if home.kind == "apartment_building" else 210
            amount = float(rng.randint(base - 30, base + 60))
            self.residents[payer].rent = {
                "amount": amount, "landlord_id": landlord.id, "due_weekday": due[landlord.id],
                "covers": sorted(a for a in hh["members"] if a != payer), "missed_weeks": 0,
                "owed": 0.0, "home": home.id,
            }
            self._tie(payer, landlord.id, "landlord", "tenant", rng.randint(-1, 3))
            if home.kind == "apartment_building":
                home.owner = landlord.id

    def make_phones_and_looks(self) -> None:
        persona_pool = D.load("personas")
        used: set[str] = set()
        for rid in sorted(self.residents):
            r = self.residents[rid]
            r.phone["number"] = phone_number_for(self.spec.seed, rid)
        for rid in sorted(self.residents):
            r = self.residents[rid]
            contacts = {}
            for oid, rel in r.relationships.items():
                if self.residents[oid].household == r.household or rel.sentiment >= 2 \
                        or rel.label in ("boss", "works for me", "landlord", "tenant"):
                    contacts[oid] = self.residents[oid].phone["number"]
                    rel.number_shared = True
            r.phone["contacts"] = contacts
            # What somebody who has never been told their name would call them.
            rng = random.Random(int(hashlib.sha256(f"{self.spec.seed}|look|{rid}".encode()).hexdigest()[:12], 16))
            gender = self.meta[rid]["gender"]
            noun = {"woman": "woman", "man": "man"}.get(gender, "person")
            their = {"woman": "her", "man": "his"}.get(gender, "their")
            if r.age < 18:
                age_phrase = f"teenage {'girl' if noun == 'woman' else 'boy' if noun == 'man' else 'kid'}"
                noun = ""
            elif r.age < 30:
                age_phrase = f"young {noun}"
                noun = ""
            else:
                decade = {3: "thirties", 4: "forties", 5: "fifties", 6: "sixties", 7: "seventies"}.get(r.age // 10, "eighties")
                age_phrase = f"{noun} in {their} {decade}"
                noun = ""
            uniform = self.meta[rid].get("uniform", "")
            details = [d for d in persona_pool["descriptor_detail"]
                       if "beard" not in d or (gender == "man" and r.age >= 18)]
            for _ in range(30):
                build = rng.choice(persona_pool["descriptor_build"])
                detail = uniform if uniform and rng.random() < 0.6 else rng.choice(details)
                text = f"a {build} {age_phrase} {detail}".replace("  ", " ").strip()
                if text not in used:
                    break
            used.add(text)
            r.persona["descriptor"] = text

    def place_at_dawn(self, world: World) -> None:
        weekday = world.time.weekday_index
        for rid in sorted(self.residents):
            r = self.residents[rid]
            entry = r.scheduled_entry(world.time.tick, weekday)
            world.place(rid, entry.location_id)
            r.asleep = entry.activity == "sleep"
            r.needs = {k: float(v.get("start", 50.0)) for k, v in self.config.needs["kinds"].items()}
            r.urgent_armed = {k: True for k in self.config.needs["kinds"]}
            r.urgent_armed["cash"] = True

    # -- assemble ------------------------------------------------------------------------------------------

    def build(self) -> Town:
        clock.configure(**self.config.clock)
        self.make_neighbourhoods()
        self.make_households()
        self.make_homes()
        self.make_public_places()
        self.make_jobs()
        self.name_public_places()
        self.make_routines()
        self.make_ties()
        self.make_money_and_rent()
        self.make_phones_and_looks()
        world = World(time=GameTime(1, START_TICK), places=self.places, positions={},
                      seed=self.spec.seed,
                      households={hid: {k: v for k, v in hh.items() if k != "roles"}
                                  for hid, hh in self.households.items()})
        self.place_at_dawn(world)
        for r in self.residents.values():
            r.persona["status"] = self.meta[r.id]["status"]
            r.persona["culture"] = self.meta[r.id]["culture"]
        spec_dict = self.spec.to_dict()
        spec_dict["neighbourhoods"] = [{"id": nb["id"], "name": nb["name"],
                                        "streets": [s["name"] for s in nb["streets"]]}
                                       for nb in self.neighbourhoods]
        return Town(spec_dict, world, self.residents, self.config)


def _entries(blocks: list[dict[str, Any]]) -> list[ScheduleEntry]:
    return [ScheduleEntry.from_dict(b) for b in blocks]


def build(spec: TownSpec, config: Config) -> Town:
    return Builder(spec, config).build()
