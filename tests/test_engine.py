"""The tick loop: budget, fairness, refusals, and resuming mid-day."""

from __future__ import annotations

import asyncio
import json
import shutil

import pytest

from populace.gen.generate import generate
from populace.sim import actions as A
from populace.sim.run import build_engine, run_town
from populace.state.town import Town


@pytest.fixture(scope="module")
def town50(tmp_path_factory):
    root = tmp_path_factory.mktemp("w") / "w50"
    asyncio.run(generate("a small town of 50 people with a diner, a grocery and a workshop", root, seed=3))
    return root


def _copy(src, tmp_path, name="t"):
    dest = tmp_path / name
    shutil.copytree(src, dest)
    return dest


def _events(run_dir):
    return [json.loads(l) for l in open(run_dir / "events.jsonl")]


async def test_a_day_runs_within_the_budget(town50, tmp_path):
    root = _copy(town50, tmp_path)
    out = await run_town(root, 48, mock=True, run_id="r")
    reports = out["reports"]
    assert len(reports) == 48 and not reports[-1].stopped
    for r in reports:
        # The budget is every call; the only overrun allowed is the retries.
        assert r.calls <= r.budget + r.retries, r.to_dict()
    assert out["town"].world.time.day == 2 and out["town"].world.time.tick == 12
    kinds = {e["kind"] for e in _events(out["run_dir"])}
    assert {"arrive", "depart", "work_start", "wage", "sleep", "wake", "eat"} <= kinds


async def test_nobody_goes_days_without_a_thought(tmp_path):
    """At the laptop preset (about 120 decisions a day), everybody in a town of
    200 has thought by the end of day 3. The quick preset buys one decision a
    tick, 48 a day, and cannot promise this; that is what low fidelity means."""
    root = tmp_path / "w"
    await generate("a suburb of 200 people with a strip mall, a school and a factory", root, seed=7)
    out = await run_town(root, 48 * 3, mock=True, preset="laptop", run_id="r")
    town = out["town"]
    never = [r.id for r in town.residents.values() if r.last_model_tick < 0]
    assert never == [], f"{len(never)} of 200 never thought in three days"


async def test_stopping_and_resuming_mid_day_changes_nothing(town50, tmp_path):
    straight = _copy(town50, tmp_path, "a")
    split = _copy(town50, tmp_path, "b")
    one = await run_town(straight, 30, mock=True, run_id="r")
    await run_town(split, 13, mock=True, run_id="r")
    two = await run_town(split, 17, mock=True, run_id="r")
    strip = lambda evs: [{k: v for k, v in e.items()} for e in evs]
    assert strip(_events(one["run_dir"])) == strip(_events(two["run_dir"]))
    a, b = Town.load(straight), Town.load(split)
    for rid in a.residents:
        assert a.residents[rid].to_dict() == b.residents[rid].to_dict()


# -- no silent no-ops ---------------------------------------------------------------


def _engine(town, tmp_path):
    town.root = tmp_path
    engine = build_engine(town, mock=True, run_id="r")
    from populace.sim.engine import TickReport
    engine.report = TickReport(day=1, tick=town.world.time.tick)
    return engine


def _refusals(engine):
    engine._flush()
    return [e for e in engine.telemetry.read_stream("events") if e["kind"] in ("refused", "buy_fail")]


@pytest.mark.parametrize("setup,act,expect", [
    ("closed", A.Action("buy", target="coffee"), "was shut"),
    ("unstaffed", A.Action("buy", target="coffee"), "nobody behind the counter"),
    ("jobless", A.Action("work", target=None), "no job"),
    ("absent", A.Action("give", target="lee_moss", amount=5), "weren't there"),
    ("away_from_home", A.Action("eat"), "nothing of mine to eat"),
])
def test_an_action_that_cannot_happen_says_so(town, tmp_path, setup, act, expect):
    engine = _engine(town, tmp_path)
    sam = town.residents["sam_lamb"]
    if setup in ("closed", "unstaffed", "away_from_home"):
        town.world.place("sam_lamb", "cafe")
    if setup == "closed":
        town.world.time = town.world.time.__class__(1, 40)
        town.world.place("ann_reed", "cafe")
    if setup == "jobless":
        sam.job = None
    engine._economy({"sam_lamb": act})
    refusals = _refusals(engine)
    assert refusals and expect in refusals[0]["detail"]
    assert expect in sam.memory[-1].text, "the reason reaches the actor's own memory"


def test_buying_with_too_little_money_is_seen_and_said(town, tmp_path):
    engine = _engine(town, tmp_path)
    town.world.place("sam_lamb", "cafe")
    town.world.place("ann_reed", "cafe")
    town.residents["sam_lamb"].money = 1
    engine._economy({"sam_lamb": A.Action("buy", target="coffee")})
    assert _refusals(engine)[0]["kind"] == "buy_fail"


def test_every_resolver_branch_that_skips_an_action_says_why():
    """Static: in the resolvers, a `continue` that drops somebody's action must
    follow a _refuse or an emit, unless it is only filtering by action kind."""
    import ast
    import pathlib

    import populace.sim.engine as E
    tree = ast.parse(pathlib.Path(E.__file__).read_text())
    offences = []
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
               and n.name in ("_moves", "_economy")]:
        for node in ast.walk(fn):
            if not isinstance(node, ast.If):
                continue
            body = node.body
            if not any(isinstance(s, ast.Continue) for s in body):
                continue
            test = ast.unparse(node.test)
            said = any("_refuse" in ast.unparse(s) or "emit" in ast.unparse(s) for s in body)
            if not said and "act.action" not in test:
                offences.append(f"{fn.name}: if {test}: continue")
    assert offences == [], offences


def test_a_boss_facing_a_worker_who_keeps_missing_shifts_has_business(town):
    """A reason to think, not an order: the gate's mock week never fired
    anybody because no boss ever got a thought while facing the absentee."""
    from populace.sim.triggers import _debtor_present

    sam, pat = town.residents["sam_lamb"], town.residents["pat_reed"]
    pat.job.employer_id = sam.id
    town.world.place(pat.id, "workshop")
    town.world.place(sam.id, "workshop")
    assert _debtor_present(sam, town, set()) is None
    pat.job.no_shows = 2
    assert _debtor_present(sam, town, set()) == pat.id
