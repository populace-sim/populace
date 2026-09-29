"""State, events, memory, locality and saves."""

from __future__ import annotations

import json

from populace.sim import memory as M
from populace.sim.events import Event, NameIndex, as_seen_by, known_as, leak_check
from populace.state import locality
from populace.state.town import Town


def _event(town, kind, actor, target=None, **kw):
    a = town.residents[actor]
    t = town.residents[target] if target else None
    return Event(kind=kind, day=town.world.time.day, tick=town.world.time.tick,
                 location_id=kw.pop("where", town.world.location_of(actor)), actor=actor,
                 actor_name=a.name, target=target, target_name=t.name if t else None, **kw)


# -- saves --------------------------------------------------------------------


def test_a_town_round_trips_through_its_directory(town, tmp_path):
    town.save(tmp_path, full=True)
    again = Town.load(tmp_path)
    assert again.validate() == []
    for rid, r in town.residents.items():
        assert again.residents[rid].to_dict() == r.to_dict()
    assert again.world.to_dict() == town.world.to_dict()


def test_a_tick_saves_only_the_residents_it_touched(town, tmp_path):
    town.save(tmp_path, full=True)
    before = {p.name: p.stat().st_mtime_ns for p in (tmp_path / "residents").glob("*.json")}
    town.residents["ann_reed"].money = 1.0
    town.touch("ann_reed")
    town.save()
    after = {p.name: p.stat().st_mtime_ns for p in (tmp_path / "residents").glob("*.json")}
    changed = sorted(k for k in after if after[k] != before[k])
    assert changed == ["ann_reed.json"]
    assert json.loads((tmp_path / "residents" / "ann_reed.json").read_text())["money"] == 1.0


def test_a_day_snapshot_is_a_full_copy(town, tmp_path):
    town.save(tmp_path, full=True)
    dest = town.snapshot_day(1)
    assert sorted(p.name for p in (dest / "residents").glob("*.json")) == sorted(
        f"{rid}.json" for rid in town.residents)


def test_a_broken_schedule_is_reported_not_repaired(town):
    town.residents["jo_lamb"].schedule.pop()
    assert any("jo_lamb" in p and "covers up to" in p for p in town.validate())


# -- witnesses ------------------------------------------------------------------


def test_nobody_sees_anybody_in_the_offtown_place(town):
    town.world.place("jo_lamb", "city")
    town.world.place("sam_hart", "city")
    assert M.witnesses(town, _event(town, "eat", "jo_lamb", detail="lunch")) == []


def test_private_events_have_no_witnesses_and_sleepers_see_nothing(town):
    assert M.witnesses(town, _event(town, "wage", "pat_reed", amount=40)) == []
    town.residents["lee_moss"].asleep = True
    seen = M.witnesses(town, _event(town, "eat", "pat_reed", detail="toast"))
    assert seen == ["ann_reed", "sam_hart"]


def test_a_stranger_walking_in_is_remembered_only_by_people_who_know_them(town):
    """Arrive is rated below the witness threshold: Pat remembers his boss
    coming in, and Ann, who has no dealings with Sam Lamb, does not."""
    town.world.place("sam_lamb", "house_2")
    event = _event(town, "arrive", "sam_lamb", where="house_2")
    who = M.record(town, event)
    assert "pat_reed" in who and "ann_reed" not in who


def test_the_three_renderings_of_one_event(town):
    town.world.place("sam_lamb", "workshop")
    town.world.place("pat_reed", "workshop")
    town.world.place("ann_reed", "workshop")
    # They work together: each has been given the other's name.
    town.residents["sam_lamb"].learn_name("pat_reed", 0, "always")
    town.residents["pat_reed"].learn_name("sam_lamb", 0, "always")
    event = _event(town, "hired", "sam_lamb", "pat_reed", detail="Mornings, weekdays.")
    M.record(town, event)
    assert town.residents["sam_lamb"].memory[-1].text.startswith("I took Pat Reed on")
    assert town.residents["pat_reed"].memory[-1].text.startswith("Sam Lamb took me on")
    # Ann has been given neither name, so she reads descriptions of both.
    ann_saw = town.residents["ann_reed"].memory[-1].text
    assert "Sam Lamb" not in ann_saw and "Pat Reed" not in ann_saw
    assert "a tall man with sawdust on his sleeves" in ann_saw


# -- names ------------------------------------------------------------------------


def test_the_name_index_finds_full_and_first_names_as_whole_words():
    index = NameIndex([("a", "Sam Lamb"), ("b", "Sam Hart"), ("c", "Lee Moss")])
    assert index.find("Sam said Lee was late") == {"a", "b", "c"}
    # A full name is one person; it does not also name everybody called Sam.
    assert index.find("Sam Lamb waved") == {"a"}
    assert index.find("Samuel and Leeds") == set()


def test_a_name_you_were_not_given_reads_as_a_description(town):
    ann = town.residents["ann_reed"]
    assert as_seen_by("Lee Moss said so.", ann, town) == (
        "An older man who reads the paper standing up said so.")
    ann.learn_name("lee_moss", 1)
    assert as_seen_by("Lee Moss said so.", ann, town) == "Lee Moss said so."
    assert known_as(town.residents["lee_moss"], ann) == "Lee Moss"


def test_somebody_you_know_is_not_half_renamed_by_a_stranger_who_shares_a_first_name(town):
    """Alive's bug: a player called Dara turned a neighbour Dara into a person
    made of two people. Here Pat knows Sam Lamb and not Sam Hart."""
    pat = town.residents["pat_reed"]
    pat.learn_name("sam_lamb", 1)
    text = as_seen_by("Sam Lamb and Sam Hart argued.", pat, town)
    assert text == "Sam Lamb and a young woman with a bike helmet argued."


def test_a_secret_is_caught_in_paraphrase(town):
    secrets = town.secrets()
    assert leak_check("they said sam borrowed money against the workshop tools", secrets) == ["sam_lamb"]
    assert leak_check("sam fixed a chair at the workshop", secrets) == []


# -- retrieval ----------------------------------------------------------------------


def test_retrieval_keeps_the_latest_and_the_heaviest(town):
    from populace.clock import GameTime

    lee = town.residents["lee_moss"]
    lee.remember(GameTime(1, 1), "The boiler went out.", importance=9)
    for t in range(2, 40):
        lee.remember(GameTime(1, t), f"Nothing much happened at {t}.", importance=1)
    got = M.retrieve(lee, M.ObservationContext("cafe"), cap=5)
    texts = [m.text for m in got]
    assert "The boiler went out." in texts
    assert "Nothing much happened at 39." in texts
    assert len(got) == 5


# -- locality -----------------------------------------------------------------------


def test_the_circle_is_household_first_and_capped(town):
    town.config.raw["locality"]["people_cap"] = 3
    sam = town.residents["sam_lamb"]
    got = locality.circle(town, sam)
    assert len(got) == 3
    assert "jo_lamb" in got and "pat_reed" in got  # household, then a relationship


def test_names_are_seeded_from_the_circle_only(town):
    town.config.raw["locality"]["people_cap"] = 2
    locality.refresh(town)
    locality.seed_acquaintance(town)
    for r in town.residents.values():
        assert set(r.names_known) == set(r.circle)
    assert not town.residents["ann_reed"].knows_name("sam_lamb")


def test_places_known_start_at_home_and_work_and_stay_under_the_cap(town):
    town.config.raw["locality"]["places_cap"] = 3
    got = locality.places_known(town, town.residents["pat_reed"])
    assert got[:2] == ["house_2", "workshop"]
    assert len(got) == 3 and "city" not in got
