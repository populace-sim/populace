"""The tick loop.

Ported from Alive's `Engine.run_tick`, much smaller. One tick, in order:

1. **needs** rise and fall; urgency is edge-detected; rent falls due; debts
   pass their day
2. **selection**: the scheduler picks who is worth a call, within the budget
3. **decisions** for those, concurrently: prompt, call, parse, validate, one
   retry with the reason, then the free fallback
4. **everybody else** carries on with a standing intent or their schedule, free
5. **resolution**: sleep and waking, moves, work and wages, buying, eating,
   giving, flavour; then conversations and texts
6. **memories** from the witnesses captured at the moment each event happened
7. **save** what changed, **log** the tick, and at midnight the **night**

**No silent no-ops.** Any action that cannot happen goes through `_refuse`,
which emits a private `refused` event and writes the reason into the actor's
own memory, so the next prompt carries it. A guard test holds every refusal
branch to that.
"""

from __future__ import annotations

import asyncio
import time as _time
from dataclasses import dataclass, field
from typing import Any

from .. import clock
from ..providers.costs import ProviderDown, RunStopped, ValidationAlarm
from ..state import locality
from ..state.resident import Resident
from . import actions as A
from . import memory as M
from .events import Event, known_as, public_text
from .scheduler import Selection, budget, select
from .triggers import check_urgent, pair_key, salient_ids

RENT_TICK = 18  # nine in the morning
INTENT_TTL = 4
EVENT_SOURCE = {A.SOURCE_MODEL: "resident", A.SOURCE_RETRY: "resident", A.SOURCE_MOCK: "resident",
                A.SOURCE_INTENT: "intent", A.SOURCE_SCHEDULE: "schedule"}


def decision_id(day: int, tick: int, resident_id: str) -> str:
    return f"d{day}t{tick}:{resident_id}"

# Whose opinion moves when something happens between two people: the one it
# was done to. (holder, about, delta key)
TRUST_FROM_EVENT: dict[str, tuple[str, str, str]] = {
    "loan": ("target", "actor", "loan_received"),
    "gift": ("target", "actor", "gift"),
    "given": ("target", "actor", "gift"),
    "number": ("target", "actor", "number"),
    "introduced": ("target", "actor", "introduced"),
    "promise_kept": ("target", "actor", "promise_kept"),
    "promise_broken": ("target", "actor", "promise_broken"),
    "fired": ("target", "actor", "fired"),
    "no_show": ("target", "actor", "no_show"),
    "stood_up": ("actor", "target", "stood_up"),
}


@dataclass
class TickReport:
    day: int
    tick: int
    wall_ms: float = 0.0
    calls: int = 0
    calls_by_role: dict[str, int] = field(default_factory=dict)
    budget: int = 0
    triggers: dict[str, int] = field(default_factory=dict)
    candidates: int = 0
    deferred: int = 0
    residents_thinking: int = 0
    model_actions: int = 0
    intent_actions: int = 0
    schedule_actions: int = 0
    retries: int = 0
    fallbacks: int = 0
    json_first_try: int = 0
    events: int = 0
    refusals: int = 0
    conversations: int = 0
    lines: int = 0
    texts: int = 0
    stopped: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


class Engine:
    def __init__(self, town, runner, telemetry):
        self.town = town
        self.runner = runner
        self.telemetry = telemetry
        self.config = town.config
        self._pending: list[tuple[Event, list[str], int | None, bool, str, str | None]] = []
        # Who this tick's events come from: a resident's decision, a standing
        # intent, their routine, or the engine itself (rent, the night).
        self.tick_sources: dict[str, str] = {}
        self.tick_decisions: dict[str, str] = {}
        self.last_events: list[Event] = []
        self.witnessed: dict[str, list[Event]] = {}
        self.local_lines: dict[str, list[tuple[str, list[str]]]] = {}
        self.spoken_today: set[str] = set()
        self.earned: dict[str, float] = {}
        self.no_show_today: set[str] = set()
        self.talks: list[tuple[str, A.Action]] = []
        self.texts: list[tuple[str, A.Action]] = []
        self.offers: dict[str, dict] = {}           # this tick: what somebody put on the table
        self.asks: dict[str, dict] = {}             # this tick: what somebody asked for
        self.meetups: list[dict[str, Any]] = []     # invitations, kept or stood up at the hour
        self.pair_today: dict[str, int] = {}        # conversations each pair has had today
        self.pair_last: dict[str, int] = {}         # the tick each pair last talked, today
        self.spoken_lines: dict[str, list[str]] = {}  # each resident's lines today
        self.phone_carry: dict[str, Any] = {}
        self.event_seq = 0
        # Hooks the later milestones fill: conversations, texts, the night.
        self.converse = None
        self.send_texts = None
        self.night = None
        # Service id -> the agent that answers it (step 4b); a service with no
        # agent is one nobody answers, and residents are told so.
        self.agents: dict = {}
        self.contact_service = None
        self._load_carry()

    # -- carry: what survives a stop and resume mid-day --------------------------

    def _load_carry(self) -> None:
        carry = self.town.meta.engine_carry or {}
        self.last_events = [Event.from_dict(e) for e in carry.get("last_events", [])]
        self.witnessed = {k: [Event.from_dict(e) for e in v]
                          for k, v in carry.get("witnessed", {}).items()}
        self.local_lines = {k: [(t, list(w)) for t, w in v]
                            for k, v in carry.get("local_lines", {}).items()}
        self.spoken_today = set(carry.get("spoken_today", []))
        self.earned = dict(carry.get("earned", {}))
        self.no_show_today = set(carry.get("no_show_today", []))
        self.event_seq = int(carry.get("event_seq", 0))
        self.meetups = [dict(m) for m in carry.get("meetups", [])]
        self.pair_today = {k: int(v) for k, v in dict(carry.get("pair_today", {})).items()}
        self.pair_last = {k: int(v) for k, v in dict(carry.get("pair_last", {})).items()}
        self.spoken_lines = {k: list(v) for k, v in carry.get("spoken_lines", {}).items()}
        self.phone_carry = dict(carry.get("phone", {}))

    def _save_carry(self) -> None:
        self.town.meta.engine_carry = {
            "last_events": [e.to_dict() for e in self.last_events],
            "witnessed": {k: [e.to_dict() for e in v] for k, v in sorted(self.witnessed.items())},
            "local_lines": {k: [[t, w] for t, w in v] for k, v in sorted(self.local_lines.items())},
            "spoken_today": sorted(self.spoken_today),
            "earned": dict(sorted(self.earned.items())),
            "no_show_today": sorted(self.no_show_today),
            "event_seq": self.event_seq,
            "meetups": self.meetups,
            "pair_today": dict(sorted(self.pair_today.items())),
            "pair_last": dict(sorted(self.pair_last.items())),
            "spoken_lines": {k: v[-12:] for k, v in sorted(self.spoken_lines.items())},
            "phone": self.phone_carry,
        }

    # -- events --------------------------------------------------------------------

    def event(self, kind: str, actor: Resident, **kwargs) -> Event:
        world = self.town.world
        target = kwargs.pop("target", None)
        return Event(kind=kind, day=world.time.day, tick=world.time.tick,
                     location_id=kwargs.pop("location_id", world.location_of(actor.id)),
                     actor=actor.id, actor_name=actor.name, target=target,
                     target_name=self.town.residents[target].name if target in self.town.residents else None,
                     **kwargs)

    def emit(self, event: Event, actor_importance: int | None = None,
             exclude: set[str] | None = None, skip_actor: bool = False,
             source: str | None = None) -> None:
        """Queue an event with the witnesses who could see it AT THIS MOMENT."""
        seen = M.witnesses(self.town, event)
        if exclude:
            seen = [r for r in seen if r not in exclude]
        self.emit_seen(event, seen, actor_importance, skip_actor, source)

    def emit_seen(self, event: Event, seen: list[str], actor_importance: int | None = None,
                  skip_actor: bool = False, source: str | None = None) -> None:
        """Queue an event whose witnesses the caller has already worked out.
        `source` overrides the tick's own (an injection's events say so)."""
        self._pending.append((event, list(seen), actor_importance, skip_actor,
                              source or self.tick_sources.get(event.actor, "engine"),
                              None if source else self.tick_decisions.get(event.actor)))

    def _refuse(self, resident: Resident, action: A.Action, reason: str) -> None:
        """No silent no-ops: an action that cannot happen says so, to the actor."""
        self.emit(self.event("refused", resident, detail=reason, importance=1,
                             tags=(action.action,)))
        self.report.refusals += 1

    def _log_decision(self, trigger, act: A.Action) -> None:
        """Why somebody did what they did: the report's answer to "why"."""
        world = self.town.world
        did = decision_id(world.time.day, world.time.tick, trigger.resident_id)
        if act.from_model:
            self.tick_decisions[trigger.resident_id] = did
        self.telemetry.log_decision({
            "decision_id": did, "day": world.time.day, "tick": world.time.tick,
            "resident": trigger.resident_id, "trigger": trigger.name, "about": trigger.about,
            "source": act.source if act.from_model else "fallback", **{
                k: v for k, v in act.to_dict().items() if k not in ("source",)},
        })

    def _flush(self) -> None:
        """Write memories from the captured witnesses, apply trust, log."""
        for event, seen, importance, skip_actor, source, decision in self._pending:
            M.record_with_witnesses(self.town, event, seen, importance, skip_actor)
            self._apply_trust(event)
            self.event_seq += 1
            self.telemetry.log_event({"event_id": self.event_seq, **event.to_dict(),
                                      "witnesses": seen,
                                      "source": source, "decision": decision})
            for rid in seen:
                self.witnessed.setdefault(rid, []).append(event)
            if not event.is_private:
                place = self.town.world.places[event.location_id]
                self.local_lines.setdefault(event.location_id, []).append(
                    (public_text(event, place.name), [event.actor] + seen))
            self.last_events.append(event)
        self.report.events += len(self._pending)
        self._pending = []

    def _apply_trust(self, event: Event) -> None:
        spec = TRUST_FROM_EVENT.get(event.kind)
        if spec is None or not event.actor or not event.target:
            return
        holder_key, about_key, delta_key = spec
        holder = self.town.residents.get(event.target if holder_key == "target" else event.actor)
        about = event.target if about_key == "target" else event.actor
        delta = int(self.config.trust["deltas"].get(delta_key, 0))
        if holder is None or not delta or holder.id == about:
            return
        holder.relationship_with(about).add_trust(delta, self.town.world.time.day)
        self.town.touch(holder.id)

    def lines_for(self, resident: Resident) -> list[str]:
        """What this resident saw here in the last half hour, and nothing else."""
        here = self.town.world.location_of(resident.id)
        return [text for text, who in self.local_lines.get(here, []) if resident.id in who][-8:]

    # -- 1. the world moves on its own -------------------------------------------------

    def _needs(self) -> dict[str, str]:
        kinds = self.config.needs["kinds"]
        urgent: dict[str, str] = {}
        for r in self.town.present():
            for name, need in kinds.items():
                rate = float(need["sleep_rate"] if r.asleep else need["rate"])
                r.adjust_need(name, rate)
            fired = check_urgent(r, self.config.needs, self.town)
            if fired:
                urgent[r.id] = fired
                self.emit(self.event("need_urgent", r, detail=self._urgency_text(fired)))
            self.town.touch(r.id)
        return urgent

    @staticmethod
    def _urgency_text(need: str) -> str:
        return {"cash": "The rent is coming and the money isn't there."}.get(
            need, f"My {need} has got the better of me.")

    def _keep_arrangements(self) -> None:
        """Two people who said they would be somewhere, and the hour arriving.
        Both there is `together`, seen by the room; one there is `stood_up`,
        private to the one who waited. An invitation nobody accepted is a
        sentence and nothing more."""
        world = self.town.world
        now = world.time.total_ticks
        from ..state.resident import Intent
        kept = []
        for m in self.meetups:
            if not m.get("accepted"):
                if now <= m["at"]:
                    kept.append(m)
                continue
            a, b = (self.town.residents.get(x) for x in m["who"])
            if a is None or b is None:
                continue
            if m["at"] - now in (1, 2):
                for r in (a, b):
                    r.intent = Intent("move", m["where"], m["at"] + 1)
                kept.append(m)
                continue
            if now < m["at"]:
                kept.append(m)
                continue
            here_a = world.location_of(a.id) == m["where"] and not a.asleep
            here_b = world.location_of(b.id) == m["where"] and not b.asleep
            if here_a and here_b:
                self.emit(self.event("together", a, target=b.id, location_id=m["where"]))
                for x, y in ((a, b), (b, a)):
                    x.relationship_with(y.id).add_trust(int(self.config.trust["deltas"]["together"]), world.time.day)
            elif here_a or here_b:
                waiter, absent = (a, b) if here_a else (b, a)
                self.emit(self.event("stood_up", waiter, target=absent.id, location_id=m["where"]))
        self.meetups = kept

    def _rent_day(self) -> None:
        world = self.town.world
        if world.time.tick != RENT_TICK:
            return
        for r in self.town.present():
            rent = r.rent
            if not rent or int(rent["due_weekday"]) != world.time.weekday_index:
                continue
            landlord = self.town.residents.get(rent["landlord_id"])
            due = float(rent["amount"]) + float(rent.get("owed", 0))
            together = landlord is not None and world.location_of(landlord.id) == world.location_of(r.id)
            if r.money >= due:
                r.money = round(r.money - due, 2)
                if landlord:
                    landlord.money = round(landlord.money + due, 2)
                rent["owed"] = 0.0
                self.emit(self.event("rent_paid", r, target=rent["landlord_id"], amount=due,
                                     force_private=not together))
            else:
                rent["owed"] = round(float(rent.get("owed", 0)) + float(rent["amount"]), 2)
                rent["missed_weeks"] = int(rent.get("missed_weeks", 0)) + 1
                self.emit(self.event("rent_missed", r, target=rent["landlord_id"],
                                     amount=float(rent["amount"]), force_private=True))
                if landlord:
                    # Their book, not a sighting: the landlord knows because the money did not come.
                    landlord.remember(world.time, f"{known_as(r, landlord)}'s rent did not come in: "
                                      f"${rent['owed']:.0f} owed now.", importance=6,
                                      involved=[r.id, landlord.id])
                    self.town.touch(landlord.id)
            self.town.touch(r.id)

    def _debts_due(self) -> None:
        world = self.town.world
        if world.time.tick != RENT_TICK:
            return
        for r in self.town.present():
            for owe in r.obligations.get("owes", []):
                due = owe.get("due_day")
                if due is not None and world.time.day == int(due) + 1 and not owe.get("overdue"):
                    owe["overdue"] = True
                    self.emit(self.event("debt_overdue", r, target=owe.get("to"),
                                         amount=float(owe.get("amount", 0)), tags=(owe.get("kind", "loan"),)))
                    self.town.touch(r.id)

    # -- 2-3. decisions ---------------------------------------------------------------------

    def mock_state(self, r: Resident, trigger: str | None, about: str | None) -> dict[str, Any]:
        """What the mock may read. It never parses a prompt."""
        world = self.town.world
        here = world.location_of(r.id)
        place = world.places[here]
        present = [x for x in world.occupants(here) if x != r.id] if not world.is_offtown(here) else []
        plan = r.schedule_action(world.time.tick, world.time.weekday_index)
        return {
            "id": r.id, "where": here, "home": r.home, "open": world.is_open(here),
            "trigger": trigger, "about": about,
            "present": [{"id": x, "asleep": self.town.residents[x].asleep,
                         "known": r.knows_name(x), "sentiment": r.sentiment(x),
                         "name": known_as(self.town.residents[x], r)} for x in present],
            "for_sale": [{"id": t.id, "name": t.name, "price": t.price, "satiety": t.satiety}
                         for t in place.for_sale()],
            "needs": dict(r.needs), "money": r.money,
            "schedule": {"action": plan["action"], "goto": plan["goto"], "activity": plan["activity"]},
            "job": r.job.workplace if r.job else None,
            "places_known": list(r.places_known),
            "numbers": sorted((r.phone or {}).get("contacts", {})),
            "owed_by": {o.get("from"): o.get("amount") for o in r.obligations.get("owed", [])},
            "owes": {o.get("to"): o.get("amount") for o in r.obligations.get("owes", [])},
            "rent_owed": float((r.rent or {}).get("owed", 0)),
            "services": sorted(getattr(self.town, "services", {}) or {}),
            "service_channels": {k: v.get("channels") or ["text"] for k, v in self.town.services.items()},
            "problems": [p.get("kind") for p in r.problems if not p.get("resolved")],
            "unreported": [p.get("kind") for p in r.problems if not p.get("resolved") and not p.get("reported")],
            "arc_stage": (r.arc or {}).get("stage"),
            "boss": r.job.employer_id if r.job else None,
            # Their own staff, here, who have missed a shift this week.
            "slackers": sorted(x for x in present if (self.town.residents[x].job is not None
                               and self.town.residents[x].job.employer_id == r.id
                               and self.town.residents[x].job.no_shows >= 1)),
            "leisure": [p for p in r.places_known if world.places[p].public][:4],
            "hirers": sorted({h for pl in world.places.values() for h in pl.hires
                              if h in present and not self.town.residents[h].asleep
                              and any(int(o.get("slots", 1)) > len(o.get("filled_by", [])) for o in pl.openings)}),
        }

    async def _decide(self, r: Resident, trigger: str, about: str | None) -> A.Action:
        from ..prompt.blocks import build_decision_prompt

        world = self.town.world
        if trigger == "phone":
            # Answering a text is one call and not a decision: the day carries on.
            from . import phone as PH
            await PH.reply_turn(self, r)
            r.last_model_tick = world.time.total_ticks
            return A.fallback(r, self.town)
        salient = salient_ids(r, world.time.day) if trigger == "goal" else None
        system, messages, _ = build_decision_prompt(r, self.town, self.lines_for(r), trigger,
                                                     salient, self.extra_lines(r))
        meta = {"char_id": r.id, "day": world.time.day, "tick": world.time.tick,
                "decision_id": decision_id(world.time.day, world.time.tick, r.id),
                "mock_state": self.mock_state(r, trigger, about)}
        attempts = int(self.config.engine["retry_limit"]) + 1
        convo = list(messages)
        transport_only = True
        for attempt in range(1, attempts + 1):
            result = await self.runner.call("npc_decision", system, convo,
                                            {**meta, "attempt": attempt,
                                             "call_id": f"{meta['decision_id']}#{attempt}"})
            if not result.ok:
                if attempt < attempts:
                    self.report.retries += 1
                continue
            transport_only = False
            raw = A.extract_json(result.text)
            try:
                if raw is None:
                    raise A.InvalidAction("no JSON object found in the response")
                action = A.validate(raw, r, self.town,
                                    source=A.SOURCE_MODEL if attempt == 1 else A.SOURCE_RETRY)
            except A.InvalidAction as exc:
                if attempt < attempts:
                    self.report.retries += 1
                    convo = convo + [
                        {"role": "assistant", "content": result.text or "(empty)"},
                        {"role": "user", "content": f"That didn't work: {exc}\n"
                                                    "Reply with one valid JSON object and nothing else."},
                    ]
                continue
            self.runner.meter.note_validation(True)
            if attempt == 1:
                self.report.json_first_try += 1
            r.last_model_tick = world.time.total_ticks
            return action
        if not transport_only:
            self.runner.meter.note_validation(False)
        self.report.fallbacks += 1
        r.last_model_tick = world.time.total_ticks
        return A.fallback(r, self.town)

    def extra_lines(self, r: Resident) -> list[str]:
        """Lines other modules add to a resident's prompt (injections, services)."""
        hooks = getattr(self, "prompt_extras", None)
        return hooks(r) if hooks else []

    # -- 5. resolution -----------------------------------------------------------------------

    def _sleep_and_wake(self, actions: dict[str, A.Action]) -> None:
        for rid in sorted(actions):
            r, act = self.town.residents[rid], actions[rid]
            if act.action == "sleep":
                if not r.asleep:
                    r.asleep = True
                    self.emit(self.event("sleep", r))
            elif r.asleep:
                r.asleep = False
                self.emit(self.event("wake", r))
            self.town.touch(rid)

    def _moves(self, actions: dict[str, A.Action]) -> None:
        world = self.town.world
        for rid in sorted(actions):
            act = actions[rid]
            if act.action != "move" or not act.target:
                continue
            r = self.town.residents[rid]
            if act.target not in world.places:
                self._refuse(r, act, f"there is no such place as {act.target}")
                continue
            origin = world.location_of(rid)
            if origin == act.target:
                self._refuse(r, act, "I was already there")
                continue
            self.emit(self.event("depart", r, location_id=origin))
            world.place(rid, act.target)
            self.emit(self.event("arrive", r, location_id=act.target))
            self.town.touch(rid)

    def _staffed(self, place, here: str) -> bool:
        """A shop is a person as much as a set of hours: somebody who works here
        has to be here, awake, for it to sell anything."""
        if not place.workplace_of:
            return True
        return any(self.town.world.location_of(s) == here and not self.town.residents[s].asleep
                   for s in place.workplace_of if s in self.town.residents)

    def _economy(self, actions: dict[str, A.Action]) -> None:
        world = self.town.world
        t = world.time
        satiety_need = next((n for n, v in self.config.needs["kinds"].items() if "urgent_above" in v), None)
        for rid in sorted(actions):
            r, act = self.town.residents[rid], actions[rid]
            here = world.location_of(rid)
            place = world.places[here]
            job = r.job
            if act.action == "work":
                if job is None:
                    self._refuse(r, act, "I have no job to work at")
                elif here != job.workplace:
                    self._refuse(r, act, f"I wasn't at work to do it")
                elif not job.on_shift(t.tick, t.weekday_index):
                    self._refuse(r, act, "it isn't my shift")
                else:
                    if rid not in self.earned:
                        self.emit(self.event("work_start", r))
                    self.earned[rid] = round(self.earned.get(rid, 0.0) + job.wage_per_tick, 2)
            elif act.action == "buy":
                thing = place.thing_by_name(act.target or "")
                if thing is None or thing.price is None:
                    self._refuse(r, act, f"there was no {act.target_raw or act.target} for sale")
                elif not world.is_open(here):
                    self._refuse(r, act, f"{place.name} was shut")
                elif not self._staffed(place, here):
                    self._refuse(r, act, f"there was nobody behind the counter at {place.name}")
                elif r.money < float(thing.price):
                    self.emit(self.event("buy_fail", r, detail=thing.name, amount=float(thing.price)))
                else:
                    r.money = round(r.money - float(thing.price), 2)
                    owner = self.town.residents.get(place.owner or "")
                    if owner is not None:
                        owner.money = round(owner.money + float(thing.price), 2)
                        self.town.touch(owner.id)
                    if satiety_need and thing.satiety:
                        r.adjust_need(satiety_need, -float(thing.satiety))
                    self.emit(self.event("buy", r, detail=thing.name, amount=float(thing.price)))
            elif act.action == "eat":
                at_work = job is not None and here == job.workplace
                if here != r.home and not at_work:
                    self._refuse(r, act, "there was nothing of mine to eat here")
                else:
                    if satiety_need:
                        r.adjust_need(satiety_need, -float(self.config.needs["home_meal_satiety"]) * 2)
                    self.emit(self.event("eat", r, detail="at home" if here == r.home else "what I brought"))
            elif act.action == "give":
                other = self.town.residents.get(act.target or "")
                amount = float(act.amount or 0)
                if other is None or world.location_of(other.id) != here:
                    self._refuse(r, act, "they weren't there to hand it to")
                elif amount <= 0 or amount > r.money:
                    self._refuse(r, act, f"I didn't have ${amount:.0f} to give")
                else:
                    r.money = round(r.money - amount, 2)
                    other.money = round(other.money + amount, 2)
                    self.emit(self.event("given", r, target=other.id, amount=amount))
                    self.town.touch(other.id)
            elif act.action == "other" and act.target:
                self.emit(self.event("other", r, detail=act.target), act.importance)
            self.town.touch(rid)

    def _shifts(self) -> None:
        """Wages at the end of a shift; a no-show when somebody never came."""
        world = self.town.world
        t = world.time
        grace = int(self.config.economy["no_show_grace_ticks"])
        for r in self.town.present():
            job = r.job
            if job is None:
                continue
            if r.id in self.earned and not job.on_shift(t.tick, t.weekday_index):
                pay = self.earned.pop(r.id)
                r.money = round(r.money + pay, 2)
                self.emit(self.event("wage", r, amount=pay))
                self.emit(self.event("work_end", r, location_id=job.workplace))
                self.town.touch(r.id)
            if job.on_shift(t.tick, t.weekday_index) and t.tick - job.shift_start == grace \
                    and r.id not in self.earned and r.id not in self.no_show_today:
                self.no_show_today.add(r.id)
                job.no_shows += 1
                self.emit(self.event("no_show", r, location_id=job.workplace, target=job.employer_id))
                boss = self.town.residents.get(job.employer_id or "")
                if boss is not None:
                    boss.remember(t, f"{known_as(r, boss)} didn't turn up for the shift.", importance=5,
                                  involved=[r.id])
                    self.town.touch(boss.id)
                self.town.touch(r.id)

    # -- one tick --------------------------------------------------------------------------------

    async def run_tick(self) -> TickReport:
        started = _time.perf_counter()
        world = self.town.world
        self.report = TickReport(day=world.time.day, tick=world.time.tick)
        meter = self.runner.meter
        meter.start_tick()
        self.report.budget = budget(self.town)[0]
        self.tick_sources, self.tick_decisions = {}, {}
        try:
            self.offers = {}
            self.asks = {}
            from ..inject import apply as INJ
            INJ.expire(self)
            INJ.apply_due(self)
            urgent = self._needs()
            self._keep_arrangements()
            from . import lives
            lives.check_departures(self)
            self._rent_day()
            self._debts_due()
            previous = self.last_events
            self.last_events = []
            witnessed, self.witnessed = self.witnessed, {}
            selection: Selection = select(self.town, previous, urgent, self.spoken_today, witnessed)
            self.report.triggers = selection.names
            self.report.candidates = selection.candidates
            self.report.deferred = len(selection.deferred)
            self.report.residents_thinking = len(selection.decide)
            decided = await asyncio.gather(*(self._decide(self.town.residents[t.resident_id], t.name, t.about)
                                            for t in selection.decide))
            actions: dict[str, A.Action] = {}
            for trigger, act in zip(selection.decide, decided):
                actions[trigger.resident_id] = act
                A.set_intent(self.town.residents[trigger.resident_id], act, self.town, INTENT_TTL)
                self._log_decision(trigger, act)
            for r in self.town.present():
                if r.id not in actions:
                    actions[r.id] = A.fallback(r, self.town)
            self.tick_sources = {rid: EVENT_SOURCE.get(a.source, "schedule") for rid, a in actions.items()}
            for act in actions.values():
                if act.source in (A.SOURCE_MODEL, A.SOURCE_RETRY, A.SOURCE_MOCK):
                    self.report.model_actions += 1
                elif act.source == A.SOURCE_INTENT:
                    self.report.intent_actions += 1
                else:
                    self.report.schedule_actions += 1
            self.local_lines = {}
            self._sleep_and_wake(actions)
            self._moves(actions)
            INJ.notice_pass(self)
            self._economy(actions)
            self._shifts()
            self.talks = [(rid, a) for rid, a in sorted(actions.items()) if a.action == "talk"]
            self.texts = [(rid, a) for rid, a in sorted(actions.items()) if a.action == "contact"]
            if self.converse is not None:
                await self.converse(self)
            else:
                for rid, act in self.talks:
                    self._refuse(self.town.residents[rid], act, "conversations are not built yet")
            if self.send_texts is not None:
                await self.send_texts(self)
            else:
                for rid, act in self.texts:
                    self._refuse(self.town.residents[rid], act, "texts are not built yet")
            self._flush()
            for r in self.town.present():
                M.enforce_raw_cap(r, int(self.config.reflection["raw_memory_cap"]))
        except RunStopped as stop:
            self.report.stopped = f"{type(stop).__name__}: {stop}"
            self._flush()
        self.report.calls = meter.tick_calls
        self.report.calls_by_role = dict(meter.tick_calls_by_role)
        self.town.meta.ticks_run += 1
        self.town.meta.model_calls = meter.calls_total
        last_of_day = world.time.is_last_tick_of_day
        if self.report.stopped is None:
            if last_of_day:
                await self.end_of_day()
            world.time = world.time.advance()
        self._save_carry()
        self.town.save()
        self.report.wall_ms = round((_time.perf_counter() - started) * 1000, 1)
        self.telemetry.log_tick(self.report.to_dict())
        return self.report

    async def end_of_day(self) -> None:
        day = self.town.world.time.day
        # Night events are the engine's, not the last tick's decisions.
        self.tick_sources, self.tick_decisions = {}, {}
        if self.town.services:
            from ..agents.contact import judge_promises
            judge_promises(self, day)
        if self.night is not None:
            await self.night(self, day)
            self._flush()
        self.spoken_today = set()
        self.no_show_today = set()
        self.pair_today = {}
        self.pair_last = {}
        self.spoken_lines = {}
        for r in self.town.residents.values():
            r.threads = [t for t in r.threads if t.get("day", 0) >= day]
            if r.job:
                if self.town.world.time.weekday_index == 6:
                    r.job.no_shows = 0
        locality.refresh(self.town)
        self.telemetry.write_day(day)
        self.town.world.clear_public_log()
        self.town.snapshot_day(day)
        if self.telemetry.enabled:
            from ..observe import digest
            digest.write(self.town, self.telemetry.log_dir, f"day_{day:02d}")
