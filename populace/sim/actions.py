"""Actions: what a resident can do, parsed and validated from a model reply.

Ported from Alive's `actions.py`. This milestone carries only the parsing
helpers generation needs; the action set, validation and the free fallbacks
arrive with the tick loop.
"""

from __future__ import annotations

import json
import re
from typing import Any

from .. import clock

_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def extract_json(text: str) -> dict | None:
    """Pull one JSON object out of model output, tolerating fences and stray prose."""
    if not text:
        return None
    candidates: list[str] = []
    fenced = _FENCE.search(text)
    if fenced:
        candidates.append(fenced.group(1))
    candidates.append(text)
    for candidate in candidates:
        candidate = candidate.strip()
        start = candidate.find("{")
        if start == -1:
            continue
        depth = 0
        in_string = False
        escaped = False
        for i in range(start, len(candidate)):
            ch = candidate[i]
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    body = candidate[start : i + 1]
                    try:
                        parsed = json.loads(body)
                    except json.JSONDecodeError:
                        try:
                            parsed = json.loads(_drop_plus_signs(body))
                        except json.JSONDecodeError:
                            break
                    return parsed if isinstance(parsed, dict) else None
    return None


def _drop_plus_signs(body: str) -> str:
    """`"delta": +1` is how a person writes a positive change, and our own
    reflection schema says "-3 to +3"; JSON has no leading plus. Drop a plus
    that stands where a value starts and is followed by a digit, outside strings."""
    out: list[str] = []
    in_string = escaped = False
    last = ""
    for i, ch in enumerate(body):
        if in_string:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "+" and last in ":,[" and body[i + 1 : i + 2].isdigit():
            continue
        if not ch.isspace():
            last = ch
        out.append(ch)
    return "".join(out)


def _norm(s: Any) -> str:
    """Lower-cased and stripped of the punctuation our own prompts wear.

    Every id in a prompt is shown in square brackets, and a small model copies
    the display form back verbatim; taking the brackets off is our job, not
    something to nag the model about.
    """
    return str(s or "").strip().strip("[]<>\"'`").strip().lower()


# -- the action set -------------------------------------------------------------------------

from dataclasses import dataclass  # noqa: E402
from typing import TYPE_CHECKING  # noqa: E402

from ..prompt.rules import ACTION_TYPES, INTENTS  # noqa: E402
from ..state.resident import Intent, Resident  # noqa: E402
from .events import known_as  # noqa: E402

if TYPE_CHECKING:  # pragma: no cover
    from ..state.town import Town

SOURCE_MODEL = "model"
SOURCE_RETRY = "retry"
SOURCE_INTENT = "intent"
SOURCE_SCHEDULE = "schedule"
SOURCE_MOCK = "mock"


@dataclass
class Action:
    action: str
    target: str | None = None  # a resolved id, or free text for "other"
    target_raw: str | None = None
    dialogue: str | None = None
    reasoning: str = ""
    importance: int = 2
    source: str = SOURCE_MODEL
    intent: str | None = None
    offer: dict[str, Any] | None = None     # {"money": 20}
    ask_for: dict[str, Any] | None = None   # {"money": 40} | {"job": True} | {"time": "rent"}
    invite: dict[str, Any] | None = None    # {"where": place, "when": "now"}
    deal: dict[str, Any] | None = None
    amount: float | None = None             # give: how much
    channel: str | None = None              # contact: "text" (default), "call" or "visit"

    @property
    def from_model(self) -> bool:
        return self.source in {SOURCE_MODEL, SOURCE_RETRY, SOURCE_MOCK}

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in (
            "action", "target", "dialogue", "reasoning", "importance", "source", "intent",
            "offer", "ask_for", "invite", "deal", "amount", "channel")}


class InvalidAction(Exception):
    """The model produced something we cannot act on. The message goes into the retry."""


def resolve_place(raw: Any, town: "Town") -> str | None:
    needle = _norm(raw)
    if not needle:
        return None
    places = town.world.places
    if needle in places:
        return needle
    for pid, place in sorted(places.items()):
        if _norm(place.name) == needle:
            return pid
    return None


def resolve_person(raw: Any, town: "Town", among: list[str]) -> str | None:
    needle = _norm(raw)
    if not needle:
        return None
    spaced = needle.replace("_", " ").replace("-", " ").strip()
    for rid in among:
        if rid == needle:
            return rid
    for rid in among:
        if _norm(town.residents[rid].name) in (needle, spaced):
            return rid
    for rid in among:
        first = _norm(town.residents[rid].name).split()[0]
        if first in (needle, spaced):
            return rid
    return None


def school_of(resident: Resident) -> str | None:
    """Where a pupil or student goes to school, from their routine."""
    return next((e.location_id for e in resident.schedule if e.activity == "school"), None)


def may_enter(resident: Resident, place_id: str, town: "Town") -> bool:
    """Public places, your own home, and the homes of people you know."""
    place = town.world.places.get(place_id)
    if place is None:
        return False
    if town.world.is_offtown(place_id):
        # Out of town is where a job or a routine takes you, and nowhere else.
        if resident.job is not None and resident.job.workplace == place_id:
            return True
        return any(e.location_id == place_id for e in list(resident.schedule) + list(resident.off_schedule))
    if place.public or place_id == resident.home:
        return True
    return any(town.residents[rid].home == place_id for rid in resident.relationships
               if rid in town.residents)


_INTENT_MARKERS = (
    " so that ", " so he ", " so she ", " so they ", " so nobody ", " so no one ",
    " without letting ", " without anyone ", " to avoid ", " hoping ", " because i ",
    " so i ", " while ",
)
_CONCEALMENT = ("pretending", "pretend ", "feigning", "feign ", "making a show of",
                "acting like", "acting casual", "trying to look", "so as not to")
_FIRST_PERSON = {"i", "i'm", "im", "my", "me", "mine", "myself", "we", "our", "us"}
MAX_OTHER_CHARS = 120


def observable_phrase(text: str) -> str:
    """Reduce a free-text action to what somebody across the room would see.
    Verbatim from Alive: cut the part that gives away intent, refuse first person."""
    phrase = " ".join(text.strip().split())
    lowered = f" {phrase.lower()} "
    for marker in _INTENT_MARKERS:
        idx = lowered.find(marker)
        if idx != -1:
            phrase = phrase[: max(0, idx - 1)].rstrip(" ,;:-")
            lowered = f" {phrase.lower()} "
    if not phrase:
        raise InvalidAction("describe only what somebody watching would see, with no reason attached")
    low = phrase.lower()
    for verb in _CONCEALMENT:
        if verb in low:
            raise InvalidAction(
                f"drop {verb.strip()!r} - a stranger cannot see that you are pretending, "
                "only what you appear to be doing. Describe just that.")
    words = {w.strip(".,;:!?\"'").lower() for w in phrase.split()}
    if words & _FIRST_PERSON:
        raise InvalidAction("write the phrase as a description of you from outside - no 'I', 'my' or 'me'")
    if len(phrase) > MAX_OTHER_CHARS:
        phrase = phrase[:MAX_OTHER_CHARS].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return phrase


def _money(value: Any, what: str) -> float:
    try:
        amount = round(float(value), 2)
    except (TypeError, ValueError):
        raise InvalidAction(f"{what} has to be a number") from None
    if amount < 1:
        raise InvalidAction(f"{what} has to be at least a dollar")
    return amount


def _names(town: "Town", viewer: Resident, ids: list[str]) -> list[str]:
    """People named the way this resident may name them: an error message is a
    prompt too, and Alive's named strangers in its retries."""
    return [f"{known_as(town.residents[i], viewer)} [{i}]" for i in ids]


def validate(raw: dict, resident: Resident, town: "Town", source: str = SOURCE_MODEL) -> Action:
    """Raw model JSON to an Action, or InvalidAction with a message fit for the retry."""
    if not isinstance(raw, dict):
        raise InvalidAction("response was not a JSON object")
    action = _norm(raw.get("action"))
    if action in ("walk", "go"):
        action = "move"
    elif action in ("home", "go home", "go_home"):
        # The routine line reads "home at [house_1]"; a small model copies the
        # activity back as the verb. At home it means staying put.
        here_now = town.world.location_of(resident.id)
        action = "wait" if here_now == resident.home else "move"
        raw = {**raw, "target": resident.home} if action == "move" else raw
    elif action == "work" and resident.job is None:
        # A pupil or student says "work" and means school; the second live day
        # stopped on this.
        school = school_of(resident)
        if school is not None:
            here_now = town.world.location_of(resident.id)
            action = "wait" if here_now == school else "move"
            raw = {**raw, "target": school} if action == "move" else raw
    if action not in ACTION_TYPES:
        raise InvalidAction(f"'action' must be one of {sorted(ACTION_TYPES)}; got {raw.get('action')!r}")
    target_raw = raw.get("target")
    dialogue = str(raw.get("dialogue")).strip() if raw.get("dialogue") else None
    reasoning = str(raw.get("reasoning") or "").strip()
    try:
        importance = max(1, min(10, int(raw.get("importance", 2))))
    except (TypeError, ValueError):
        importance = 2
    world = town.world
    here = world.location_of(resident.id)
    present = [r for r in world.occupants(here) if r != resident.id]
    target: str | None = None
    intent = _norm(raw.get("intent")) or None
    intent = intent if intent in INTENTS else None
    offer = ask_for = invite = None
    deal = raw.get("deal") if isinstance(raw.get("deal"), dict) else None
    amount = None
    channel = None

    if action == "move":
        target = resolve_place(target_raw, town)
        known = ", ".join(resident.places_known)
        if target is None and not target_raw:
            raise InvalidAction(f"moving needs a place: where to? The places you know: {known}")
        if target is None:
            raise InvalidAction(f"there is no place called {target_raw!r}; the places you know: {known}")
        if target == here:
            raise InvalidAction(f"you are already at {target}; pick a different action")
        if not may_enter(resident, target, town):
            if world.is_offtown(target):
                raise InvalidAction(f"nothing takes you to {world.places[target].name} today; "
                                    f"the places you know: {known}")
            raise InvalidAction(f"{world.places[target].name} is somebody's home you have no reason "
                                f"to walk into; the places you know: {known}")
    elif action == "talk":
        target = resolve_person(target_raw, town, present)
        if target is None:
            raise InvalidAction(f"{target_raw!r} is not here. With you right now: "
                                f"{', '.join(_names(town, resident, present)) or 'nobody'}")
        if not dialogue:
            raise InvalidAction("talk needs your opening line in 'dialogue'")
        if isinstance(raw.get("offer"), dict) and raw["offer"].get("money") is not None:
            offer = {"money": _money(raw["offer"]["money"], "an offer of money")}
            if offer["money"] > resident.money:
                raise InvalidAction(f"you haven't got ${offer['money']:.0f} - you have ${resident.money:.2f}")
        if isinstance(raw.get("ask_for"), dict):
            ask = raw["ask_for"]
            ask_for = {}
            if ask.get("money") is not None:
                ask_for["money"] = _money(ask["money"], "asking for money")
            if ask.get("job"):
                ask_for["job"] = True
            if _norm(ask.get("time")) == "rent":
                ask_for["time"] = "rent"
            ask_for = ask_for or None
        if isinstance(raw.get("invite"), dict):
            where = resolve_place(raw["invite"].get("where"), town)
            if where is not None:
                invite = {"where": where, "when": _norm(raw["invite"].get("when")) or "now"}
    elif action == "work":
        if resident.job is None:
            raise InvalidAction("you don't have a job to go to; pick a different action")
        job = resident.job
        t = world.time
        if here != job.workplace:
            # "work" from somewhere else means going to work - if the shift is on
            # or about to start. Step 4's live day refused it nineteen times.
            soon = any(job.on_shift(t.tick + k, t.weekday_index)
                       for k in range(0, 3) if t.tick + k < clock.TICKS_PER_DAY)
            if not soon:
                raise InvalidAction(f"your shift is {job.shift_label()}"
                                    + ("" if job.works_on(t.weekday_index) else ", and not today")
                                    + "; it isn't now. Pick something else to do.")
            if not may_enter(resident, job.workplace, town):
                raise InvalidAction("you can't get to work from here")
            action = "move"
        target = job.workplace
    elif action == "eat":
        at_work = resident.job is not None and here == resident.job.workplace
        if here != resident.home and not at_work:
            food = [t.name for t in world.places[here].for_sale() if t.satiety > 0]
            raise InvalidAction("you can eat at home, or what you brought at work; here you would "
                                f"have to buy something. Food for sale here: {food or 'none'}")
    elif action == "sleep":
        if here != resident.home:
            raise InvalidAction("you can only sleep at home; go home first")
    elif action == "buy":
        place = world.places[here]
        thing = place.thing_by_name(str(target_raw or ""))
        if thing is None or thing.price is None:
            raise InvalidAction(f"{target_raw!r} isn't for sale at {place.name}. "
                                f"For sale: {[t.name for t in place.for_sale()] or 'nothing'}")
        target = thing.id
    elif action == "give":
        target = resolve_person(target_raw, town, present)
        if target is None:
            raise InvalidAction(f"{target_raw!r} is not here to hand anything to. With you right now: "
                                f"{', '.join(_names(town, resident, present)) or 'nobody'}")
        amount = _money(raw.get("amount"), "'amount'")
        if amount > resident.money:
            raise InvalidAction(f"you haven't got ${amount:.0f} - you have ${resident.money:.2f}")
    elif action == "contact":
        numbers = sorted((resident.phone or {}).get("contacts", {}))
        services = sorted(getattr(town, "services", {}) or {})
        needle = _norm(target_raw)
        if needle in services:
            target = needle
        else:
            target = resolve_person(target_raw, town, numbers)
        if target is None:
            raise InvalidAction(
                f"you have no number for {target_raw!r}. Numbers you have: "
                f"{', '.join(_names(town, resident, numbers)) or 'none'}"
                + (f"; services you know: {', '.join(services)}" if services else ""))
        if not dialogue:
            raise InvalidAction("contact needs the words of your text in 'dialogue'")
        limit = int(town.config.phone["max_text_chars"])
        dialogue = dialogue[:limit]
        channel = _norm(raw.get("channel")) or "text"
        if channel not in ("text", "call", "visit"):
            raise InvalidAction(f"'channel' is \"text\", \"call\" or \"visit\"; got {raw.get('channel')!r}")
        if target in services:
            offered = town.services[target].get("channels") or ["text"]
            if channel not in offered:
                raise InvalidAction(f"{town.services[target]['name']} can be reached by "
                                    f"{' or '.join(offered)}, not {channel}")
            if channel == "visit" and not town.services[target].get("storefront"):
                raise InvalidAction(f"{town.services[target]['name']} has no counter in town to visit")
        elif channel != "text":
            raise InvalidAction("you can only text a person from here; to talk, go where they are")
    elif action == "other":
        text = str(target_raw or dialogue or reasoning).strip()
        if not text:
            raise InvalidAction("'other' needs a short description in 'target'")
        target = observable_phrase(text)
        dialogue = None

    if action != "talk":
        intent = offer = ask_for = invite = deal = None
    return Action(action=action, target=target,
                  target_raw=str(target_raw) if target_raw is not None else None,
                  dialogue=dialogue if action in ("talk", "contact") else None,
                  channel=channel if action == "contact" else None,
                  reasoning=reasoning, importance=importance, source=source, intent=intent,
                  offer=offer, ask_for=ask_for, invite=invite, deal=deal, amount=amount)


# -- the free actions ------------------------------------------------------------------------


def from_schedule(resident: Resident, town: "Town") -> Action:
    """The zero-cost action: do what the day usually says, walking there first."""
    world = town.world
    time = world.time
    entry = resident.scheduled_entry(time.tick, time.weekday_index)
    here = world.location_of(resident.id)
    leave_day = (resident.arc or {}).get("leave_day")
    if leave_day is not None and int(leave_day) <= time.day:
        return Action("wait", reasoning="the day to go has come", importance=6, source=SOURCE_SCHEDULE)
    if entry.location_id != here:
        return Action("move", target=entry.location_id, target_raw=entry.location_id,
                      reasoning=f"heading to the usual {entry.activity} block",
                      importance=1, source=SOURCE_SCHEDULE)
    plan = resident.schedule_action(time.tick, time.weekday_index)
    action, target = plan["action"], None
    hungry = _hunger(resident, town) >= 35
    if action == "eat":
        at_work = resident.job is not None and here == resident.job.workplace
        if not hungry:
            action = "work" if at_work and resident.job.on_shift(time.tick, time.weekday_index) else "wait"
        elif here == resident.home or at_work:
            action = "eat"
        else:
            food = sorted((t for t in world.places[here].for_sale() if t.satiety > 0
                           and (t.price or 0) <= resident.money), key=lambda t: (t.price, t.id))
            if food and world.is_open(here):
                action, target = "buy", food[0].id
            else:
                action = "wait"
    elif action == "work":
        if resident.job is None:
            action = "wait"
        else:
            target = resident.job.workplace
    elif plan["activity"] == "errand" and time.tick == entry.start_tick + 1:
        # An errand to a shop is shopping: on arriving, buy the week's things
        # if they sell them, or the cheapest thing that will do.
        sale = sorted(world.places[here].for_sale(), key=lambda t: (t.name != "groceries", t.price, t.id))
        affordable = [t for t in sale if (t.price or 0) <= resident.money]
        if affordable:
            action, target = "buy", affordable[0].id
    return Action(action, target=target, reasoning=plan["reasoning"], importance=1,
                  source=SOURCE_SCHEDULE)


def _hunger(resident: Resident, town: "Town") -> float:
    """The need that eating answers: the first configured need that climbs."""
    for name, need in town.config.needs["kinds"].items():
        if "urgent_above" in need:
            return float(resident.needs.get(name, 0.0))
    return 0.0


def from_intent(resident: Resident, town: "Town") -> Action | None:
    """Carry on with the last model decision if it still stands, for no call."""
    intent = resident.intent
    if intent is None:
        return None
    world = town.world
    if world.time.total_ticks >= intent.expires_tick:
        resident.intent = None
        return None
    here = world.location_of(resident.id)
    if intent.action == "move":
        if intent.target == here:
            resident.intent = Intent("wait", here, intent.expires_tick)
            return Action("wait", reasoning="I came here for a reason; give it a minute",
                          importance=1, source=SOURCE_INTENT)
        if intent.target not in world.places:
            resident.intent = None
            return None
        return Action("move", target=intent.target, target_raw=intent.target,
                      reasoning="still on my way", importance=1, source=SOURCE_INTENT)
    if intent.action == "talk":
        other = town.residents.get(intent.target or "")
        if other is None or intent.target not in world.occupants(here) or other.asleep:
            resident.intent = None
            return None
        if intent.dialogue:
            # A conversation that had no budget last tick, said now for no call.
            line, resident.intent = intent.dialogue, None
            return Action("talk", target=intent.target, target_raw=intent.target, dialogue=line,
                          reasoning="what I meant to say earlier", importance=4,
                          source=SOURCE_INTENT)
        return None
    if intent.action in {"work", "sleep", "wait"}:
        return Action(intent.action, reasoning="carrying on with what I was doing",
                      importance=1, source=SOURCE_INTENT)
    resident.intent = None
    return None


def fallback(resident: Resident, town: "Town") -> Action:
    """Intent first, schedule second, so the schedule cannot undo a decision."""
    return from_intent(resident, town) or from_schedule(resident, town)


def set_intent(resident: Resident, action: Action, town: "Town", ttl_ticks: int) -> None:
    """Make a model decision sticky for a few ticks, against ping-pong."""
    if not action.from_model:
        return
    if action.action in {"wait", "other", "give", "contact", "talk", "buy", "eat"}:
        resident.intent = None
        return
    resident.intent = Intent(action.action, action.target, town.world.time.total_ticks + ttl_ticks)
