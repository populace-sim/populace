"""A resident: who they are, what they need, who they know, what they remember.

Ported from Alive's `characters.py`. Kept: memories, relationships with a
trust counter that is never shown as a number, the schedule that tiles the day,
jobs, sticky intents, names held versus faces seen, what has been talked
through, what they were told about whom, obligations, the phone, the arc.

Changed:

* **Needs are a dict of whatever the config defines**, not hunger and energy
  hardcoded into loading and saving.
* **Days off.** A job has working weekdays; on the others a resident follows
  `off_schedule`. Alive's residents lived the same day seven times a week.
* **Locality.** `circle` is the people this resident actually knows about and
  `places_known` the places they have reason to go; see `state/locality.py`.
* Left behind with the systems they served: condition, drink, inventory,
  record, bans, housing status, habit.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from .. import clock
from ..clock import GameTime, tick_to_hhmm

SCHEMA_VERSION = 1

MEMORY_KINDS = {"observation", "dialogue", "reflection", "belief"}
SCHEDULE_ACTIVITIES = {"sleep", "work", "eat", "leisure", "home", "errand", "school"}

# How far somebody trusts you, in the words they would use. The counter behind
# these moves on events, and nothing ever shows the number.
TRUST_STAGES = (
    "knows your face",
    "warming up",
    "would vouch for you",
    "would take you in",
)
DEFAULT_TRUST_THRESHOLDS = (0, 5, 25, 60)


class ResidentError(Exception):
    """Raised when resident data is malformed."""


def stage_for(trust: int, thresholds=DEFAULT_TRUST_THRESHOLDS) -> int:
    stage = 0
    for index, line in enumerate(thresholds):
        if trust >= line:
            stage = index
    return stage


def stage_words(stage: int) -> str:
    return TRUST_STAGES[max(0, min(len(TRUST_STAGES) - 1, int(stage)))]


def phone_number_for(town_seed: int, resident_id: str) -> str:
    """A stable, town-specific number: 555 plus four digits."""
    digest = hashlib.sha256(f"{town_seed}|{resident_id}".encode()).hexdigest()
    return f"555-{int(digest[:8], 16) % 10000:04d}"


def _default_obligations() -> dict[str, Any]:
    return {"owes": [], "owed": []}


def _default_phone() -> dict[str, Any]:
    return {"number": "", "contacts": {}, "threads": {}}


def _default_arc() -> dict[str, Any]:
    return {"stage": "settled", "since_day": 0, "last_review_day": 0,
            "leave_day": None, "leave_tick": None, "detail": None}


@dataclass
class Memory:
    """One thing a resident saw, did, was told, or concluded."""

    id: int
    day: int
    tick: int
    kind: str
    text: str
    importance: int
    involved: list[str] = field(default_factory=list)
    location_id: str | None = None
    source_ids: list[int] = field(default_factory=list)

    @property
    def total_ticks(self) -> int:
        return (self.day - 1) * clock.TICKS_PER_DAY + self.tick

    def stamp(self) -> str:
        return f"Day {self.day} {tick_to_hhmm(self.tick)}"

    @staticmethod
    def from_dict(d: dict) -> "Memory":
        return Memory(
            id=int(d["id"]), day=int(d["day"]), tick=int(d["tick"]), kind=d["kind"],
            text=d["text"], importance=int(d["importance"]),
            involved=list(d.get("involved", [])), location_id=d.get("location_id"),
            source_ids=[int(x) for x in d.get("source_ids", [])],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id, "day": self.day, "tick": self.tick, "kind": self.kind,
            "text": self.text, "importance": self.importance,
            "involved": list(self.involved), "location_id": self.location_id,
            "source_ids": list(self.source_ids),
        }


@dataclass
class Relationship:
    label: str
    sentiment: int  # -10..10
    notes: list[str] = field(default_factory=list)
    # Something unresolved sits between these two, independent of fondness.
    friction: bool = False
    # `trust` is internal and moves only on things that happened. `stage` is
    # what a prompt renders, in words, and catches up at nightly reflection so
    # the cached character block stays byte-identical through the day.
    trust: int = 0
    stage: int = 0
    trust_recent: list[list[int]] = field(default_factory=list)  # [[day, delta]]
    lately: str | None = None
    promises: list[dict[str, Any]] = field(default_factory=list)
    moments: list[str] = field(default_factory=list)
    number_shared: bool = False
    met_day: int | None = None
    last_talk_day: int | None = None

    @staticmethod
    def from_dict(d: dict) -> "Relationship":
        sentiment = int(d.get("sentiment", 0))
        trust = int(d["trust"]) if "trust" in d else max(0, min(100, 20 + 5 * sentiment))
        return Relationship(
            label=d.get("label", "acquaintance"),
            sentiment=sentiment,
            notes=list(d.get("notes", [])),
            friction=bool(d.get("friction", False)),
            trust=trust,
            stage=int(d.get("stage", stage_for(trust))),
            trust_recent=[list(e) for e in d.get("trust_recent", [])],
            lately=d.get("lately"),
            promises=list(d.get("promises", [])),
            moments=list(d.get("moments", [])),
            number_shared=bool(d.get("number_shared", False)),
            met_day=d.get("met_day"),
            last_talk_day=d.get("last_talk_day"),
        )

    def to_dict(self) -> dict:
        return {
            "label": self.label, "sentiment": self.sentiment, "notes": list(self.notes),
            "friction": self.friction, "trust": self.trust, "stage": self.stage,
            "trust_recent": [list(e) for e in self.trust_recent], "lately": self.lately,
            "promises": list(self.promises), "moments": list(self.moments),
            "number_shared": self.number_shared, "met_day": self.met_day,
            "last_talk_day": self.last_talk_day,
        }

    def add_trust(self, delta: int, day: int, keep_days: int = 7) -> int:
        before = self.trust
        self.trust = max(0, min(100, self.trust + int(delta)))
        moved = self.trust - before
        if moved:
            self.trust_recent.append([int(day), moved])
            self.trust_recent = [e for e in self.trust_recent if e[0] > day - keep_days]
        return moved

    def recent_trust(self, day: int, window_days: int) -> int:
        return sum(e[1] for e in self.trust_recent if e[0] > day - window_days)

    def add_moment(self, moment: str) -> None:
        if moment and moment not in self.moments:
            self.moments.append(moment)

    def open_promises(self) -> list[dict[str, Any]]:
        return [p for p in self.promises if p.get("status") == "open"]

    def add_promise(self, promise: dict[str, Any], cap: int = 5) -> None:
        self.promises.append(promise)
        del self.promises[:-cap]

    def add_note(self, note: str, cap: int = 5) -> None:
        note = note.strip()
        if note:
            self.notes.append(note)
            del self.notes[:-cap]


@dataclass
class ScheduleEntry:
    """Half-open [start_tick, end_tick) block of an ordinary day."""

    start_tick: int
    end_tick: int
    activity: str
    location_id: str

    @staticmethod
    def from_dict(d: dict) -> "ScheduleEntry":
        return ScheduleEntry(int(d["start_tick"]), int(d["end_tick"]), d["activity"],
                             d["location_id"])

    def to_dict(self) -> dict:
        return {"start_tick": self.start_tick, "end_tick": self.end_tick,
                "activity": self.activity, "location_id": self.location_id}


@dataclass
class Job:
    title: str
    workplace: str
    wage_per_tick: float
    shift_start: int
    shift_end: int
    # Weekday indices worked, Monday = 0.
    days: list[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])
    # Who took them on and answers for them; None for owners and the self-employed.
    employer_id: str | None = None
    start_day: int = 1
    hired_day: int | None = None
    no_shows: int = 0
    last_no_show_day: int | None = None

    def works_on(self, weekday_index: int) -> bool:
        return weekday_index in self.days

    def on_shift(self, tick: int, weekday_index: int) -> bool:
        return self.works_on(weekday_index) and self.shift_start <= tick < self.shift_end

    def shift_label(self) -> str:
        return f"{tick_to_hhmm(self.shift_start)}-{tick_to_hhmm(self.shift_end)}"

    @staticmethod
    def from_dict(d: dict) -> "Job":
        return Job(
            title=d["title"], workplace=d["workplace"], wage_per_tick=float(d["wage_per_tick"]),
            shift_start=int(d["shift"]["start"]), shift_end=int(d["shift"]["end"]),
            days=[int(x) for x in d.get("days", [0, 1, 2, 3, 4])],
            employer_id=d.get("employer_id"), start_day=int(d.get("start_day", 1)),
            hired_day=d.get("hired_day"), no_shows=int(d.get("no_shows", 0)),
            last_no_show_day=d.get("last_no_show_day"),
        )

    def to_dict(self) -> dict:
        return {
            "title": self.title, "workplace": self.workplace, "wage_per_tick": self.wage_per_tick,
            "shift": {"start": self.shift_start, "end": self.shift_end}, "days": list(self.days),
            "employer_id": self.employer_id, "start_day": self.start_day,
            "hired_day": self.hired_day, "no_shows": self.no_shows,
            "last_no_show_day": self.last_no_show_day,
        }


@dataclass
class Intent:
    """A model decision that stays sticky for a few ticks, so the schedule
    cannot immediately drag somebody back where they came from. `dialogue`
    carries an opening line a conversation had no budget for this tick, so it
    can be said next tick without another call."""

    action: str
    target: str | None
    expires_tick: int  # absolute total ticks
    dialogue: str | None = None

    @staticmethod
    def from_dict(d: dict) -> "Intent":
        return Intent(d["action"], d.get("target"), int(d["expires_tick"]), d.get("dialogue"))

    def to_dict(self) -> dict:
        return {"action": self.action, "target": self.target,
                "expires_tick": self.expires_tick, "dialogue": self.dialogue}


def _entries(blocks: list[dict]) -> list[ScheduleEntry]:
    return [ScheduleEntry.from_dict(b) for b in blocks]


@dataclass
class Resident:
    id: str
    name: str
    age: int
    home: str
    persona: dict[str, Any]
    schedule: list[ScheduleEntry]
    needs: dict[str, float]
    money: float
    household: str = ""
    neighbourhood: str = ""
    # The ordinary day on the days `schedule` does not apply (weekends, days
    # off). `routine_days` are the weekday indices `schedule` covers; None
    # means every day.
    off_schedule: list[ScheduleEntry] = field(default_factory=list)
    routine_days: list[int] | None = None
    job: Job | None = None
    goals_active: list[str] = field(default_factory=list)
    relationships: dict[str, Relationship] = field(default_factory=dict)
    rent: dict[str, Any] | None = None
    memory: list[Memory] = field(default_factory=list)
    # status
    asleep: bool = False
    intent: Intent | None = None
    last_model_tick: int = -999
    urgent_armed: dict[str, bool] = field(default_factory=dict)
    pending_trigger: str | None = None
    # Faces clocked, {id: day}: one look each, not one every half hour.
    noticed: dict[str, int] = field(default_factory=dict)
    # Names actually held, {id: {"day", "how"}}. A name is handed over, never
    # caught by standing near somebody; see `knows_name`.
    names_known: dict[str, dict[str, Any]] = field(default_factory=dict)
    # What has been talked through today, so it is not raised again.
    threads: list[dict[str, Any]] = field(default_factory=list)
    # What they were told about other people: {id: [{by, claim, day, ...}]}.
    told_about: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    obligations: dict[str, Any] = field(default_factory=_default_obligations)
    phone: dict[str, Any] = field(default_factory=_default_phone)
    arc: dict[str, Any] = field(default_factory=_default_arc)
    competence: dict[str, float] = field(default_factory=dict)
    # Off town: a bus that has gone.
    away: dict[str, Any] | None = None
    # Locality: who and where this resident knows about. Refreshed nightly.
    circle: list[str] = field(default_factory=list)
    places_known: list[str] = field(default_factory=list)
    # Things wrong in their life that an injection put there and that somebody
    # might fix: {problem_id, kind, since_day, since_tick, service_hint, ...}.
    problems: list[dict[str, Any]] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    # -- persona -----------------------------------------------------------

    @property
    def secret(self) -> str:
        return str(self.persona.get("secret", ""))

    @property
    def public_bio(self) -> str:
        return str(self.persona.get("public_bio", ""))

    @property
    def long_term_goal(self) -> str:
        return str(self.persona.get("long_term_goal", ""))

    @property
    def first_name(self) -> str:
        return self.name.split()[0]

    # -- schedule ------------------------------------------------------------

    def day_schedule(self, weekday_index: int) -> list[ScheduleEntry]:
        if (self.routine_days is not None and weekday_index not in self.routine_days
                and self.off_schedule):
            return self.off_schedule
        return self.schedule

    def scheduled_entry(self, tick: int, weekday_index: int = 0) -> ScheduleEntry:
        for entry in self.day_schedule(weekday_index):
            if entry.start_tick <= tick < entry.end_tick:
                return entry
        raise ResidentError(f"{self.id}: no schedule entry covering tick {tick}")

    def schedule_action(self, tick: int, weekday_index: int = 0) -> dict[str, Any]:
        """The zero-cost default action for this tick."""
        entry = self.scheduled_entry(tick, weekday_index)
        action = {"sleep": "sleep", "work": "work", "eat": "eat"}.get(entry.activity, "wait")
        return {
            "action": action, "target": None, "dialogue": None,
            "reasoning": f"following the usual {entry.activity} block",
            "importance": 1, "goto": entry.location_id, "activity": entry.activity,
        }

    # -- needs -----------------------------------------------------------------

    def adjust_need(self, key: str, delta: float) -> None:
        self.needs[key] = max(0.0, min(100.0, self.needs.get(key, 0.0) + delta))

    # -- relationships -----------------------------------------------------------

    def relationship(self, other_id: str) -> Relationship | None:
        return self.relationships.get(other_id)

    def sentiment(self, other_id: str) -> int:
        rel = self.relationships.get(other_id)
        return rel.sentiment if rel else 0

    def trust_stage(self, other_id: str, thresholds=DEFAULT_TRUST_THRESHOLDS) -> int:
        """The live stage off the counter; validators ask this. Prompts read
        `Relationship.stage`, which only catches up at night."""
        rel = self.relationships.get(other_id)
        return stage_for(rel.trust, thresholds) if rel else 0

    def relationship_with(self, other_id: str) -> Relationship:
        rel = self.relationships.get(other_id)
        if rel is None:
            rel = Relationship(label="somebody I've had dealings with", sentiment=0)
            self.relationships[other_id] = rel
        return rel

    def has_met(self, other_id: str) -> bool:
        return other_id in self.relationships

    def knows_name(self, other_id: str) -> bool:
        """May this person put a name to that one. Not the same as having met:
        two people can share an afternoon's work without either saying what
        they are called."""
        return other_id == self.id or other_id in self.names_known

    def learn_name(self, other_id: str, day: int, how: str = "said") -> bool:
        """Called only where a name was actually said out loud in front of them."""
        if other_id == self.id or other_id in self.names_known:
            return False
        self.names_known[other_id] = {"day": int(day), "how": how}
        return True

    def owes_to(self, other_id: str, kind: str | None = None) -> float:
        return round(sum(float(o.get("amount", 0)) for o in self.obligations.get("owes", [])
                         if o.get("to") == other_id and (kind is None or o.get("kind") == kind)), 2)

    def owed_by(self, other_id: str, kind: str | None = None) -> float:
        return round(sum(float(o.get("amount", 0)) for o in self.obligations.get("owed", [])
                         if o.get("from") == other_id and (kind is None or o.get("kind") == kind)), 2)

    # -- memory --------------------------------------------------------------------

    def todays_threads(self, day: int) -> list[dict[str, Any]]:
        return [t for t in self.threads if t.get("day") == day]

    def add_thread(self, other: str, topic: str, outcome: str, day: int, tick: int) -> None:
        self.threads.append({"other": other, "topic": topic[:120],
                             "outcome": (outcome or "")[:120], "day": day, "tick": tick})
        del self.threads[:-30]

    def next_memory_id(self) -> int:
        return max((m.id for m in self.memory), default=0) + 1

    def remember(
        self,
        time: GameTime,
        text: str,
        kind: str = "observation",
        importance: int = 2,
        involved: list[str] | None = None,
        location_id: str | None = None,
        source_ids: list[int] | None = None,
    ) -> Memory:
        if kind not in MEMORY_KINDS:
            raise ResidentError(f"unknown memory kind: {kind}")
        mem = Memory(
            id=self.next_memory_id(), day=time.day, tick=time.tick, kind=kind, text=text,
            importance=max(1, min(10, int(importance))), involved=sorted(involved or []),
            location_id=location_id, source_ids=sorted(source_ids or []),
        )
        self.memory.append(mem)
        return mem

    # -- what an outsider may see ----------------------------------------------------

    def public(self) -> dict[str, Any]:
        """What a stranger or an external agent may know: nothing private."""
        return {
            "id": self.id, "name": self.name, "age": self.age, "home": self.home,
            "workplace": self.job.workplace if self.job else None,
            "descriptor": self.persona.get("descriptor", ""),
        }

    # -- serialisation -----------------------------------------------------------------

    @staticmethod
    def from_dict(d: dict) -> "Resident":
        status = d.get("status", {})
        return Resident(
            schema_version=int(d.get("schema_version", SCHEMA_VERSION)),
            id=d["id"], name=d["name"], age=int(d["age"]), home=d["home"],
            household=d.get("household", ""), neighbourhood=d.get("neighbourhood", ""),
            persona=dict(d.get("persona", {})),
            schedule=_entries(d.get("schedule", [])),
            off_schedule=_entries(d.get("off_schedule", [])),
            routine_days=[int(x) for x in d["routine_days"]] if d.get("routine_days") is not None else None,
            needs={k: float(v) for k, v in (d.get("needs") or {}).items()},
            money=float(d.get("money", 0)),
            job=Job.from_dict(d["job"]) if d.get("job") else None,
            goals_active=list(d.get("goals_active", [])),
            relationships={k: Relationship.from_dict(v)
                           for k, v in (d.get("relationships") or {}).items()},
            rent=dict(d["rent"]) if d.get("rent") else None,
            memory=[Memory.from_dict(m) for m in d.get("memory", [])],
            asleep=bool(status.get("asleep", False)),
            intent=Intent.from_dict(status["intent"]) if status.get("intent") else None,
            last_model_tick=int(status.get("last_model_tick", -999)),
            urgent_armed=dict(status.get("urgent_armed", {})),
            pending_trigger=status.get("pending_trigger"),
            away=dict(status["away"]) if status.get("away") else None,
            noticed={k: int(v) for k, v in (d.get("noticed") or {}).items()},
            names_known={k: dict(v) for k, v in (d.get("names_known") or {}).items()},
            threads=list(d.get("threads", [])),
            told_about={k: [dict(e) for e in v] for k, v in (d.get("told_about") or {}).items()},
            obligations={**_default_obligations(), **(d.get("obligations") or {})},
            phone={**_default_phone(), **(d.get("phone") or {})},
            arc={**_default_arc(), **(d.get("arc") or {})},
            competence={k: float(v) for k, v in (d.get("competence") or {}).items()},
            circle=list(d.get("circle", [])),
            places_known=list(d.get("places_known", [])),
            problems=[dict(p) for p in d.get("problems", [])],
        )

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "id": self.id, "name": self.name, "age": self.age, "home": self.home,
            "household": self.household, "neighbourhood": self.neighbourhood,
            "job": self.job.to_dict() if self.job else None,
            "persona": {k: self.persona[k] for k in sorted(self.persona)},
            "goals_active": list(self.goals_active),
            "relationships": {k: self.relationships[k].to_dict()
                              for k in sorted(self.relationships)},
            "schedule": [s.to_dict() for s in self.schedule],
            "off_schedule": [s.to_dict() for s in self.off_schedule],
            "routine_days": list(self.routine_days) if self.routine_days is not None else None,
            "needs": {k: self.needs[k] for k in sorted(self.needs)},
            "money": self.money,
            "rent": self.rent,
            "status": {
                "asleep": self.asleep,
                "intent": self.intent.to_dict() if self.intent else None,
                "last_model_tick": self.last_model_tick,
                "urgent_armed": {k: self.urgent_armed[k] for k in sorted(self.urgent_armed)},
                "pending_trigger": self.pending_trigger,
                "away": self.away,
            },
            "noticed": {k: self.noticed[k] for k in sorted(self.noticed)},
            "names_known": {k: dict(self.names_known[k]) for k in sorted(self.names_known)},
            "threads": list(self.threads),
            "told_about": {k: self.told_about[k] for k in sorted(self.told_about)},
            "obligations": self.obligations,
            "phone": self.phone,
            "arc": self.arc,
            "competence": {k: self.competence[k] for k in sorted(self.competence)},
            "circle": list(self.circle),
            "places_known": list(self.places_known),
            "problems": [dict(p) for p in self.problems],
            "memory": [m.to_dict() for m in self.memory],
        }

    def validate(self, location_ids: set[str], resident_ids: set[str],
                 need_kinds: set[str] | None = None) -> list[str]:
        problems: list[str] = []
        if self.home not in location_ids:
            problems.append(f"{self.id}: home {self.home!r} is not a place")
        if self.job:
            if self.job.workplace not in location_ids:
                problems.append(f"{self.id}: workplace {self.job.workplace!r} is not a place")
            if not 0 <= self.job.shift_start < self.job.shift_end <= clock.TICKS_PER_DAY:
                problems.append(f"{self.id}: bad shift {self.job.shift_start}..{self.job.shift_end}")
            if self.job.employer_id and self.job.employer_id not in resident_ids:
                problems.append(f"{self.id}: employer {self.job.employer_id!r} is not a resident")
        for label, day in (("schedule", self.schedule), ("off_schedule", self.off_schedule)):
            if label == "off_schedule" and not day:
                continue
            problems += _tiling_problems(self.id, label, day, location_ids)
        for other_id, rel in sorted(self.relationships.items()):
            if other_id == self.id:
                problems.append(f"{self.id}: has a relationship with itself")
            elif other_id not in resident_ids:
                problems.append(f"{self.id}: relationship with unknown resident {other_id!r}")
            if not -10 <= rel.sentiment <= 10:
                problems.append(f"{self.id}: sentiment for {other_id} out of range")
        if self.rent and self.rent.get("landlord_id") not in resident_ids:
            problems.append(f"{self.id}: rent landlord is not a resident")
        for key, value in self.needs.items():
            if not 0 <= value <= 100:
                problems.append(f"{self.id}: need {key} out of range: {value}")
        if need_kinds is not None and set(self.needs) != set(need_kinds):
            problems.append(f"{self.id}: needs {sorted(self.needs)} are not {sorted(need_kinds)}")
        for field_name in ("personality", "speech_style", "public_bio", "long_term_goal",
                           "descriptor"):
            if not self.persona.get(field_name):
                problems.append(f"{self.id}: persona missing {field_name}")
        for cid in self.circle:
            if cid not in resident_ids:
                problems.append(f"{self.id}: circle holds unknown resident {cid!r}")
        for pid in self.places_known:
            if pid not in location_ids:
                problems.append(f"{self.id}: knows unknown place {pid!r}")
        for side, key in (("owes", "to"), ("owed", "from")):
            for entry in self.obligations.get(side, []):
                if entry.get(key) not in resident_ids:
                    problems.append(f"{self.id}: {side} an unknown resident {entry.get(key)!r}")
        return problems


def _tiling_problems(rid: str, label: str, day: list[ScheduleEntry],
                     location_ids: set[str]) -> list[str]:
    """A day must tile [0, TICKS_PER_DAY) exactly: no gaps, no overlaps."""
    problems: list[str] = []
    cursor = 0
    for entry in sorted(day, key=lambda e: e.start_tick):
        if entry.activity not in SCHEDULE_ACTIVITIES:
            problems.append(f"{rid}: {label} has unknown activity {entry.activity!r}")
        if entry.location_id not in location_ids:
            problems.append(f"{rid}: {label} block at {entry.start_tick} uses unknown "
                            f"place {entry.location_id!r}")
        if entry.start_tick != cursor:
            problems.append(f"{rid}: {label} gap or overlap at tick {cursor}")
        if entry.end_tick <= entry.start_tick:
            problems.append(f"{rid}: {label} has an empty block at {entry.start_tick}")
        cursor = max(cursor, entry.end_tick)
    if cursor != clock.TICKS_PER_DAY:
        problems.append(f"{rid}: {label} covers up to {cursor}, needs {clock.TICKS_PER_DAY}")
    return problems


def tile(blocks: list[dict[str, Any]], home: str) -> list[dict[str, Any]]:
    """Make blocks cover the whole day exactly, filling any gap with home."""
    out: list[dict[str, Any]] = []
    cursor = 0
    for block in sorted(blocks, key=lambda b: b["start_tick"]):
        block = dict(block)
        block["start_tick"] = max(block["start_tick"], cursor)
        block["end_tick"] = min(block["end_tick"], clock.TICKS_PER_DAY)
        if block["end_tick"] <= block["start_tick"]:
            continue
        if block["start_tick"] > cursor:
            out.append({"start_tick": cursor, "end_tick": block["start_tick"],
                        "activity": "home", "location_id": home})
        out.append(block)
        cursor = block["end_tick"]
    if cursor < clock.TICKS_PER_DAY:
        out.append({"start_tick": cursor, "end_tick": clock.TICKS_PER_DAY,
                    "activity": "home", "location_id": home})
    return out


def set_work_block(resident: Resident, workplace: str, start: int, end: int) -> None:
    """Put a shift into somebody's ordinary day, re-tiling around it. Being
    hired has to change the day, or the new hand never turns up."""
    start = max(0, min(clock.TICKS_PER_DAY - 1, int(start)))
    end = max(start + 1, min(clock.TICKS_PER_DAY, int(end)))
    kept: list[dict[str, Any]] = []
    for entry in resident.schedule:
        block = entry.to_dict()
        if block["activity"] == "work":
            continue  # one job at a time
        if block["end_tick"] <= start or block["start_tick"] >= end:
            kept.append(block)
            continue
        if block["start_tick"] < start:
            kept.append({**block, "end_tick": start})
        if block["end_tick"] > end:
            kept.append({**block, "start_tick": end})
    kept.append({"start_tick": start, "end_tick": end, "activity": "work",
                 "location_id": workplace})
    resident.schedule = _entries(tile(kept, resident.home))


def clear_work_blocks(resident: Resident, workplace: str | None = None) -> None:
    """Take the shift back out. What is left is time of their own."""
    kept = [e.to_dict() for e in resident.schedule
            if not (e.activity == "work" and (workplace is None or e.location_id == workplace))]
    resident.schedule = _entries(tile(kept, resident.home))
