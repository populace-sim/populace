"""The ISP demo: its helpdesk's rules, its schedule, and a small run end to end."""

from __future__ import annotations

import asyncio
import json

from populace.agents.protocol import Message
from populace.demos import isp
from populace.observe import service_metrics
from populace.observe.report import load, render


class Ctx:
    def __init__(self, day=1):
        self.day = day
        self.actions = []

    def resolve(self, note="", kind=None):
        self.actions.append(("resolve", kind))
        return 1

    def credit(self, amount, reason=""):
        self.actions.append(("credit", amount))

    def dispatch(self, at, fixes=True, note="", kind=None):
        self.actions.append(("dispatch", at, kind))

    def promise(self, what, by_day, kind=None):
        self.actions.append(("promise", by_day, kind))

    def note(self, text):
        self.actions.append(("note", text))


def _msg(text, problems, number="555-1", address="4 Elm Street", channel="text", day=1):
    return Message(service="northline", channel=channel,
                   customer={"name": "Ann Reed", "number": number, "address": address},
                   text=text, thread=[], day=day, time="09:00", problems=problems)


def test_a_wrong_bill_is_corrected_and_nothing_else_is_touched():
    agent, ctx = isp.NorthlineSupport(), Ctx()
    reply = agent.handle(_msg("My bill is way too high", ["a Northline bill of $184.60"]), ctx)
    assert ("resolve", "billing") in ctx.actions
    assert "bill" in reply.text


def test_an_outage_is_a_known_fault_once_two_on_a_street_report_it():
    agent = isp.NorthlineSupport()
    first = agent.handle(_msg("Internet's down", ["no internet"], number="1"), Ctx())
    second = agent.handle(_msg("No internet here", ["no internet"], number="2", address="9 Elm Street"), Ctx())
    assert "known fault" not in first.text
    assert "known fault on Elm Street" in second.text


def test_slow_internet_gets_an_engineer_and_a_promise_for_the_line_only():
    agent, ctx = isp.NorthlineSupport(), Ctx()
    agent.handle(_msg("It's crawling", ["very slow internet"]), ctx)
    assert ("dispatch", "Day 2 10:00", "internet") in ctx.actions
    assert ("promise", 2, "internet") in ctx.actions


def test_having_to_chase_earns_one_credit():
    agent = isp.NorthlineSupport()
    agent.handle(_msg("Still down", ["no internet"]), Ctx())
    ctx2, ctx3 = Ctx(), Ctx()
    agent.handle(_msg("Still down!", ["no internet"]), ctx2)
    agent.handle(_msg("STILL down", ["no internet"]), ctx3)
    assert ("credit", 10.0) in ctx2.actions
    assert not any(a[0] == "credit" for a in ctx3.actions), "one credit, not one per chase"


def test_a_billing_fix_does_not_fix_the_internet(tmp_path):
    from populace.agents.contact import resolve_problems
    from tests.conftest import build_small_town

    town = build_small_town()
    sam = town.residents["sam_lamb"]
    sam.problems = [{"kind": "billing", "inj": "i1", "resolved": False},
                    {"kind": "internet", "inj": "i2", "resolved": False}]
    resolve_problems(sam, {"handles": ["internet", "billing"]}, 20, town, kind="billing")
    assert [p["resolved"] for p in sam.problems] == [True, False]


def _town(tmp_path, residents=40):
    return asyncio.run(isp.build(tmp_path / "isp", residents=residents, seed=7))


def test_the_schedule_fits_the_town_and_nothing_is_refused(tmp_path):
    built = _town(tmp_path)
    kinds = [r["kind"] for r in built["scheduled"]]
    assert built["refused"] == []
    assert kinds.count("event.outage") == 3 and kinds.count("service.register") == 1
    assert 1 <= kinds.count("event.letter") <= 12


def test_the_demo_runs_in_mock_and_the_report_has_the_service(tmp_path):
    from populace.sim.run import run_town, ticks_for_days

    _town(tmp_path)
    result = asyncio.run(run_town(tmp_path / "isp", ticks_for_days(2), mock=True, run_id="t",
                                  agents={"northline": isp.NorthlineSupport()}))
    text = render(result["run_dir"])
    assert "## The service" in text and "Northline Internet" in text
    m = service_metrics.compute(load(result["run_dir"]))["northline"]
    assert m["affected"] > 0 and m["contacts"] > 0
    assert m["invented_contacts"] == 0, "the mock only gets in touch about a real problem"
    contacts = [json.loads(l) for l in open(result["run_dir"] / "contacts.jsonl")]
    assert {c["channel"] for c in contacts} <= {"text", "call", "visit"}
