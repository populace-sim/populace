"""Mechanical realism flags: things in a run's logs that should not happen.

Each flag is computed from the run directory alone (events, decisions,
conversations, calls, ticks and the snapshots), with no model and no town
loaded, so a report on somebody else's run needs nothing but the folder. Each
returns a list of findings, each a dict with at least `day`, `tick`, `who`
(resident ids, possibly empty) and `what` (a sentence with ids in it; the
report turns ids into names).

A flag is a prompt to look, not a verdict. `tests/test_report.py` breaks a run
on purpose and watches each one fire, because a check that never fires is not
a passing check.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any, Callable

from .voice import is_echo

# Which way each money event moves cash: (actor's sign, target's sign).
MONEY_FLOW = {
    "wage": (+1, 0), "buy": (-1, 0), "rent_paid": (-1, +1), "loan": (-1, +1),
    "repay": (-1, +1), "gift": (-1, +1), "given": (-1, +1),
    # A service crediting a customer: money from outside the town, on the record.
    "credit": (+1, 0),
}
AWAKE_KINDS = {"arrive", "depart", "conversation", "buy", "eat", "work_start", "wage", "given",
               "gift", "loan", "repay", "other", "text_sent"}
ID = re.compile(r"\br\d{3,}\b")
STUCK_RUN = 4          # the same chosen action and target, decision after decision
NO_REACTION_TICKS = 4  # how long a witness of something big may go without a thought
BIG = 7                # importance that counts as big
TICKS_PER_DAY = 48

FLAGS: dict[str, Callable[["Run"], list[dict[str, Any]]]] = {}
DESCRIPTIONS: dict[str, str] = {}


def flag(name: str, description: str):
    def register(fn):
        FLAGS[name] = fn
        DESCRIPTIONS[name] = description
        return fn
    return register


class Run:
    """Everything a flag may read, loaded once."""

    def __init__(self, events, decisions, conversations, calls, ticks, start, end, manifest=None,
                 contacts=None, injections=None):
        self.contacts = contacts or []
        self.injections = injections or []
        self.events = events
        self.decisions = decisions
        self.conversations = conversations
        self.calls = calls
        self.ticks = ticks
        self.start = start or {"residents": {}, "places": {}}
        self.end = end or self.start
        self.manifest = manifest or {}

    def place(self, pid: str) -> dict[str, Any]:
        return self.start["places"].get(pid) or self.end["places"].get(pid) or {}


def _f(day, tick, who, what, **extra) -> dict[str, Any]:
    return {"day": day, "tick": tick, "who": list(who), "what": what, **extra}


def _norm(line: str) -> str:
    return " ".join(re.findall(r"[a-z0-9']+", (line or "").lower()))


@flag("repeated_line", "somebody said the same line, word for word, more than once")
def repeated_line(run: Run) -> list[dict[str, Any]]:
    seen: dict[tuple[str, str], list[tuple[int, int]]] = defaultdict(list)
    for c in run.conversations:
        for line in c.get("lines", []):
            text = _norm(line.get("text", ""))
            if len(text.split()) >= 4:
                seen[(line["speaker"], text)].append((c["day"], c["tick"]))
    out = []
    for (who, text), when in sorted(seen.items(), key=lambda kv: kv[1][0]):
        if len(when) > 1:
            out.append(_f(when[1][0], when[1][1], [who],
                          f"{who} said \"{text}\" {len(when)} times", times=len(when)))
    return out


@flag("echo", "a reply that repeats most of the line it answers")
def echo(run: Run) -> list[dict[str, Any]]:
    out = []
    for c in run.conversations:
        lines = c.get("lines", [])
        for prev, cur in zip(lines, lines[1:]):
            if cur["speaker"] != prev["speaker"] and is_echo(cur.get("text", ""), prev.get("text", ""), set()):
                out.append(_f(c["day"], c["tick"], [cur["speaker"]],
                              f"{cur['speaker']} echoed {prev['speaker']}: \"{cur.get('text', '')}\""))
    return out


@flag("stuck", f"the same decision {STUCK_RUN} times running")
def stuck(run: Run) -> list[dict[str, Any]]:
    by_resident: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for d in run.decisions:
        if d.get("source") != "fallback":
            by_resident[d["resident"]].append(d)
    out = []
    for rid, ds in sorted(by_resident.items()):
        streak = 1
        for prev, cur in zip(ds, ds[1:]):
            same = (prev["action"], prev.get("target")) == (cur["action"], cur.get("target"))
            streak = streak + 1 if same else 1
            if streak == STUCK_RUN:
                out.append(_f(cur["day"], cur["tick"], [rid],
                              f"{rid} chose {cur['action']} {cur.get('target') or ''}".rstrip()
                              + f" {STUCK_RUN} times running"))
    return out


@flag("impossible_move", "somebody arrived in a home that is neither theirs nor anybody's they know")
def impossible_move(run: Run) -> list[dict[str, Any]]:
    out = []
    for e in run.events:
        if e["kind"] != "arrive":
            continue
        place = run.place(e["location_id"])
        if not place:
            out.append(_f(e["day"], e["tick"], [e["actor"]], f"{e['actor']} arrived at an unknown place {e['location_id']}"))
            continue
        if place.get("public", True) or place.get("kind") == "offtown":
            continue
        who = run.start["residents"].get(e["actor"]) or {}
        if who.get("home") == e["location_id"]:
            continue
        ties = set((run.end["residents"].get(e["actor"]) or who).get("ties", {}))
        if not ties & set(place.get("residents", [])):
            out.append(_f(e["day"], e["tick"], [e["actor"]],
                          f"{e['actor']} walked into {place.get('name', e['location_id'])}, a home of strangers"))
    return out


@flag("sleepless", "active through a stretch of 24 hours with no sleep in it")
def sleepless(run: Run) -> list[dict[str, Any]]:
    """Going to sleep and waking up are both markers of a night; a stretch of a
    whole day between two markers (or the run's ends) with the person up and
    about in it is a day without sleep."""
    ticks = [t["day"] * TICKS_PER_DAY + t["tick"] for t in run.ticks if "tick" in t and t.get("kind") != "night"]
    if not ticks:
        return []
    first, last = min(ticks), max(ticks)
    markers: dict[str, list[int]] = defaultdict(list)
    active: dict[str, list[int]] = defaultdict(list)
    for e in run.events:
        at = e["day"] * TICKS_PER_DAY + e["tick"]
        if e["kind"] in ("sleep", "wake"):
            markers[e["actor"]].append(at)
        elif e["kind"] in AWAKE_KINDS:
            active[e["actor"]].append(at)
    out = []
    for rid in sorted(active):
        edges = [first - 1] + sorted(markers[rid]) + [last + 1]
        for a, b in zip(edges, edges[1:]):
            if b - a > TICKS_PER_DAY and any(a < t < b for t in active[rid]):
                out.append(_f(a // TICKS_PER_DAY, max(a, first) % TICKS_PER_DAY, [rid],
                              f"{rid} was up and about for {(b - a) // 2} hours without sleeping"))
                break
    return out


@flag("no_reaction", f"saw something of importance {BIG}+ and had no thought for {NO_REACTION_TICKS} ticks")
def no_reaction(run: Run) -> list[dict[str, Any]]:
    thought = defaultdict(list)
    for d in run.decisions:
        thought[d["resident"]].append(d["day"] * TICKS_PER_DAY + d["tick"])
    last = max((t["day"] * TICKS_PER_DAY + t["tick"] for t in run.ticks if "tick" in t), default=0)
    out = []
    for e in run.events:
        if (e.get("importance") or 0) < BIG or e["kind"] in ("need_urgent",):
            continue
        at = e["day"] * TICKS_PER_DAY + e["tick"]
        if at + NO_REACTION_TICKS > last:
            continue
        for rid in sorted(set(e.get("witnesses", [])) | {e.get("target")} - {None, e["actor"]}):
            if not any(at <= t <= at + NO_REACTION_TICKS for t in thought.get(rid, [])):
                out.append(_f(e["day"], e["tick"], [rid, e["actor"]],
                              f"{rid} saw {e['actor']}'s {e['kind'].replace('_', ' ')} and did not react"))
    return out


@flag("ghost_contact", "a text between two people with no tie at all")
def ghost_contact(run: Run) -> list[dict[str, Any]]:
    out = []
    for e in run.events:
        if e["kind"] != "text_sent" or not e.get("target"):
            continue
        ties = set((run.end["residents"].get(e["actor"]) or {}).get("ties", {}))
        if e["target"] not in ties:
            out.append(_f(e["day"], e["tick"], [e["actor"], e["target"]],
                          f"{e['actor']} texted {e['target']}, whom they have no tie to"))
    return out


@flag("money_from_nowhere", "somebody's money changed by more than the run's money events explain")
def money_from_nowhere(run: Run) -> list[dict[str, Any]]:
    if not run.start["residents"] or run.end is run.start:
        return []
    expected: dict[str, float] = defaultdict(float)
    cutoff = (run.end.get("day", 0), run.end.get("tick", 0))
    for e in run.events:
        if (e["day"], e["tick"]) > cutoff:
            continue  # after the snapshot being compared against
        flow = MONEY_FLOW.get(e["kind"])
        if not flow or not e.get("amount"):
            continue
        amount = float(e["amount"])
        expected[e["actor"]] += flow[0] * amount
        if flow[1] and e.get("target"):
            expected[e["target"]] += flow[1] * amount
        if e["kind"] == "buy":
            owner = run.place(e["location_id"]).get("owner")
            if owner:
                expected[owner] += amount
    out = []
    for rid, before in sorted(run.start["residents"].items()):
        after = run.end["residents"].get(rid)
        if after is None:
            continue
        drift = round(after["money"] - before["money"] - expected[rid], 2)
        if abs(drift) > 0.05:
            out.append(_f(run.end.get("day", 0), run.end.get("tick", 0), [rid],
                          f"{rid}'s money moved ${drift:+.2f} more than their money events say",
                          drift=drift))
    return out


@flag("promise_ignored", "a broken promise the person let down never did anything about")
def promise_ignored(run: Run) -> list[dict[str, Any]]:
    out = []
    for e in run.events:
        if e["kind"] != "promise_broken" or not e.get("target"):
            continue
        at = e["day"] * TICKS_PER_DAY + e["tick"]
        wronged, promiser = e["target"], e["actor"]
        reacted = any(d["resident"] == wronged and d["day"] * TICKS_PER_DAY + d["tick"] >= at
                      and (d.get("target") == promiser or promiser in str(d.get("about") or ""))
                      for d in run.decisions)
        if not reacted:
            out.append(_f(e["day"], e["tick"], [wronged, promiser],
                          f"{wronged} was let down by {promiser} and never took it up with them"))
    return out


@flag("provider_down_window", "a stretch of ticks where the model did not answer")
def provider_down_window(run: Run) -> list[dict[str, Any]]:
    out = []
    by_tick = defaultdict(lambda: [0, 0])
    for c in run.calls:
        key = (c.get("day"), c.get("tick"))
        by_tick[key][0] += 1
        by_tick[key][1] += 1 if c.get("error") else 0
    window: list[tuple[int, int]] = []
    for key in sorted(k for k in by_tick if k[0] is not None):
        total, failed = by_tick[key]
        if total and failed == total:
            window.append(key)
            continue
        if len(window) >= 2:
            out.append(_f(window[0][0], window[0][1], [], f"every call failed for {len(window)} ticks running",
                          ticks=len(window)))
        window = []
    if len(window) >= 2:
        out.append(_f(window[0][0], window[0][1], [], f"every call failed for {len(window)} ticks running",
                      ticks=len(window)))
    for t in run.ticks:
        if t.get("stopped"):
            out.append(_f(t.get("day"), t.get("tick"), [], f"the run stopped: {t['stopped']}"))
    return out


@flag("id_spoken", "somebody said a resident id out loud")
def id_spoken(run: Run) -> list[dict[str, Any]]:
    out = []
    for c in run.conversations:
        for line in c.get("lines", []):
            if ID.search(line.get("text", "")):
                out.append(_f(c["day"], c["tick"], [line["speaker"]],
                              f"{line['speaker']} said an id aloud: \"{line.get('text', '')}\""))
    return out


@flag("name_unknown", "somebody used the name of a person whose name they had not been given")
def name_unknown(run: Run) -> list[dict[str, Any]]:
    """A full name, or a first name only one person in town has, said by
    somebody who knows no one of that name as of that day."""
    people = {rid: r["name"] for rid, r in run.end["residents"].items()}
    by_first: dict[str, list[str]] = defaultdict(list)
    for rid, name in people.items():
        by_first[name.split()[0]].append(rid)
    out = []
    for c in run.conversations:
        for line in c.get("lines", []):
            speaker = line["speaker"]
            known = {rid for rid, day in ((run.end["residents"].get(speaker) or {})
                                          .get("names_known", {})).items() if day <= c["day"]}
            known.add(speaker)
            text = line.get("text", "")
            for first, rids in by_first.items():
                if len(first) < 3 or not re.search(rf"\b{re.escape(first)}\b", text):
                    continue
                if set(rids) & known:
                    continue
                full = [r for r in rids if re.search(rf"\b{re.escape(people[r])}\b", text)]
                if full or len(rids) == 1:
                    rid = (full or rids)[0]
                    out.append(_f(c["day"], c["tick"], [speaker, rid],
                                  f"{speaker} called {rid} by name without having been given it: \"{text}\""))
    return out


# What makes a line a claim that money is owed between two people. Talking about
# prices is not; talking about a debt is.
CLAIM_WORDS = ("owe", "owes", "owed", "owing", "debt", "pay me back", "pay you back",
               "paid me back", "paid you back", "pay it back", "pay him back", "pay her back",
               "lent", "loaned", "borrowed", "lend me")
# The events that put money between two people.
MONEY_BETWEEN = {"loan", "repay", "gift", "given", "rent_paid", "rent_missed"}


def _money_ties(run: Run) -> set[frozenset]:
    """Pairs with a standing reason to talk about money: a recorded debt either
    way at the start or the end, a landlord, or an employer."""
    pairs: set[frozenset] = set()
    for snap in (run.start, run.end):
        for rid, r in snap.get("residents", {}).items():
            for o in r.get("owes") or []:
                if o.get("to"):
                    pairs.add(frozenset((rid, o["to"])))
            if (r.get("rent") or {}).get("landlord"):
                pairs.add(frozenset((rid, r["rent"]["landlord"])))
            if (r.get("job") or {}).get("employer"):
                pairs.add(frozenset((rid, r["job"]["employer"])))
    return pairs


@flag("claim_unfounded", "somebody spoke of money owed between them and a person with no debt, loan, rent or wage between them")
def claim_unfounded(run: Run) -> list[dict[str, Any]]:
    from .. import words as W

    ties = _money_ties(run)
    moved: dict[frozenset, list[tuple[int, int]]] = defaultdict(list)
    for e in run.events:
        if e["kind"] in MONEY_BETWEEN and e.get("target"):
            moved[frozenset((e["actor"], e["target"]))].append((e["day"], e["tick"]))
    out = []
    for c in run.conversations:
        people = c.get("participants") or sorted({l["speaker"] for l in c.get("lines", [])})
        for line in c.get("lines", []):
            text = line.get("text", "")
            if not W.contains(text, CLAIM_WORDS):
                continue
            speaker = line["speaker"]
            for other in people:
                if other == speaker:
                    continue
                pair = frozenset((speaker, other))
                if pair in ties or any(t <= (c["day"], c["tick"]) for t in moved.get(pair, [])):
                    continue
                out.append(_f(c["day"], c["tick"], [speaker, other],
                              f"{speaker} spoke of money owed with {other}, and nothing stands "
                              f"between them: \"{text}\""))
    return out


GROUNDING_GRACE = 12   # half-hour ticks a just-fixed problem still counts as a reason to call


def service_handles(run: Run) -> dict[str, set[str]]:
    return {r["params"]["id"]: set(r["params"].get("handles") or [])
            for r in run.injections if r.get("kind") == "service.register" and not r.get("refused")}


def grounded(run: Run, contact: dict[str, Any]) -> bool:
    """Did the resident, or anybody they live with, have an open problem of a
    kind this service handles when they got in touch?"""
    handles = service_handles(run).get(contact["service"], set())
    residents = run.end.get("residents", {})
    me = residents.get(contact["resident"]) or {}
    home, household = me.get("home"), me.get("household")
    # The household: same home and, where recorded, the same household (a block
    # of flats is many households).
    house = [r for rid, r in residents.items() if rid == contact["resident"]
             or (home and r.get("home") == home and (not household or r.get("household") == household))]
    at = contact["day"] * TICKS_PER_DAY + contact["tick"] - TICKS_PER_DAY  # totals count from Day 1
    for r in house:
        for p in r.get("problems") or []:
            if handles and p.get("kind") not in handles:
                continue
            since = int(p.get("since") or 0)
            fixed = p.get("resolved_at")
            if since <= at and (not p.get("resolved") or fixed is None or int(fixed) + GROUNDING_GRACE > at):
                return True
    return False


@flag("contact_ungrounded", "a resident got in touch with a service about a problem nobody in their home had")
def contact_ungrounded(run: Run) -> list[dict[str, Any]]:
    if not run.end.get("residents"):
        return []
    out = []
    for c in run.contacts:
        if not grounded(run, c):
            said = next((l["text"] for l in c.get("lines", []) if l["from"] == "customer"), "")
            out.append(_f(c["day"], c["tick"], [c["resident"]],
                          f"{c['resident']} got in touch with {c['service']} with no such problem at home"
                          + (f": \"{said}\"" if said else ""), service=c["service"],
                          answered=not c.get("failed"),
                          # A note on the account changes nothing in the town.
                          actions=[a["do"] for a in c.get("actions", []) if a["do"] != "note"]))
    return out


def run_all(run: Run) -> dict[str, list[dict[str, Any]]]:
    return {name: fn(run) for name, fn in FLAGS.items()}
