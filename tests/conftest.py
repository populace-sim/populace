"""A small hand-built town for unit tests.

Written by hand rather than generated, so unit tests do not move when
generation changes. Six residents, two households, a cafe, a workshop, an
off-town workplace.
"""

from __future__ import annotations

import pytest

from populace import clock
from populace.clock import GameTime
from populace.config import Config
from populace.state.place import Place, Thing, World
from populace.state.resident import Job, Relationship, Resident, ScheduleEntry, tile
from populace.state.town import Town

PERSONA = {
    "personality": "Even-tempered until the last minute.",
    "speech_style": "Short sentences.",
    "public_bio": "Has lived here a while.",
    "long_term_goal": "Keep things steady.",
    "descriptor": "somebody in a grey coat",
    "secret": "",
}


def _day(home: str, work: str | None) -> list[ScheduleEntry]:
    blocks = [
        {"start_tick": 0, "end_tick": 14, "activity": "sleep", "location_id": home},
        {"start_tick": 44, "end_tick": 48, "activity": "sleep", "location_id": home},
    ]
    if work:
        blocks.append({"start_tick": 18, "end_tick": 34, "activity": "work", "location_id": work})
    return [ScheduleEntry.from_dict(b) for b in tile(blocks, home)]


def _resident(rid, name, home, household, work=None, secret="", descriptor=None, **kw):
    persona = dict(PERSONA, secret=secret, descriptor=descriptor or f"the one they call {rid}-ish")
    job = Job("hand", work, 3.0, 18, 34) if work else None
    return Resident(
        id=rid, name=name, age=kw.pop("age", 40), home=home, persona=persona,
        schedule=_day(home, work), needs={"hunger": 20.0, "energy": 80.0}, money=100.0,
        household=household, neighbourhood="north", job=job, **kw,
    )


def build_small_town() -> Town:
    clock.configure(48, 30)
    places = {
        "house_1": Place("house_1", "3 Birch Road", "house", "A narrow house.",
                         neighbourhood="north", street="Birch Road", number=3, public=False),
        "house_2": Place("house_2", "5 Birch Road", "house", "A house with a porch.",
                         neighbourhood="north", street="Birch Road", number=5, public=False),
        "cafe": Place("cafe", "The Corner Cafe", "cafe", "Six tables.", neighbourhood="north",
                      open_hours={"start": 14, "end": 36},
                      things=[Thing("coffee", "coffee", ["food"], price=3, satiety=5)]),
        "workshop": Place("workshop", "Lamb's Workshop", "workshop", "Sawdust.",
                          neighbourhood="north", open_hours={"start": 16, "end": 36}),
        "city": Place("city", "the city", "offtown", "Somewhere else."),
    }
    residents = {
        r.id: r for r in [
            _resident("sam_lamb", "Sam Lamb", "house_1", "h1", "workshop",
                      secret="Sam borrowed money against the workshop tools last winter"),
            _resident("jo_lamb", "Jo Lamb", "house_1", "h1", "city"),
            _resident("pat_reed", "Pat Reed", "house_2", "h2", "workshop",
                      descriptor="a tall man with sawdust on his sleeves"),
            _resident("ann_reed", "Ann Reed", "house_2", "h2", "cafe"),
            _resident("sam_hart", "Sam Hart", "house_2", "h2", "city",
                      descriptor="a young woman with a bike helmet", age=22),
            _resident("lee_moss", "Lee Moss", "house_2", "h3", "cafe",
                      descriptor="an older man who reads the paper standing up", age=67),
        ]
    }
    places["house_1"].residents_of = ["jo_lamb", "sam_lamb"]
    places["house_2"].residents_of = ["ann_reed", "lee_moss", "pat_reed", "sam_hart"]
    places["workshop"].workplace_of = ["pat_reed", "sam_lamb"]
    places["workshop"].owner = "sam_lamb"
    places["workshop"].hires = ["sam_lamb"]
    places["cafe"].workplace_of = ["ann_reed", "lee_moss"]
    residents["sam_lamb"].relationships["pat_reed"] = Relationship("works for me", 3, trust=30)
    residents["pat_reed"].relationships["sam_lamb"] = Relationship("boss", 1, trust=25)
    world = World(time=GameTime(1, 16), places=places,
                  positions={rid: r.home for rid, r in residents.items()})
    spec = {"name": "Birchfield", "seed": 3, "description": "a test town"}
    return Town(spec, world, residents, Config.build("laptop"))


@pytest.fixture
def town() -> Town:
    return build_small_town()
