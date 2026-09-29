"""External agents: a resident reaches a service by their own choice, the
agent's answer changes the world through the record, and every failure is
said."""

from __future__ import annotations

import asyncio
import json
import socket
import time

import pytest

from populace.agents import AgentContext, HttpAgent, Message, Reply
from populace.agents.basic import EchoAgent, HelpdeskAgent
from populace.agents.contact import contact_service, judge_promises
from populace.agents.http import serve
from populace.inject import inject
from populace.inject import apply as INJ
from populace.observe import flags as F
from populace.sim import actions as A
from populace.sim.engine import TickReport
from populace.sim.run import build_engine


@pytest.fixture
def engine(town, tmp_path):
    town.root = tmp_path
    town.save(tmp_path, full=True)
    e = build_engine(town, mock=True, run_id="r")
    e.report = TickReport(day=1, tick=town.world.time.tick)
    return e


def _service(engine, **extra):
    inject(engine.town, {"kind": "service.register", "params": {
        "id": "northline", "name": "Northline Internet", "purpose": "home internet",
        "channels": ["text", "call", "visit"], "storefront": "cafe", "handles": ["internet"], **extra}})
    INJ.apply_due(engine)


def _outage(engine, home="house_1", until="Day 3 12:00"):
    inject(engine.town, {"kind": "event.outage", "params": {"service": "internet", "homes": [home], "until": until}})
    INJ.apply_due(engine)
    engine._flush()


def _contact(engine, rid="sam_lamb", channel="text", words="Our internet is down."):
    r = engine.town.residents[rid]
    act = A.validate({"action": "contact", "target": "northline", "dialogue": words, "channel": channel},
                     r, engine.town)
    asyncio.run(contact_service(engine, r, act))
    engine._flush()
    return r


def _contacts(engine):
    path = engine.telemetry.log_dir / "contacts.jsonl"
    return [json.loads(l) for l in open(path)] if path.exists() else []


def _mem(r, needle):
    return [m.text for m in r.memory if needle in m.text]


def test_a_helpdesk_books_an_engineer_and_the_engineer_fixes_it(engine):
    _service(engine)
    _outage(engine)
    engine.agents = {"northline": HelpdeskAgent("Northline Internet")}
    sam = _contact(engine)
    assert _mem(sam, "I texted Northline Internet"), "one line of memory for the contact"
    assert [a["do"] for a in _contacts(engine)[0]["actions"]] == ["dispatch", "promise"]
    world = engine.town.world
    while world.time.total_ticks < 48 + 18:          # Day 2 09:00
        world.time = world.time.advance()
    INJ.apply_due(engine)
    engine._flush()
    assert all(p["resolved"] for p in sam.problems)
    assert _mem(sam, "came round and sorted the internet")
    judge_promises(engine, 2)
    engine._flush()
    assert _mem(sam, "They did.")


def test_nobody_answering_is_said(engine):
    _service(engine)
    sam = _contact(engine)
    assert _mem(sam, "nobody answered")
    assert _contacts(engine)[0]["failed"] == "nobody answered"


def test_out_of_hours_is_said(engine):
    _service(engine, hours={"open": "09:00", "close": "17:00"})
    engine.agents = {"northline": EchoAgent()}
    sam = _contact(engine)
    assert _mem(sam, "they were closed")


def test_an_agent_that_breaks_is_a_dead_line_not_a_crash(engine):
    class Broken:
        def handle(self, message, ctx):
            raise RuntimeError("boom")

    _service(engine)
    engine.agents = {"northline": Broken()}
    sam = _contact(engine)
    assert _mem(sam, "the line went dead")


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_an_http_agent_answers_through_a_server(engine):
    port = _free_port()
    server = serve(HelpdeskAgent("Northline Internet"), port)
    try:
        _service(engine)
        _outage(engine)
        engine.agents = {"northline": HttpAgent(f"http://127.0.0.1:{port}/", timeout=5)}
        sam = _contact(engine)
    finally:
        server.shutdown()
    assert _mem(sam, "engineer will be with you")
    assert [a["do"] for a in _contacts(engine)[0]["actions"]] == ["dispatch", "promise"]


def test_an_http_agent_that_never_answers_times_out_and_is_said(engine):
    class Slow:
        def handle(self, message, ctx):
            time.sleep(3)
            return "too late"

    port = _free_port()
    server = serve(Slow(), port)
    try:
        _service(engine)
        engine.agents = {"northline": HttpAgent(f"http://127.0.0.1:{port}/", timeout=0.5)}
        started = time.perf_counter()
        sam = _contact(engine)
        assert time.perf_counter() - started < 2.5
    finally:
        server.shutdown()
    assert _mem(sam, "the line went dead")


def test_a_call_goes_back_and_forth_within_the_budget(engine):
    class Chatty:
        def handle(self, message, ctx):
            return Reply("Go on.")

    from populace.providers.base import ModelResult

    async def always_one_more(role, system, messages, meta=None):
        engine.runner.meter.tick_calls += 1
        return ModelResult(text='{"line": "And when will it be back?", "end_conversation": false}')

    _service(engine)
    _outage(engine)
    engine.agents = {"northline": Chatty()}
    engine.runner.call = always_one_more
    engine.runner.meter.start_tick()
    _contact(engine, channel="call")
    lines = _contacts(engine)[0]["lines"]
    assert len([l for l in lines if l["from"] == "customer"]) >= 2
    engine.town.world.time = engine.town.world.time.advance()
    engine.runner.meter.start_tick()
    engine.runner.meter.tick_calls = 999                 # the tick's budget is gone
    _contact(engine, rid="jo_lamb", channel="call")
    assert len([l for l in _contacts(engine)[1]["lines"] if l["from"] == "customer"]) == 1


def test_a_visit_is_made_at_the_counter_and_seen_there(engine):
    _service(engine)
    engine.agents = {"northline": EchoAgent()}
    world = engine.town.world
    world.place("ann_reed", "cafe")
    _contact(engine, channel="visit")
    assert world.location_of("sam_lamb") == "cafe"
    assert _mem(engine.town.residents["ann_reed"], "at the counter")


def test_a_credit_is_money_on_the_record(engine):
    class Generous:
        def handle(self, message, ctx):
            ctx.credit(15, "sorry")
            return "There you go."

    _service(engine)
    engine.agents = {"northline": Generous()}
    before = engine.town.residents["sam_lamb"].money
    sam = _contact(engine)
    assert sam.money == before + 15
    events = [json.loads(l) for l in open(engine.telemetry.log_dir / "events.jsonl")]
    credit = [e for e in events if e["kind"] == "credit"]
    assert credit and credit[0]["amount"] == 15 and credit[0]["source"] == "agent:northline"


def test_a_promise_not_kept_is_judged_broken(engine):
    class Talker:
        def handle(self, message, ctx):
            ctx.promise("fixed tonight", message.day)
            return "We'll have it back tonight."

    _service(engine)
    _outage(engine)
    engine.agents = {"northline": Talker()}
    sam = _contact(engine)
    judge_promises(engine, 1)
    engine._flush()
    assert _mem(sam, "They didn't.")


@pytest.mark.parametrize("raw, reason", [
    ({"channel": "fax"}, "'channel' is"),
    ({"channel": "call", "target": "pat_reed"}, "only text a person"),
])
def test_how_a_service_can_be_reached_is_checked(engine, raw, reason):
    _service(engine)
    r = engine.town.residents["sam_lamb"]
    r.phone.setdefault("contacts", {})["pat_reed"] = "555"
    with pytest.raises(A.InvalidAction, match=reason):
        A.validate({"action": "contact", "target": "northline", "dialogue": "hi", **raw}, r, engine.town)


def test_a_visit_needs_a_counter(engine):
    inject(engine.town, {"kind": "service.register", "params": {
        "id": "northline", "name": "Northline Internet", "purpose": "home internet", "channels": ["text", "visit"]}})
    INJ.apply_due(engine)
    with pytest.raises(A.InvalidAction, match="no counter"):
        A.validate({"action": "contact", "target": "northline", "dialogue": "hi", "channel": "visit"},
                   engine.town.residents["sam_lamb"], engine.town)


def test_the_message_carries_what_a_service_would_know_and_no_more(engine):
    seen = {}

    class Spy:
        def handle(self, message, ctx):
            seen.update(message.to_dict())
            return None

    _service(engine)
    _outage(engine)
    engine.agents = {"northline": Spy()}
    _contact(engine)
    assert set(seen["customer"]) == {"name", "number", "address"}
    assert seen["problems"] == ["no internet"]
    assert "secret" not in json.dumps(seen) and "persona" not in json.dumps(seen)


def test_the_run_command_attaches_agents_by_name():
    from populace.cli import _agents_from

    got = _agents_from(["northline=helpdesk", "shop=echo", "far=http://127.0.0.1:9/"])
    assert type(got["northline"]).__name__ == "HelpdeskAgent"
    assert type(got["shop"]).__name__ == "EchoAgent"
    assert isinstance(got["far"], HttpAgent)
    with pytest.raises(SystemExit, match="SERVICE="):
        _agents_from(["nonsense"])


# -- a household knows who has already reported it ------------------------------------


def test_the_household_learns_that_somebody_has_reported_it(engine):
    """On the PC's 32B day all three Masons and all three Sokolovs reported the
    same outage separately: nobody at home knew somebody else already had."""
    town = engine.town
    world = town.world
    _service(engine)
    _outage(engine, home="house_1")                    # Sam and Jo Lamb
    engine.agents = {"northline": HelpdeskAgent("Northline Internet")}
    world.place("sam_lamb", "house_1")
    world.place("jo_lamb", "house_1")
    _contact(engine, rid="sam_lamb")
    INJ.notice_pass(engine)
    engine._flush()
    jo = town.residents["jo_lamb"]
    line = next(l for l in INJ.prompt_lines(engine, jo) if l.startswith("At home"))
    assert "got on to Northline Internet" in line and "engineer" in line
    assert _mem(jo, "got on to Northline Internet")
    sam_line = next(l for l in INJ.prompt_lines(engine, town.residents["sam_lamb"]) if l.startswith("At home"))
    assert "You got on to Northline Internet" in sam_line


def test_somebody_out_learns_it_on_getting_home(engine):
    town = engine.town
    world = town.world
    _service(engine)
    _outage(engine, home="house_1")
    engine.agents = {"northline": HelpdeskAgent("Northline Internet")}
    world.place("sam_lamb", "house_1")
    world.place("jo_lamb", "cafe")
    _contact(engine, rid="sam_lamb")
    INJ.notice_pass(engine)
    engine._flush()
    jo = town.residents["jo_lamb"]
    assert not any("got on to" in l for l in INJ.prompt_lines(engine, jo)), "she was out"
    world.place("jo_lamb", "house_1")
    INJ.notice_pass(engine)
    engine._flush()
    assert any("got on to Northline Internet" in l for l in INJ.prompt_lines(engine, jo))


def test_a_failed_contact_is_not_a_report(engine):
    _service(engine)
    _outage(engine, home="house_1")
    engine.town.world.place("jo_lamb", "house_1")
    _contact(engine, rid="sam_lamb")                   # nobody answers
    INJ.notice_pass(engine)
    engine._flush()
    assert not any("got on to" in l for l in INJ.prompt_lines(engine, engine.town.residents["jo_lamb"]))


def test_a_fix_at_home_is_fixed_for_everybody_who_lives_there(engine):
    """The internet is the house's, not the caller's."""
    town = engine.town
    _service(engine)
    _outage(engine, home="house_1")
    engine.agents = {"northline": HelpdeskAgent("Northline Internet")}
    _contact(engine, rid="sam_lamb")
    world = town.world
    while world.time.total_ticks < 48 + 18:
        world.time = world.time.advance()
    INJ.apply_due(engine)
    engine._flush()
    assert all(p["resolved"] for p in town.residents["jo_lamb"].problems)


def test_a_named_building_gives_the_service_its_street_address(engine):
    """Live, "Clover Court" (5 Clover Street) went to the helpdesk as the
    address, so its "known fault" was counted per building, not per street."""
    from populace.agents.contact import customer

    town = engine.town
    home = town.world.places["house_1"]
    home.name, home.street, home.number = "Birch Court", "Birch Road", 3
    assert customer(town.residents["sam_lamb"], town)["address"] == "3 Birch Road"


def test_a_promise_is_judged_on_the_problem_it_was_about(engine):
    """Live, two "back by tomorrow" promises made as the first outage ended were
    judged broken because a second outage had begun by the night they fell due."""
    town = engine.town

    class Promiser:
        def handle(self, message, ctx):
            ctx.promise("back by tomorrow", message.day + 1, kind="internet")
            return "Back by tomorrow."

    _service(engine)
    _outage(engine, until="Day 1 12:00")
    engine.agents = {"northline": Promiser()}
    sam = _contact(engine)
    world = town.world
    while world.time.total_ticks < 25:
        world.time = world.time.advance()
    INJ.apply_due(engine)                              # the first outage ends
    _outage(engine, until="Day 3 12:00")               # a second one begins
    judge_promises(engine, 2)
    engine._flush()
    assert _mem(sam, "They did."), "the promise was about the first outage, which was put right"
    assert all(p.get("resolved_by") in (None, "schedule") or p["resolved_by"].startswith("service")
               for p in sam.problems)
    assert any(p.get("resolved_by") == "schedule" for p in sam.problems)


def test_a_block_of_flats_is_not_one_household(engine):
    """In the mock demo one resident's report reached all fifteen people in her block."""
    town = engine.town
    world = town.world
    _service(engine)
    _outage(engine, home="house_2")                    # Pat and Ann Reed (h2), Lee Moss (h3) share it
    engine.agents = {"northline": HelpdeskAgent("Northline Internet")}
    for rid in ("ann_reed", "pat_reed", "lee_moss"):
        world.place(rid, "house_2")
    _contact(engine, rid="ann_reed")
    INJ.notice_pass(engine)
    engine._flush()
    assert any("got on to" in l for l in INJ.prompt_lines(engine, town.residents["pat_reed"]))
    assert not any("got on to" in l for l in INJ.prompt_lines(engine, town.residents["lee_moss"])), \
        "a neighbour in the same building is not the household"


def test_an_async_agent_gets_the_time_it_asks_for_and_no_more(engine, monkeypatch):
    from populace.agents import contact as C
    monkeypatch.setattr(C, "AGENT_TIMEOUT_S", 0.05)

    class Slow:
        timeout_s = 1.0

        async def handle(self, message, ctx):
            await asyncio.sleep(0.2)
            ctx.log({"thought": "slowly"})
            return Reply("Got it.", end=True)

    class TooSlow(Slow):
        timeout_s = 0.1

    _service(engine)
    engine.agents = {"northline": Slow()}
    sam = _contact(engine)
    assert _mem(sam, "Got it.")
    logged = [json.loads(l) for l in open(engine.telemetry.log_dir / "agent_calls.jsonl")]
    assert logged == [{"day": 1, "tick": engine.town.world.time.tick, "service": "northline",
                       "resident": "sam_lamb", "thought": "slowly"}]
    engine.agents = {"northline": TooSlow()}
    pat = _contact(engine, rid="pat_reed")
    assert _mem(pat, "the line went dead")


def test_a_note_on_the_account_is_not_acting_on_a_claim(engine):
    class Notes:
        def handle(self, message, ctx):
            ctx.note("customer says the internet is down; line is fine")
            return Reply("Your line looks fine from here.", end=True)

    _service(engine)
    engine.agents = {"northline": Notes()}
    _contact(engine)                      # nobody at Sam's has a problem
    run = F.Run([], [], [], [], [], {}, {"residents": {}}, {}, _contacts(engine), [])
    run.end = {"residents": {"sam_lamb": {"problems": []}}}
    flagged = F.contact_ungrounded(run)
    assert flagged and flagged[0]["actions"] == []
