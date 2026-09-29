"""How a town dealt with an outside service, from a run directory alone.

Per registered service: who had a problem it handles, who got in touch, how
long they waited, how, whether a household reported it more than once, what
got fixed on which day and what was still broken at the end, the promises the
service made and whether a broken one was chased, and how many residents
talked about switching provider. The last is a keyword proxy and is labelled
as one.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import median
from typing import Any

from .. import words as W
from . import flags as F

TPD = 48
SWITCHING = ("switch provider", "switching provider", "switch providers", "another provider",
             "new provider", "change provider", "changing provider", "cancel my", "cancel our",
             "cancelling", "leave northline", "leaving northline", "switch to")


def _t(c: dict[str, Any]) -> int:
    """A contact or decision's time on the problems' clock: ticks from Day 1."""
    return (c["day"] - 1) * TPD + c["tick"]


def _restores(ctx: dict[str, Any]) -> dict[str, int]:
    """When each outage was put right by the schedule, by injection id."""
    return {r["id"][:-len("-end")]: (r["day"] - 1) * TPD + r["tick"]
            for r in ctx.get("injections", []) if r.get("kind") == "_restore" and not r.get("refused")}


def _fixed_by(p: dict[str, Any], restores: dict[str, int]) -> str:
    if p.get("resolved_by"):
        return "schedule" if p["resolved_by"] == "schedule" else "service"
    # Runs from before resolved_by was recorded: a problem that ended exactly
    # when its injection's schedule put it right was the schedule's doing.
    at, inj = p.get("resolved_at"), p.get("inj")
    return "schedule" if inj in restores and at is not None and int(at) == restores[inj] else "service"


def compute(ctx: dict[str, Any]) -> dict[str, dict[str, Any]]:
    run = ctx["run"]
    contacts = ctx.get("contacts", [])
    services: dict[str, dict[str, Any]] = {}
    for rec in ctx.get("injections", []):
        if rec.get("kind") == "service.register" and not rec.get("refused"):
            services[rec["params"]["id"]] = rec["params"]
    for c in contacts:
        services.setdefault(c["service"], {"id": c["service"], "name": c["service"]})
    restores = _restores(ctx)
    end_t = (run.end.get("day", 1) - 1) * TPD + run.end.get("tick", 0)
    out = {}
    for sid, svc in sorted(services.items()):
        handles = set(svc.get("handles") or [])
        problems: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for rid, r in run.end.get("residents", {}).items():
            for p in r.get("problems") or []:
                if not handles or p.get("kind") in handles:
                    problems[rid].append(p)
        mine = [c for c in contacts if c["service"] == sid]
        # A contact about a problem nobody at home had is the simulation
        # inventing it; the rest are the service's real workload.
        invented = [c for c in mine if not F.grounded(run, c)]
        invented_ids = {id(c) for c in invented}
        real = [c for c in mine if id(c) not in invented_ids]
        by_resident: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for c in mine:
            by_resident[c["resident"]].append(c)
        affected = sorted(problems)
        tried = [r for r in affected if any(id(c) not in invented_ids for c in by_resident.get(r, []))]
        reached = [r for r in tried if any(not c.get("failed") and id(c) not in invented_ids
                                           for c in by_resident[r])]
        only_recording = [r for r in tried if r not in reached]

        def window(p):
            fixed = p.get("resolved_at")
            return int(p.get("since") or 0), (int(fixed) if p.get("resolved") and fixed is not None else end_t)

        # How long each resident waited before getting in touch about each
        # problem: from when that problem began to their first contact in it.
        waits = []
        for rid in affected:
            for p in problems[rid]:
                start, stop = window(p)
                during = [_t(c) for c in by_resident.get(rid, []) if start <= _t(c) <= stop]
                if during:
                    waits.append((min(during) - start) / 2)
        decided = {d["resident"] for d in run.decisions if d["resident"] in problems
                   and any(window(p)[0] <= _t(d) <= window(p)[1] for p in problems[d["resident"]])}
        homes: dict[str, set[str]] = defaultdict(set)
        for rid in tried:
            home = (run.end["residents"].get(rid) or {}).get("home")
            if home:
                homes[home].add(rid)
        fixed_on = {"service": Counter(), "schedule": Counter()}
        still_open = 0
        for rid, ps in problems.items():
            for p in ps:
                if p.get("resolved") and p.get("resolved_at") is not None:
                    fixed_on[_fixed_by(p, restores)][int(p["resolved_at"]) // TPD + 1] += 1
                elif not p.get("resolved"):
                    still_open += 1
        promised = [(c, a) for c in mine for a in c.get("actions", []) if a["do"] == "promise"]
        promised_invented = sum(1 for c, _ in promised if id(c) in invented_ids)
        broken = [e for e in run.events if e["kind"] == "service_promise_broken" and sid in (e.get("tags") or [])]
        kept = sum(1 for e in run.events if e["kind"] == "service_promise_kept" and sid in (e.get("tags") or []))
        chased_broken = sum(1 for e in broken if any(c["resident"] == e["actor"] and (c["day"], c["tick"]) > (e["day"], e["tick"])
                                                    for c in mine))
        # Chasing: getting in touch again after being promised something,
        # before the day it was promised for had passed.
        chasers = set()
        for c, a in promised:
            for later in by_resident[c["resident"]]:
                if _t(later) > _t(c) and later["day"] <= int(a["by_day"]):
                    chasers.add(c["resident"])
        switching = set()
        for d in run.decisions:
            if W.contains(f"{d.get('reasoning') or ''} {d.get('dialogue') or ''}", SWITCHING):
                switching.add(d["resident"])
        for conv in run.conversations:
            for line in conv.get("lines", []):
                if W.contains(line.get("text", ""), SWITCHING):
                    switching.add(line["speaker"])
        for c in mine:
            for line in c.get("lines", []):
                if line["from"] == "customer" and W.contains(line["text"], SWITCHING):
                    switching.add(c["resident"])
        out[sid] = {
            "name": svc.get("name", sid),
            "affected": len(affected),
            "decided_while_open": len(decided),
            "tried": len(tried),
            "reached": len(reached),
            "only_recording": sorted(only_recording),
            "contact_rate_pct": round(100 * len(tried) / len(affected), 1) if affected else 0.0,
            "hours_to_contact": {"median": round(median(waits), 1) if waits else None,
                                 "max": max(waits) if waits else None, "n": len(waits)},
            "contacts": len(mine),
            "answered": sum(1 for c in mine if not c.get("failed")),
            "failed": dict(Counter(c["failed"].split(";")[0] for c in mine if c.get("failed"))),
            "channels": dict(Counter(c["channel"] for c in mine)),
            "grounded_contacts": len(real),
            "invented_contacts": len(invented),
            "invented_by": sorted({c["resident"] for c in invented}),
            "agent_did_on_invented": dict(Counter(a["do"] for c in invented for a in c.get("actions", [])
                                                if a["do"] != "note")),
            "contacted_twice_or_more": sum(1 for r, cs in by_resident.items() if len(cs) > 1),
            "chased_a_promise": len(chasers),
            "homes_reporting_more_than_once": sum(1 for rs in homes.values() if len(rs) > 1),
            "homes_reporting": len(homes),
            "agent_did": dict(Counter(a["do"] for c in mine for a in c.get("actions", []))),
            "fixed_by_service_by_day": dict(sorted(fixed_on["service"].items())),
            "restored_by_schedule_by_day": dict(sorted(fixed_on["schedule"].items())),
            "still_broken_at_end": still_open,
            "promises_made": len(promised), "promises_to_invented": promised_invented,
            "promises_kept": kept, "promises_broken": len(broken),
            "promises_pending": max(0, len(promised) - kept - len(broken)),
            "broken_then_chased": chased_broken,
            "talked_of_switching": sorted(switching),
        }
    return out


def section(ctx: dict[str, Any]) -> list[str]:
    """The report's "The service" section, or nothing if no service was registered."""
    metrics = compute(ctx)
    if not metrics:
        return []
    book = ctx["book"]
    lines = ["## The service", ""]
    for sid, m in metrics.items():
        wait = m["hours_to_contact"]
        rows = [
            ("Residents with a problem it handles", m["affected"]),
            ("...who had at least one decision while it was open", m["decided_while_open"]),
            ("...who tried to get in touch", f"{m['tried']} ({m['contact_rate_pct']}%)"),
            ("...who reached the service", m["reached"]),
            ("...who only ever got the recording", len(m["only_recording"])),
            ("Hours from a problem starting to getting in touch about it, median / longest",
             f"{wait['median']} / {wait['max']} (over {wait['n']})" if wait["median"] is not None else "-"),
            ("Contacts, answered / all", f"{m['answered']} / {m['contacts']}"),
            ("Got nowhere", ", ".join(f"{k} {v}" for k, v in m["failed"].items()) or "0"),
            ("By channel", ", ".join(f"{k} {v}" for k, v in sorted(m["channels"].items())) or "-"),
            ("Contacts about a real problem at home", m["grounded_contacts"]),
            ("Contacts about a problem nobody at home had (the simulation inventing one)",
             f"{m['invented_contacts']} from {len(m['invented_by'])} residents"
             + (f"; the agent answered with {', '.join(f'{k} {v}' for k, v in sorted(m['agent_did_on_invented'].items()))}"
                if m["agent_did_on_invented"] else "")),
            ("Residents who got in touch twice or more", m["contacted_twice_or_more"]),
            ("...who chased something they had been promised", m["chased_a_promise"]),
            ("Homes that got in touch, and of those more than one person",
             f"{m['homes_reporting']}, {m['homes_reporting_more_than_once']}"),
            ("What the agent did", ", ".join(f"{k} {v}" for k, v in sorted(m["agent_did"].items())) or "-"),
            ("Problems the service fixed, by day",
             ", ".join(f"Day {d}: {n}" for d, n in m["fixed_by_service_by_day"].items()) or "none"),
            ("Problems that ended on the schedule (not the service's doing), by day",
             ", ".join(f"Day {d}: {n}" for d, n in m["restored_by_schedule_by_day"].items()) or "none"),
            ("Still broken at the end", m["still_broken_at_end"]),
            ("Promises made / to people with no such problem", f"{m['promises_made']} / {m['promises_to_invented']}"),
            ("Promises kept / broken / not yet due at the end / broken and then chased",
             f"{m['promises_kept']} / {m['promises_broken']} / {m['promises_pending']} / {m['broken_then_chased']}"),
            ("Talked of switching provider (keyword proxy)", len(m["talked_of_switching"])),
        ]
        lines += [f"**{m['name']}** (`{sid}`)", "", "| | |", "|---|---|"]
        lines += [f"| {k} | {v} |" for k, v in rows]
        if m["invented_by"]:
            lines += ["", "Got in touch about a problem nobody at home had: "
                      + ", ".join(book.name(r) for r in m["invented_by"][:8]) + "."]
        if m["talked_of_switching"]:
            lines += ["", "Talked of switching: " + ", ".join(book.name(r) for r in m["talked_of_switching"][:8]) + "."]
        lines.append("")
    return lines
