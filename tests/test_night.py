"""The night: reflection, its cap, promises judged, the weekly review, leaving."""

from __future__ import annotations

import pytest

from populace.clock import GameTime
from populace.sim import lives, nightly
from populace.sim import reflection as R
from populace.sim.engine import TickReport
from populace.sim.run import build_engine


@pytest.fixture
def engine(town, tmp_path):
    town.root = tmp_path
    e = build_engine(town, mock=True, run_id="r")
    e.report = TickReport(day=1, tick=town.world.time.tick)
    return e


def _day(town, rid, *texts, involved=()):
    r = town.residents[rid]
    return [r.remember(GameTime(1, 20 + i), t, importance=5, involved=list(involved)) for i, t in enumerate(texts)]


def test_a_belief_must_rest_on_todays_memories(town):
    sam = town.residents["sam_lamb"]
    mems = _day(town, "sam_lamb", "Pat was late again.", involved=["pat_reed"])
    raw = {"summary": "long day", "beliefs": [
        {"text": "Pat is slipping.", "importance": 6, "source_memory_ids": [mems[0].id]},
        {"text": "Something is off.", "importance": 6, "source_memory_ids": [9999]},
        {"text": "Lee has it in for me.", "importance": 6, "source_memory_ids": [mems[0].id]},
    ], "relationship_updates": [
        {"character_id": "pat_reed", "delta": 9, "note": "late again"},
        {"character_id": "lee_moss", "delta": -2, "note": "never saw him"},
    ]}
    result = R.validate(raw, sam, town, 1)
    assert [b["text"] for b in result.beliefs] == ["Pat is slipping."]
    assert len(result.rejected) == 3
    assert result.relationship_updates == [{"character_id": "pat_reed", "delta": 3, "note": "late again",
                                            "label": None}]


def test_the_reflection_prompt_names_nobody_the_reader_was_not_given(town):
    ann = town.residents["ann_reed"]
    _day(town, "ann_reed", "A tall man with sawdust on his sleeves bought coffee.", involved=["pat_reed"])
    text = R.build_prompt(ann, town, 1)
    assert "Pat Reed" not in text
    assert "a tall man with sawdust on his sleeves" in text


async def test_the_nights_cap_is_a_rota_and_everybody_else_gets_a_recap(engine):
    town = engine.town
    town.config.raw["reflection"]["nightly_cap"] = 2
    for rid in town.residents:
        _day(town, rid, f"{rid} had an ordinary day at work.", "Came home tired.")
    await nightly.night(engine, 1)
    assert engine.night_report["reflected"] <= 2
    assert engine.night_report["recapped"] == len(town.residents) - 2
    reflections = [c for c in engine.telemetry.read_stream("calls") if c["role"] == "reflection"]
    assert len(reflections) == 2, "a recap costs no call"
    recaps = [m for r in town.residents.values() for m in r.memory if m.kind == "reflection"]
    assert recaps


async def test_a_failed_reflection_falls_back_to_the_recap(engine, monkeypatch):
    """A garbled reply must not leave a resident's night blank, nor send them
    to the back of the rota as if they had had their turn."""
    town = engine.town
    town.config.raw["reflection"]["nightly_cap"] = 2

    async def garbled(resident, town, runner, day, review):
        return R.ReflectionResult(resident_id=resident.id, error="no JSON in reflection response")

    monkeypatch.setattr(R, "reflect_one", garbled)
    for rid in town.residents:
        _day(town, rid, f"{rid} had an ordinary day at work.", "Came home tired.")
    await nightly.night(engine, 1)
    assert engine.night_report["reflected"] == 0
    assert engine.night_report["failed"] == 2
    assert engine.night_report["recapped"] == len(town.residents)
    blank = [r.id for r in town.residents.values() if not any(m.kind == "reflection" for m in r.memory)]
    assert blank == []
    assert not any((r.arc or {}).get("last_reflection_day") for r in town.residents.values())


def test_a_money_promise_is_judged_on_the_money(town):
    sam, pat = town.residents["sam_lamb"], town.residents["pat_reed"]
    from populace.sim import economy as E
    E.add_obligation(pat, sam, "loan", 40, 1, due_day=2)
    promise = {"what": "pay you back the forty", "made_day": 1, "by_day": 1, "status": "open",
               "about": "money", "owed_when_made": 40.0, "by": "me"}
    pat.relationship_with("sam_lamb").add_promise(dict(promise))
    sam.relationship_with("pat_reed").add_promise({**promise, "by": "them"})
    judged = R.settle_promises(town, 1)
    assert judged == [("pat_reed", "sam_lamb", False)]
    assert sam.relationships["pat_reed"].promises[-1]["status"] == "broken", "both heads agree"


def test_a_vague_promise_lapses_quietly(town):
    pat = town.residents["pat_reed"]
    pat.relationship_with("sam_lamb").add_promise({"what": "come by sometime", "by_day": 1, "status": "open",
                                                   "about": "other", "owed_when_made": 0, "by": "me"})
    assert R.settle_promises(town, 1) == []
    assert pat.relationships["sam_lamb"].promises[-1]["status"] == "lapsed"


def test_the_weekly_review_is_offset_per_person(town):
    days = {rid: [d for d in range(7, 21) if lives.review_due(r, d, 7)] for rid, r in town.residents.items()}
    assert all(len(v) == 2 for v in days.values())
    assert len({v[0] for v in days.values()}) > 1, "the whole town does not reconsider on one night"


def test_a_life_choice_has_to_be_possible(town):
    lee = town.residents["lee_moss"]
    with pytest.raises(lives.ArcRefused):
        lives.validate_arc({"choice": "leave_town", "day": 1, "reason": "enough"}, lee, town)
    with pytest.raises(lives.ArcRefused):
        lives.validate_arc({"choice": "seek_work", "workplace": "house_1"}, lee, town)
    ok = lives.validate_arc({"choice": "leave_town", "day": 4, "reason": "enough"}, lee, town)
    lives.apply_arc(ok, lee, town)
    assert lee.goals_active[0].startswith("Leave town on Day 4")


def test_leaving_town_is_seen_and_takes_them_off_the_rosters(engine):
    town = engine.town
    sam = town.residents["sam_lamb"]
    sam.arc = {**sam.arc, "leave_day": 1, "detail": "for the city"}
    town.world.place("sam_lamb", "workshop")
    town.world.place("pat_reed", "workshop")
    town.world.time = GameTime(1, lives.LEAVE_TICK)
    lives.check_departures(engine)
    engine._flush()
    assert sam.away and town.world.is_offtown(town.world.location_of("sam_lamb"))
    assert sam.job is None and "sam_lamb" not in town.world.places["workshop"].workplace_of
    assert any("left town" in m.text for m in town.residents["pat_reed"].memory)
