"""Injection: things dropped into a town land as witnessed events, never as
thoughts, and anything that cannot land is refused on the record."""

from __future__ import annotations

import json

import pytest

from populace.inject import InjectionRefused, inject, inject_many, validate
from populace.inject import apply as INJ
from populace.sim.engine import TickReport
from populace.sim.run import build_engine
from populace.state import locality
from populace.state.town import Town


@pytest.fixture
def engine(town, tmp_path):
    town.root = tmp_path
    town.save(tmp_path, full=True)
    e = build_engine(town, mock=True, run_id="r")
    e.report = TickReport(day=1, tick=town.world.time.tick)
    return e


def _land(engine):
    """Apply what is due, let people notice, and write the memories."""
    INJ.apply_due(engine)
    INJ.notice_pass(engine)
    engine._flush()


def _memories(r, needle):
    return [m.text for m in r.memory if needle in m.text]


# -- refusals -------------------------------------------------------------------------


@pytest.mark.parametrize("raw, reason", [
    ({"kind": "place.explode", "params": {}}, "no such kind"),
    ({"kind": "place.close", "at": "Day 1 06:00", "params": {"place": "cafe", "days": 2}}, "already passed"),
    ({"kind": "place.close", "params": {"place": "moon", "days": 2}}, "no place"),
    ({"kind": "place.close", "params": {"place": "cafe", "days": 15}}, "1 to 14"),
    ({"kind": "event.notice", "params": {"place": "cafe", "text": "Everyone knows the cafe is cursed"}},
     "reaches into a mind"),
    ({"kind": "event.notice", "params": {"place": "cafe", "text": "Ask Sam Lamb about the tools"}},
     "names Sam Lamb"),
    ({"kind": "event.letter", "params": {"to": "sam_lamb", "from": "the bank", "text": "Hello",
                                         "beliefs": ["the bank is watching"]}}, "cannot set beliefs"),
    ({"kind": "event.outage", "params": {"service": "internet", "until": "Day 2 10:00"}}, "reaches no homes"),
    ({"kind": "service.register", "params": {"id": "cafe", "name": "X", "purpose": "y"}}, "already taken"),
])
def test_what_cannot_land_is_refused_on_the_record(town, raw, reason):
    with pytest.raises(InjectionRefused, match=reason):
        inject(town, raw)
    assert town.world.refused[-1]["reason"].find(reason.split()[0]) >= 0


def test_the_same_injection_twice_is_refused(town):
    raw = {"kind": "event.notice", "params": {"place": "cafe", "text": "Quiz night Friday"}}
    inject(town, raw)
    with pytest.raises(InjectionRefused, match="already in the town"):
        inject(town, raw)


def test_a_bad_file_is_refused_line_by_line_and_the_good_lines_stand(town):
    done, refused = inject_many(town, [
        {"kind": "event.notice", "params": {"place": "cafe", "text": "Quiz night Friday"}},
        {"kind": "event.notice", "params": {"place": "moon", "text": "x"}},
    ])
    assert len(done) == 1 and len(refused) == 1 and len(town.world.scheduled) == 1


# -- landing ---------------------------------------------------------------------------


def test_a_closure_is_seen_by_whoever_is_there_and_noticed_later_by_arrivals(engine):
    town = engine.town
    world = town.world
    world.place("ann_reed", "cafe")
    world.place("pat_reed", "house_2")
    rec = inject(town, {"kind": "place.close", "params": {"place": "cafe", "days": 3, "reason": "a burst pipe"}})
    _land(engine)
    assert town.world.time.day in world.places["cafe"].closed_on
    assert _memories(town.residents["ann_reed"], "burst pipe"), "the person there saw the sign go up"
    assert not _memories(town.residents["pat_reed"], "burst pipe"), "nobody elsewhere knows"
    world.place("pat_reed", "cafe")
    INJ.notice_pass(engine)
    engine._flush()
    assert _memories(town.residents["pat_reed"], "burst pipe"), "arriving later, he notices it"
    INJ.notice_pass(engine)
    engine._flush()
    assert len(_memories(town.residents["pat_reed"], "burst pipe")) == 1, "once, not every half hour"
    events = [json.loads(l) for l in open(engine.telemetry.log_dir / "events.jsonl")]
    assert {e["source"] for e in events if e["kind"] in ("changed", "noticed")} == {f"inject:{rec['id']}"}


def test_a_new_place_is_known_only_to_those_who_have_seen_it(engine):
    town = engine.town
    world = town.world
    world.place("ann_reed", "cafe")
    inject(town, {"kind": "place.new", "params": {
        "name": "Birch Bakery", "kind": "bakery", "hours": {"open": "07:00", "close": "15:00"},
        "things": [{"name": "loaf", "price": 3, "satiety": 20}], "announce_at": ["cafe"]}})
    _land(engine)
    locality.refresh(town)
    knowers = {rid for rid, r in town.residents.items() if "birch_bakery" in r.places_known}
    assert knowers == {"ann_reed"}, "the nightly rebuild must not hand it to everybody"


def test_an_outage_is_a_problem_at_home_until_it_ends(engine):
    town = engine.town
    world = town.world
    inject(town, {"kind": "event.outage", "params": {"service": "internet", "homes": ["house_1"],
                                                     "until": "Day 1 10:00"}})
    _land(engine)
    sam = town.residents["sam_lamb"]
    assert [p["kind"] for p in sam.problems if not p["resolved"]] == ["internet"]
    assert any(l.startswith("At home: no internet") for l in INJ.prompt_lines(engine, sam))
    assert not town.residents["pat_reed"].problems, "next door is not on the list"
    while world.time.total_ticks < 20:
        world.time = world.time.advance()
    _land(engine)
    assert all(p["resolved"] for p in sam.problems)
    assert not any(l.startswith("At home") for l in INJ.prompt_lines(engine, sam))


def test_a_newcomer_is_a_stranger_to_everybody_but_their_hosts(engine):
    town = engine.town
    inject(town, {"kind": "event.arrival", "params": {
        "name": "Rae Holt", "age": 30, "descriptor": "a woman with a rucksack and a map",
        "host": "pat_reed"}})
    _land(engine)
    rid = next(r for r in town.residents if town.residents[r].name == "Rae Holt")
    assert rid.startswith("r")
    assert town.residents["pat_reed"].knows_name(rid)
    assert not town.residents["sam_lamb"].knows_name(rid)
    assert town.residents[rid].persona["arrived_day"] == 1


def test_a_letter_waits_at_home_for_the_one_it_is_for(engine):
    town = engine.town
    world = town.world
    world.place("jo_lamb", "house_1")
    world.place("sam_lamb", "workshop")
    inject(town, {"kind": "event.letter", "params": {"to": "sam_lamb", "from": "the council",
                                                     "text": "Your bins go out on Tuesdays now."}})
    _land(engine)
    assert not _memories(town.residents["jo_lamb"], "bins"), "not hers to read"
    world.place("sam_lamb", "house_1")
    INJ.notice_pass(engine)
    engine._flush()
    assert _memories(town.residents["sam_lamb"], "bins")


def test_a_service_shows_only_to_those_who_know_of_it(engine):
    town = engine.town
    inject(town, {"kind": "service.register", "params": {
        "id": "northline", "name": "Northline Internet", "purpose": "home internet",
        "channels": ["text", "call"], "known_by": ["sam_lamb"]}})
    _land(engine)
    assert any("Northline Internet [northline]" in l for l in INJ.prompt_lines(engine, town.residents["sam_lamb"]))
    assert not any("Northline" in l for l in INJ.prompt_lines(engine, town.residents["pat_reed"]))


def test_what_changed_is_at_most_three_lines(engine):
    town = engine.town
    town.world.place("ann_reed", "cafe")
    for n in range(5):
        inject(town, {"kind": "event.notice", "params": {"place": "cafe", "text": f"Notice number {n}"}})
    _land(engine)
    lines = [l for l in INJ.prompt_lines(engine, town.residents["ann_reed"]) if l.startswith("Seen at")]
    assert len(lines) == 3


def test_a_scheduled_injection_survives_a_save_and_lands_after_the_resume(engine, tmp_path):
    town = engine.town
    inject(town, {"kind": "event.notice", "at": "Day 1 09:00", "params": {"place": "cafe", "text": "Open mic"}})
    town.save(full=True)
    again = Town.load(tmp_path)
    assert [m["kind"] for m in again.world.scheduled] == ["event.notice"]
    e = build_engine(again, mock=True, run_id="r2")
    e.report = TickReport(day=1, tick=again.world.time.tick)
    while again.world.time.total_ticks < 18:
        again.world.time = again.world.time.advance()
    _land(e)
    assert again.world.injected and again.world.injected[0]["kind"] == "event.notice"


def test_an_injection_whose_place_has_gone_is_refused_when_it_falls_due(engine):
    town = engine.town
    inject(town, {"kind": "place.price", "params": {"place": "cafe", "item": "coffee", "price": 4}})
    town.world.places["cafe"].things = []
    _land(engine)
    assert "could not apply" in town.world.refused[-1]["reason"]
    assert not town.world.injected


def test_validate_does_not_schedule(town):
    validate({"kind": "event.notice", "params": {"place": "cafe", "text": "x"}}, town)
    assert town.world.scheduled == []


def test_a_service_may_name_a_counter_that_is_about_to_open(town):
    inject(town, {"kind": "place.new", "params": {"id": "shop_x", "name": "The Line Shop", "kind": "phone_shop"}})
    inject(town, {"kind": "service.register", "params": {
        "id": "linecorp", "name": "Line Corp", "purpose": "phones", "channels": ["visit"], "storefront": "shop_x"}})
    with pytest.raises(InjectionRefused, match="no storefront"):
        inject(town, {"kind": "service.register", "params": {
            "id": "other", "name": "Other", "purpose": "phones", "storefront": "nowhere"}})
