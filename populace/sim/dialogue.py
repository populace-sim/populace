"""Conversations: one speaker per call, one line per call.

Ported from Alive's `dialogue.py`. Each line is written by a call that sees
only the speaker's own blocks, their own memories and the words said aloud, so
nobody can be handed the other person's secret. Kept from Alive: the closing
line, the questions-already-asked note, spent touchstones, lines already said
today, what the speaker actually knows about anybody named who is not here, the
guard that catches a claimed sighting the speaker does not have, the note that
makes an answer to an offer or an invitation compulsory, commitments turned
into promises, names learned only when said aloud, and trust from talking.

Left behind: the player branch, the clinic and bar hooks, and the second-call
commitment judge (a call a real budget cannot spare; `looks_like_a_commitment`
is logged instead).

The number of lines a conversation may buy is set by the scheduler per tick.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .. import words as W
from ..prompt import profiles
from ..prompt.blocks import CACHE_CONTROL, character_block, needs_line, shared_block
from ..state.resident import Relationship, Resident
from .actions import extract_json
from .events import as_seen_by, known_as
from .memory import ObservationContext, retrieve

if TYPE_CHECKING:  # pragma: no cover
    from ..state.town import Town
    from .engine import Engine

_INSTRUCTIONS = """\
YOU ARE IN A CONVERSATION

Somebody is talking with you. Reply with one line - what you actually say out
loud, in your own voice. Keep it short: people speak in fragments, not
paragraphs. Under thirty words.

You do not have to be helpful, forthcoming, or pleasant. You can deflect, change
the subject, answer a different question, or end it. If they are asking about
something you would rather not discuss, behave like someone who would rather not
discuss it.

Do not invent things about people who are not here. Do not report what somebody
else said, saw, or thinks unless it is in your memories above - and if it is,
say who told you. Making up "so-and-so has been saying X" is the one move that
breaks this whole town, because the other person will believe it and carry it
for days.

Set `end_conversation` to true when this has run its course - which is usually
after two or three lines each. Conversations here are short and most of them
settle nothing.

Do not repeat a phrase you have already used today - people vary how they say
things, and saying the same sentence twice in one day reads as malfunction.

Reply with one JSON object and nothing else:
{"line": "what you say out loud",
 "end_conversation": true or false,
 "importance": 1-10, how much this exchange will stay with you,
 "gist": only when ending - at most a dozen words on what this was about,
 "outcome": only when ending - what was settled or left hanging, a few words,
 "settles": only if this conversation finished off one of the things you were
 trying to do - repeat that goal's wording here, else null,
 "deal": null, or - only when this line of yours is what makes it so, and you
 have the standing for it - one of the objects listed under WHAT YOU CAN MAKE
 HAPPEN in your rules. Say it in the line as well: the line is what they hear,
 the deal is the bookkeeping under it. One you have no standing for simply does
 not happen, and you are left having promised what you cannot give.,
 "commitments": ALWAYS present. [] on nearly every line. When THIS line of
 yours commits you to doing a particular thing by a particular day - "I'll
 have your forty on Tuesday", "I'll come and look at it tomorrow" - put it here
 as [{"what": "pay back the forty", "by_when": 2, "to": "their id"}], where
 by_when is how many days from today. A promise nobody wrote down is not a
 promise: they will hold you to this, and so will you. Vague warmth is not a
 commitment - "I'll see what I can do" is [], and so is "I'll be honest with
 you".}"""

CLOSING_LINE = """\
This is the last thing you will say in this exchange. Make it a closing line -
you have somewhere to be, or you have said what you came to say - and set
`end_conversation` to true."""

HEAVY_TALK = 7
COMMITMENT_CUES = ("i'll", "i will", "i'm going to", "promise", "by friday", "by monday",
                   "by tuesday", "by wednesday", "by thursday", "by saturday", "by sunday",
                   "by tomorrow", "tomorrow", "you'll have")
MAX_COMMITMENT_DAYS = 14
_RECENCY_MARKERS = (
    "earlier", "this morning", "this afternoon", "this evening", "just now",
    "a minute ago", "an hour ago", "an hour back", "hour back", "came through",
    "came in", "came by", "was in", "been in", "just missed", "was here",
    "half hour", "few minutes", "saw her", "saw him", "saw them", "in and out",
)
_PLAIN = {"that", "this", "then", "them", "they", "what", "when", "with", "your", "youre",
          "here", "there", "just", "well", "have", "been", "will", "would", "about", "like",
          "know", "dont", "cant", "isnt", "yeah", "okay", "right", "thing", "things", "much",
          "some", "come", "going", "tell", "said"}


@dataclass
class ConversationResult:
    initiator: str
    target: str
    location_id: str
    lines: list[dict[str, str]] = field(default_factory=list)
    ended_by: str = "cap"
    gist: str = ""
    outcome: str = ""
    settles_by: dict[str, str] = field(default_factory=dict)
    importance: int = 4
    importance_by: dict[str, int] = field(default_factory=dict)
    calls: int = 0
    retries: int = 0
    deals: list[dict[str, Any]] = field(default_factory=list)
    unwritten_commitments: int = 0

    def transcript(self, names: dict[str, str], limit: int | None = None) -> str:
        lines = self.lines[-limit:] if limit else self.lines
        return "\n".join(f'{names.get(l["speaker"], l["speaker"])}: "{l["text"]}"' for l in lines)

    def to_dict(self, day: int, tick: int) -> dict[str, Any]:
        return {"day": day, "tick": tick, "location_id": self.location_id,
                "participants": [self.initiator, self.target], "initiator": self.initiator,
                "lines": self.lines, "ended_by": self.ended_by, "gist": self.gist,
                "outcome": self.outcome, "importance": self.importance,
                "importance_by": dict(self.importance_by), "calls": self.calls,
                "unwritten_commitments": self.unwritten_commitments}


# -- what goes in front of the speaker --------------------------------------------------


def _mentioned_elsewhere(speaker: Resident, town: "Town", result: ConversationResult,
                         exclude: set[str]) -> str:
    """Everything the speaker actually has on anybody just named who is not here.
    Silence about a third party is an invitation to invent one."""
    said = " ".join(line["text"] for line in result.lines[-3:])
    lines = []
    for rid in sorted(town.names.find(said) - exclude):
        other = town.residents[rid]
        about = [m for m in speaker.memory if rid in m.involved]
        name = known_as(other, speaker)
        if not about:
            lines.append(f"  {name}: you know nothing about them beyond their face.")
            continue
        latest = max(about, key=lambda m: (m.total_ticks, m.id))
        when = "today" if latest.day == town.world.time.day else f"on day {latest.day}"
        lines.append(f"  {name}: the last of them you have is {when}, [{latest.stamp()}] {latest.text[:160]}")
    if not lines:
        return ""
    return "\nSomebody not here has been mentioned. This is everything you have on them:\n" + "\n".join(lines) + "\n"


def _already_covered(speaker: Resident, other: Resident, town: "Town") -> str:
    lines = [f"  - {t['topic']} -> {t['outcome']}" for t in speaker.todays_threads(town.world.time.day)
             if t.get("other") == other.id]
    if not lines:
        return ""
    return ("\nYou two already talked today:\n" + "\n".join(lines[-4:]) +
            "\nThat ground is covered. Do not go over it again unless something new "
            "has happened since - talk about something else, or keep it brief.\n")


def _questions_asked(speaker: Resident, result: ConversationResult) -> str:
    asked = [l["text"] for l in result.lines if l["speaker"] == speaker.id and "?" in l["text"]]
    if not asked:
        return ""
    return ("\nQuestions you have ALREADY ASKED them in this conversation. Do not\n"
            "ask any of these again, in any wording:\n" + "\n".join(f'  "{q}"' for q in asked[-6:]) +
            "\nOne question per line, at most. A reply that is two questions is an\n"
            "interrogation, not a conversation.\n")


def _distinctive(phrase: str) -> set[str]:
    cleaned = "".join(c if c.isalnum() or c.isspace() else " " for c in phrase.lower())
    return {w for w in cleaned.split() if len(w) >= 4 and w not in _PLAIN}


def _signature_note(speaker: Resident, result: ConversationResult) -> str:
    phrases = speaker.persona.get("signature_phrases") or []
    mine = [l["text"] for l in result.lines if l["speaker"] == speaker.id]
    if not phrases or not mine:
        return ""

    def used_in(text: str) -> list[str]:
        return [p for p in phrases if W.contains(text, [p]) or (_distinctive(p) & _distinctive(text))]

    spent = sorted({p for line in mine for p in used_in(line)})
    if not spent:
        return ""
    note = ("\nTouchstones you have ALREADY used in this exchange. A phrase that turns up "
            "in every line is not a signature, it is a tic - do not use these again here, "
            "or the words in them:\n" + "\n".join(f'  "{p}"' for p in spent) + "\n")
    if used_in(mine[-1]):
        note += "Your last line already had one in it. This line has none of them, in any form.\n"
    return note


def _own_lines_today(spoken: list[str] | None) -> str:
    if not spoken:
        return ""
    return ("\nLines you have already said today - do not reuse their phrasing:\n"
            + "\n".join(f'  "{line}"' for line in spoken[-10:]) + "\n")


def pending_note(pending: dict | None) -> str:
    """What is on the table for the speaker, and that answering it in words is
    not answering it. In Alive an offer of coffee was accepted in words and no
    money moved; a social deal did not read like a deal to the model."""
    if not pending:
        return ""
    if pending.get("settled"):
        return (f"\nALREADY SETTLED, BY YOU, IN THIS EXCHANGE\n\n{pending['settled']}\n\n"
                "That is done. Do not take it again and do not go back on it here.\n")
    return f"""
ON THE TABLE RIGHT NOW

{pending['what']}

Your reply MUST carry a "deal" this time. Not optional:

  {{"kind": "{pending['kind']}", "accept": true}}    you are taking it
  {{"kind": "{pending['kind']}", "accept": false}}   you are not

Say whatever you like in the line. But saying yes in words and leaving the deal
out means it did not happen: no money moves, nothing is arranged. Answer in both.
"""


def unsupported_claim(line: str, speaker: Resident, town: "Town", present: set[str],
                      context: str = "") -> str | None:
    """Does this line claim to have seen somebody today whom the speaker has not
    seen? Specific, checkable, false, and the other person carries it for days,
    so it is caught here rather than trusted to instructions."""
    if not W.contains(line, _RECENCY_MARKERS):
        return None
    today = town.world.time.day
    for rid in sorted(town.names.find(f"{context} {line}") - present):
        if any(rid in m.involved and m.day == today for m in speaker.memory):
            continue
        return (f"You have not seen {known_as(town.residents[rid], speaker)} at all today, so you "
                "cannot say when or where they were. Say you don't know, or talk about something else.")
    return None


def speaker_prompt(speaker: Resident, other: Resident, town: "Town", result: ConversationResult,
                   spoken_today: list[str] | None = None, closing: bool = False,
                   pending: dict | None = None) -> str:
    world = town.world
    place = world.places[result.location_id]
    rel = speaker.relationships.get(other.id)
    feeling = f"You feel {rel.sentiment:+d} about them ({rel.label})." if rel else "You barely know them."
    notes = "\n".join(f"  {n}" for n in (rel.notes if rel else []))
    window = int(town.config.dialogue["transcript_window"])
    ctx = ObservationContext(location_id=result.location_id, present_ids=[other.id],
                             keywords=[l["text"] for l in result.lines[-window:]])
    memories = retrieve(speaker, ctx, cap=8, now_ticks=world.time.total_ticks, weights=town.config.memory)
    recalled = "\n".join(f"  [{m.stamp()}] {m.text}" for m in memories)
    names = {result.initiator: known_as(town.residents[result.initiator], speaker),
             result.target: known_as(town.residents[result.target], speaker)}
    instructions = _INSTRUCTIONS + profiles.dialogue_extra(str(town.config.prompt.get("profile") or "frontier"))
    closing_note = f"\n{CLOSING_LINE}\n" if closing else ""
    text = f"""\
You are talking with {known_as(other, speaker)} at {place.name}. {world.time.label()}.
{feeling}
{notes}
What you remember about them and about this:
{recalled or '  nothing in particular'}
{needs_line(speaker, town)}
{_news(speaker, town)}
What has been said so far:
{result.transcript(names, limit=window)}
{_already_covered(speaker, other, town)}{_own_lines_today(spoken_today)}{_mentioned_elsewhere(speaker, town, result, {speaker.id, other.id})}
{instructions}
{_questions_asked(speaker, result)}{_signature_note(speaker, result)}{pending_note(pending)}{closing_note}
You can see everything you have already said in this conversation, above. If
you have already asked them something, you have your answer or you have been
dodged, and asking it again in different words is worse than either - it reads
as not having listened. Ask something else, say something, or let it go.

Last thing: do not supply a detail you do not have. Not where somebody went,
not when they were last in, not what they said. "I couldn't tell you" is always
available and is what a real person says."""
    # The last gate before the words go out, and the only one that catches every
    # way a name can get in.
    return as_seen_by(text, speaker, town)


def _news(speaker: Resident, town: "Town") -> str:
    """What the speaker has at home or has seen lately - the same facts their
    decisions carry. Retrieval alone lost them by the afternoon, and on the
    PC's 32B day nothing injected was passed on in conversation."""
    from ..inject.apply import what_changed
    lines = what_changed(town, speaker)
    if not lines:
        return ""
    return "What's new with you today, yours to mention or not:\n" + "\n".join(f"  {l}" for l in lines) + "\n"


def looks_like_a_commitment(line: str) -> bool:
    return W.contains(line, COMMITMENT_CUES)


def validate_commitments(raw, speaker_id: str, other_id: str, everyone) -> list[dict]:
    """Keep the ones that are a thing by a day. `to` is advisory, checked only
    for naming a different real person: nobody promises somebody else's errand."""
    out: list[dict] = []
    if not isinstance(raw, list):
        return out
    for entry in raw[:3]:
        if not isinstance(entry, dict):
            continue
        what = str(entry.get("what") or "").strip()[:120]
        try:
            days = int(entry.get("by_when"))
        except (TypeError, ValueError):
            continue
        if not what or not 1 <= days <= MAX_COMMITMENT_DAYS:
            continue
        to = str(entry.get("to") or "").strip()
        if to and to != other_id and to in everyone:
            continue
        out.append({"what": what, "in_days": days})
    return out


def dialogue_mock_state(speaker: Resident, other: Resident, town: "Town", result: ConversationResult,
                        line_no: int, max_lines: int, pending: dict | None,
                        other_ask: dict | None = None) -> dict[str, Any]:
    hires_here = [pid for pid, p in town.world.places.items() if speaker.id in p.hires
                  and any(int(o.get("slots", 1)) > len(o.get("filled_by", [])) for o in p.openings)]
    asked_job = any("job" in l["text"].lower() or "work" in l["text"].lower()
                    for l in result.lines if l["speaker"] == other.id)
    return {"line_no": line_no, "max_lines": max_lines, "other_name": known_as(other, speaker),
            "sentiment": speaker.sentiment(other.id), "pending": (pending or {}).get("kind"),
            "settled": bool((pending or {}).get("settled")), "can_hire": bool(hires_here),
            "other_asked_job": asked_job, "other_has_job": other.job is not None,
            "owed_by_other": speaker.owed_by(other.id), "money": speaker.money,
            "trust_stage": speaker.trust_stage(other.id, tuple(town.config.trust["thresholds"])),
            "other_ask": other_ask or {}, "other_id": other.id,
            "owes_other": speaker.owes_to(other.id),
            "other_just_lent": any(d["speaker"] == other.id and (d.get("deal") or {}).get("kind") == "loan"
                                   for d in result.deals),
            "is_their_boss": bool(other.job and other.job.employer_id == speaker.id),
            "is_my_boss": bool(speaker.job and speaker.job.employer_id == other.id),
            "other_no_shows": other.job.no_shows if other.job else 0,
            "arc_stage": (speaker.arc or {}).get("stage"),
            "places": [p for p in speaker.places_known if town.world.places[p].public][:4],
            # The latest thing the speaker saw posted or change, so the mock
            # can pass news on the way a live speaker might.
            "news": next((n["text"] for n in sorted(town.world.notices,
                                                   key=lambda n: -n["seen_by"].get(speaker.id, -1))
                          if speaker.id in n["seen_by"]), None),
            "problems": [p.get("text") for p in speaker.problems if not p.get("resolved")]}


async def run_conversation(town: "Town", runner, initiator_id: str, target_id: str,
                           opening_line: str, max_lines: int,
                           spoken_today: dict[str, list[str]] | None = None,
                           pending: dict[str, dict] | None = None,
                           asks: dict[str, dict] | None = None) -> ConversationResult:
    """Run the exchange. The opening line is free: it came with the decision."""
    world = town.world
    result = ConversationResult(initiator=initiator_id, target=target_id,
                                location_id=world.location_of(initiator_id),
                                lines=[{"speaker": initiator_id, "text": opening_line}])
    speaker_id, other_id = target_id, initiator_id
    system_for: dict[str, list[dict]] = {}
    for line_no in range(2, max_lines + 1):
        speaker = town.residents[speaker_id]
        other = town.residents[other_id]
        if speaker_id not in system_for:
            system_for[speaker_id] = [
                {"type": "text", "text": shared_block(town), "cache_control": CACHE_CONTROL},
                {"type": "text", "text": character_block(speaker, town), "cache_control": CACHE_CONTROL},
            ]
        system = system_for[speaker_id]
        closing = line_no == max_lines
        prompt = speaker_prompt(speaker, other, town, result, (spoken_today or {}).get(speaker_id, []),
                                closing, (pending or {}).get(speaker_id))
        meta = {"char_id": speaker_id, "day": world.time.day, "tick": world.time.tick,
                "sub_idx": line_no, "mock_state": dialogue_mock_state(
                    speaker, other, town, result, line_no, max_lines, (pending or {}).get(speaker_id),
                    {k: v for k, v in ((asks or {}).get(other_id) or {}).items()
                     if ((asks or {}).get(other_id) or {}).get("to") == speaker_id})}
        response = await runner.call("dialogue", system, [{"role": "user", "content": prompt}], meta)
        result.calls += 1
        payload = extract_json(response.text) if response.ok else None
        if not payload or not str(payload.get("line") or "").strip():
            response = await runner.call("dialogue", system, [{"role": "user", "content": prompt}],
                                         {**meta, "attempt": 2})
            result.calls += 1
            result.retries += 1
            payload = extract_json(response.text) if response.ok else None
            if not payload or not str(payload.get("line") or "").strip():
                result.ended_by = "no_reply"
                break
        text = str(payload["line"]).strip()[:400]
        present = {speaker_id, other_id}
        context = " ".join(l["text"] for l in result.lines[-2:])
        problem = unsupported_claim(text, speaker, town, present, context)
        if problem:
            retry = await runner.call("dialogue", system, [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": response.text or text},
                {"role": "user", "content": f"No. {problem}\n\nThat line claimed a sighting you do not "
                                            "have. Say the same thing without it. Reply with the JSON object only."},
            ], {**meta, "attempt": 2})
            result.calls += 1
            result.retries += 1
            retried = extract_json(retry.text) if retry.ok else None
            candidate = str((retried or {}).get("line") or "").strip()[:400]
            if candidate and not unsupported_claim(candidate, speaker, town, present, context):
                text, payload = candidate, retried
            else:
                text = "I couldn't tell you."
                payload = {"line": text, "end_conversation": True, "importance": 2}
        result.lines.append({"speaker": speaker_id, "text": text})
        try:
            importance = int(payload.get("importance") or 0)
        except (TypeError, ValueError):
            importance = 0
        result.importance_by[speaker_id] = max(result.importance_by.get(speaker_id, 0), importance)
        result.importance = max(result.importance, importance)
        if isinstance(payload.get("deal"), dict):
            result.deals.append({"speaker": speaker_id, "line_no": line_no, "deal": dict(payload["deal"])})
            if pending and speaker_id in pending and not pending[speaker_id].get("settled"):
                answered = pending[speaker_id]
                took = payload["deal"].get("accept") is not False
                pending[speaker_id] = {"settled": ("You already said yes: " if took else
                                                   "You already said no: ") + answered["what"]}
        promised = validate_commitments(payload.get("commitments"), speaker_id, other_id, town.residents)
        if not promised and looks_like_a_commitment(text):
            result.unwritten_commitments += 1
        for entry in promised:
            result.deals.append({"speaker": speaker_id, "line_no": line_no,
                                 "deal": {"kind": "promise", "by": "me", **entry}})
        if payload.get("gist"):
            result.gist = str(payload["gist"])[:120]
        if payload.get("outcome"):
            result.outcome = str(payload["outcome"])[:120]
        if payload.get("settles"):
            result.settles_by[speaker_id] = str(payload["settles"])[:200]
        if payload.get("end_conversation"):
            result.ended_by = "both_done"
            break
        speaker_id, other_id = other_id, speaker_id
    else:
        result.ended_by = "cap"
    result.importance = max(3, min(10, result.importance))
    if not result.gist:
        result.gist = opening_line[:80]
    return result


# -- after the talking -----------------------------------------------------------------


def names_said(text: str, town: "Town", by_speaker: Resident) -> list[str]:
    """Whose names were said out loud in this line, of the names the speaker
    holds: nobody can hand over a name they have not got."""
    return sorted(rid for rid in town.names.find(text)
                  if rid == by_speaker.id or by_speaker.knows_name(rid))


def learn_names_said(result: ConversationResult, town: "Town", heard_by: list[str]) -> None:
    """Everybody who heard a name being said now has it. The one place a name
    is handed over: saying your own, being introduced, being talked about."""
    day = town.world.time.day
    listeners = list(dict.fromkeys([result.initiator, result.target] + list(heard_by or [])))
    for line in result.lines:
        speaker = town.residents.get(line.get("speaker", ""))
        if speaker is None:
            continue
        for named in names_said(str(line.get("text") or ""), town, speaker):
            for rid in listeners:
                listener = town.residents.get(rid)
                if listener is not None and listener.id != speaker.id and listener.learn_name(named, day, "said"):
                    town.touch(rid)


def remembered_exchange(result: ConversationResult, viewer_id: str, town: "Town") -> str:
    other_id = result.target if viewer_id == result.initiator else result.initiator
    viewer = town.residents[viewer_id]
    other_name = known_as(town.residents[other_id], viewer)
    place = town.world.places[result.location_id].name
    body = " ".join(f'{"I" if l["speaker"] == viewer_id else other_name}: "{l["text"]}"'
                    for l in result.lines)
    if len(body) > 420:
        body = body[:417] + "..."
    return as_seen_by(f"Talked with {other_name} at {place}. {body}", viewer, town)


def bystander_text(result: ConversationResult, town: "Town") -> str:
    """The shape of it from across the room, from words said aloud. Names are
    shielded per witness on the way into memory."""
    a = town.residents[result.initiator].name
    b = town.residents[result.target].name
    opener = result.lines[0]["text"] if result.lines else ""
    if len(opener) > 60:
        opener = (opener[:60].rsplit(" ", 1)[0].rstrip(" ,;:-") or opener[:57]) + "..."
    return f'{a} and {b} were talking. {a} said something like "{opener}"'


def _word_overlap(goal: str, claimed: str) -> float:
    goal_words = {w.strip(".,;:!?\"'") for w in goal.lower().split() if len(w) >= 3}
    claimed_words = {w.strip(".,;:!?\"'") for w in claimed.lower().split() if len(w) >= 3}
    return len(goal_words & claimed_words) / len(claimed_words) if claimed_words else 0.0


def settle_goal(resident: Resident, claimed: str) -> str | None:
    best, score = None, 0.0
    for goal in resident.goals_active:
        s = _word_overlap(goal, claimed or "")
        if s > score:
            best, score = goal, s
    if best is not None and score >= 0.6:
        resident.goals_active.remove(best)
        return best
    return None


def _talk_trust(viewer: Resident, other_id: str, result: ConversationResult, town: "Town") -> None:
    """Once a day, whatever was said, and a little more if it mattered to them."""
    deltas = town.config.trust["deltas"]
    rel = viewer.relationships.get(other_id)
    if rel is None:
        return
    day = town.world.time.day
    if rel.met_day == day and rel.last_talk_day is None:
        rel.add_trust(int(deltas["met"]), day)
    elif rel.last_talk_day == day:
        return
    else:
        rel.add_trust(int(deltas["talked"]), day)
    if int(result.importance_by.get(viewer.id, result.importance) or 0) >= HEAVY_TALK:
        rel.add_trust(int(deltas["heavy_talk"]), day)
    rel.last_talk_day = day


def record_for_participants(result: ConversationResult, town: "Town") -> None:
    time = town.world.time
    for viewer_id in (result.initiator, result.target):
        other_id = result.target if viewer_id == result.initiator else result.initiator
        viewer = town.residents[viewer_id]
        if other_id not in viewer.relationships:
            viewer.relationships[other_id] = Relationship(
                label="somebody I've met", sentiment=0, trust=0, met_day=time.day,
                notes=[f"We spoke at {town.world.places[result.location_id].name}."])
        _talk_trust(viewer, other_id, result, town)
        viewer.add_thread(other=other_id, topic=result.gist or result.lines[0]["text"][:80],
                          outcome=result.outcome or "nothing settled", day=time.day, tick=time.tick)
        settled = settle_goal(viewer, result.settles_by.get(viewer_id, ""))
        if settled:
            viewer.remember(time, f"That settles it - no longer worrying about: {settled}",
                            importance=5, involved=[other_id], location_id=result.location_id)
        viewer.remember(time, remembered_exchange(result, viewer_id, town), kind="dialogue",
                        importance=max(3, min(10, result.importance_by.get(viewer_id, result.importance))),
                        involved=[other_id], location_id=result.location_id)
        town.touch(viewer_id)


# -- the engine's conversation phase -----------------------------------------------------


def _pending_for(engine: "Engine", a: str, b: str) -> dict[str, dict]:
    """What each has been handed by the other and has not answered."""
    town = engine.town
    out: dict[str, dict] = {}
    for speaker_id, other_id in ((a, b), (b, a)):
        other = town.residents[other_id]
        speaker = town.residents[speaker_id]
        offer = engine.offers.get(other_id) or {}
        if offer.get("money") and offer.get("to") == speaker_id:
            owed = other.owes_to(speaker_id) + (float((other.rent or {}).get("owed", 0))
                                                 if (other.rent or {}).get("landlord_id") == speaker_id else 0)
            kind = "repay" if owed > 0 else "gift_accept"
            out[speaker_id] = {"kind": kind, "what": as_seen_by(
                f"{known_as(other, speaker)} has offered you ${float(offer['money']):.0f}"
                + (" against what they owe you." if kind == "repay" else "."), speaker, town)}
            continue
        asked = next((m for m in engine.meetups if m["who"] == sorted((speaker_id, other_id))
                      and not m["accepted"] and m.get("asked_by") == other_id), None)
        if asked is not None:
            out[speaker_id] = {"kind": "accept", "what": (
                f"{known_as(other, speaker)} has asked you to meet them at "
                f"{town.world.places[asked['where']].name}.")}
    return out


async def converse(engine: "Engine") -> None:
    """Pair the talk decisions, grant each conversation the lines the budget
    allows, run them concurrently, and commit in pairing order."""
    from . import deals as DL
    from .scheduler import budget

    town = engine.town
    world = town.world
    today = world.time.day
    busy: set[str] = set()
    paired: list[tuple[str, str, Any]] = []
    for rid, act in engine.talks:
        r = town.residents[rid]
        target = act.target
        here = world.location_of(rid)
        if target not in world.occupants(here):
            engine.emit(engine.event("talk_missed", r, target=target))
            continue
        key = "|".join(sorted((rid, target)))
        # One conversation a pair a day, as in Alive, "unless something new has
        # happened since": they came back in, or this opening puts something on
        # the table (money, a request, an invitation, a deal). Never a third.
        talks = engine.pair_today.get(key, 0)
        from ..inject.apply import news_since
        # Something seen or learned since they last spoke is something to say.
        news = news_since(town, r, getattr(engine, "pair_last", {}).get(key, -1))
        new_business = bool(act.offer or act.ask_for or act.invite or act.deal) or news
        came_back = any(e.kind == "arrive" and e.actor == target for e in engine.last_events)
        if talks >= 2 or (talks == 1 and not (new_business or came_back)):
            engine._refuse(r, act, f"I had already talked with {known_as(town.residents[target], r)} today")
            continue
        if rid in busy or target in busy:
            engine.emit(engine.event("talk_declined", r, target=target))
            continue
        other = town.residents[target]
        if other.asleep:
            other.asleep = False
            engine.emit(engine.event("woken", other, target=rid))
        busy.update({rid, target})
        paired.append((rid, target, act))

    total, _ = budget(town)
    remaining = total - engine.runner.meter.tick_calls
    max_lines = int(town.config.dialogue["max_lines"])
    min_bought = int(town.config.dialogue["min_bought_lines"])
    grants: list[tuple[str, str, Any, int]] = []
    for rid, target, act in paired:
        if remaining < min_bought:
            # No budget left this tick: the line keeps, and is said next tick for free.
            r = town.residents[rid]
            from ..state.resident import Intent
            r.intent = Intent("talk", target, world.time.total_ticks + 2, dialogue=act.dialogue)
            engine.emit(engine.event("talk_deferred", r, target=target))
            continue
        lines = min(max_lines, 1 + remaining)
        remaining -= lines - 1
        grants.append((rid, target, act, lines))
        # What the opening line put on the table, to this person and nobody
        # else, and only once the conversation is actually happening.
        if act.offer:
            engine.offers[rid] = {**act.offer, "to": target}
        if act.ask_for:
            engine.asks[rid] = {**act.ask_for, "to": target}
        if act.invite:
            engine.meetups.append({"who": sorted((rid, target)), "where": act.invite["where"],
                                   "at": world.time.total_ticks + 4, "accepted": False, "asked_by": rid})
        key = "|".join(sorted((rid, target)))
        engine.pair_today[key] = engine.pair_today.get(key, 0) + 1
        engine.pair_last[key] = world.time.total_ticks

    results = await asyncio.gather(*(
        run_conversation(town, engine.runner, rid, target, act.dialogue or "...", lines,
                         engine.spoken_lines, _pending_for(engine, rid, target), engine.asks)
        for rid, target, act, lines in grants))

    for (rid, target, act, _), result in zip(grants, results):
        record_for_participants(result, town)
        initiator = town.residents[rid]
        event = engine.event("conversation", initiator, target=target,
                             detail=bystander_text(result, town), spoken=result.lines[0]["text"],
                             importance=3)
        engine.emit(event, exclude={target}, skip_actor=True)
        overheard = list(engine._pending[-1][1])
        for line in result.lines:
            engine.spoken_lines.setdefault(line["speaker"], []).append(line["text"])
        engine.spoken_today.add(pair_key := "|".join(sorted((rid, target))))
        record = result.to_dict(today, world.time.tick)
        record["channel"] = "face"
        record["overheard_by"] = overheard
        record["deals"] = []
        if act.deal:
            record["deals"].append(DL.apply_one(engine, result, rid, act.deal, 1))
        record["deals"].extend(DL.apply_all(engine, result))
        learn_names_said(result, town, overheard)
        record["conv_id"] = f"d{today}t{world.time.tick}:{pair_key}"
        engine.telemetry.log_conversation(record)
        names = {x: town.residents[x].name for x in (rid, target)}
        engine.telemetry.scene(f"\n**{world.time.hhmm} - {world.places[result.location_id].name}**\n"
                               + result.transcript(names), day=today)
        engine.report.conversations += 1
        engine.report.lines += len(result.lines)
        engine.report.retries += result.retries
