"""`populace report runs/<id>`: one run, in plain language, for the experimenter.

Deterministic markdown, no model: the same run directory always gives the same
bytes (`tests/test_report.py` holds a golden copy). Everything comes from the
run's own logs and snapshots, and every id is turned back into a name through
the run's `names.json` (`observe/names.py`), the one lookup.

Sections, in order: what kind of run it was; the numbers; what happened, with
the reasons people gave; who did what; what changed between the start and the
end; anything injected; how well the model did its job; the realism flags; and
an appendix with every conversation and every refusal.

Residents never read this. It is the experimenter's view and names everybody.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ..clock import tick_to_hhmm
from ..sim.events import Event, public_text
from . import digest
from . import flags as F
from . import voice
from .names import NameBook

ROUTINE = {"arrive", "depart", "sleep", "wake", "eat", "work_start", "work_end", "wage",
           "need_urgent", "talk_deferred", "buy", "woken", "text_received"}
TOP_EVENTS = 15
TICKS = 48
TOP_PEOPLE = 10
FLAG_EXAMPLES = 5


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load(run_dir: str | Path) -> dict[str, Any]:
    run_dir = Path(run_dir)
    if not (run_dir / "events.jsonl").exists():
        raise SystemExit(f"{run_dir} is not a run directory: no events.jsonl")
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    events = _read_jsonl(run_dir / "events.jsonl")
    start = digest.load(run_dir, "start")
    end = digest.latest(run_dir)
    book = NameBook.load(run_dir)
    if not book.names:
        # Runs from before names.json: events carry the names they were written with.
        book = NameBook({**{e["actor"]: e["actor_name"] for e in events if e.get("actor_name")},
                         **{e["target"]: e["target_name"] for e in events if e.get("target_name")}})
    run = F.Run(events, _read_jsonl(run_dir / "decisions.jsonl"),
                _read_jsonl(run_dir / "conversations.jsonl"), _read_jsonl(run_dir / "calls.jsonl"),
                _read_jsonl(run_dir / "ticks.jsonl"), start, end, manifest,
                _read_jsonl(run_dir / "contacts.jsonl"), _read_jsonl(run_dir / "injections.jsonl"))
    world_path = run_dir.parents[1] / "world.json" if len(run_dir.parents) > 1 else None
    refused_at_schedule = []
    if world_path is not None and world_path.exists():
        refused_at_schedule = json.loads(world_path.read_text(encoding="utf-8")).get("refused", [])
    return {"dir": run_dir, "run": run, "book": book, "manifest": manifest,
            "injections": _read_jsonl(run_dir / "injections.jsonl"),
            "contacts": _read_jsonl(run_dir / "contacts.jsonl"),
            "agents": json.loads((run_dir / "agents.json").read_text(encoding="utf-8"))
            if (run_dir / "agents.json").exists() else {},
            "agent_calls": _read_jsonl(run_dir / "agent_calls.jsonl"),
            "refused_injections": refused_at_schedule}


def when(day: Any, tick: Any) -> str:
    return f"Day {day} {tick_to_hhmm(int(tick))}" if tick is not None else f"Day {day}"


def _place(run: F.Run, pid: str) -> str:
    return run.place(pid).get("name", pid)


def describe(e: dict[str, Any], run: F.Run, book: NameBook) -> str:
    """What happened, as the experimenter needs it: the truth, not what a
    bystander saw. Falls back to the bystander's sentence."""
    who, them = book.name(e["actor"]), book.name(e.get("target")) or "somebody"
    amount = f"${float(e['amount']):.0f}" if e.get("amount") else ""
    kind, detail = e["kind"], e.get("detail") or ""
    special = {
        "refused": f"{who} tried to {(e.get('tags') or ['do something'])[0]} and could not: {detail}",
        "loan": f"{who} lent {them} {amount}. {detail}",
        "repay": f"{who} paid {them} back {amount}. {detail}",
        "hired": f"{who} took {them} on.",
        "fired": f"{who} let {them} go.",
        "quit": f"{who} quit.",
        "leave_town": f"{who} left town. {detail}",
        "text_sent": f"{who} texted {them}: \"{e.get('spoken') or detail}\"",
        "no_show": f"{who} did not turn up for their shift at {_place(run, e['location_id'])}.",
        "buy_fail": f"{who} could not afford {detail}.",
        "noticed": f"{who} noticed: {detail}",
        "service_promise_kept": f"{who}: {detail}",
        "service_promise_broken": f"{who}: {detail}",
        "contact": f"{who}: {detail}",
        "contact_failed": f"{who}: {detail}",
        "gift": f"{who} gave {them} {amount or detail} as a gift.",
        "given": f"{who} handed {them} {amount or 'some cash'}.",
        "rent_paid": f"{who} paid {them} {amount} rent.",
    }
    if kind in special:
        text = special[kind]
    else:
        event = Event.from_dict({**e, "actor_name": who, "target_name": book.name(e.get("target")) or None})
        text = public_text(event, _place(run, e["location_id"]))
    return book.restore(" ".join(text.split()))


def _decision_index(run: F.Run) -> dict[str, dict[str, Any]]:
    return {d["decision_id"]: d for d in run.decisions}


def _reason(e: dict[str, Any], decisions: dict[str, dict[str, Any]], book: NameBook) -> str:
    d = decisions.get(e.get("decision") or "")
    if not d or not d.get("reasoning"):
        return ""
    return book.restore(str(d["reasoning"]).strip())


def _label_run(m: dict[str, Any]) -> list[str]:
    out = []
    if m.get("mock"):
        out.append("> **Mock run.** Every call was answered by the mock provider, which is "
                   "deterministic and deliberately imperfect. The numbers below test the engine; "
                   "they say nothing about how a model behaves.")
    else:
        # The file name only: a server reports its full local path.
        models = [re.split(r"[\\/]", str(x))[-1] for x in (m.get('model') or [])]
        out.append(f"> **Live run** on {', '.join(models or ['an unnamed model'])}, "
                   f"{m.get('profile', 'frontier')} prompt profile.")
    if m.get("low_fidelity"):
        out.append(">\n> **LOW FIDELITY: preset quick.** About one resident thinks per tick; "
                   "most of the town ran on routine. Do not read this as a full run.")
    return out


def _glance(m: dict[str, Any]) -> list[str]:
    if not m:
        return ["No manifest: the run did not finish writing one."]
    calls = m.get("calls", {})
    d = m.get("decisions", {})
    rows = [
        ("Residents", m.get("residents")),
        ("From", f"{m.get('from')} for {m.get('ticks')} half-hour ticks"),
        ("Preset", f"{m.get('preset')} ({m.get('budget_per_tick')} calls a tick)"),
        ("Wall clock", f"{m.get('wall_s')} s ({m.get('minutes_per_day')} min per in-game day)"),
        ("Residents thinking per tick", f"{m.get('residents_thinking_per_tick', {}).get('mean')} on average"),
        ("Residents who thought at least once", m.get("distinct_residents_who_thought")),
        ("Calls", f"{calls.get('total')} ({', '.join(f'{k} {v}' for k, v in sorted(calls.get('by_role', {}).items()))})"),
        ("Ticks over budget", calls.get("over_budget_ticks")),
        ("Decisions valid first try", f"{d.get('json_valid_first_try_pct')}%"),
        ("Conversations / lines / texts", f"{m.get('conversations')} / {m.get('lines')} / {m.get('texts')}"),
        ("Events / refusals", f"{m.get('events')} / {m.get('refusals')}"),
    ]
    if m.get("stopped"):
        rows.append(("Stopped early", m["stopped"]))
    return ["| | |", "|---|---|"] + [f"| {k} | {v} |" for k, v in rows]


def _what_happened(ctx) -> list[str]:
    run, book = ctx["run"], ctx["book"]
    decisions = _decision_index(run)
    notable = [e for e in run.events if e["kind"] not in ROUTINE]
    # The same injected thing seen or noticed by many people is one line with
    # a count, at the first time and place it was seen, not one line each.
    # Twelve letters sent at once are one line; the same outage on two
    # different days is two.
    began: dict[str, int] = {}
    for e in notable:
        if str(e.get("source") or "").startswith("inject:"):
            t = e["day"] * TICKS + e["tick"]
            began[e["source"]] = min(began.get(e["source"], t), t)
    seen_together: dict[tuple, list[dict[str, Any]]] = {}
    rest = []
    for e in notable:
        if str(e.get("source") or "").startswith("inject:") and e["kind"] in ("changed", "noticed"):
            key = ((e.get("tags") or [e["kind"]])[0], e.get("detail"), began[e["source"]])
            seen_together.setdefault(key, []).append(e)
        else:
            rest.append(e)
    counts: dict[int, int] = {}
    for group in seen_together.values():
        first = min(group, key=lambda e: (e["day"], e["tick"], e.get("event_id", 0)))
        people = {w for e in group for w in ([e["actor"]] if e["kind"] == "noticed" else e.get("witnesses", []))}
        counts[id(first)] = len(people)
        rest.append(first)
    notable = rest
    # What was injected always makes the list; it is what the run is about.
    notable.sort(key=lambda e: (id(e) not in counts, -(e.get("importance") or 0),
                                e["day"], e["tick"], e.get("event_id", 0)))
    out = []
    if not notable:
        return ["Nothing out of the ordinary: the town ran on routine."]
    for e in sorted(notable[:TOP_EVENTS], key=lambda e: (e["day"], e["tick"], e.get("event_id", 0))):
        if id(e) in counts:
            n = counts[id(e)]
            text = book.restore(e.get("detail") or e["kind"])
            line = f"- **{when(e['day'], e['tick'])}**: {text} (seen by {n} resident{'s' if n != 1 else ''})"
            out.append(line)
            continue
        line = f"- **{when(e['day'], e['tick'])}**, {_place(run, e['location_id'])}: {describe(e, run, book)}"
        why = _reason(e, decisions, book)
        if why:
            line += f"  \n  *Why, in {book.name(e['actor'])}'s words:* {why}"
        out.append(line)
    # Conversations about what was injected come first: they are the story.
    from .. import words as W
    _, wordsets = injection_groups(ctx)
    injected_words = sorted({w for ws in wordsets.values() for w in ws})

    def about_it(c):
        return bool(injected_words) and any(W.contains(l.get("text", ""), injected_words) for l in c.get("lines", []))

    talks = sorted(run.conversations, key=lambda c: (not about_it(c), -len(c.get("deals") or []),
                                                     -int(c.get("importance") or 0), c["day"], c["tick"]))[:3]
    if talks:
        out += ["", "The conversations that mattered most:", ""]
        for c in sorted(talks, key=lambda c: (c["day"], c["tick"])):
            out += _conversation(c, run, book)
    return out


def _conversation(c: dict[str, Any], run: F.Run, book: NameBook) -> list[str]:
    who = " and ".join(book.name(p) for p in c.get("participants", []))
    head = f"**{when(c['day'], c['tick'])}**, {who} at {_place(run, c.get('location_id') or '')}"
    if c.get("channel") and c["channel"] != "face":
        head += f" ({c['channel']})"
    out = [head + ":", ""]
    for line in c.get("lines", []):
        out.append(f"> {book.name(line['speaker'])}: {book.restore(line.get('text', ''))}  ")
    for deal in c.get("deals") or []:
        state = "landed" if deal.get("ok") else f"did not land ({deal.get('reason')})"
        out.append(f"> *{deal.get('kind')} by {book.name(deal.get('speaker'))}: {state}*  ")
    return out + [""]


def _who(ctx) -> list[str]:
    run, book = ctx["run"], ctx["book"]
    start, end = run.start["residents"], run.end["residents"]
    thought = Counter(d["resident"] for d in run.decisions if d.get("source") != "fallback")
    talked = Counter(p for c in run.conversations for p in c.get("participants", []))
    refused = Counter(e["actor"] for e in run.events if e["kind"] == "refused")
    by_decision: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for d in run.decisions:
        by_decision[d["resident"]].append(d)
    everyone = sorted(set(start) | set(end) | set(thought), key=lambda r: (-(thought[r] + talked[r]), r))
    out = []
    for rid in everyone[:TOP_PEOPLE]:
        money = _money_delta(rid, start, end)
        out.append(f"**{book.name(rid)}** thought {_times(thought[rid])}, talked {_times(talked[rid])}"
                   + (f", was refused {_times(refused[rid])}" if refused[rid] else "")
                   + (f", money {money}" if money else "") + ".")
        reasons = []
        for d in by_decision.get(rid, []):
            r = book.restore(str(d.get("reasoning") or "").strip())
            if r and r not in reasons:
                reasons.append(r)
        for r in reasons[:3]:
            out.append(f"- {r}")
        out.append("")
    out += ["Everybody:", "", "| Resident | Thoughts | Conversations | Money | Refused |",
            "|---|---|---|---|---|"]
    for rid in sorted(everyone, key=lambda r: book.name(r)):
        out.append(f"| {book.label(rid)} | {thought[rid]} | {talked[rid]} | "
                   f"{_money_delta(rid, start, end) or '-'} | {refused[rid] or '-'} |")
    return out


def _times(n: int) -> str:
    return {0: "never", 1: "once", 2: "twice"}.get(n, f"{n} times")


def _money_delta(rid, start, end) -> str:
    if rid not in start or rid not in end:
        return ""
    delta = round(end[rid]["money"] - start[rid]["money"], 2)
    return f"{'+' if delta >= 0 else '-'}${abs(delta):.0f}" if abs(delta) >= 0.5 else ""


def _changed(ctx) -> list[str]:
    run, book = ctx["run"], ctx["book"]
    start, end = run.start["residents"], run.end["residents"]
    if not start or run.end is run.start:
        return ["No end-of-day snapshot: the run did not finish a day, so nothing can be compared."]
    out = []
    jobs = []
    for rid in sorted(start):
        a, b = (start[rid].get("job") or {}), ((end.get(rid) or {}).get("job") or {})
        if a.get("workplace") != b.get("workplace"):
            before = _place(run, a["workplace"]) if a else "no job"
            after = _place(run, b["workplace"]) if b else "no job"
            jobs.append(f"- {book.name(rid)}: {before} to {after}")
    out += ["**Work.**", ""] + (jobs or ["- Nobody's work changed."]) + [""]
    deltas = sorted(((round(end[r]["money"] - start[r]["money"], 2), r) for r in start if r in end))
    total = round(sum(d for d, _ in deltas), 2)
    out += ["**Money.**", "", f"- The town's residents together: {'+' if total >= 0 else '-'}${abs(total):.0f}."]
    for d, r in deltas[:3]:
        if d < 0:
            out.append(f"- Down most: {book.name(r)}, -${abs(d):.0f}.")
    for d, r in reversed(deltas[-3:]):
        if d > 0:
            out.append(f"- Up most: {book.name(r)}, +${d:.0f}.")
    out.append("")
    ties = []
    new_ties = names = 0
    for rid in sorted(start):
        if rid not in end:
            continue
        a, b = start[rid].get("ties", {}), end[rid].get("ties", {})
        new_ties += len(set(b) - set(a))
        names += len(set(end[rid].get("names_known", {})) - set(start[rid].get("names_known", {})))
        for other in sorted(set(a) & set(b)):
            if a[other]["stage"] != b[other]["stage"] or abs(b[other]["sentiment"] - a[other]["sentiment"]) >= 3:
                ties.append(f"- {book.name(rid)} on {book.name(other)}: stage {a[other]['stage']} to "
                            f"{b[other]['stage']}, feeling {a[other]['sentiment']:+d} to {b[other]['sentiment']:+d}")
    out += ["**People.**", "", f"- {new_ties} new acquaintances made, {names} names learned."]
    out += ties[:12] + ([f"- ...and {len(ties) - 12} more."] if len(ties) > 12 else []) + [""]
    beliefs = []
    for rid in sorted(start):
        if rid in end:
            fresh = [b for b in end[rid].get("beliefs", []) if b not in start[rid].get("beliefs", [])]
            beliefs += [f"- {book.name(rid)}: {book.restore(b)}" for b in fresh[:1]]
    out += ["**What people came to believe** (one each, first eight):", ""] + (beliefs[:8] or ["- Nothing new."]) + [""]
    lives = []
    for rid in sorted(start):
        a, b = start[rid].get("arc", {}), (end.get(rid) or {}).get("arc", {})
        if a.get("stage") != b.get("stage") and b.get("stage"):
            lives.append(f"- {book.name(rid)}: {b.get('stage').replace('_', ' ')}. {book.restore(b.get('goal') or '')}")
        if (end.get(rid) or {}).get("gone") and not start[rid].get("gone"):
            lives.append(f"- {book.name(rid)} left town.")
    out += ["**Lives.**", ""] + (lives or ["- Nobody changed course."])
    return out


COMMON = set("""home went came back sign door open opened closed today tomorrow night morning
evening afternoon week weekend monday tuesday wednesday thursday friday saturday sunday o'clock
eight seven nine
ten eleven twelve about there their people place very thank thanks being customer month""".split())


def _inj_words(params: dict) -> list[str]:
    """The distinctive words of what was injected - its own text, not the
    place it happened at - for spotting it in talk."""
    from ..sim.memory import STOPWORDS
    texts = [str(params.get(k) or "") for k in ("text", "reason", "service", "name", "purpose", "kind")]
    seen: list[str] = []
    for text in texts:
        for w in re.findall(r"[a-z][a-z']{3,}", text.lower()):
            if w not in STOPWORDS and w not in COMMON and w not in seen:
                seen.append(w)
    return seen[:8]


def injection_groups(ctx) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[str]]]:
    """The run's applied injections, the same thing sent to several people at
    once (twelve wrong bills) as one group; and each group's own words."""
    applied = [r for r in ctx.get("injections", []) if not r.get("refused") and not r["kind"].startswith("_")]
    groups: dict[str, list[dict[str, Any]]] = {}
    for rec in applied:
        same = {k: v for k, v in (rec.get("params") or {}).items() if k != "to"}
        key = json.dumps([rec["kind"], rec["day"], rec["tick"], same], sort_keys=True, default=str)
        groups.setdefault(key, []).append(rec)
    # A new place's name tends to borrow its owner's ("Northline Internet shop"),
    # which would credit outage talk to the shop; a place keeps only the words
    # nothing else injected uses.
    wordsets = {key: _inj_words(g[0].get("params") or {}) for key, g in groups.items()}
    for key, g in groups.items():
        if g[0]["kind"] == "place.new":
            others = {w for k, ws in wordsets.items() if k != key for w in ws}
            others |= {w for r in ctx.get("injections", []) if r.get("kind") == "service.register"
                       for w in _inj_words(r.get("params") or {})}
            wordsets[key] = [w for w in wordsets[key] if w not in others]
    return groups, wordsets


def _injected(ctx) -> list[str]:
    """Each injection and its ripples: who saw it, who noticed it later, who
    it touched directly, and the conversations it may have travelled through."""
    from .. import words as W

    run, book = ctx["run"], ctx["book"]
    applied = [r for r in ctx.get("injections", []) if not r.get("refused") and not r["kind"].startswith("_")]
    ended = {r["id"][:-len("-end")]: r for r in ctx.get("injections", [])
             if r["kind"] == "_restore" and not r.get("refused")}
    failed = [r for r in ctx.get("injections", []) if r.get("refused")]
    refused = ctx.get("refused_injections", [])
    contacts = ctx.get("contacts", [])
    if not applied and not failed and not refused and not contacts:
        return ["Nothing was injected into this run."]
    out = ["\"Passed on in conversation\" counts only lines from somebody who knew to somebody "
           "who had not seen it themselves: word of mouth to new people. People talking it over "
           "with others who already knew is not counted here.", ""]
    groups, wordsets = injection_groups(ctx)
    for key, group in groups.items():
        rec = dict(group[0])
        rec["affected"] = sorted({r for g in group for r in g.get("affected", [])})
        srcs = {f"inject:{g['id']}" for g in group}
        # Its own events: an outage's coming back on shares the source, not the kind.
        mine = [e for e in run.events if e.get("source") in srcs and (e.get("tags") or [rec["kind"]])[0] == rec["kind"]]
        saw = sorted({w for e in mine if e["kind"] == "changed" for w in e.get("witnesses", [])})
        noticed = {}
        for e in mine:
            if e["kind"] == "noticed":
                noticed.setdefault(e["actor"], (e["day"], e["tick"]))
        knew_at = {rid: (rec["day"], rec["tick"]) for rid in saw}
        for rid, first_seen in noticed.items():
            knew_at.setdefault(rid, first_seen)
        for rid in rec.get("affected", []):
            if rid in book.names:
                knew_at.setdefault(rid, (rec["day"], rec["tick"]))
        words = wordsets[key]
        spread = []
        for c in run.conversations:
            at = (c["day"], c["tick"])
            people = c.get("participants", [])
            knowers = [p for p in people if p in knew_at and knew_at[p] <= at]
            others = [p for p in people if p not in knowers]
            if not knowers or not others or not words:
                continue
            said = [l for l in c.get("lines", []) if l["speaker"] in knowers
                    and W.contains(l.get("text", ""), words)]
            if said:
                spread.append((c, knowers, others, said[0]))
        if rec["kind"] == "service.register":
            p = rec.get("params") or {}
            known = p.get("known_by", "everyone")
            out += [f"**{when(rec['day'], rec['tick'])}: service.register** ({rec['id']}). "
                    f"{p.get('name')} [{p.get('id')}], {p.get('purpose')}; by "
                    f"{' or '.join(p.get('channels') or ['text'])}"
                    + (f"; open {p['hours']['open']}-{p['hours']['close']}" if (p.get("hours") or {}).get("open") else "")
                    + ".", "",
                    f"- Known to: {'everybody' if known == 'everyone' else known}.", ""]
            continue
        what = mine[0]["detail"] if mine and mine[0].get("detail") else rec["kind"]
        label_ = rec["id"] if len(group) == 1 else f"{len(group)} of them, to {len(rec['affected'])} residents"
        out += [f"**{when(rec['day'], rec['tick'])}: {rec['kind']}** ({label_}). {book.restore(what)}", ""]
        out.append(f"- Saw it happen: {', '.join(book.name(r) for r in saw) or 'nobody'}.")
        if rec["id"] in ended:
            out.append(f"- Ended: {when(ended[rec['id']]['day'], ended[rec['id']]['tick'])}.")
        if noticed:
            first = sorted(noticed.items(), key=lambda kv: kv[1])
            out.append(f"- Noticed it later: {len(noticed)}, first "
                       + ", ".join(f"{book.name(r)} ({when(*t)})" for r, t in first[:5])
                       + (" and more" if len(first) > 5 else "") + ".")
        else:
            out.append("- Noticed it later: nobody.")
        touched = [r for r in rec.get("affected", []) if r in book.names]
        if touched:
            out.append(f"- Touched directly: {len(touched)} ({', '.join(book.name(r) for r in touched[:6])}"
                       + (" and more" if len(touched) > 6 else "") + ").")
        out.append(f"- Knew of it by the end: {len(knew_at)}.")
        heard = sorted({o for _, _, others, _ in spread for o in others})
        if spread:
            out.append(f"- Possibly heard of it in conversation, not having seen it: {len(heard)}.")
            out.append(f"- Possibly passed on in conversation ({len(spread)}; a keyword proxy on "
                       f"{', '.join(words[:4])}):")
            for c, knowers, others, line in spread[:3]:
                out.append(f"  - {when(c['day'], c['tick'])}: {book.name(line['speaker'])} to "
                           f"{', '.join(book.name(o) for o in others)}: \"{book.restore(line['text'])}\"")
        else:
            out.append("- Passed on in conversation: no sign of it.")
        out.append("")
    out += _contacts_summary(ctx)
    if failed or refused:
        out += ["**Refused**, with the reason:", ""]
        for r in failed:
            out.append(f"- {r['kind']} ({r['id']}), when it fell due: {r['refused']}")
        for r in refused:
            kind = r["raw"].get("kind") if isinstance(r.get("raw"), dict) else r.get("raw")
            out.append(f"- {kind}, when it was scheduled: {r['reason']}")
    return out


def _contacts_summary(ctx) -> list[str]:
    """Who reached out to which service, how, and what came of it."""
    run, book = ctx["run"], ctx["book"]
    contacts = ctx.get("contacts", [])
    if not contacts:
        return []
    out = []
    by_service: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for c in contacts:
        by_service[c["service"]].append(c)
    kept = Counter(e["kind"] for e in run.events if e["kind"] in ("service_promise_kept", "service_promise_broken"))
    for sid, cs in sorted(by_service.items()):
        ok = [c for c in cs if not c.get("failed")]
        failed = [c for c in cs if c.get("failed")]
        people = sorted({c["resident"] for c in cs})
        acts = Counter(a["do"] for c in ok for a in c.get("actions", []))
        channels = Counter(c["channel"] for c in cs)
        first = min(cs, key=lambda c: (c["day"], c["tick"]))
        out += [f"**Contacts with `{sid}`**: {len(cs)} from {len(people)} residents "
                f"({', '.join(f'{n} by {ch}' for ch, n in sorted(channels.items()))}), the first at "
                f"{when(first['day'], first['tick'])}.", ""]
        out.append(f"- Answered: {len(ok)}. Got nowhere: {len(failed)}"
                   + (f" ({'; '.join(sorted({c['failed'] for c in failed}))})" if failed else "") + ".")
        if acts:
            out.append("- What the agent did: " + ", ".join(f"{k} {v}" for k, v in sorted(acts.items())) + ".")
        who = ctx.get("agents", {}).get(sid)
        if who:
            out.append(f"- Answered by: {_agent_label(who)}.")
        mine = [a for a in ctx.get("agent_calls", []) if a.get("service") == sid]
        calls = [c for a in mine for c in a.get("calls", [])]
        if calls:
            lat = sorted(c.get("latency_s", 0) for c in calls)
            refused = [r for a in mine for r in a.get("refused", [])]
            out.append(f"- The agent's own model: {len(calls)} calls for {len(mine)} replies "
                       f"({sum(1 for c in calls if c.get('attempt', 1) > 1)} retries), median "
                       f"{lat[len(lat) // 2]:.1f} s; {sum(1 for a in mine if a.get('failed'))} gave no usable "
                       f"answer; {len(refused)} action{'s' if len(refused) != 1 else ''} it asked for "
                       "that the desk cannot do"
                       + (f" ({'; '.join(sorted({r['why'] for r in refused})[:3])})" if refused else "") + ".")
        repeat = [r for r, n in Counter(c["resident"] for c in cs).items() if n > 1]
        out.append(f"- Came back more than once: {len(repeat)}.")
        if kept:
            out.append(f"- Promises kept / broken: {kept['service_promise_kept']} / {kept['service_promise_broken']}.")
        out.append("")
    return out


def _agent_label(who: dict[str, Any]) -> str:
    name = str(who.get("agent", "")).rsplit(".", 1)[-1]
    detail = ", ".join(f"{k} {v}" for k, v in who.items() if k not in ("agent",) and v)
    return f"`{name}`" + (f" ({detail})" if detail else "")


def _findings(ctx) -> list[str]:
    from .findings import section
    return section(ctx)


def _service_section(ctx) -> list[str]:
    from .service_metrics import section
    return section(ctx)


def _quality(ctx) -> list[str]:
    run, book, m = ctx["run"], ctx["book"], ctx["manifest"]
    d = m.get("decisions", {})
    calls = m.get("calls", {})
    out = []
    if m.get("mock"):
        out += ["*Mock run: these numbers describe the mock provider, which errs on purpose.*", ""]
    rows = [
        ("Decisions valid first try", f"{d.get('json_valid_first_try_pct')}%"),
        ("Retries / fell back to routine", f"{d.get('retries')} / {d.get('fallbacks')}"),
        ("Call latency, median / p90", f"{calls.get('latency_s', {}).get('median')} s / {calls.get('latency_s', {}).get('p90')} s"),
        ("Server errors", calls.get("errors")),
        ("Share of input read from the prompt cache", calls.get("cache_read_share")),
    ]
    if run.conversations:
        v = voice.score_conversations(run.conversations, book.names)
        rows += [
            ("Replies that echo the line before", f"{v['echoed_pct_of_replies']}%"),
            ("Lines with the speaker's own name", f"{v['said_their_own_name_pct_of_lines']}%"),
            ("Questions left unanswered", f"{v['questions_left_on_the_floor']} of {v['questions_asked']}"),
            ("Lines repeating what the speaker already said today", f"{v['repeated_themselves_pct_of_lines']}%"),
            ("Deals asserted / landed", f"{v['deals_asserted']} / {v['deals_landed']}"),
            ("Things said about somebody that they never said",
             f"{v['misattributed']} of the {v['attributions']} such claims"),
        ]
    flags = ctx["flags"]
    rows += [
        ("Names used without having been given", len(flags.get("name_unknown", []))),
        ("Ids said out loud", len(flags.get("id_spoken", []))),
    ]
    return out + ["| | |", "|---|---|"] + [f"| {k} | {v} |" for k, v in rows]


def _flags(ctx) -> list[str]:
    book, flags = ctx["book"], ctx["flags"]
    out = ["| Flag | Count | What it means |", "|---|---|---|"]
    for name, found in flags.items():
        out.append(f"| `{name}` | {len(found)} | {F.DESCRIPTIONS[name]} |")
    for name, found in flags.items():
        if not found:
            continue
        out += ["", f"**`{name}`**, first {min(len(found), FLAG_EXAMPLES)} of {len(found)}:", ""]
        for f in found[:FLAG_EXAMPLES]:
            out.append(f"- {when(f['day'], f['tick'])}: {book.restore(f['what'])}")
    return out


def _appendix(ctx) -> list[str]:
    run, book = ctx["run"], ctx["book"]
    out = ["### Every conversation", ""]
    if not run.conversations:
        out.append("None.")
    for c in sorted(run.conversations, key=lambda c: (c["day"], c["tick"], c.get("conv_id", ""))):
        out += _conversation(c, run, book)
    if ctx.get("contacts"):
        out += ["### Every contact with a service", ""]
        for c in ctx["contacts"]:
            head = f"**{when(c['day'], c['tick'])}**, {book.name(c['resident'])} to `{c['service']}` by {c['channel']}"
            if c.get("failed"):
                out += [head + f": got nowhere - {c['failed']}.", ""]
                continue
            out += [head + ":", ""]
            for line in c.get("lines", []):
                who = book.name(c["resident"]) if line["from"] == "customer" else c["service"]
                out.append(f"> {who}: {book.restore(line['text'])}  ")
            for a in c.get("actions", []):
                out.append(f"> *{a['do']}: {', '.join(f'{k} {v}' for k, v in a.items() if k != 'do' and v != '')}*  ")
            out.append("")
    reasons = Counter(book.restore(e.get("detail") or "") for e in run.events if e["kind"] == "refused")
    out += ["### Every refusal, by reason", ""]
    out += [f"- {n} x {r}" for r, n in sorted(reasons.items(), key=lambda kv: (-kv[1], kv[0]))] or ["None."]
    return out


def render(run_dir: str | Path) -> str:
    ctx = load(run_dir)
    ctx["flags"] = F.run_all(ctx["run"])
    m = ctx["manifest"]
    title = f"# {m.get('town') or ctx['run'].start.get('town') or 'A town'}: run `{Path(run_dir).name}`"
    parts = [
        [title, ""] + _label_run(m),
        ["## At a glance", ""] + _glance(m),
        _findings(ctx),
        ["## What happened", "", "The most important things that happened, in order, with the reason "
         "the person gave when it was their own decision.", ""] + _what_happened(ctx),
        ["## Who did what", ""] + _who(ctx),
        ["## What changed", "", "From the start of the run to the last night it finished.", ""] + _changed(ctx),
        ["## Injected", ""] + _injected(ctx),
        _service_section(ctx),
        ["## How well the model did its job", ""] + _quality(ctx),
        ["## Realism flags", "", "Mechanical checks over the logs. A flag is a reason to look, not a verdict.", ""]
        + _flags(ctx),
        ["## Appendix", ""] + _appendix(ctx),
    ]
    return "\n".join("\n".join(p).rstrip() + "\n" for p in parts if p)


def write(run_dir: str | Path, out: str | Path | None = None) -> Path:
    path = Path(out) if out else Path(run_dir) / "report.md"
    path.write_text(render(run_dir), encoding="utf-8")
    return path
