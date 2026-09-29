"""From a sentence to a town: the spec, the skeleton, the prose, and locality."""

from __future__ import annotations

import json
from collections import defaultdict

import pytest

from populace.config import Config
from populace.gen import enrich as E
from populace.gen.generate import generate
from populace.gen.spec import merge_model_answer, parse_description
from populace.providers import mock as M
from populace.state.town import Town

SUBURB = "a suburb of 200 people with a strip mall, a school and a factory"


# -- reading the description ------------------------------------------------------


def test_the_description_is_read_by_rules():
    spec = parse_description(SUBURB, seed=7)
    assert spec.population == 200
    asked = {p["kind"] for p in spec.places if p["asked"]}
    # A strip mall is several shops; the school and the factory are what they say.
    assert {"grocery", "pharmacy", "laundromat", "diner", "hair_salon", "school", "factory"} <= asked
    added = {p["kind"] for p in spec.places if not p["asked"]}
    assert "park" in added  # a town of 200 has one whether or not anybody said so


def test_counts_names_and_size_words():
    spec = parse_description("a village called Upper Ashby with two pubs and a church", seed=1)
    assert spec.name == "Upper Ashby"
    assert spec.population == 60
    assert spec.count("bar") == 2
    assert parse_description("fifty people and a diner").population == 50


def test_a_model_reading_is_kept_only_if_it_validates():
    rules = parse_description(SUBURB, seed=7)
    good = merge_model_answer(rules, {"population": 180, "places": [{"kind": "factory", "count": 2}]})
    assert good is not None and good.population == 180 and good.count("factory") == 2
    assert merge_model_answer(rules, {"places": [{"kind": "casino", "count": 1}]}) is None
    assert merge_model_answer(rules, {"places": [{"kind": "house", "count": 3}]}) is None


# -- the town ---------------------------------------------------------------------


async def _make(tmp_path, description=SUBURB, seed=7, name="t"):
    town, report = await generate(description, tmp_path / name, seed=seed)
    return town, report


async def test_the_same_description_and_seed_make_the_same_town(tmp_path):
    a, _ = await _make(tmp_path, name="a")
    b, _ = await _make(tmp_path, name="b")
    c, _ = await _make(tmp_path, seed=8, name="c")
    dump = lambda t: json.dumps({"w": t.world.to_dict(),
                                 "r": {k: v.to_dict() for k, v in sorted(t.residents.items())}},
                                sort_keys=True)
    assert dump(a) == dump(b)
    assert dump(a) != dump(c)


@pytest.mark.parametrize("description,expected", [
    ("a hamlet of 12 people with a pub", 12),
    ("a small town of 50 people with a diner, a grocery and a workshop", 50),
    (SUBURB, 200),
    ("a town of 400 people with a high street and an industrial estate", 400),
])
async def test_towns_of_every_size_validate_and_have_exactly_that_many_people(
        tmp_path, description, expected):
    town, report = await _make(tmp_path, description)
    assert town.validate() == []
    assert len(town.residents) == expected == report["population"]
    reloaded = Town.load(tmp_path / "t")
    assert reloaded.validate() == []


async def test_the_people_who_run_places_work_there_and_landlords_are_real(tmp_path):
    town, _ = await _make(tmp_path)
    for place in town.world.places.values():
        for rid in place.hires:
            assert town.residents[rid].job.workplace == place.id
        for opening in place.openings:
            assert len(opening["filled_by"]) <= opening["slots"]
    landlords = defaultdict(set)
    for r in town.residents.values():
        if r.rent:
            landlord = town.residents[r.rent["landlord_id"]]
            assert landlord.household != r.household
            landlords[r.rent["home"]].add(landlord.id)
    assert all(len(v) == 1 for v in landlords.values()), "one landlord per building"
    assert sum(o["slots"] - len(o["filled_by"]) for p in town.world.places.values()
               for o in p.openings) > 0, "somewhere is a hand short"


async def test_pupils_go_to_school_on_weekdays_and_not_at_weekends(tmp_path):
    town, _ = await _make(tmp_path)
    pupils = [r for r in town.residents.values() if r.persona["status"] == "pupil"]
    assert pupils
    for r in pupils:
        assert r.scheduled_entry(20, 0).activity == "school"
        assert r.scheduled_entry(20, 6).activity != "school"


async def test_names_come_from_the_circle_and_strangers_are_descriptions(tmp_path):
    town, _ = await _make(tmp_path)
    cap = town.config.locality["people_cap"]
    for r in town.residents.values():
        assert len(r.circle) <= cap
        assert set(r.names_known) == set(r.circle)
        assert len(r.places_known) <= town.config.locality["places_cap"]
    descriptors = [r.persona["descriptor"] for r in town.residents.values()]
    assert len(set(descriptors)) == len(descriptors), "no two people look the same from across a street"


# -- persona prose ----------------------------------------------------------------


async def test_every_persona_is_complete_and_says_where_it_came_from(tmp_path):
    town, report = await _make(tmp_path)
    sources = report["persona_sources"]
    assert sources["mock"] + sources["template"] == 200
    assert sources["template"] <= 20, "the mock answers nearly everybody; templates are the fallback"
    for r in town.residents.values():
        for key in E.REQUIRED:
            assert r.persona[key]
        assert r.persona["gossip"] in E.DISPOSITIONS
        assert 1 <= len(r.goals_active) <= 2


async def test_the_validator_refuses_a_stranger_named_and_a_secret_given_away(tmp_path):
    town, _ = await _make(tmp_path, "a hamlet of 12 people with a pub")
    rid = sorted(town.residents)[0]
    allowed = E._allowed_names(town, [rid])
    stranger = next(r for r in town.residents.values()
                    if not set(r.name.split()) & allowed)
    sheet = E.template_sheet(town, rid, E._person_rng(town, rid))
    assert E.validate_person(town, rid, sheet, allowed) == []
    named = dict(sheet, backstory=f"Grew up next door to {stranger.name} and never forgave them.")
    assert any("nobody they know" in p for p in E.validate_person(town, rid, named, allowed))
    leaky = dict(sheet, secret="Lost a large sum on online betting last spring.",
                 public_bio="Everybody knows they lost a large sum on online betting last spring.")
    assert any("gives away" in p for p in E.validate_person(town, rid, leaky, allowed))
    assert E.validate_person(town, rid, dict(sheet, gossip="loud"), allowed)


async def test_a_batch_the_model_gets_wrong_twice_falls_back_to_templates_and_says_so(
        tmp_path, monkeypatch):
    monkeypatch.setitem(M._HANDLERS, "chargen", lambda rng, state, meta: "not json at all")
    town, report = await _make(tmp_path, "a hamlet of 12 people with a pub")
    assert report["persona_sources"]["template"] == 12
    assert all(r.persona["source"] == "template" for r in town.residents.values())
    assert report["model_calls"] == 3 * 2, "three batches of five, each asked twice"


async def test_an_interrupted_generation_does_not_pay_for_a_batch_twice(tmp_path):
    _, first = await _make(tmp_path, "a hamlet of 12 people with a pub", name="same")
    import shutil
    for p in (tmp_path / "same").iterdir():
        if p.name != "cache":
            shutil.rmtree(p) if p.is_dir() else p.unlink()
    _, second = await generate("a hamlet of 12 people with a pub", tmp_path / "same", seed=7)
    assert second["persona_sources"]["cached"] > 0
    assert second["model_calls"] < first["model_calls"]


async def test_a_generated_town_carries_nothing_of_alive(tmp_path):
    from tests.guards.test_content_clean import offences_in

    town, _ = await _make(tmp_path)
    text = json.dumps({k: v.to_dict() for k, v in town.residents.items()}) + \
        json.dumps(town.world.to_dict())
    assert offences_in(text) == []


def test_a_sentence_where_a_list_belongs_is_the_same_answer():
    """The first live run: a 7B wrote current_goals as one sentence, and ten
    otherwise good sheets were refused over the container."""
    sheet = E.normalise_sheet({
        "current_goals": "To find a steadier job and keep the kids fed this week.",
        "tastes": {"likes": "spicy food, history books", "dislikes": ["loud music"]},
        "gossip": " Talker ",
    })
    assert sheet["current_goals"] == ["To find a steadier job and keep the kids fed this week."]
    assert sheet["tastes"]["likes"] == ["spicy food", "history books"]
    assert sheet["gossip"] == "talker"


async def test_the_retry_says_what_was_wrong(tmp_path, monkeypatch):
    def first_wrong_then_right(rng, state, meta):
        town = E._MOCK_TOWNS[state["town_key"]]
        people = [dict(E.template_sheet(town, rid, E._person_rng(town, rid)), id=rid)
                  for rid in state["ids"]]
        if meta.get("attempt") == 1:
            people = [dict(p, gossip="loud") for p in people]
        return {"people": people}

    monkeypatch.setitem(M._HANDLERS, "chargen", first_wrong_then_right)
    town, report = await _make(tmp_path, "a hamlet of 12 people with a pub")
    assert report["persona_sources"]["mock"] > 0
    calls = [json.loads(l) for l in open(tmp_path / "t" / "runs" / "generate" / "calls.jsonl")]
    retries = [c for c in calls if c["attempt"] == 2]
    assert retries, "a wrong first answer must be asked again"
    said = retries[0]["prompt"][-1]["content"]
    assert "could not be used" in said and "gossip must be" in said
    assert retries[0]["prompt"][1]["role"] == "assistant", "the model sees what it said"


async def test_a_template_stand_in_is_never_cached(tmp_path, monkeypatch):
    monkeypatch.setitem(M._HANDLERS, "chargen", lambda rng, state, meta: "not json at all")
    await generate("a hamlet of 12 people with a pub", tmp_path / "t", seed=7)
    assert not list((tmp_path / "t" / "cache" / "enrich").glob("*.json"))


# -- the owner's three generation bugs, from the Westfield sample -------------------

import re as _re

from populace.gen import data as GD
from populace import words as WW


async def test_nobody_is_sent_to_a_place_that_is_shut(tmp_path):
    """Two residents were at the pub at 14:00; it opens at 16:00."""
    town, _ = await _make(tmp_path)
    offences = []
    for r in town.residents.values():
        for weekday in range(7):
            for e in r.day_schedule(weekday):
                place = town.world.places[e.location_id]
                if not place.public or e.activity in ("work", "sleep", "home"):
                    continue
                if r.job and e.location_id == r.job.workplace:
                    continue
                shut = [t for t in range(e.start_tick, e.end_tick)
                        if not place.is_open(t, None, weekday)]
                if shut:
                    offences.append(f"{r.id} {e.activity} at {place.name} on day {weekday} "
                                    f"from tick {e.start_tick}, shut at {shut[0]}")
    assert offences == [], "\n".join(offences[:10])


def _matches_pool(text: str, pool: list[str]) -> bool:
    for template in pool:
        pattern = _re.escape(template)
        pattern = _re.sub(r"\\\{\w+\\\}", ".+", pattern)
        if _re.fullmatch(pattern, text):
            return True
    return False


async def test_pupils_and_retired_people_get_sheets_that_fit_them(tmp_path):
    town, _ = await _make(tmp_path)
    grouped = GD.load("personas")["grouped"]
    work_words = ["job", "boss", "shift", "promoted", "coworker", "workplace", "career"]
    checked = 0
    for r in town.residents.values():
        group = E.group_of(r)
        if group not in ("pupil", "retired") or r.persona.get("source") != "mock":
            continue
        for field in ("backstory", "secret", "long_term_goal"):
            assert _matches_pool(r.persona[field], grouped[field][group]), (r.id, field, r.persona[field])
        assert _matches_pool(r.goals_active[0], grouped["weekly"][group]) or \
            r.goals_active[0].startswith("Find the rent"), (r.id, r.goals_active)
        if group == "pupil":
            for field in ("backstory", "secret", "long_term_goal"):
                assert not WW.contains(r.persona[field], work_words), (r.id, field, r.persona[field])
        checked += 1
    assert checked >= 20


async def test_a_town_does_not_say_the_same_thing_about_everybody(tmp_path):
    town, report = await _make(tmp_path)
    assert E.repeated(town) == {}, E.repeated(town)
    weekly = {r.goals_active[0] for r in town.residents.values()}
    assert len(weekly) >= len(town.residents) // 2
    for r in town.residents.values():
        for field in E.REQUIRED:
            sentences = [x.strip() for x in _re.split(r"(?<=[.!?])\s+", r.persona[field]) if x.strip()]
            assert len(sentences) == len(set(sentences)), (r.id, field)
        for field in ("backstory", "secret", "long_term_goal"):
            assert not _re.search(r"\[\w+\]", r.persona[field]), (r.id, field, "a slot went unfilled")


async def test_one_batch_cannot_hand_two_people_the_same_secret(tmp_path, monkeypatch):
    def everybody_the_same(rng, state, meta):
        town = E._MOCK_TOWNS[state["town_key"]]
        people = []
        for rid in state["ids"]:
            sheet = E.template_sheet(town, rid, E._person_rng(town, rid, str(meta.get("attempt"))))
            if meta.get("attempt") == 1:
                sheet["secret"] = "Is quietly worried about their health and has not said."
            people.append(dict(sheet, id=rid))
        return {"people": people}

    monkeypatch.setitem(M._HANDLERS, "chargen", everybody_the_same)
    town, _ = await _make(tmp_path, "a hamlet of 12 people with a pub")
    calls = [json.loads(l) for l in open(tmp_path / "t" / "runs" / "generate" / "calls.jsonl")]
    retries = [c for c in calls if c["attempt"] == 2]
    assert retries and "repeats" in retries[0]["prompt"][-1]["content"]
    secrets = [r.persona["secret"] for r in town.residents.values()]
    assert secrets.count("Is quietly worried about their health and has not said.") <= 3


async def test_only_grown_men_are_described_with_a_beard(tmp_path):
    """The live proof showed a stranger as "a stocky young woman with a neat beard"."""
    town, _ = await _make(tmp_path)
    bearded = [r.persona["descriptor"] for r in town.residents.values() if "beard" in r.persona["descriptor"]]
    assert bearded, "the check never fired"
    wrong = [d for d in bearded if any(w in d.split() for w in ("woman", "girl", "boy", "kid", "person"))]
    assert wrong == []


async def test_a_new_town_starts_with_its_trust_stages_settled(tmp_path):
    """Stages only caught up at night, so on day one every prompt described a
    partner as somebody who "knows your face"."""
    from populace.state.resident import stage_for

    town, _ = await _make(tmp_path)
    thresholds = tuple(town.config.trust["thresholds"])
    rels = [rel for r in town.residents.values() for rel in r.relationships.values()]
    assert any(rel.stage > 0 for rel in rels), "the check never fired"
    assert all(rel.stage == stage_for(rel.trust, thresholds) for rel in rels)


async def test_first_names_do_not_repeat_while_the_pool_has_fresh_ones(tmp_path):
    """A 12-person hamlet had three men called Julio. Readers, and the check
    for names said without being given, both rely on first names telling
    people apart."""
    from collections import Counter

    from populace.gen.generate import generate

    town, _ = await generate("a hamlet of 12 people with a pub, a shop and a cafe", tmp_path / "h", seed=5)
    firsts = Counter(r.name.split()[0] for r in town.residents.values())
    assert firsts.most_common(1)[0][1] == 1, firsts.most_common(3)


async def test_how_people_deal_with_a_broken_service_varies_across_a_town(tmp_path):
    """Step 4's live day: twelve people without internet, a helpdesk everybody
    knew of, and nobody got in touch. Reasons and permission, per character -
    never one line telling everybody to ring."""
    from collections import Counter

    from populace.prompt.blocks import character_block, when_things_break

    town, _ = await _make(tmp_path)
    ways = Counter(when_things_break(r) for r in town.residents.values())
    assert len(ways) >= 3, ways
    assert ways.most_common(1)[0][1] <= 0.7 * len(town.residents), ways
    r = next(iter(town.residents.values()))
    assert when_things_break(r) in character_block(r, town)
