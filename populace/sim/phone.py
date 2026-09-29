"""The phone: texts between people who hold each other's numbers.

Ported from Alive's `phone.py`, with one thing added: residents can **start** a
text (the `contact` action). In Alive they could only reply.

A text is words and nothing more: no money, no job, no favour moves by text,
and nothing arranged by text has happened until it happens in person. The
sender must hold the recipient's number; there is no directory. Both people
remember it, and the names in those memories go through the funnel (Alive
wrote raw names here). Replies are one call, capped per day, and never
interrupt the day: somebody texted while working carries on working.

A text to a service goes to the agents layer (step 4) when one is registered.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..prompt.blocks import CACHE_CONTROL, character_block, shared_block
from ..state.resident import Resident
from .actions import extract_json
from .events import known_as
from .memory import ObservationContext, retrieve

if TYPE_CHECKING:  # pragma: no cover
    from ..state.town import Town
    from .engine import Engine

TEXT_INSTRUCTIONS = """\
Reply the way you would actually text: short, in your own voice, under
twenty-five words. Or do not reply at all, which is a real answer and a common
one - {"reply": null} if you have nothing to say, or you are busy, or you would
rather deal with them face to face.

A text is words. You cannot hand over money, a job or a favour by text, and
nothing arranged by text has happened until it happens in person. If something
needs doing, say when and where.

Reply with one JSON object and nothing else:
{"reply": "what you send back, or null", "importance": 1-10}"""


class PhoneError(Exception):
    pass


def exchange_numbers(a: Resident, b: Resident) -> None:
    a.phone.setdefault("contacts", {})[b.id] = b.phone.get("number", "")
    b.phone.setdefault("contacts", {})[a.id] = a.phone.get("number", "")


def has_number(resident: Resident, other_id: str) -> bool:
    return other_id in (resident.phone.get("contacts") or {})


def thread(resident: Resident, other_id: str) -> list[dict[str, Any]]:
    return list((resident.phone.get("threads") or {}).get(other_id) or [])


def unread(resident: Resident) -> list[tuple[str, dict[str, Any]]]:
    out = []
    for other_id, messages in sorted((resident.phone.get("threads") or {}).items()):
        for m in messages:
            if m.get("from") != resident.id and not m.get("read"):
                out.append((other_id, m))
    return out


def mark_read(resident: Resident, other_id: str | None = None) -> None:
    for oid, messages in (resident.phone.get("threads") or {}).items():
        if other_id is None or oid == other_id:
            for m in messages:
                if m.get("from") != resident.id:
                    m["read"] = True


def send_text(town: "Town", sender_id: str, to_id: str, text: str, max_chars: int = 240) -> dict[str, Any]:
    body = str(text or "").strip()[:max_chars]
    if not body:
        raise PhoneError("a text with no words in it")
    sender = town.residents.get(sender_id)
    recipient = town.residents.get(to_id)
    if sender is None or recipient is None:
        raise PhoneError("there is nobody at that number")
    if not has_number(sender, to_id):
        raise PhoneError(f"I have not got {known_as(recipient, sender)}'s number")
    time = town.world.time
    message = {"from": sender_id, "to": to_id, "text": body, "day": time.day, "tick": time.tick,
               "read": False}
    sender.phone.setdefault("threads", {}).setdefault(to_id, []).append({**message, "read": True})
    recipient.phone.setdefault("threads", {}).setdefault(sender_id, []).append(message)
    if sender_id not in recipient.phone.get("contacts", {}):
        # Their number is on your phone now, whether or not you saved it.
        recipient.phone.setdefault("contacts", {})[sender_id] = sender.phone.get("number", "")
    sender.remember(time, f'I texted {known_as(recipient, sender)}: "{body}"', kind="dialogue",
                    importance=3, involved=[to_id], location_id=town.world.location_of(sender_id))
    recipient.remember(time, f'{known_as(sender, recipient)} texted: "{body}"', kind="dialogue",
                       importance=4, involved=[sender_id], location_id=town.world.location_of(to_id))
    town.touch(sender_id)
    town.touch(to_id)
    return message


def build_prompt(resident: Resident, other_id: str, town: "Town") -> str:
    other = town.residents.get(other_id)
    their_name = known_as(other, resident) if other else "somebody"
    ctx = ObservationContext(location_id=town.world.location_of(resident.id),
                             present_ids=[other_id] if other else [],
                             keywords=[m.get("text", "") for m in thread(resident, other_id)[-3:]])
    memories = retrieve(resident, ctx, cap=6, now_ticks=town.world.time.total_ticks,
                        weights=town.config.memory)
    recalled = "\n".join(f"  [{m.stamp()}] {m.text}" for m in memories)
    lines = "\n".join(f'  {"You" if m.get("from") == resident.id else their_name}: "{m.get("text", "")}"'
                      for m in thread(resident, other_id)[-8:])
    where = town.world.places[town.world.location_of(resident.id)].name
    return f"""\
YOUR PHONE

{town.world.time.label()}. You are at {where}, and your phone has gone.

The thread with {their_name}:
{lines or '  (nothing yet)'}

What you have about them and about this:
{recalled or '  nothing in particular'}

{TEXT_INSTRUCTIONS}"""


def can_reply(other_id: str, carry: dict[str, Any], day: int, cfg: dict[str, Any]) -> bool:
    counts = (carry.get("phone_replies") or {}).get(str(day), {})
    if sum(counts.values()) >= int(cfg["reply_cap_per_day"]):
        return False
    return counts.get(other_id, 0) < int(cfg["reply_cap_per_person_per_day"])


def note_reply(other_id: str, carry: dict[str, Any], day: int) -> None:
    replies = carry.setdefault("phone_replies", {})
    counts = replies.setdefault(str(day), {})
    counts[other_id] = counts.get(other_id, 0) + 1
    for key in [k for k in replies if k != str(day)]:
        replies.pop(key)


async def reply_turn(engine: "Engine", resident: Resident) -> dict[str, Any] | None:
    """One call, one short answer or none. Not a conversation."""
    town = engine.town
    waiting = unread(resident)
    if not waiting:
        return None
    other_id = waiting[0][0]
    day = town.world.time.day
    carry = engine.phone_carry
    if not can_reply(other_id, carry, day, town.config.phone) or other_id not in town.residents:
        mark_read(resident, other_id)
        return None
    system = [{"type": "text", "text": shared_block(town), "cache_control": CACHE_CONTROL},
              {"type": "text", "text": character_block(resident, town), "cache_control": CACHE_CONTROL}]
    response = await engine.runner.call(
        "dialogue", system, [{"role": "user", "content": build_prompt(resident, other_id, town)}],
        {"char_id": resident.id, "day": day, "tick": town.world.time.tick, "sub_idx": 100,
         "mock_state": {"text": True, "sentiment": resident.sentiment(other_id)}})
    mark_read(resident, other_id)
    note_reply(other_id, carry, day)
    payload = extract_json(response.text) if response.ok else None
    reply = str((payload or {}).get("reply") or "").strip()
    if not reply:
        return None  # silence is a real answer, and the texts are read
    engine.report.texts += 1
    return send_text(town, resident.id, other_id, reply, int(town.config.phone["max_text_chars"]))


async def send_texts(engine: "Engine") -> None:
    """The `contact` action: a text to somebody whose number you hold, or to a
    registered service (step 4). Capped per day; every failure said."""
    town = engine.town
    cap = int(town.config.phone["send_cap_per_day"])
    day = town.world.time.day
    for rid, act in engine.texts:
        r = town.residents[rid]
        sent = engine.phone_carry.setdefault("sent", {}).setdefault(str(day), {})
        if sent.get(rid, 0) >= cap:
            engine._refuse(r, act, "I had already texted enough people today")
            continue
        if act.target in town.services:
            handler = getattr(engine, "contact_service", None)
            if handler is None:
                engine._refuse(r, act, f"nobody answered at {act.target}")
            else:
                await handler(engine, r, act)
            sent[rid] = sent.get(rid, 0) + 1
            continue
        try:
            send_text(town, rid, act.target or "", act.dialogue or "", int(town.config.phone["max_text_chars"]))
        except PhoneError as exc:
            engine._refuse(r, act, str(exc))
            continue
        sent[rid] = sent.get(rid, 0) + 1
        engine.emit(engine.event("text_sent", r, target=act.target, spoken=act.dialogue))
        engine.report.texts += 1
