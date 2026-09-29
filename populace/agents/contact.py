"""A resident contacting a service, from the engine's side.

`contact_service` is what the `contact` action reaches when its target is a
registered service. By text it is one exchange: the resident's words, the
agent's reply. By phone or at the counter it goes back and forth within the
tick, each of the resident's later lines a model call that has to fit the
tick's budget; when the budget is spent, the resident says goodbye. At the
counter, whoever else is there sees them at it.

Every way it can fail is said: no agent answers the service, it is out of
hours, the agent errors or does not answer in time. Each is a
`contact_failed` event and a line in the resident's memory.

What the agent did through its `AgentContext` becomes the world: problems
resolved, money credited, somebody sent round at a time, promises judged on
their day (`judge_promises`, at night). The resident remembers one line per
contact. Everything is logged to the run's `contacts.jsonl`.
"""

from __future__ import annotations

import asyncio
import inspect
import json
from typing import TYPE_CHECKING, Any

from .. import clock
from ..inject import InjectionRefused, label, parse_at
from ..sim.actions import extract_json
from ..sim.events import Event
from .protocol import AgentContext, Message, Reply

if TYPE_CHECKING:  # pragma: no cover
    from ..sim.actions import Action
    from ..sim.engine import Engine
    from ..state.resident import Resident

AGENT_TIMEOUT_S = 10.0
CALL_TURNS = 3          # the resident speaks at most this many times on a call or at a counter


def _hhmm(total_or_tick: int) -> str:
    return clock.tick_to_hhmm(total_or_tick % clock.TICKS_PER_DAY)


def _in_hours(service: dict[str, Any], tick: int) -> bool:
    hours = service.get("hours")
    if not hours:
        return True
    start = _to_tick(hours["open"])
    end = _to_tick(hours["close"])
    return start <= tick < end if start <= end else (tick >= start or tick < end)


def _to_tick(hhmm: str) -> int:
    hours, minutes = (int(x) for x in hhmm.split(":"))
    return (hours * 60 + minutes) // clock.MINUTES_PER_TICK


def customer(r: "Resident", town) -> dict[str, Any]:
    """What a service would know about a customer: name, number, address."""
    home = town.world.places.get(r.home)
    # A street address, as a service would hold it: a named block ("Clover
    # Court") is still "5 Clover Street" on the account.
    if home is None:
        address = ""
    elif home.street:
        address = f"{home.number} {home.street}" if home.number else home.street
    else:
        address = home.name
    return {"name": r.name, "number": (r.phone or {}).get("number", ""), "address": address}


def _event(engine: "Engine", kind: str, r: "Resident", service: dict[str, Any], detail: str,
           public: bool, importance: int = 4, amount: float | None = None) -> None:
    world = engine.town.world
    event = Event(kind=kind, day=world.time.day, tick=world.time.tick, location_id=world.location_of(r.id),
                  actor=r.id, actor_name=r.name, detail=detail, importance=importance, amount=amount,
                  force_private=not public, tags=(service["id"],))
    engine.emit(event, source=f"agent:{service['id']}")


def _fail(engine: "Engine", r: "Resident", service: dict[str, Any], channel: str, reason: str,
          lines: list | None = None) -> None:
    _event(engine, "contact_failed", r, service, f"I tried to reach {service['name']}: {reason}.",
           public=channel == "visit", importance=5)
    engine.telemetry.log_contact({
        "day": engine.town.world.time.day, "tick": engine.town.world.time.tick, "service": service["id"],
        "resident": r.id, "channel": channel, "lines": lines or [], "actions": [], "failed": reason})
    engine.report.refusals += 1


async def contact_service(engine: "Engine", r: "Resident", act: "Action") -> None:
    town = engine.town
    world = town.world
    service = town.services[act.target]
    channel = act.channel or "text"
    agent = (getattr(engine, "agents", None) or {}).get(service["id"])
    if agent is None:
        _fail(engine, r, service, channel, "nobody answered")
        return
    if not _in_hours(service, world.time.tick):
        h = service["hours"]
        _fail(engine, r, service, channel, f"they were closed; a recording gave their hours, {h['open']}-{h['close']}")
        return
    if channel == "visit":
        store = service["storefront"]
        if world.location_of(r.id) != store:
            engine.emit(engine.event("depart", r))
            world.place(r.id, store)
            engine.emit(engine.event("arrive", r))
    thread = service.setdefault("threads", {}).setdefault(r.id, [])
    ctx = AgentContext(engine, r, service["id"])
    lines: list[dict[str, str]] = []
    text = act.dialogue or ""
    turns = 1 if channel == "text" else CALL_TURNS
    problems = [p.get("text") or p.get("kind") for p in r.problems if not p.get("resolved")]
    for turn in range(turns):
        lines.append({"from": "customer", "text": text})
        message = Message(service=service["id"], channel=channel, customer=customer(r, town), text=text,
                          thread=list(thread), day=world.time.day, time=_hhmm(world.time.tick),
                          problems=problems)
        thread.append({"from": "customer", "text": text})
        try:
            raw = agent.handle(message, ctx)
            if inspect.isawaitable(raw):
                # An agent may say how long it needs (a model-backed one
                # waits for the server); otherwise the default.
                raw = await asyncio.wait_for(raw, float(getattr(agent, "timeout_s", None) or AGENT_TIMEOUT_S))
            reply = Reply.of(raw)
        except Exception as exc:  # an agent is somebody else's code: any failure is a failed contact
            reason = "the line went dead" if isinstance(exc, (asyncio.TimeoutError, TimeoutError)) \
                else f"the line went dead ({type(exc).__name__})"
            _fail(engine, r, service, channel, reason, lines)
            return
        if reply is None or not reply.text:
            break
        lines.append({"from": "agent", "text": reply.text})
        thread.append({"from": "agent", "text": reply.text})
        if reply.end or turn == turns - 1:
            break
        nxt = await _next_line(engine, r, service, channel, lines)
        if nxt is None:
            break
        text = nxt
    applied = _apply(engine, r, service, ctx.actions)
    _remember(engine, r, service, channel, lines, applied)
    from ..inject.apply import report_to_household
    said = next((l["text"] for l in reversed(lines) if l["from"] == "agent"), None)
    report_to_household(engine, r, service, said)
    engine.telemetry.log_contact({
        "day": world.time.day, "tick": world.time.tick, "service": service["id"], "resident": r.id,
        "channel": channel, "lines": lines, "actions": ctx.actions})
    engine.report.texts += 1 if channel == "text" else 0


async def _next_line(engine: "Engine", r: "Resident", service: dict[str, Any], channel: str,
                     lines: list[dict[str, str]]) -> str | None:
    """The resident's next line, if the tick's budget has a call left."""
    from ..prompt.blocks import character_block, shared_block
    from ..sim.events import as_seen_by
    from ..sim.scheduler import budget

    town = engine.town
    total, _ = budget(town)
    if total - engine.runner.meter.tick_calls < 1:
        return None
    where = f"on the phone to {service['name']}" if channel == "call" else f"at the counter of {service['name']}"
    said = "\n".join(f"  {'You' if l['from'] == 'customer' else service['name']}: {l['text']}" for l in lines)
    problems = [p.get("text") or p.get("kind") for p in r.problems if not p.get("resolved")]
    user = as_seen_by(
        f"You are {where} ({service['purpose']}).\n"
        + (f"At home: {', '.join(problems)}.\n" if problems else "")
        + f"So far:\n{said}\n\n"
        "Say your next line, or end it if you are done. Reply with JSON only: "
        '{"line": "(what you say)", "end_conversation": true or false}', r, town)
    response = await engine.runner.call(
        "dialogue", [{"type": "text", "text": shared_block(town)},
                     {"type": "text", "text": character_block(r, town)}],
        [{"role": "user", "content": user}],
        {"char_id": r.id, "day": town.world.time.day, "tick": town.world.time.tick, "sub_idx": len(lines),
         "mock_state": {"service": service["name"], "problems": problems,
                        "agent_said": lines[-1]["text"], "line_no": len(lines)}})
    data = extract_json(response.text) if response.ok else None
    if not data or not str(data.get("line") or "").strip() or data.get("end_conversation"):
        return None
    return str(data["line"]).strip()[: int(town.config.phone["max_text_chars"])]


def _apply(engine: "Engine", r: "Resident", service: dict[str, Any], actions: list[dict[str, Any]]) -> list[str]:
    """What the agent did, made real. Returns short sentences for the memory."""
    town = engine.town
    world = town.world
    done = []
    for a in actions:
        kind = a["do"]
        if kind == "resolve":
            fixed = resolve_problems(r, service, world.time.total_ticks, town, a.get("kind"))
            town.touch(r.id)
            if fixed:
                done.append(f"they sorted the {', '.join(fixed)}")
        elif kind == "credit":
            r.money = round(r.money + float(a["amount"]), 2)
            town.touch(r.id)
            _event(engine, "credit", r, service, f"{service['name']} credited me ${a['amount']:.2f}"
                   + (f" ({a['reason']})" if a.get("reason") else "") + ".", public=False, amount=a["amount"])
            done.append(f"they credited me ${a['amount']:.2f}")
        elif kind == "dispatch":
            try:
                at = parse_at(a["at"], town)
            except InjectionRefused as exc:
                a["refused"] = str(exc)
                continue
            at = max(at, world.time.total_ticks + 1)
            world.scheduled.append({"id": f"d{world.time.total_ticks}-{r.id}-{service['id']}", "kind": "_dispatch",
                                    "at": at, "params": {"service": service["id"], "resident": r.id,
                                                         "fixes": a.get("fixes", True), "kind": a.get("kind")}})
            done.append(f"somebody is coming round {label(at)}")
        elif kind == "promise":
            service.setdefault("promises", []).append({
                "resident": r.id, "what": a["what"], "by_day": int(a["by_day"]), "kind": a.get("kind"),
                "made": world.time.total_ticks, "judged": None,
                # The problems it is about: those open at home now, of its kind.
                "injs": sorted({p["inj"] for p in r.problems if p.get("inj") and not p.get("resolved")
                                and (not a.get("kind") or p.get("kind") == a["kind"])})})
            done.append(f"they promised: {a['what']}, by Day {a['by_day']}")
    return done


def resolve_problems(r: "Resident", service: dict[str, Any], now: int, town=None,
                     kind: str | None = None) -> list[str]:
    """Fix what the service handles at this customer's home - one kind, or
    every kind it handles - for everybody who lives there, since the line is
    the house's, not the caller's."""
    handles = {kind} if kind else set(service.get("handles") or [])
    fixed = []
    injs = set()
    for p in r.problems:
        if not p.get("resolved") and (not handles or p.get("kind") in handles):
            p["resolved"] = True
            p["resolved_at"] = now
            p["resolved_by"] = f"service:{service.get('id', '')}"
            fixed.append(p.get("kind"))
            if p.get("inj"):
                injs.add(p["inj"])
    if town is not None and injs and r.home in town.world.places:
        for other_id in town.world.places[r.home].residents_of:
            other = town.residents.get(other_id)
            # The household's line, not the whole building's.
            if other is None or other is r or other.household != r.household:
                continue
            for p in other.problems:
                if p.get("inj") in injs and not p.get("resolved"):
                    p["resolved"] = True
                    p["resolved_at"] = now
                    p["resolved_by"] = f"service:{service.get('id', '')}"
                    town.touch(other_id)
    return fixed


def _remember(engine: "Engine", r: "Resident", service: dict[str, Any], channel: str,
              lines: list[dict[str, str]], done: list[str]) -> None:
    verb = {"text": "texted", "call": "rang", "visit": "went to the counter at"}[channel]
    theirs = next((l["text"] for l in reversed(lines) if l["from"] == "agent"), None)
    detail = (f"I {verb} {service['name']}"
              + (f"; they said: \"{theirs}\"" if theirs else "; no reply yet")
              + (f" - {'; '.join(done)}" if done else "") + ".")
    _event(engine, "contact", r, service, detail, public=channel == "visit", importance=5)


def judge_promises(engine: "Engine", day: int) -> None:
    """A service's promise is kept if the customer's problem is resolved by the
    night of the day it named."""
    town = engine.town
    for service in town.services.values():
        for p in service.get("promises", []):
            if p["judged"] is not None or p["by_day"] > day:
                continue
            r = town.residents.get(p["resident"])
            if r is None:
                p["judged"] = "gone"
                continue
            handles = {p["kind"]} if p.get("kind") else set(service.get("handles") or [])
            if p.get("injs"):
                # Judged on the problems it was made about, not on whatever
                # else has gone wrong since.
                open_ = [x for x in r.problems if not x.get("resolved") and x.get("inj") in p["injs"]]
            else:
                open_ = [x for x in r.problems if not x.get("resolved") and (not handles or x.get("kind") in handles)]
            kept = not open_
            p["judged"] = "kept" if kept else "broken"
            _event(engine, "service_promise_kept" if kept else "service_promise_broken", r, service,
                   f"{service['name']} said: {p['what']}, by Day {p['by_day']}. "
                   + ("They did." if kept else "They didn't."), public=False, importance=4 if kept else 7)
