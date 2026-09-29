"""The report: the same run always reads the same, and every flag can fire.

`tests/fixtures/run_small/` is one mock day of a 12-person hamlet with its
expected report; rebuild both with `tests/fixtures/make_run_small.py --write`
when a change is meant to alter them, and read the diff.
"""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest

from populace.observe import flags as F
from populace.observe.report import load, render

FIXTURE = Path(__file__).parent / "fixtures" / "run_small"


def test_the_report_of_a_fixed_run_is_the_golden_copy():
    assert render(FIXTURE) == (FIXTURE / "report.md").read_text(encoding="utf-8")


def test_the_report_names_people_and_hides_ids():
    text = render(FIXTURE)
    names = json.loads((FIXTURE / "names.json").read_text(encoding="utf-8"))
    body = text.split("## Who did what")[1].split("Everybody:")[0]
    assert any(n in body for n in names.values())
    # Ids appear only where a label puts one next to a name for grep.
    import re
    for m in re.finditer(r"\br\d{3}\b", text):
        before = text[max(0, m.start() - 60):m.start()]
        assert before.rstrip().endswith("("), f"a bare id in the report: ...{before}{m.group(0)}"


def test_a_run_without_snapshots_or_names_still_reports(tmp_path):
    """Runs from before step 3 have neither; the report says what it cannot do."""
    old = tmp_path / "old"
    shutil.copytree(FIXTURE, old)
    shutil.rmtree(old / "snapshots")
    (old / "names.json").unlink()
    (old / "decisions.jsonl").unlink()
    text = render(old)
    assert "nothing can be compared" in text
    assert "## Realism flags" in text


@pytest.fixture
def run():
    return copy.deepcopy(load(FIXTURE)["run"])


def _stranger_pair(run):
    """Somebody, and a person they have no tie to and no name for."""
    res = run.end["residents"]
    for a in sorted(res):
        for b in sorted(res):
            if a != b and b not in res[a]["ties"] and b not in res[a]["names_known"]:
                return a, b
    raise AssertionError("everybody in the fixture knows everybody")


def _conv(run, lines, day=1, tick=30):
    run.conversations.append({"day": day, "tick": tick, "participants": sorted({s for s, _ in lines}),
                              "lines": [{"speaker": s, "text": t} for s, t in lines], "deals": []})


def _event(run, **kw):
    base = {"day": 1, "tick": 20, "actor": "r001", "target": None, "location_id": "bridge_street_11",
            "amount": None, "detail": "", "importance": 2, "witnesses": [], "kind": "other"}
    run.events.append({**base, **kw})


def _breaks(run, name: str) -> list:
    return F.FLAGS[name](run)


# Flags about how people talk may fire on the mock, which repeats and echoes
# its stock lines on purpose. These others mean the engine or the logs are
# wrong, and must be silent on a clean run.
ENGINE_FLAGS = ("impossible_move", "sleepless", "ghost_contact", "money_from_nowhere",
                "provider_down_window", "id_spoken", "name_unknown")


def test_the_engine_flags_are_quiet_on_the_clean_fixture(run):
    found = {name: len(found) for name, found in F.run_all(run).items()}
    assert {k: found[k] for k in ENGINE_FLAGS if found[k]} == {}


def test_repeated_line_fires(run):
    _conv(run, [("r001", "I'll see you at the pub tonight then"), ("r002", "Right.")], tick=20)
    _conv(run, [("r001", "I'll see you at the pub tonight then"), ("r003", "Right.")], tick=30)
    assert any("r001" in f["who"] for f in _breaks(run, "repeated_line"))


def test_echo_fires(run):
    _conv(run, [("r001", "The roof on the shop is leaking again"),
                ("r002", "The roof on the shop is leaking again")])
    assert _breaks(run, "echo")


def test_stuck_fires(run):
    for tick in range(20, 20 + F.STUCK_RUN):
        run.decisions.append({"decision_id": f"x{tick}", "day": 1, "tick": tick, "resident": "r001",
                              "action": "move", "target": "pub", "source": "model"})
    assert _breaks(run, "stuck")


def test_impossible_move_fires(run):
    res, places = run.end["residents"], run.start["places"]
    a, home = next((a, pid) for a in sorted(res) for pid, p in sorted(places.items())
                   if not p["public"] and p["residents"] and a not in p["residents"]
                   and not set(p["residents"]) & set(res[a]["ties"]))
    _event(run, kind="arrive", actor=a, location_id=home)
    assert _breaks(run, "impossible_move")


def test_sleepless_fires(run):
    run.events = [e for e in run.events if not (e["actor"] == "r001" and e["kind"] in ("sleep", "wake"))]
    _event(run, kind="arrive", actor="r001", day=1, tick=30, location_id="bridge_street_11")
    assert any(f["who"] == ["r001"] for f in _breaks(run, "sleepless"))


def test_no_reaction_fires(run):
    _event(run, kind="fired", actor="r001", target="r002", importance=9, witnesses=["r003"], day=1, tick=14)
    run.decisions = [d for d in run.decisions if not (d["resident"] in ("r002", "r003")
                                                      and d["day"] == 1 and 14 <= d["tick"] <= 18)]
    assert _breaks(run, "no_reaction")


def test_ghost_contact_fires(run):
    a, b = _stranger_pair(run)
    _event(run, kind="text_sent", actor=a, target=b)
    assert _breaks(run, "ghost_contact")


def test_money_from_nowhere_fires(run):
    run.end["residents"]["r001"]["money"] += 500
    found = _breaks(run, "money_from_nowhere")
    assert [f["who"] for f in found] == [["r001"]]


def test_promise_ignored_fires(run):
    _event(run, kind="promise_broken", actor="r001", target="r002", day=1, tick=40)
    run.decisions = [d for d in run.decisions if not (d["resident"] == "r002" and d.get("target") == "r001")]
    assert _breaks(run, "promise_ignored")


def test_provider_down_window_fires(run):
    for c in run.calls:
        if c.get("day") == 1 and c.get("tick") in (20, 21, 22):
            c["error"] = "connection refused"
    assert _breaks(run, "provider_down_window")


def test_id_spoken_fires(run):
    _conv(run, [("r001", "Have you seen r002 today?"), ("r002", "No.")])
    assert _breaks(run, "id_spoken")


def test_name_unknown_fires_on_a_name_never_given(run):
    a, b = _stranger_pair(run)
    name = run.end["residents"][b]["name"]
    _conv(run, [(a, f"Morning, {name}."), (b, "Morning.")])
    assert any(f["who"] == [a, b] for f in _breaks(run, "name_unknown"))


def test_name_unknown_is_quiet_about_names_already_held(run):
    a = "r001"
    b = next(iter(run.end["residents"][a]["names_known"]))
    _conv(run, [(a, f"Morning, {run.end['residents'][b]['name']}."), (b, "Morning.")])
    assert not any(f["who"] == [a, b] for f in _breaks(run, "name_unknown"))


def test_every_flag_has_a_test():
    import inspect
    here = inspect.getsource(inspect.getmodule(test_every_flag_has_a_test))
    missing = [name for name in F.FLAGS if f"test_{name}_fires" not in here]
    assert missing == []


async def test_narration_is_labelled_and_works_from_the_record():
    from populace.config import Config
    from populace.observe.narrate import facts_from, narrate

    text = render(FIXTURE)
    story = await narrate(FIXTURE, text, Config.build(), mock=True)
    assert story.startswith("## The day, as a model tells it")
    assert "It can be wrong" in story
    assert "## What happened" in facts_from(text) and "## Who did what" not in facts_from(text)


def test_a_narrator_that_brings_in_people_is_called_out():
    from populace.observe.narrate import invented_people

    names = {"r001": "Ann Reed", "r002": "Sam Lamb"}
    assert invented_people("Ann Reed met Sam Lamb.", "Ann Reed went out.", names) == ["Sam Lamb"]


def test_claim_unfounded_fires(run):
    """The step 3 live day: a pupil told a housemate "you still haven't paid me
    back that $900", and no such debt existed anywhere."""
    a, b = _stranger_pair(run)
    _conv(run, [(a, "You still haven't paid me back that $900."), (b, "I know.")])
    found = _breaks(run, "claim_unfounded")
    assert any(f["who"][:2] == [a, b] for f in found)


def test_claim_unfounded_is_quiet_when_a_loan_backs_it(run):
    a, b = _stranger_pair(run)
    _event(run, kind="loan", actor=a, target=b, amount=30.0, day=1, tick=20)
    _conv(run, [(a, "You still owe me that thirty."), (b, "Friday, I promise.")], tick=30)
    assert not any(f["who"][:2] == [a, b] for f in _breaks(run, "claim_unfounded"))


def test_claim_unfounded_is_quiet_when_a_debt_stands_either_way(run):
    a, b = _stranger_pair(run)
    run.start["residents"][b]["owes"] = [{"to": a, "amount": 40.0, "kind": "loan"}]
    _conv(run, [(b, "I'll pay you back on Friday."), (a, "Fine.")])
    assert not any(set(f["who"][:2]) == {a, b} for f in _breaks(run, "claim_unfounded"))


def test_talking_about_money_is_not_a_claim(run):
    a, b = _stranger_pair(run)
    _conv(run, [(a, "Groceries cost $40 now, can you believe it?"), (b, "Terrible.")])
    assert not any(f["who"][:2] == [a, b] for f in _breaks(run, "claim_unfounded"))


# -- contacts about problems nobody had ------------------------------------------------------


def _someone_with_no_problem_at_home(run):
    """Break the fixture: one household's problems never happened."""
    res = run.end["residents"]
    rid = sorted(res)[0]
    for r in res.values():
        if r.get("home") == res[rid].get("home"):
            r["problems"] = []
    return rid


def test_contact_ungrounded_fires(run):
    """Live on the 32B, six residents got in touch about problems they did not
    have; the helpdesk credited one of them for an outage that never happened."""
    rid = _someone_with_no_problem_at_home(run)
    run.contacts.append({"day": 1, "tick": 30, "service": "northline", "resident": rid, "channel": "text",
                         "lines": [{"from": "customer", "text": "My internet's been down all morning."}],
                         "actions": [{"do": "credit", "amount": 10}]})
    found = [f for f in _breaks(run, "contact_ungrounded") if f["who"] == [rid]]
    assert found and found[0]["actions"] == ["credit"]


def test_the_real_contacts_in_the_fixture_are_all_grounded(run):
    assert run.contacts and _breaks(run, "contact_ungrounded") == []


def test_a_housemates_problem_is_grounds_to_call(run):
    """A wrong bill goes to one person; their partner ringing about it is real."""
    res = run.end["residents"]
    holder = next(rid for rid, r in sorted(res.items()) if r.get("problems"))
    mate = next((rid for rid, r in sorted(res.items())
                 if rid != holder and r.get("home") == res[holder]["home"]), None)
    assert mate, "the fixture needs a two-person home with a problem"
    for r in res.values():
        if r is not res[holder]:
            r["problems"] = []
    p = res[holder]["problems"][0]
    day, tick = divmod(int(p["since"]) + 1, F.TICKS_PER_DAY)
    run.contacts.append({"day": day + 1, "tick": tick, "service": "northline", "resident": mate,
                         "channel": "text", "lines": [], "actions": []})
    assert not any(f["who"] == [mate] for f in _breaks(run, "contact_ungrounded"))


def test_hours_to_first_contact_count_from_the_same_clock():
    """Problems count ticks from Day 1 and contacts carry a day number; the
    service section read every wait a day too long."""
    import copy as _c
    from populace.observe import service_metrics as SM

    ctx = load(FIXTURE)
    ctx = {**ctx, "run": _c.deepcopy(ctx["run"])}
    res = ctx["run"].end["residents"]
    rid = next(r for r, x in sorted(res.items()) if x.get("problems"))
    since = int(res[rid]["problems"][0]["since"])
    day, tick = divmod(since + 2, F.TICKS_PER_DAY)             # an hour after it began
    ctx["contacts"] = [{"day": day + 1, "tick": tick, "service": "northline", "resident": rid,
                        "channel": "text", "lines": [], "actions": []}]
    m = SM.compute(ctx)["northline"]
    assert m["hours_to_contact"]["median"] == 1.0


# -- findings: the agent's mistakes, apart from the simulation's --------------------------


def _ctx_with(extra_contacts=(), mutate=None):
    import copy as _c

    ctx = load(FIXTURE)
    ctx = {**ctx, "run": _c.deepcopy(ctx["run"])}
    if mutate:
        mutate(ctx["run"])
    ctx["run"].contacts = list(ctx["run"].contacts) + list(extra_contacts)
    ctx["contacts"] = ctx["run"].contacts
    ctx["flags"] = F.run_all(ctx["run"])
    return ctx


def _clear_home(run):
    res = run.end["residents"]
    rid = sorted(res)[0]
    for r in res.values():
        if r.get("home") == res[rid].get("home"):
            r["problems"] = []
    return rid


def test_crediting_an_invented_outage_is_the_agents_mistake_and_the_invention_is_the_sims():
    from populace.observe import findings

    holder = {}
    ctx = _ctx_with(mutate=lambda run: holder.setdefault("rid", _clear_home(run)))
    ctx["run"].contacts.append({"day": 2, "tick": 20, "service": "northline", "resident": holder["rid"],
                                "channel": "text", "actions": [{"do": "credit", "amount": 10}],
                                "lines": [{"from": "customer", "text": "Internet's down."}]})
    ctx["flags"] = F.run_all(ctx["run"])
    found = findings.compute(ctx)
    assert any("did not have" in x for x in found["agent"])
    assert any("invented problems" in x for x in found["sim"])


def test_correcting_a_bill_that_was_already_right_is_found():
    from populace.observe import findings

    holder = {}
    ctx = _ctx_with(mutate=lambda run: holder.setdefault("rid", _clear_home(run)))
    ctx["run"].contacts.append({"day": 2, "tick": 20, "service": "northline", "resident": holder["rid"],
                                "channel": "text", "lines": [],
                                "actions": [{"do": "resolve", "kind": "billing"}]})
    ctx["flags"] = F.run_all(ctx["run"])
    assert any("not broken" in x for x in findings.compute(ctx)["agent"])


def test_messages_left_out_of_hours_and_never_worked_are_found():
    from populace.observe import findings

    ctx = _ctx_with()
    res = ctx["run"].end["residents"]
    rid = next(r for r, x in sorted(res.items()) if x.get("problems"))
    for p in res[rid]["problems"]:
        p["resolved"], p["resolved_at"] = False, None
    ctx["run"].contacts = [c for c in ctx["run"].contacts if c["resident"] != rid] + [
        {"day": 1, "tick": 44, "service": "northline", "resident": rid, "channel": "text",
         "lines": [], "actions": [], "failed": "they were closed; a recording gave their hours"}]
    ctx["contacts"] = ctx["run"].contacts
    ctx["flags"] = F.run_all(ctx["run"])
    assert any("out-of-hours" in x for x in findings.compute(ctx)["agent"])


def test_the_report_labels_the_two_groups():
    text = render(FIXTURE)
    assert "### What the agent got wrong" in text and "### Where the simulation is weak" in text
    assert text.index("## Findings") < text.index("## What happened")


# -- the retelling leads with what was injected --------------------------------------------


def test_the_narrator_is_fed_the_injections_the_service_and_findings_first():
    from populace.observe.narrate import facts_from

    facts = facts_from(render(FIXTURE))
    assert facts.startswith("WHAT WAS INJECTED")
    order = [facts.index(h) for h in ("## Injected", "## The service", "## Findings", "## What happened")]
    assert order == sorted(order)


async def test_the_retelling_mentions_every_injection():
    from populace.config import Config
    from populace.observe.narrate import injected_entries, missing_injections, narrate

    text = render(FIXTURE)
    entries = injected_entries(text)
    assert {e["kind"] for e in entries} >= {"service.register", "place.close", "event.notice", "event.outage"}
    story = await narrate(FIXTURE, text, Config.build(), mock=True)
    assert "leaves out" not in story
    assert missing_injections(story, entries) == []


def test_a_retelling_that_skips_the_outage_is_called_out():
    """The live 32B's first retelling led with $62,445 in wages and never said
    the internet went off."""
    from populace.observe.narrate import injected_entries, missing_injections

    entries = injected_entries(render(FIXTURE))
    prose = ("The town earned good wages. Northline Internet took calls. The Copper Kettle shut for a "
             "burst pipe, and there was a quiz night on Friday.")
    missing = missing_injections(prose, entries)
    assert any("event.outage" in m for m in missing) and len(missing) == 1


# -- the PC's live retelling: what the checks must and must not say ------------------------


LIVE = FIXTURE.parents[2] / "docs" / "samples" / "isp-200-live-32b-report.md"


def _live_retelling():
    text = LIVE.read_text(encoding="utf-8")
    prose = text.split("## The day, as a model tells it", 1)[1].split("\n## ", 1)[0]
    prose = "\n".join(l for l in prose.splitlines() if l and not l.startswith(">") and not l.startswith("*It "))
    return text, prose.strip()


def test_the_live_retelling_leaves_no_injection_out():
    """It said "billing" and "registered"; exact whole words called the
    service's registration left out."""
    from populace.observe.narrate import injected_entries, missing_injections

    text, prose = _live_retelling()
    assert missing_injections(prose, injected_entries(text)) == []


def test_the_number_check_finds_the_live_retellings_three_errors():
    from populace.observe.narrate import facts_from, number_mismatches

    text, prose = _live_retelling()
    found = number_mismatches(prose, facts_from(text), text)
    joined = " | ".join(found)
    assert "47 households" in joined, found           # 47 residents, not households
    assert "10:00" in joined, found                   # the slow internet ran to Day 3 18:00
    assert "called" in joined, found                  # 58 of 59 contacts were texts
    assert len(found) == 3, found


def test_the_number_check_is_quiet_on_numbers_that_match():
    from populace.observe.narrate import facts_from, number_mismatches

    text, _ = _live_retelling()
    prose = ("By 07:00 on Day 1 the internet had gone off at home, affecting 43 residents. "
             "Of the 59 contact attempts, 35 were answered, and 24 came when Northline was closed.")
    assert number_mismatches(prose, facts_from(text), text) == []


def test_a_live_run_names_the_model_file_not_the_path_on_disk():
    from populace.observe.report import _label_run
    label = _label_run({"mock": False, "model": ["E:/weights/Qwen3-32B-Q4_K_M.gguf", r"C:\m\other.gguf"],
                        "profile": "compact"})[0]
    assert "Qwen3-32B-Q4_K_M.gguf, other.gguf" in label and "weights" not in label and "C:" not in label


RULES = FIXTURE.parents[2] / "docs" / "samples" / "isp-200-live-32b-rules-report.md"


def test_a_services_opening_hours_are_not_a_wrong_number():
    """The rule-based run's retelling said "Northline was open 08:00-20:00",
    which is right; the check flagged both times because the service's line
    under Injected gave no hours. The hours are elsewhere in the report."""
    from populace.observe.narrate import facts_from, number_mismatches

    text = RULES.read_text(encoding="utf-8")
    right = "Northline was open 08:00\u201320:00 but did not address these overnight calls."
    assert number_mismatches(right, facts_from(text), text) == []
    wrong = number_mismatches("Northline was open 07:00-21:00 but did not address these overnight calls.",
                              facts_from(text), text)
    assert any("07:00" in f for f in wrong) and any("21:00" in f for f in wrong), wrong


def test_a_registered_service_is_shown_with_its_hours(tmp_path):
    run = tmp_path / "town" / "runs" / "small"
    shutil.copytree(FIXTURE, run)
    path = run / "injections.jsonl"
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    for r in rows:
        if r.get("kind") == "service.register":
            r["params"]["hours"] = {"open": "08:00", "close": "20:00"}
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    text = render(run)
    line = next(l for l in text.splitlines() if ": service.register**" in l)
    assert "open 08:00-20:00" in line, line


def test_a_helpdesk_that_turned_claims_away_is_not_said_never_to_check():
    """The LLM helpdesk acted on 3 of its invented-problem contacts and turned
    others away by the line status; the finding said it never checked."""
    from populace.observe.findings import compute

    flags = {"contact_ungrounded": [
        {"who": ["r1"], "answered": True, "actions": ["dispatch"]},
        {"who": ["r2"], "answered": True, "actions": []},
        {"who": ["r3"], "answered": False, "actions": []},
    ]}
    book = type("B", (), {"name": staticmethod(lambda rid: rid.upper())})()
    run = type("R", (), {"events": [], "end": {"day": 4, "tick": 47, "residents": {}}, "contacts": [],
                         "injections": [], "decisions": [], "conversations": []})()
    ctx = {"run": run, "book": book, "flags": flags, "contacts": [], "injections": []}
    line = next(l for l in compute(ctx)["agent"] if "did not have" in l)
    assert "never checked" not in line and "The other 1 it answered got no action." in line
    flags["contact_ungrounded"][1]["actions"] = ["promise"]
    line = next(l for l in compute(ctx)["agent"] if "did not have" in l)
    assert "never checked" in line


def test_money_with_thousands_separators_is_not_split_into_counts():
    """The LLM run's retelling said "gained over $62,000, while"; the check
    read "000 while" as a count. The rule-based one: "$62,490, with"."""
    from populace.observe.narrate import _numbers

    assert _numbers("the residents collectively gained over $62,000, while relationships held") == []
    assert _numbers("Residents together gained $62,490, with the largest share") == []
    assert _numbers("1,200 residents and 3 homes") == [("1200", "residents"), ("3", "homes")]


def test_the_regenerated_retellings_raise_no_money_flags():
    from populace.observe.narrate import facts_from, number_mismatches

    for name in ("isp-200-live-32b-llm-report.md", "isp-200-live-32b-rules-report.md"):
        text = (FIXTURE.parents[2] / "docs" / "samples" / name).read_text(encoding="utf-8")
        prose = text.split("## The day, as a model tells it", 1)[1].split("\n## ", 1)[0]
        prose = "\n".join(l for l in prose.splitlines() if l and not l.startswith(">") and not l.startswith("*"))
        found = " | ".join(number_mismatches(prose, facts_from(text), text))
        assert "000 while" not in found and "490 with" not in found, found
