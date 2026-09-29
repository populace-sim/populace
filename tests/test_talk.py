"""Conversations, deals and the phone."""

from __future__ import annotations

import json

import pytest

from populace.sim import actions as A
from populace.sim import deals as DL
from populace.sim import dialogue as D
from populace.sim import phone as PH
from populace.sim.engine import TickReport
from populace.sim.run import build_engine


@pytest.fixture
def engine(town, tmp_path):
    town.root = tmp_path
    e = build_engine(town, mock=True, run_id="r")
    e.report = TickReport(day=1, tick=town.world.time.tick)
    for rid in ("sam_lamb", "pat_reed"):
        town.world.place(rid, "workshop")
    return e


def _result(a, b, where="workshop", lines=None):
    return D.ConversationResult(initiator=a, target=b, location_id=where,
                                lines=lines or [{"speaker": a, "text": "Morning."}])


def _refused(engine):
    engine._flush()
    return [e["detail"] for e in engine.telemetry.read_stream("events") if e["kind"] == "refused"]


# -- conversations ---------------------------------------------------------------------


async def test_each_line_is_written_by_a_call_that_sees_only_its_speaker(engine):
    town = engine.town
    town.residents["sam_lamb"].learn_name("pat_reed", 0)
    result = await D.run_conversation(town, engine.runner, "sam_lamb", "pat_reed", "Morning.", 5)
    calls = engine.telemetry.read_stream("calls")
    systems = {s["system_hash"]: s["blocks"][1] for s in engine.telemetry.read_stream("systems")}
    assert calls
    for c in calls:
        me = town.residents[c["char_id"]]
        assert systems[c["system_hash"]].startswith(f"YOU ARE {me.name.upper()}")
    assert len(result.lines) <= 5


def test_a_name_is_learned_only_by_being_said(engine):
    town = engine.town
    pat, sam = town.residents["pat_reed"], town.residents["sam_lamb"]
    result = _result("sam_lamb", "pat_reed", lines=[{"speaker": "sam_lamb", "text": "Morning."}])
    D.learn_names_said(result, town, [])
    assert not pat.knows_name("sam_lamb")
    result.lines.append({"speaker": "sam_lamb", "text": "I'm Sam, by the way."})
    D.learn_names_said(result, town, ["ann_reed"])
    assert pat.knows_name("sam_lamb") and town.residents["ann_reed"].knows_name("sam_lamb")
    # Nobody can hand over a name they have not got.
    result = _result("sam_lamb", "pat_reed", lines=[{"speaker": "sam_lamb", "text": "Seen Lee today?"}])
    D.learn_names_said(result, town, [])
    assert not pat.knows_name("lee_moss")


def test_a_sighting_the_speaker_does_not_have_is_caught(engine):
    town = engine.town
    sam = town.residents["sam_lamb"]
    sam.learn_name("lee_moss", 0)
    problem = D.unsupported_claim("Lee came in earlier, looking for you.", sam, town, {"sam_lamb", "pat_reed"})
    assert problem and "Lee Moss" in problem
    assert D.unsupported_claim("Lee's all right.", sam, town, {"sam_lamb"}) is None


async def test_a_talk_with_no_budget_left_keeps_for_next_tick(engine):
    town = engine.town
    engine.runner.meter.tick_calls = 99
    engine.talks = [("sam_lamb", A.Action("talk", target="pat_reed", dialogue="Got a minute?"))]
    await D.converse(engine)
    engine._flush()
    kinds = [e["kind"] for e in engine.telemetry.read_stream("events")]
    assert "talk_deferred" in kinds
    assert town.residents["sam_lamb"].intent.dialogue == "Got a minute?"


async def test_a_second_conversation_with_the_same_person_today_is_refused_out_loud(engine):
    engine.pair_today["pat_reed|sam_lamb"] = 1
    engine.talks = [("sam_lamb", A.Action("talk", target="pat_reed", dialogue="Me again."))]
    await D.converse(engine)
    assert any("already talked" in r for r in _refused(engine))


# -- deals --------------------------------------------------------------------------------


def test_a_hire_takes_the_openings_terms_and_changes_the_day(engine):
    town = engine.town
    shop = town.world.places["workshop"]
    shop.openings = [{"title": "hand", "wage_per_tick": 4.0, "shift": {"start": 16, "end": 30},
                      "days": [0, 1, 2], "slots": 1, "filled_by": []}]
    ann = town.residents["ann_reed"]
    ann.job = None
    town.world.place("ann_reed", "workshop")
    out = DL.apply_one(engine, _result("sam_lamb", "ann_reed"), "sam_lamb", {"kind": "hire", "title": "hand"}, 2)
    assert out["ok"], out
    assert ann.job.workplace == "workshop" and ann.job.wage_per_tick == 4.0 and ann.job.employer_id == "sam_lamb"
    assert any(e.activity == "work" and e.location_id == "workshop" for e in ann.schedule)
    again = DL.apply_one(engine, _result("sam_lamb", "lee_moss"), "sam_lamb", {"kind": "hire"}, 2)
    assert not again["ok"]
    assert any("no work going" in r for r in _refused(engine)), "the speaker is told it did not happen"


def test_fire_and_quit_need_the_right_person(engine):
    town = engine.town
    out = DL.apply_one(engine, _result("pat_reed", "sam_lamb"), "pat_reed", {"kind": "fire"}, 2)
    assert not out["ok"]
    out = DL.apply_one(engine, _result("pat_reed", "sam_lamb"), "pat_reed", {"kind": "quit"}, 2)
    assert out["ok"] and town.residents["pat_reed"].job is None


def test_a_loan_lives_in_both_heads_and_repayment_needs_an_offer(engine):
    town = engine.town
    sam, pat = town.residents["sam_lamb"], town.residents["pat_reed"]
    sam.relationships["pat_reed"].trust = 40
    before = sam.money
    out = DL.apply_one(engine, _result("sam_lamb", "pat_reed"), "sam_lamb",
                       {"kind": "loan", "amount": 40, "due_in_days": 3}, 2)
    assert out["ok"], out
    assert sam.money == before - 40 and pat.owes_to("sam_lamb") == 40 and sam.owed_by("pat_reed") == 40
    no_offer = DL.apply_one(engine, _result("pat_reed", "sam_lamb"), "sam_lamb", {"kind": "repay"}, 2)
    assert not no_offer["ok"]
    engine.offers["pat_reed"] = {"money": 25, "to": "sam_lamb"}
    paid = DL.apply_one(engine, _result("pat_reed", "sam_lamb"), "sam_lamb", {"kind": "repay"}, 2)
    assert paid["ok"] and pat.owes_to("sam_lamb") == 15


def test_a_promise_is_written_on_both_sides(engine):
    town = engine.town
    DL.apply_one(engine, _result("sam_lamb", "pat_reed"), "sam_lamb",
                 {"kind": "promise", "what": "fix the vice", "by": "me", "in_days": 2}, 2)
    mine = town.residents["sam_lamb"].relationships["pat_reed"].open_promises()
    theirs = town.residents["pat_reed"].relationships["sam_lamb"].open_promises()
    assert mine[0]["by"] == "me" and theirs[0]["by"] == "them" and mine[0]["what"] == "fix the vice"


def test_an_invitation_accepted_becomes_together_at_the_hour(engine):
    town = engine.town
    DL.apply_one(engine, _result("sam_lamb", "pat_reed"), "sam_lamb",
                 {"kind": "invite", "where": "cafe", "in_ticks": 1}, 2)
    DL.apply_one(engine, _result("sam_lamb", "pat_reed"), "pat_reed", {"kind": "accept"}, 3)
    town.world.time = town.world.time.advance()
    for rid in ("sam_lamb", "pat_reed"):
        town.world.place(rid, "cafe")
    engine._keep_arrangements()
    engine._flush()
    assert "together" in [e["kind"] for e in engine.telemetry.read_stream("events")]


def test_a_gift_offered_lands_only_when_taken(engine):
    town = engine.town
    sam, pat = town.residents["sam_lamb"], town.residents["pat_reed"]
    engine.offers["sam_lamb"] = {"money": 10, "to": "pat_reed"}
    before = pat.money
    out = DL.apply_one(engine, _result("sam_lamb", "pat_reed"), "pat_reed", {"kind": "gift_accept"}, 2)
    assert out["ok"] and pat.money == before + 10
    declined = DL.apply_one(engine, _result("sam_lamb", "pat_reed"), "pat_reed",
                            {"kind": "gift_accept", "accept": False}, 2)
    assert declined["declined"]


# -- the phone ----------------------------------------------------------------------------


def test_a_text_needs_a_number_and_lands_on_both_phones(engine):
    town = engine.town
    with pytest.raises(PH.PhoneError):
        PH.send_text(town, "sam_lamb", "lee_moss", "About?")
    town.residents["sam_lamb"].phone["contacts"]["lee_moss"] = "555-0001"
    PH.send_text(town, "sam_lamb", "lee_moss", "About?")
    lee = town.residents["lee_moss"]
    assert PH.unread(lee) and "texted" in lee.memory[-1].text
    assert "Sam Lamb" not in lee.memory[-1].text, "a text does not hand over a name"


async def test_contact_over_the_daily_cap_is_refused(engine):
    town = engine.town
    town.config.raw["phone"]["send_cap_per_day"] = 1
    town.residents["sam_lamb"].phone["contacts"]["lee_moss"] = "555-0001"
    engine.texts = [("sam_lamb", A.Action("contact", target="lee_moss", dialogue="one")),
                    ("sam_lamb", A.Action("contact", target="lee_moss", dialogue="two"))]
    await PH.send_texts(engine)
    assert any("enough people" in r for r in _refused(engine))


async def test_a_reply_is_one_call_and_capped(engine):
    town = engine.town
    town.config.raw["phone"]["reply_cap_per_person_per_day"] = 1
    town.residents["sam_lamb"].phone["contacts"]["lee_moss"] = "555-0001"
    for text in ("one", "two"):
        PH.send_text(town, "sam_lamb", "lee_moss", text)
        await PH.reply_turn(engine, town.residents["lee_moss"])
    calls = [c for c in engine.telemetry.read_stream("calls") if c["role"] == "dialogue"]
    assert len(calls) == 1


def test_an_offer_made_to_one_person_cannot_be_taken_by_another(engine):
    """Found by the mock gate: a request made to one person leaked into another
    conversation the same tick, and somebody lent money nobody had asked for."""
    engine.offers["sam_lamb"] = {"money": 10, "to": "ann_reed"}
    out = DL.apply_one(engine, _result("sam_lamb", "pat_reed"), "pat_reed", {"kind": "gift_accept"}, 2)
    assert not out["ok"]


async def test_new_business_earns_a_second_conversation_but_not_a_third(engine):
    engine.pair_today["pat_reed|sam_lamb"] = 1
    engine.talks = [("sam_lamb", A.Action("talk", target="pat_reed", dialogue="Here, towards it.",
                                          intent="offer", offer={"money": 5}))]
    await D.converse(engine)
    assert engine.pair_today["pat_reed|sam_lamb"] == 2
    engine.talks = [("sam_lamb", A.Action("talk", target="pat_reed", dialogue="And another thing.",
                                          intent="offer", offer={"money": 5}))]
    await D.converse(engine)
    assert any("already talked" in r for r in _refused(engine))


# -- news in conversation ----------------------------------------------------------------


def _notice_seen(engine, rid, text="Quiz night at the bar, Friday", at=None):
    world = engine.town.world
    world.notices.append({"inj": "i1", "kind": "event.notice", "places": ["cafe"], "text": text,
                          "until": None, "only": None, "reveals": None, "reported": None,
                          "seen_by": {rid: world.time.total_ticks if at is None else at}})


def test_what_a_speaker_has_seen_is_in_front_of_them_mid_conversation(engine):
    """On the PC's 32B day nothing injected was passed on in conversation. The
    talk prompt showed only memories retrieved by relevance; a notice seen at
    noon, with a few memories since, never reached it."""
    from populace.clock import GameTime

    sam = engine.town.residents["sam_lamb"]
    _notice_seen(engine, "sam_lamb")
    for n in range(6):
        sam.remember(GameTime(1, 17 + n), f"Sanded the table leg, pass {n}.", importance=2)
    prompt = D.speaker_prompt(sam, engine.town.residents["pat_reed"], engine.town, _result("sam_lamb", "pat_reed"))
    assert "Quiz night at the bar" in prompt


async def test_news_since_you_last_spoke_is_a_reason_to_talk_again(engine):
    engine.pair_today["pat_reed|sam_lamb"] = 1
    engine.pair_last = {"pat_reed|sam_lamb": engine.town.world.time.total_ticks - 4}
    _notice_seen(engine, "sam_lamb", at=engine.town.world.time.total_ticks - 1)
    engine.talks = [("sam_lamb", A.Action("talk", target="pat_reed", dialogue="Did you see the notice?"))]
    await D.converse(engine)
    assert engine.pair_today["pat_reed|sam_lamb"] == 2


async def test_old_news_is_not_a_reason_to_talk_again(engine):
    engine.pair_today["pat_reed|sam_lamb"] = 1
    engine.pair_last = {"pat_reed|sam_lamb": engine.town.world.time.total_ticks - 2}
    _notice_seen(engine, "sam_lamb", at=engine.town.world.time.total_ticks - 6)
    engine.talks = [("sam_lamb", A.Action("talk", target="pat_reed", dialogue="Me again."))]
    await D.converse(engine)
    assert any("already talked" in r for r in _refused(engine))
