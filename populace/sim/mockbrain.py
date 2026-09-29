"""What the mock decides, says and concludes, for free.

Generic behaviour driven only by the `mock_state` the engine attaches: needs,
who is here, what is for sale, the schedule, the trigger. Deterministic per
call key, and wrong on purpose some of the time: a small share of decisions
name a place the resident does not know or talk to somebody absent, so the
engine's retry and refusal paths run in every free test, the way a real
model's mistakes would drive them.
"""

from __future__ import annotations

from typing import Any

from ..providers.mock import handler

WRONG_ON_PURPOSE = 0.04

OPENERS = [
    "Morning. Busy one?", "You look like you've had a day.", "Didn't expect to see you here.",
    "Have you got a minute?", "Is it me or is it colder today?", "How's things at home?",
    "Heard anything about the factory?", "Don't suppose you've got change?",
    "You still owe me a coffee, you know.", "Long time. How are you keeping?",
]
FLAVOUR = [
    "reading the notices on the wall", "looking out of the window", "checking a phone",
    "sitting with a cup of tea", "tidying up", "stretching a stiff back", "writing a list",
]


def _hungry(state: dict[str, Any]) -> bool:
    needs = state.get("needs", {})
    return float(needs.get("hunger", 0)) >= 60


def _tired(state: dict[str, Any]) -> bool:
    needs = state.get("needs", {})
    return "energy" in needs and float(needs["energy"]) <= 25


def _schedule(state: dict[str, Any]) -> dict[str, Any]:
    plan = state["schedule"]
    if plan["goto"] != state["where"]:
        return {"action": "move", "target": plan["goto"]}
    action = plan["action"]
    if action == "eat" and state["where"] not in (state["home"], state.get("job")):
        food = sorted((t for t in state["for_sale"] if t["satiety"] > 0 and t["price"] <= state["money"]),
                      key=lambda t: t["price"])
        if food and state["open"]:
            return {"action": "buy", "target": food[0]["name"]}
        return {"action": "wait"}
    if action == "work" and not state.get("job"):
        return {"action": "wait"}
    return {"action": action}


def _talk_to(rng, state: dict[str, Any], other: dict[str, Any]) -> dict[str, Any]:
    """An opening line, sometimes carrying something: asking for money owed,
    offering money back, asking for work."""
    reply: dict[str, Any] = {"action": "talk", "target": other["id"], "dialogue": rng.choice(OPENERS)}
    owed = (state.get("owed_by") or {}).get(other["id"])
    owes = (state.get("owes") or {}).get(other["id"])
    roll = rng.random()
    if state.get("arc_stage") == "quit" and other["id"] == state.get("boss"):
        reply.update(dialogue="I need a word about the job.")
    elif owed:
        reply.update(intent="ask_for", ask_for={"money": owed}, dialogue="About that money.")
    elif owes and state["money"] >= min(owes, 20):
        reply.update(intent="offer", offer={"money": min(owes, state["money"] // 2 or 1)},
                     dialogue="Here, towards what I owe you.")
    elif not state.get("job") and roll < 0.35:
        reply.update(intent="ask_for", ask_for={"job": True}, dialogue="Any work going?")
    elif state["money"] < 30 and roll < 0.5:
        reply.update(intent="ask_for", ask_for={"money": 30}, dialogue="Could you spot me thirty till Friday?")
    elif roll < 0.12 and state["money"] > 40:
        reply.update(intent="offer", offer={"money": 10}, dialogue="Let me get this one.")
    elif roll < 0.22 and other.get("sentiment", 0) >= 2 and state.get("leisure"):
        reply.update(intent="invite", invite={"where": state["leisure"][0], "when": "later"},
                     dialogue="Fancy meeting up later?")
    elif roll < 0.4 and other.get("sentiment", 0) >= 2:
        reply.update(intent="ask_for", ask_for={"money": 30}, dialogue="Could you spot me thirty till Friday?")
    return reply


LINES = [
    "Can't complain.", "Same as ever.", "Busy week, honestly.", "Not so bad.", "You know how it is.",
    "Could be worse.", "Mind how you go.", "Right, I'd better get on.", "Haven't heard, no.",
    "Tell me about it.", "We'll see.", "Fair enough.",
]


@handler("dialogue")
def speak(rng, state: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    if state.get("service"):
        # On the phone or at a counter with an outside service.
        done = int(state.get("line_no", 2)) >= 3 or rng.random() < 0.3
        line = rng.choice(["When will it be back on?", "Right. Thanks.", "Is there anything I can do in the meantime?"])
        return {"line": line, "end_conversation": done}
    if state.get("text"):
        return {"reply": rng.choice(["Sounds good.", "Can't today, sorry.", "Ok.", None]), "importance": 2}
    line_no, max_lines = int(state.get("line_no", 2)), int(state.get("max_lines", 5))
    reply: dict[str, Any] = {"line": rng.choice(LINES), "importance": 3, "commitments": [],
                             "deal": None, "end_conversation": line_no >= min(max_lines, 3 + (rng.random() < 0.4))}
    pending = state.get("pending")
    ask = state.get("other_ask") or {}
    if pending and not state.get("settled"):
        # Money you are owed you take back; a gift you may turn down.
        took = pending == "repay" or rng.random() < 0.7
        reply["deal"] = {"kind": pending, "accept": took}
        reply["line"] = "Go on then, thanks." if took else "No, you keep it."
    elif state.get("arc_stage") == "quit" and state.get("is_my_boss"):
        reply["deal"] = {"kind": "quit"}
        reply["line"] = "I'm done here. This is my notice."
    elif state.get("is_their_boss") and state.get("other_no_shows", 0) >= 1 \
            and rng.random() < (0.7 if state.get("other_no_shows", 0) >= 2 else 0.15):
        reply["deal"] = {"kind": "fire"}
        reply["line"] = ("That's twice now. I'm letting you go." if state.get("other_no_shows", 0) >= 2
                         else "You never turned up. I'm letting you go.")
    elif state.get("other_just_lent"):
        reply["line"] = "Thanks. I'll pay you back in a couple of days, promise."
        reply["commitments"] = [{"what": "pay you back", "by_when": 2, "to": state.get("other_id")}]
    elif state.get("owes_other", 0) > 0 and rng.random() < 0.6:
        reply["line"] = "I'll have it back to you in a couple of days."
        reply["commitments"] = [{"what": "pay you back", "by_when": 2, "to": state.get("other_id")}]
    elif state.get("problems") and rng.random() < 0.3:
        reply["line"] = f"We've had {state['problems'][0]} at home all day. Nightmare."
    elif state.get("news") and rng.random() < 0.3:
        reply["line"] = f"Did you see? {state['news']}"
    elif ask.get("job") and state.get("can_hire") and not state.get("other_has_job") and rng.random() < 0.5:
        reply["deal"] = {"kind": "hire", "start": "tomorrow"}
        reply["line"] = "Come in tomorrow and we'll see how you get on."
    elif ask.get("money") and state.get("trust_stage", 0) >= 2 and state.get("money", 0) > 80 and rng.random() < 0.6:
        reply["deal"] = {"kind": "loan", "amount": min(float(ask["money"]), 40), "due_in_days": 5}
        reply["line"] = "Go on. Friday, mind."
    elif ask.get("money") and rng.random() < 0.5:
        reply["line"] = "I haven't got it to spare, sorry."
        reply["commitments"] = []
    elif state.get("owed_by_other", 0) > 0 and rng.random() < 0.4:
        reply["line"] = "I'll have it for you Friday."
    elif rng.random() < 0.06:
        reply["line"] = "I'll drop it round tomorrow."
        reply["commitments"] = [{"what": "drop it round", "by_when": 1, "to": state.get("other_id")}]
    elif rng.random() < 0.04 and state.get("trust_stage", 0) >= 2:
        reply["deal"] = {"kind": "number"}
        reply["line"] = "Here, take my number."
    elif rng.random() < 0.03 and state.get("places"):
        reply["deal"] = {"kind": "invite", "where": state["places"][0], "in_ticks": 4}
        reply["line"] = "Meet me later?"
    if reply["end_conversation"]:
        reply["gist"] = "a few words in passing"
        reply["outcome"] = "nothing much"
    return reply


@handler("npc_decision")
def decide(rng, state: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    if not state:
        return {"action": "wait", "reasoning": "nothing doing", "importance": 1}
    reply: dict[str, Any]
    awake = [p for p in state["present"] if not p["asleep"]]
    trigger = state.get("trigger")
    roll = rng.random()
    if meta.get("attempt", 1) == 1 and roll < WRONG_ON_PURPOSE:
        # Wrong the way models are wrong: a place that is not there.
        reply = {"action": "move", "target": "the old quarry"}
    elif _tired(state) and state["where"] == state["home"]:
        reply = {"action": "sleep"}
    elif _tired(state):
        reply = {"action": "move", "target": state["home"]}
    elif _hungry(state):
        food = sorted((t for t in state["for_sale"] if t["satiety"] > 0 and t["price"] <= state["money"]),
                      key=lambda t: t["price"])
        if state["where"] == state["home"]:
            reply = {"action": "eat"}
        elif food and state["open"]:
            reply = {"action": "buy", "target": food[0]["name"]}
        else:
            reply = {"action": "move", "target": state["home"]}
    elif any(p["id"] in (state.get("owes") or {}) for p in awake) and state["money"] > 20 and roll < 0.6:
        creditor = next(p for p in awake if p["id"] in state["owes"])
        reply = _talk_to(rng, state, creditor)
    elif not state.get("job") and state.get("hirers") and roll < 0.7:
        who = next(p for p in awake if p["id"] in state["hirers"])
        reply = {"action": "talk", "target": who["id"], "dialogue": "Any work going?",
                 "intent": "ask_for", "ask_for": {"job": True}}
    elif any(p["id"] in (state.get("slackers") or []) for p in awake) and roll < 0.8:
        reply = _talk_to(rng, state, next(p for p in awake if p["id"] in state["slackers"]))
    elif state.get("arc_stage") == "quit" and any(p["id"] == state.get("boss") for p in awake):
        reply = _talk_to(rng, state, next(p for p in awake if p["id"] == state.get("boss")))
    elif trigger in ("addressed", "scene", "goal", "new_face", "business") and awake and roll < 0.6:
        other = next((p for p in awake if p["id"] == state.get("about")), awake[0])
        reply = _talk_to(rng, state, other)
    elif trigger == "phone" and state.get("numbers"):
        reply = {"action": "wait"}
    elif state.get("problems") and state.get("services") and (
            roll < 0.5 if state.get("unreported", state["problems"]) else roll < 0.08):
        sid = state["services"][0]
        channels = (state.get("service_channels") or {}).get(sid) or ["text"]
        reply = {"action": "contact", "target": sid,
                 "channel": "call" if "call" in channels and rng.random() < 0.4 else "text",
                 "dialogue": f"Hi, I'm having trouble with my {state['problems'][0].replace('_', ' ')}."}
    elif roll < 0.62:
        reply = _schedule(state)
    elif roll < 0.72 and state["places_known"]:
        options = [p for p in state["places_known"] if p != state["where"]]
        reply = {"action": "move", "target": rng.choice(options)} if options else {"action": "wait"}
    elif roll < 0.8 and awake:
        reply = _talk_to(rng, state, awake[int(rng.random() * len(awake))])
    elif roll < 0.86 and state.get("numbers"):
        reply = {"action": "contact", "target": state["numbers"][int(rng.random() * len(state["numbers"]))],
                 "dialogue": rng.choice(["You about later?", "Call me when you get this.",
                                         "Did you hear back?", "Running late, sorry."])}
    elif roll < 0.9 and awake and state["money"] > 30:
        reply = {"action": "give", "target": awake[0]["id"], "amount": 10}
    elif roll < 0.95:
        reply = {"action": "other", "target": rng.choice(FLAVOUR)}
    else:
        reply = {"action": "wait"}
    reply.setdefault("target", None)
    reply.setdefault("dialogue", None)
    reply["reasoning"] = "(mock) " + (trigger or "nothing in particular")
    reply["importance"] = 5 if reply["action"] == "talk" else 2
    return reply


@handler("reflection")
def reflect(rng, state: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    ids = state.get("heavy_ids") or state.get("memory_ids") or []
    out: dict[str, Any] = {"summary": "(mock) An ordinary day, mostly.", "beliefs": [],
                           "relationship_updates": [], "goal_update": {"action": "keep"}}
    if ids:
        out["beliefs"].append({"text": "(mock) Things are about the same as they were.",
                               "importance": 3, "source_memory_ids": ids[:2]})
        if rng.random() < 0.1:
            out["beliefs"].append({"text": "(mock) cites nothing real", "importance": 3,
                                   "source_memory_ids": [99999]})
    seen = state.get("seen") or []
    if seen and rng.random() < 0.5:
        out["relationship_updates"].append({"character_id": seen[0], "delta": rng.choice([-1, 1, 2]),
                                            "note": "(mock) we talked", "label": None})
    if state.get("review"):
        roll = rng.random()
        hires = state.get("hires") or []
        if state.get("between_jobs") and hires and roll < 0.6:
            out["arc_update"] = {"choice": "seek_work", "workplace": hires[0], "reason": "(mock) need the money"}
        elif state.get("has_job") and roll < 0.08:
            out["arc_update"] = {"choice": "quit", "reason": "(mock) had enough"}
        elif roll < 0.05:
            out["arc_update"] = {"choice": "leave_town", "day": int(state["day"]) + 3,
                                 "reason": "(mock) time for a change"}
        else:
            out["arc_update"] = {"choice": "keep"}
    return out
