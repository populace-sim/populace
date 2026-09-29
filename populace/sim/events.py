"""Typed events and their renderings: the anti-omniscience boundary.

Ported from Alive's `events.py`. Resolution emits `Event` objects carrying only
what a bystander could observe: who acted, what they did, where, to whom,
anything said aloud, and a visible outcome. Personas, secrets, needs, balances
and private reasoning are not fields on this struct, so `public_text` cannot
leak them: not because it is careful, but because it has nothing to leak.

`private_text` is the actor's own first-person memory of the same moment and is
the only renderer allowed to consult the resident's private state.

**Names.** A name is something somebody hands you. `as_seen_by` rewrites every
name in a text that the reader has not been given into a description of that
person. In Alive it scanned every resident for every line; here a `NameIndex`
finds the names a text mentions in one regex pass, which is what makes it
affordable at 200 residents.

Kept kinds are those of a town with work, money, promises, talk and phones.
Arrive and depart are rated below the witness threshold, so a stranger walking
through a room is remembered only by people who know them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Iterable

if TYPE_CHECKING:  # pragma: no cover
    from ..state.resident import Resident

# How memorable an event is to a bystander by default, 1-10. A model-assigned
# importance overrides this for the actor's own action and for dialogue.
IMPORTANCE_RUBRIC = {
    "arrive": 2,
    "depart": 1,
    "work_start": 2,
    "work_end": 2,
    "eat": 2,
    "buy": 3,
    "buy_fail": 5,
    "refused": 1,
    "thought_better": 3,
    "sleep": 1,
    "wake": 1,
    "woken": 4,
    "wait": 1,
    "other": 3,
    "talk_missed": 2,
    "talk_declined": 3,
    "talk_deferred": 2,
    "conversation": 5,
    "text_sent": 3,
    "text_received": 4,
    "rent_paid": 4,
    "rent_missed": 7,
    "date": 6,
    "promise": 5,
    "promise_kept": 5,
    "promise_broken": 6,
    "stood_up": 6,
    "together": 5,
    "introduced": 5,
    "invite": 4,
    "accept": 4,
    "number": 4,
    "gift": 5,
    "given": 5,
    "wage": 2,
    "need_urgent": 4,
    "hired": 6,
    "fired": 8,
    "quit": 7,
    "no_show": 6,
    "loan": 6,
    "repay": 5,
    "debt_overdue": 5,
    "leave_town": 8,
}

# Events nobody else can see, even standing in the same room.
PRIVATE_ONLY = {
    "wage",
    "need_urgent",
    "refused",
    # An absence is not a sighting: the employer knows because it is their roster.
    "no_show",
    "debt_overdue",
    # What today is to you is yours.
    "date",
    # Being stood up is one person sitting there.
    "stood_up",
    # Whether a promise was kept is settled at day's end, on the record.
    "promise_kept", "promise_broken",
    # Thinking better of something is not a thing anybody watched.
    "thought_better",
    # A text is read on a screen nobody else is looking at.
    "text_sent", "text_received",
    # Noticing a sign is in your own head; the sign itself is the public part.
    "noticed",
    # What a service did for you, and whether it kept its word, is your business.
    "credit", "service_promise_kept", "service_promise_broken",
}

# Two-person moments the other half remembers in their own first person.
TARGET_REMEMBERS = {
    "hired", "fired", "quit", "loan", "repay", "gift", "given", "number", "invite",
    "accept", "introduced", "promise", "promise_kept", "promise_broken",
    "text_received",
}


@dataclass(frozen=True)
class Event:
    """One observable thing that happened. Public fields only."""

    kind: str
    day: int
    tick: int
    location_id: str
    actor: str
    actor_name: str
    target: str | None = None
    target_name: str | None = None
    detail: str = ""  # a visible noun: "a sandwich", "the early shift"
    spoken: str | None = None  # words said out loud
    amount: float | None = None  # a sum named in the open
    importance: int | None = None  # model-assigned override
    # A normally-public kind that happened with nobody to see it.
    force_private: bool = False
    tags: tuple[str, ...] = field(default_factory=tuple)

    @property
    def base_importance(self) -> int:
        if self.importance is not None:
            return max(1, min(10, self.importance))
        return IMPORTANCE_RUBRIC.get(self.kind, 2)

    @property
    def is_private(self) -> bool:
        return self.force_private or self.kind in PRIVATE_ONLY

    def involved(self) -> list[str]:
        return sorted({x for x in (self.actor, self.target) if x})

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind, "day": self.day, "tick": self.tick,
            "location_id": self.location_id, "actor": self.actor,
            "actor_name": self.actor_name, "target": self.target,
            "target_name": self.target_name, "detail": self.detail, "spoken": self.spoken,
            "amount": self.amount, "importance": self.base_importance,
            "force_private": self.force_private, "tags": list(self.tags),
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Event":
        return Event(
            kind=d["kind"], day=int(d["day"]), tick=int(d["tick"]),
            location_id=d["location_id"], actor=d["actor"],
            actor_name=d.get("actor_name", d["actor"]), target=d.get("target"),
            target_name=d.get("target_name"), detail=d.get("detail", ""),
            spoken=d.get("spoken"), amount=d.get("amount"), importance=d.get("importance"),
            force_private=bool(d.get("force_private", False)), tags=tuple(d.get("tags", ())),
        )


def money(amount: float | None) -> str:
    if amount is None:
        return ""
    return f"${amount:,.0f}" if float(amount).is_integer() else f"${amount:,.2f}"


def public_text(event: Event, place_name: str) -> str:
    """What a bystander would later say they saw. Never touches a Resident."""
    who = event.actor_name
    them = event.target_name or "someone"
    kind = event.kind
    if kind == "changed":
        return event.detail
    if kind == "contact":
        return f"{who} was at the counter at {place_name}, sorting something out."
    if kind == "contact_failed":
        return f"{who} was at the counter at {place_name} and got nowhere."
    if kind == "arrive":
        return f"{who} came into {place_name}."
    if kind == "depart":
        return f"{who} left {place_name}."
    if kind == "work_start":
        return f"{who} started a shift at {place_name}."
    if kind == "work_end":
        return f"{who} finished their shift at {place_name}."
    if kind == "eat":
        return f"{who} ate {event.detail or 'something'}."
    if kind == "buy":
        price = f" for {money(event.amount)}" if event.amount else ""
        return f"{who} bought {event.detail or 'something'}{price}."
    if kind == "buy_fail":
        return f"{who} counted out their cash and put {event.detail or 'it'} back."
    if kind in ("refused", "thought_better"):
        return f"{who} stood there a moment and did nothing."
    if kind == "sleep":
        return f"{who} turned in."
    if kind == "wake":
        return f"{who} got up."
    if kind == "woken":
        return f"{who} was woken up by {them}."
    if kind == "wait":
        return f"{who} was at {place_name}."
    if kind == "other":
        return f"{who} is {event.detail}".rstrip(".") + "."
    if kind == "talk_missed":
        return f"{who} looked around for {them}, who had already gone."
    if kind == "talk_declined":
        return f"{who} went to say something to {them} and thought better of it."
    if kind == "talk_deferred":
        return f"{who} caught {them}'s eye and let it keep."
    if kind == "conversation":
        return event.detail or f"{who} and {them} talked."
    if kind in ("text_sent", "text_received"):
        return f"{who} looked at their phone."
    if kind == "rent_paid":
        return f"{who} handed {them} the rent."
    if kind == "rent_missed":
        return f"{who} told {them}, out loud, that the rent wasn't coming this week."
    if kind == "date":
        return f"{who} had something on their mind today."
    if kind == "gift":
        return f"{who} bought {them} {event.detail or 'something'}."
    if kind == "given":
        return f"{who} handed {them} some cash."
    if kind == "promise":
        return f"{who} told {them} they would: {event.detail}."
    if kind == "promise_kept":
        return f"{who} did what they told {them} they would."
    if kind == "promise_broken":
        return f"{who} did not do what they told {them} they would."
    if kind == "number":
        return f"{who} gave {them} their number."
    if kind == "invite":
        return f"{who} asked {them} to {event.detail}."
    if kind == "accept":
        return f"{them} and {who} arranged to meet at {event.detail}."
    if kind == "introduced":
        return f"{who} introduced {them} to {event.detail}."
    if kind == "together":
        return f"{who} and {them} {event.detail or 'sat together'} at {place_name}."
    if kind == "stood_up":
        return f"{who} waited at {place_name}."
    if kind == "hired":
        return f"{who} took {them} on at {place_name}."
    if kind == "fired":
        return f"{who} let {them} go."
    if kind == "quit":
        return f"{who} told {them} they were done at {place_name}."
    if kind == "loan":
        # Cash changing hands is a thing you see. How much is not.
        return f"{who} handed {them} some cash."
    if kind == "repay":
        return f"{who} paid {them} something back."
    if kind == "leave_town":
        return f"{who} left town with a bag."
    return f"{who} {kind.replace('_', ' ')}."


def private_text(event: Event, resident: "Resident", place_name: str) -> str:
    """The actor's own memory: may use their private state."""
    kind = event.kind
    them = event.target_name or "them"
    if kind == "noticed":
        return f"I noticed, at {place_name}: {event.detail}"
    if kind in ("contact", "contact_failed", "credit", "service_promise_kept", "service_promise_broken"):
        return event.detail
    if kind == "changed":
        return event.detail
    if kind == "arrive":
        return f"I walked into {place_name}."
    if kind == "depart":
        return f"I left {place_name}."
    if kind == "work_start":
        return f"I started my shift at {place_name}."
    if kind == "work_end":
        return f"I finished my shift at {place_name}."
    if kind == "eat":
        return f"I ate {event.detail or 'something'}."
    if kind == "buy":
        return (f"I bought {event.detail or 'something'} for {money(event.amount)}. "
                f"That leaves me {money(resident.money)}.")
    if kind == "buy_fail":
        return (f"I couldn't cover {event.detail or 'it'}: {money(event.amount)}, "
                f"and I have {money(resident.money)}.")
    if kind == "refused":
        return f"I couldn't: {event.detail}."
    if kind == "thought_better":
        return f"I meant to, and didn't: {event.detail}."
    if kind == "sleep":
        return "I went to bed."
    if kind == "wake":
        return "I got up."
    if kind == "woken":
        return f"{them} woke me up."
    if kind == "wait":
        return f"I stayed at {place_name}."
    if kind == "other":
        return f"I'm {event.detail}".rstrip(".") + "."
    if kind == "talk_missed":
        return f"I went to talk to {them} and they'd already gone."
    if kind == "talk_declined":
        return f"I meant to talk to {them} but the moment passed."
    if kind == "talk_deferred":
        return f"I meant to say something to {them}; it can keep till the next chance."
    if kind == "wage":
        return f"I got paid {money(event.amount)} for the shift."
    if kind == "rent_paid":
        return (f"Rent: {money(event.amount)} to {them}. Paid. "
                f"That leaves me {money(resident.money)}.")
    if kind == "rent_missed":
        return (f"Rent came due, {money(event.amount)} to {them}, and I haven't got it. "
                f"I have {money(resident.money)}.")
    if kind == "text_sent":
        return f'I texted {them}: "{event.spoken or event.detail}"'
    if kind == "date":
        return event.detail
    if kind == "gift":
        return f"I bought {them} {event.detail or 'something'}."
    if kind == "given":
        return f"I gave {them} {money(event.amount)}."
    if kind == "promise":
        return f"I told {them} I would: {event.detail}."
    if kind == "promise_kept":
        return f"I said I would and I did. {them} knows it."
    if kind == "promise_broken":
        return f"I told {them} I would, and I did not."
    if kind == "number":
        return f"I gave {them} my number."
    if kind == "invite":
        return f"I asked {them} to {event.detail}."
    if kind == "accept":
        return f"I said yes to {them}. {event.detail}."
    if kind == "introduced":
        return f"I introduced {them} to {event.detail or 'somebody'}."
    if kind == "together":
        return f"I spent {event.detail or 'a while'} with {them} at {place_name}."
    if kind == "stood_up":
        return f"I waited at {place_name}. {them} did not come."
    if kind == "need_urgent":
        return event.detail
    if kind == "conversation":
        return event.detail or f"I talked with {them}."
    if kind == "hired":
        return f"I took {them} on. {event.detail}".rstrip() + ("" if event.detail.endswith(".") else ".")
    if kind == "fired":
        return f"I let {them} go."
    if kind == "quit":
        return f"I told {them} I was done. No more {event.detail or 'shifts'}."
    if kind == "no_show":
        return f"I didn't make my shift at {place_name}."
    if kind == "loan":
        return f"I lent {them} {money(event.amount)}. {event.detail}".rstrip()
    if kind == "repay":
        return f"I paid {them} {money(event.amount)} back. {event.detail}".rstrip()
    if kind == "debt_overdue":
        return f"I owe {them} {money(event.amount)} and the day's gone."
    if kind == "leave_town":
        return f"I left town. {event.detail}".rstrip()
    return public_text(event, place_name)


def target_text(event: Event, resident: "Resident", place_name: str) -> str:
    """The other half of a two-person moment, in their own first person."""
    kind = event.kind
    who = event.actor_name
    if kind == "hired":
        return f"{who} took me on at {place_name}. {event.detail}".rstrip()
    if kind == "fired":
        return f"{who} let me go."
    if kind == "quit":
        return f"{who} told me they were done. That is a {event.detail or 'shift'} to fill."
    if kind == "loan":
        return f"{who} lent me {money(event.amount)}. {event.detail}".rstrip()
    if kind == "repay":
        return f"{who} paid me {money(event.amount)} back."
    if kind == "gift":
        return f"{who} bought me {event.detail or 'something'}."
    if kind == "given":
        return f"{who} gave me {money(event.amount)}."
    if kind == "promise":
        return f"{who} told me they would: {event.detail}."
    if kind == "promise_kept":
        return f"{who} said they would, and they did."
    if kind == "promise_broken":
        return f"{who} told me they would, and did not."
    if kind == "number":
        return f"{who} gave me their number."
    if kind == "invite":
        return f"{who} asked me to {event.detail}."
    if kind == "accept":
        return f"{who} said yes. {event.detail}."
    if kind == "introduced":
        return f"{who} introduced me to {event.detail or 'somebody'}."
    if kind == "text_received":
        return f'{who} texted me: "{event.spoken or event.detail}"'
    return public_text(event, place_name)


# -- names ------------------------------------------------------------------------


class NameIndex:
    """Finds which residents a piece of text names, in one regex pass.

    Full names and first names of three letters or more. Rebuilt when the
    population changes (an arrival, a departure); `version` lets a holder know.
    """

    def __init__(self, people: Iterable[tuple[str, str]] = ()):
        self.version = 0
        self.rebuild(people)

    def rebuild(self, people: Iterable[tuple[str, str]]) -> None:
        self.full: dict[str, str] = {}
        self.first: dict[str, set[str]] = {}
        for rid, name in people:
            if not name:
                continue
            self.full[name] = rid
            first = name.split()[0]
            if len(first) >= 3:
                self.first.setdefault(first, set()).add(rid)
        tokens = sorted(set(self.full) | set(self.first), key=len, reverse=True)
        self._pattern = (
            re.compile(r"\b(?:" + "|".join(re.escape(t) for t in tokens) + r")\b")
            if tokens else None
        )
        self.version += 1

    def find(self, text: str) -> set[str]:
        """Ids of everybody named in the text, as whole words.

        A full name names one person; a bare first name names everybody who
        has it, since the text cannot say which of them was meant.
        """
        if not text or self._pattern is None:
            return set()
        out: set[str] = set()
        for token in self._pattern.findall(text):
            if token in self.full:
                out.add(self.full[token])
            out |= self.first.get(token, set())
        return out


def _swap_name(text: str, name: str, label: str) -> str:
    if not name:
        return text
    out = re.sub(rf"\b{re.escape(name)}\b", label, text)
    first = name.split()[0]
    if len(first) >= 3:
        out = re.sub(rf"\b{re.escape(first)}\b", label, out)
    if out.startswith(label) and label[:1].islower():
        out = label[:1].upper() + out[1:]
    return out


def as_seen_by(text: str, viewer: "Resident | None", town) -> str:
    """Rewrite every name in this text that the viewer has not been given.

    Somebody the viewer has never been told the name of reads as a description
    ("a tall man from the factory"). A person the viewer does know, who shares
    a first name with one they do not, is shielded so the bare-first-name swap
    cannot half-rename them into somebody who does not exist.
    """
    if viewer is None or not text:
        return text
    residents = town.residents
    mentioned = town.names.find(text)
    unknown = [residents[rid] for rid in sorted(mentioned)
               if rid in residents and rid != viewer.id and not viewer.knows_name(rid)]
    if not unknown:
        return text
    unknown_ids = {o.id for o in unknown}
    unknown_firsts = {o.first_name.lower() for o in unknown}
    shields: dict[str, str] = {}
    for rid in sorted(mentioned):
        other = residents.get(rid)
        if other is None or rid in unknown_ids or other.first_name.lower() not in unknown_firsts:
            continue
        if other.name not in text:
            continue
        token = f"\x00{len(shields)}\x00"
        shields[token] = other.name
        text = re.sub(rf"\b{re.escape(other.name)}\b", token, text)
    for other in sorted(unknown, key=lambda o: -len(o.name)):
        text = _swap_name(text, other.name, descriptor_for(other))
    for token, real in shields.items():
        text = text.replace(token, real)
    return text


def descriptor_for(resident: "Resident") -> str:
    """What somebody who has never been told their name would call them."""
    described = (resident.persona or {}).get("descriptor")
    if described:
        return str(described)
    age = int(resident.age or 0)
    band = "an older one" if age >= 60 else ("a young one" if age <= 23 else "somebody")
    return f"{band} from around here"


def known_as(resident: "Resident", viewer: "Resident | None") -> str:
    """The name this viewer may put to this person, or a description."""
    if viewer is None or viewer.knows_name(resident.id):
        return resident.name
    return descriptor_for(resident)


def leak_check(text: str, secrets: dict[str, str]) -> list[str]:
    """Ids of residents whose secret text appears in `text`.

    Verbatim from Alive: compared on runs of three distinctive words, because a
    secret leaks in fragments and paraphrase, not whole sentences.
    """
    def distinctive(s: str) -> list[str]:
        cleaned = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in s.lower())
        return [w for w in cleaned.split() if len(w) > 4]

    hits = []
    haystack = " ".join(distinctive(text or ""))
    for rid, secret in sorted(secrets.items()):
        if not secret:
            continue
        words = distinctive(secret)
        for i in range(len(words) - 2):
            if " ".join(words[i : i + 3]) in haystack:
                hits.append(rid)
                break
    return hits
