"""The report's findings, in two groups a reader must never confuse.

**What the agent got wrong** is about the outside service's side: the thing
under test. It acted on a problem the customer did not have; it corrected
something that was already put right; it left messages from out of hours
unworked while the problem stayed; it broke promises.

**Where the simulation is weak** is about the town's side: residents who
invented a problem, got in touch at hours no helpdesk keeps, repeated
themselves; and the report's own proxies and model-written parts.

Every item is computed from the run's logs, and each group says so plainly
when its checks found nothing.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from . import flags as F

TPD = F.TICKS_PER_DAY
# Flags that describe how residents behaved or talked, not the engine.
SIM_FLAGS = ("repeated_line", "echo", "stuck", "no_reaction", "name_unknown", "claim_unfounded",
             "id_spoken", "sleepless", "impossible_move")


def _total(c: dict[str, Any]) -> int:
    return (c["day"] - 1) * TPD + c["tick"]


def _open_at(run: F.Run, rid: str, kind: str | None, at: int) -> bool:
    """Did anybody in this resident's home have an open problem of `kind` at `at`?"""
    residents = run.end.get("residents", {})
    me = residents.get(rid) or {}
    home, household = me.get("home"), me.get("household")
    for r_id, r in residents.items():
        if r_id != rid and (not home or r.get("home") != home
                            or (household and r.get("household") != household)):
            continue
        for p in r.get("problems") or []:
            if kind and p.get("kind") != kind:
                continue
            since, fixed = int(p.get("since") or 0), p.get("resolved_at")
            # Fixed in this very contact counts as open at it.
            if since <= at and (not p.get("resolved") or fixed is None or int(fixed) >= at):
                return True
    return False


def compute(ctx: dict[str, Any]) -> dict[str, list[str]]:
    run, book, flags = ctx["run"], ctx["book"], ctx["flags"]
    contacts = ctx.get("contacts", [])
    agent: list[str] = []
    sim: list[str] = []

    ungrounded = flags.get("contact_ungrounded", [])
    acted_on = [f for f in ungrounded if f.get("actions")]
    answered = [f for f in ungrounded if f.get("answered", True)]
    if acted_on:
        what = Counter(a for f in acted_on for a in f["actions"])
        agent.append(
            f"**It acted on problems the customer did not have.** {len(acted_on)} of the "
            f"{len(ungrounded)} contacts about a problem nobody at home had got "
            + ", ".join(f"{k} {v}" for k, v in sorted(what.items()))
            + " in reply (" + ", ".join(sorted({book.name(f['who'][0]) for f in acted_on})[:5]) + "). "
            + ("It never checked the claim against the line or the account." if len(acted_on) >= len(answered)
               else f"The other {len(answered) - len(acted_on)} it answered got no action."))

    redone = []
    for c in contacts:
        if c.get("failed"):
            continue
        for a in c.get("actions", []):
            if a["do"] == "resolve" and a.get("kind") and not _open_at(run, c["resident"], a["kind"], _total(c)):
                redone.append((c, a["kind"]))
    if redone:
        agent.append(
            f"**It fixed things that were not broken.** {len(redone)} time"
            f"{'s' if len(redone) != 1 else ''} it resolved a {'/'.join(sorted({k for _, k in redone}))} "
            "problem the customer's home did not have open, such as correcting a bill already "
            "corrected (" + ", ".join(sorted({book.name(c['resident']) for c, _ in redone})[:5]) + ").")

    by_resident = defaultdict(list)
    for c in contacts:
        by_resident[c["resident"]].append(c)
    stranded = []
    for rid, cs in by_resident.items():
        closed = [c for c in cs if (c.get("failed") or "").startswith("they were closed")]
        if not closed:
            continue
        last_closed = max(_total(c) for c in closed)
        answered_after = any(not c.get("failed") and _total(c) > last_closed for c in cs)
        end = (run.end.get("day", 0) - 1) * TPD + run.end.get("tick", 0)
        if not answered_after and _open_at(run, rid, None, end):
            stranded.append(rid)
    if stranded:
        agent.append(
            f"**It never worked its out-of-hours messages.** {len(stranded)} "
            + ("resident got only the recording, was never followed up, and still had"
               if len(stranded) == 1 else
               "residents got only the recording, were never followed up, and still had")
            + " the problem at the end (" + ", ".join(book.name(r) for r in sorted(stranded)[:5])
            + "). A real helpdesk works the overnight queue in the morning.")

    broken = [e for e in run.events if e["kind"] == "service_promise_broken"]
    if broken:
        agent.append(f"**It broke {len(broken)} promise{'s' if len(broken) != 1 else ''}** it made to "
                     "customers about when things would be fixed.")

    if ungrounded:
        sim.append(
            f"**Residents invented problems.** {len(ungrounded)} contacts from "
            f"{len({f['who'][0] for f in ungrounded})} residents were about a problem nobody in their "
            "home had. That is the simulated town making things up, not the service's doing, and "
            "it is counted apart from the real contacts in \"The service\".")
    closed_all = [c for c in contacts if (c.get("failed") or "").startswith("they were closed")]
    if contacts and closed_all:
        sim.append(
            f"**Residents often called out of hours.** {len(closed_all)} of {len(contacts)} attempts "
            f"({round(100 * len(closed_all) / len(contacts))}%) came when the service was closed. "
            "Real customers do some of this; how much is a question for the model driving them.")
    fired = [(k, len(flags.get(k, []))) for k in SIM_FLAGS if flags.get(k)]
    if fired:
        sim.append("**Realism flags fired:** " + ", ".join(f"`{k}` {n}" for k, n in fired)
                   + " (details under \"Realism flags\").")
    if ctx.get("injections"):
        sim.append("**Word of mouth is measured narrowly.** \"Passed on in conversation\" counts only "
                   "lines to somebody who had not seen it; talk among people who already knew is "
                   "not counted, so a quiet number is not the same as a quiet town.")
    if any(r.get("kind") == "service.register" for r in ctx.get("injections", [])):
        sim.append("**Talk of switching provider** is a keyword proxy, not a measured intention.")
    return {"agent": agent, "sim": sim}


def section(ctx: dict[str, Any]) -> list[str]:
    found = compute(ctx)
    if not ctx.get("contacts") and not ctx.get("injections"):
        return []
    lines = ["## Findings", "",
             "Two kinds, kept apart: mistakes by the outside agent under test, and weaknesses of the "
             "simulated town and of this report.", "",
             "### What the agent got wrong", ""]
    lines += [f"- {x}" for x in found["agent"]] or ["- Nothing these checks can see."]
    lines += ["", "### Where the simulation is weak", ""]
    lines += [f"- {x}" for x in found["sim"]] or ["- Nothing these checks can see."]
    return lines
