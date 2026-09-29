"""The decision prompt and the actions it asks for."""

from __future__ import annotations

import pytest

from populace.prompt.blocks import build_decision_prompt, character_block, shared_block
from populace.sim import actions as A
from populace.state.resident import Intent


def _prompt(town, rid):
    system, messages, _ = build_decision_prompt(town.residents[rid], town, [])
    return system, messages[0]["content"]


def test_the_rules_block_is_the_same_bytes_for_everybody(town):
    a, _ = _prompt(town, "sam_lamb")
    b, _ = _prompt(town, "ann_reed")
    assert a[0]["text"] == b[0]["text"] == shared_block(town)
    assert "Birchfield" in a[0]["text"]


def test_a_stranger_in_the_room_is_a_description_until_named(town):
    town.world.place("ann_reed", "house_1")
    _, dynamic = _prompt(town, "sam_lamb")
    assert "Ann Reed" not in dynamic
    assert "[ann_reed] the one they call ann_reed-ish" in dynamic
    town.residents["sam_lamb"].learn_name("ann_reed", 1)
    _, dynamic = _prompt(town, "sam_lamb")
    assert "[ann_reed] Ann Reed" in dynamic


def test_a_stranger_named_in_your_own_notes_is_masked_too(town):
    """The sweep's other half: the funnel really does fire on prose."""
    town.residents["sam_lamb"].persona["backstory"] = "Grew up next door to Lee Moss."
    text = character_block(town.residents["sam_lamb"], town)
    assert "Lee Moss" not in text
    assert "an older man who reads the paper standing up" in text


def test_the_reader_sees_only_the_places_and_people_they_know(town):
    from populace.state import locality
    locality.refresh(town)
    text = character_block(town.residents["jo_lamb"], town)
    assert "PLACES YOU KNOW" in text and "[house_1]" in text
    assert "[city]" not in text.split("PLACES YOU KNOW")[1].split("PEOPLE YOU KNOW")[0]


# -- validation -------------------------------------------------------------------


def _v(town, rid, **raw):
    return A.validate(raw, town.residents[rid], town)


def test_moving_somewhere_unknown_lists_the_places_you_know(town):
    town.residents["sam_lamb"].places_known = ["house_1", "workshop", "cafe"]
    with pytest.raises(A.InvalidAction, match="the places you know: house_1, workshop, cafe"):
        _v(town, "sam_lamb", action="move", target="the moon")


def test_you_cannot_walk_into_a_strangers_house(town):
    with pytest.raises(A.InvalidAction, match="somebody's home"):
        _v(town, "ann_reed", action="move", target="house_1")
    assert _v(town, "pat_reed", action="move", target="house_1").target == "house_1"  # he knows Sam


def test_talking_to_somebody_absent_names_the_room_without_leaking(town):
    town.world.place("lee_moss", "house_1")
    with pytest.raises(A.InvalidAction) as err:
        _v(town, "sam_lamb", action="talk", target="ghost", dialogue="hi")
    assert "Lee Moss" not in str(err.value)
    assert "an older man who reads the paper" in str(err.value)


def test_money_you_do_not_have_cannot_change_hands(town):
    town.world.place("pat_reed", "house_1")
    with pytest.raises(A.InvalidAction, match="you haven't got"):
        _v(town, "sam_lamb", action="give", target="pat_reed", amount=500)
    ok = _v(town, "sam_lamb", action="give", target="pat_reed", amount=20)
    assert (ok.target, ok.amount) == ("pat_reed", 20.0)


def test_a_text_needs_a_number(town):
    with pytest.raises(A.InvalidAction, match="no number"):
        _v(town, "sam_lamb", action="contact", target="lee_moss", dialogue="you about?")
    town.residents["sam_lamb"].phone["contacts"]["lee_moss"] = "555-0001"
    assert _v(town, "sam_lamb", action="contact", target="lee_moss", dialogue="about?").target == "lee_moss"


def test_you_eat_at_home_or_at_work_and_buy_anywhere_else(town):
    town.world.place("sam_lamb", "cafe")
    with pytest.raises(A.InvalidAction, match="buy something"):
        _v(town, "sam_lamb", action="eat")
    assert _v(town, "sam_lamb", action="buy", target="coffee").target == "coffee"


def test_a_deferred_line_is_said_next_tick_for_free(town):
    town.world.place("pat_reed", "house_1")
    sam = town.residents["sam_lamb"]
    sam.intent = Intent("talk", "pat_reed", town.world.time.total_ticks + 2, dialogue="Got a minute?")
    act = A.from_intent(sam, town)
    assert act.action == "talk" and act.dialogue == "Got a minute?" and act.source == A.SOURCE_INTENT


def test_the_schedule_buys_lunch_where_lunch_is_bought(town):
    sam = town.residents["sam_lamb"]
    sam.needs["hunger"] = 60
    town.world.place("sam_lamb", "cafe")
    from populace.state.resident import ScheduleEntry, tile
    sam.schedule = [ScheduleEntry.from_dict(b) for b in tile(
        [{"start_tick": 16, "end_tick": 17, "activity": "eat", "location_id": "cafe"}], "house_1")]
    act = A.from_schedule(sam, town)
    assert (act.action, act.target) == ("buy", "coffee")


def test_other_is_what_a_stranger_would_see(town):
    with pytest.raises(A.InvalidAction, match="pretending"):
        _v(town, "sam_lamb", action="other", target="pretending to read")
    assert _v(town, "sam_lamb", action="other", target="reading the paper so nobody talks to him"
              ).target == "reading the paper"


def test_a_plus_sign_on_a_number_is_not_a_broken_reply():
    """The reflection schema itself says "-3 to +3", and the live 7B wrote
    `"delta": +1` in nine of twenty reflections on the one-day proof. A plus
    inside a string is the resident's own words and stays."""
    reply = ('{"summary": "A +1 kind of day.", "relationship_updates": '
             '[{"character_id": "sam_lamb", "delta": +1}, {"delta": -2}], "n": [+3, 4]}')
    parsed = A.extract_json(reply)
    assert parsed is not None
    assert parsed["relationship_updates"][0]["delta"] == 1
    assert parsed["relationship_updates"][1]["delta"] == -2
    assert parsed["n"] == [3, 4]
    assert parsed["summary"] == "A +1 kind of day."
    assert A.extract_json('{"a": "+", "b": +x}') is None


def test_home_and_walk_are_read_as_what_they_mean(town):
    """The routine line says "home at [house_1]", and the live 7B answered with
    `"action": "home"` nine times in a day, and `"walk"` four. Each cost a retry."""
    sam = town.residents["sam_lamb"]
    elsewhere = next(p for p in ("workshop", "cafe") if p != town.world.location_of(sam.id))
    town.world.place(sam.id, elsewhere)
    went = _v(town, "sam_lamb", action="home")
    assert (went.action, went.target) == ("move", sam.home)
    town.world.place(sam.id, sam.home)
    assert _v(town, "sam_lamb", action="home").action == "wait"
    walked = _v(town, "sam_lamb", action="walk", target=elsewhere)
    assert (walked.action, walked.target) == ("move", elsewhere)
    with pytest.raises(A.InvalidAction, match="must be one of"):
        _v(town, "sam_lamb", action="dance")


def _pupil(town, rid="sam_hart"):
    from populace.state.resident import ScheduleEntry

    r = town.residents[rid]
    r.job = None
    r.schedule = [ScheduleEntry(0, 16, "sleep", r.home), ScheduleEntry(16, 30, "school", "city"),
                  ScheduleEntry(30, 48, "home", r.home)]
    r.off_schedule = []
    town.world.place(rid, r.home)
    return r


def test_a_pupil_may_go_to_school_in_the_city(town):
    """The second live day stopped on this: every pupil whose school is in the
    city was told the city was somebody's home."""
    _pupil(town)
    assert _v(town, "sam_hart", action="move", target="[city]").target == "city"


def test_the_city_is_refused_plainly_to_somebody_with_no_reason(town):
    town.residents["lee_moss"].job = None
    with pytest.raises(A.InvalidAction) as err:
        _v(town, "lee_moss", action="move", target="city")
    assert "somebody's home" not in str(err.value) and "nothing takes you" in str(err.value)


def test_work_for_a_pupil_means_school(town):
    _pupil(town)
    went = _v(town, "sam_hart", action="work")
    assert (went.action, went.target) == ("move", "city")


def test_walk_with_nowhere_asks_where(town):
    with pytest.raises(A.InvalidAction) as err:
        _v(town, "sam_lamb", action="walk")
    assert "None" not in str(err.value) and "where to" in str(err.value)


def test_work_from_away_means_going_to_work_when_the_shift_is_near(town):
    """19 of 26 refusals on step 4's live day were "I wasn't at work to do it"."""
    sam = town.residents["sam_lamb"]          # workshop, shift 18-34 (09:00-17:00)
    town.world.place(sam.id, sam.home)
    town.world.time = town.world.time.__class__(1, 17)
    went = _v(town, "sam_lamb", action="work")
    assert (went.action, went.target) == ("move", "workshop")
    town.world.place(sam.id, "workshop")
    assert _v(town, "sam_lamb", action="work").action == "work"


def test_work_well_off_shift_says_when_the_shift_is(town):
    sam = town.residents["sam_lamb"]
    town.world.place(sam.id, sam.home)
    town.world.time = town.world.time.__class__(1, 40)
    with pytest.raises(A.InvalidAction, match="your shift"):
        _v(town, "sam_lamb", action="work")
