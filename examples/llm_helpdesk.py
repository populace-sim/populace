"""Northline's helpdesk, answered by a language model.

The ISP demo's own helpdesk (`populace.demos.isp.NorthlineSupport`) is a
deliberately simple rule-based baseline. This one is the real thing a company
would put in front of customers: a model with a support agent's system prompt,
the customer's account in front of it, and the same four things any agent can
do to the town - correct a bill, credit money, send an engineer, promise a date.

    # mock: free, no model; the "model" is a stand-in that writes the same JSON
    .venv/bin/populace demo isp --agent northline=examples/llm_helpdesk.py

    # live, sharing the residents' server (see docs/STATUS.md for the PC's commands)
    .venv/bin/populace demo isp --model-url http://127.0.0.1:8080/v1 --concurrency 2 \\
        --profile compact --agent northline=examples/llm_helpdesk.py --run-id live-32b-4d-llm

What it sees, per message: the customer's name, number and address; their plan
and its price; their latest bill; the live status of their line; how many
other customers on their street have a fault logged; what the helpdesk already
did for them; and the engineers' diary. That is what a helpdesk screen shows.
It does not see the customer's mind, and it never hears from anyone who did
not get in touch.

What the code enforces is only what the desk physically cannot do: correct
anything but a bill from the desk, credit more than the cap, book an engineer
outside working hours, in the past, or when the day's visits are full, or
promise a day already gone. Each refusal is logged in the run's
`agent_calls.jsonl`, never silent. Judgement - whether to believe a customer,
what to promise, when to credit - is the model's, and the report measures it.

Sharing the server: the engine runs contacts one at a time after the
residents' decisions and conversations for the tick, so the agent's request
does not compete with theirs; it still holds its own one-at-a-time gate, and
waits up to `timeout_s` (the server may be finishing a queued call).
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass
from typing import Any, Protocol

from populace import words as W
from populace.agents.protocol import AgentContext, Message, Reply
from populace.sim.actions import extract_json

SYSTEM = """You are a customer support agent for {name}, a home broadband provider. Customers reach you by text message, by phone, or at the counter of the {name} shop.

Your job is to sort out the customer's problem honestly and quickly. Customers remember what you tell them, and they tell their neighbours.

WHAT YOU CAN SEE
Under each message is the customer's account, as the support system shows it: their details, plan and price, latest bill, the live status of their line, faults logged on their street, what the helpdesk has already done for them, and the engineers' diary. The line status is live from the network. What the customer tells you may be wrong, out of date, or about something that is not ours to fix; check it against the account, and ask when they do not match.

WHAT YOU CAN DO
Only the actions you list happen. Saying you did something without listing it does nothing.
- "resolve" with "kind": "billing": correct a wrong bill. Only a bill can be corrected from the desk.
- "dispatch": send an engineer to the customer's home, "at": "Day N HH:MM", between {eng_open} and {eng_close}, never in the past, and only while the diary has visits free that day. The engineer fixes the line at that home when they arrive.
- "promise": tell the customer something will be sorted by a day, e.g. {{"do": "promise", "what": "your internet working again", "by_day": 3, "kind": "internet"}}. It is checked at the end of that day: kept only if the problem is actually gone. Promise only what you expect to happen.
- "credit": money off their account, "amount" up to ${max_credit:.0f}, with a "reason". For real inconvenience, not as a reflex.
- "note": a note on the account for colleagues, "text".
Kinds are "internet" (the line: down or slow) and "billing".

HOW TO SPEAK
Plain, warm and short: two or three sentences, the way a good agent texts. Use the customer's first name. Do not repeat the same apology to everyone. Never state a fact that is not in the account or the conversation.

REPLY with one JSON object and nothing else:
{{"reply": "what you say to the customer", "actions": [ ... ], "end": true or false}}
On a text your reply is the whole exchange. On a call or at the counter, set "end" to true when you are done."""

USER = """{channel_line} {now}.

THE CUSTOMER SAYS
{text}

EARLIER IN THIS CONVERSATION AND BEFORE
{thread}

ACCOUNT
Customer: {name}, {number}, {address}
Plan: {plan}, ${price:.2f} a month
Latest bill: {bill}
Line status (live): {line}
Faults logged on {street}: {street_faults}
Already done for this customer: {history}

ENGINEERS' DIARY
{diary}"""

CHANNEL = {"text": "A text message, received", "call": "A phone call, answered", "visit": "At the shop counter,"}
MONEY = re.compile(r"\$\s?(\d+(?:\.\d{1,2})?)")
WHEN = re.compile(r"^\s*Day\s+(\d+)\s+(\d{1,2}):(\d{2})\s*$", re.IGNORECASE)
KINDS = ("internet", "billing")


@dataclass
class ChatResult:
    text: str
    latency_s: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    model: str = ""
    usage_reported: bool = False


class Chat(Protocol):
    async def __call__(self, system: str, user: str, facts: dict[str, Any]) -> ChatResult: ...


class AgentModelError(RuntimeError):
    """The model did not give a usable answer; the contact fails, and says so."""


class OpenAIChat:
    """Any OpenAI-compatible server: llama.cpp's llama-server, vLLM, mlx_lm.server,
    or a hosted API. The key, if any, comes from POPULACE_API_KEY, like the
    residents'. `thinking_off` is None for a local server started with
    thinking off (the request also asks, the llama.cpp way), or "openrouter" /
    "no-think" for a hosted one, as for the residents (`--thinking-off`)."""

    def __init__(self, base_url: str, model: str = "populace", max_tokens: int = 400,
                 temperature: float = 0.4, json_mode: bool = True, max_concurrency: int = 1,
                 timeout_s: float = 110.0, thinking_off: str | None = None):
        from openai import AsyncOpenAI

        from populace.config import THINKING_OFF
        from populace.providers.openai_compat import api_key
        self.client = AsyncOpenAI(api_key=api_key(), base_url=base_url, timeout=timeout_s, max_retries=1)
        if thinking_off is None:
            self.extra_body: dict[str, Any] = {"chat_template_kwargs": {"enable_thinking": False}}
            self.no_think = False
        else:
            how = THINKING_OFF[thinking_off]
            self.extra_body = dict(how.get("extra_body") or {})
            self.no_think = bool(how.get("no_think"))
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.json_mode = json_mode
        self._gate = asyncio.Semaphore(max_concurrency)

    async def __call__(self, system: str, user: str, facts: dict[str, Any]) -> ChatResult:
        from populace.providers.openai_compat import redact
        extra: dict[str, Any] = {"extra_body": self.extra_body} if self.extra_body else {}
        if self.no_think:
            user = user.rstrip() + "\n\n/no_think"
        if self.json_mode:
            extra["response_format"] = {"type": "json_object"}
        async with self._gate:
            started = time.perf_counter()
            response = await self.client.chat.completions.create(
                model=self.model, max_tokens=self.max_tokens, temperature=self.temperature,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}], **extra)
        usage = getattr(response, "usage", None)
        choice = response.choices[0] if response.choices else None
        return ChatResult(text=redact((choice.message.content or "") if choice else ""),
                          latency_s=time.perf_counter() - started,
                          tokens_in=getattr(usage, "prompt_tokens", 0) or 0,
                          tokens_out=getattr(usage, "completion_tokens", 0) or 0,
                          model=getattr(response, "model", self.model) or self.model,
                          usage_reported=usage is not None)


class MockChat:
    """A stand-in for the model, for building and testing: free and
    deterministic. It reads the same facts the prompt was built from and
    writes the same JSON a model would, so every piece of the agent runs.
    It says nothing about how a model would handle a customer."""

    async def __call__(self, system: str, user: str, facts: dict[str, Any]) -> ChatResult:
        first, day = facts["first"], facts["day"]
        actions: list[dict[str, Any]] = []
        said: list[str] = []
        if facts["bill_wrong"]:
            actions.append({"do": "resolve", "kind": "billing", "note": "bill corrected to plan price"})
            said.append(f"You're right, {first}: that bill was our mistake, and I've corrected it to "
                        f"${facts['price']:.2f}.")
        if facts["line"] != "ok":
            slot = facts["next_slot"]
            if slot and not facts["engineer_booked"]:
                actions.append({"do": "dispatch", "at": slot, "kind": "internet"})
                actions.append({"do": "promise", "what": "your internet working again",
                                "by_day": int(slot.split()[1]), "kind": "internet"})
                said.append(f"I can see the fault on your line. An engineer will come round {slot}.")
            elif facts["engineer_booked"]:
                said.append("Your engineer visit is booked; it's on the system.")
            else:
                actions.append({"do": "note", "text": "no engineer visits free"})
                said.append("I can see the fault. The engineers are fully booked, so I've noted it for "
                            "the network team.")
        if not said:
            said.append(f"Thanks, {first}. Your line and your account both look fine from here - "
                        "what are you seeing?")
            return ChatResult(json.dumps({"reply": " ".join(said), "actions": [], "end": facts["channel"] == "text"}))
        return ChatResult(json.dumps({"reply": " ".join(said), "actions": actions, "end": True}))


def _street(address: str) -> str:
    return re.sub(r"^\s*\d+\s*", "", address or "").strip()


def _hhmm_minutes(hhmm: str) -> int:
    h, m = (int(x) for x in hhmm.split(":"))
    return h * 60 + m


class LlmHelpdesk:
    """A helpdesk whose every reply is one model call (two if the first is
    not valid JSON). `handle` is async; the engine awaits it for `timeout_s`."""

    timeout_s = 120.0

    def __init__(self, chat: Chat, name: str = "Northline Internet", plan: str = "Northline Home 100",
                 price: float = 39.0, max_credit: float = 25.0, engineer_hours: tuple[str, str] = ("08:00", "18:00"),
                 visits_per_day: int = 8, thread_turns: int = 12):
        self.chat = chat
        self.name = name
        self.plan = plan
        self.price = price
        self.max_credit = max_credit
        self.eng_open, self.eng_close = engineer_hours
        self.visits_per_day = visits_per_day
        self.thread_turns = thread_turns
        self.done: dict[str, list[str]] = {}            # customer number -> what the desk did
        self.booked: dict[str, bool] = {}               # customer number -> an engineer is booked
        self.credited: dict[str, float] = {}            # customer number -> total credited
        self.diary: dict[int, list[str]] = {}           # day -> ["HH:MM street", ...]
        self.street_faults: dict[str, set[str]] = {}    # street -> customers whose line showed a fault

    def describe(self) -> dict[str, Any]:
        chat = self.chat
        return {"kind": "language model", "model": getattr(chat, "model", None) or type(chat).__name__,
                "server": str(getattr(getattr(chat, "client", None), "base_url", "") or "") or None}

    # What the screen shows

    def _account(self, message: Message) -> dict[str, Any]:
        bill_problem = next((p for p in message.problems if W.contains(p.lower(), ("bill",))), None)
        line_problem = next((p for p in message.problems if p is not bill_problem), None)
        bill_amount = next((float(m) for m in MONEY.findall(bill_problem or "")), None)
        if bill_problem and bill_amount is not None:
            bill = f"${bill_amount:.2f} (plan price ${self.price:.2f})"
        else:
            bill = f"${self.price:.2f}, as usual"
        line = "ok"
        if line_problem:
            line = "slow" if W.contains(line_problem.lower(), ("slow",)) else "down"
        return {"bill": bill, "bill_wrong": bill_problem is not None, "line": line,
                "line_text": {"ok": "working normally", "slow": f"degraded ({line_problem})",
                              "down": f"down ({line_problem})"}[line]}

    def _next_slot(self, day: int, now_hhmm: str) -> str | None:
        """The earliest free visit, at least an hour from now."""
        open_, close = _hhmm_minutes(self.eng_open), _hhmm_minutes(self.eng_close)
        start = _hhmm_minutes(now_hhmm) + 60
        for d in (day, day + 1, day + 2):
            if len(self.diary.get(d, [])) >= self.visits_per_day:
                continue
            first = max(open_, start) if d == day else open_
            first = -(-first // 60) * 60                  # on the hour
            if first < close:
                return f"Day {d} {first // 60:02d}:{first % 60:02d}"
        return None

    def _diary_text(self, day: int) -> str:
        out = []
        for d in (day, day + 1, day + 2):
            booked = self.diary.get(d, [])
            out.append(f"Day {d}: {len(booked)} of {self.visits_per_day} visits booked"
                       + (f" ({', '.join(sorted(booked))})" if booked else ""))
        return "\n".join(out) + f"\nVisits run {self.eng_open}-{self.eng_close}."

    # The desk's own limits

    def _check(self, a: Any, message: Message, who: str) -> str | None:
        """None if the desk can do this, else why not."""
        if not isinstance(a, dict) or a.get("do") not in ("resolve", "credit", "dispatch", "promise", "note"):
            return "not an action the desk has"
        kind = a.get("kind")
        if kind is not None and kind not in KINDS:
            return f"no such kind {kind!r}"
        do = a["do"]
        if do == "resolve" and kind != "billing":
            return "only a bill can be corrected from the desk; a line needs an engineer"
        if do == "credit":
            try:
                amount = float(a.get("amount"))
            except (TypeError, ValueError):
                return "a credit needs an amount"
            if amount <= 0 or self.credited.get(who, 0.0) + amount > self.max_credit:
                return f"credits are positive and at most ${self.max_credit:.0f} a customer"
        if do == "dispatch":
            m = WHEN.match(str(a.get("at") or ""))
            if not m:
                return "an engineer visit needs 'Day N HH:MM'"
            d, minutes = int(m.group(1)), int(m.group(2)) * 60 + int(m.group(3))
            if not _hhmm_minutes(self.eng_open) <= minutes < _hhmm_minutes(self.eng_close):
                return f"engineers work {self.eng_open}-{self.eng_close}"
            if (d, minutes) <= (message.day, _hhmm_minutes(message.time)):
                return "that time has passed"
            if len(self.diary.get(d, [])) >= self.visits_per_day:
                return f"Day {d} is fully booked"
        if do == "promise":
            try:
                by_day = int(a.get("by_day"))
            except (TypeError, ValueError):
                return "a promise needs a by_day"
            if by_day < message.day or not str(a.get("what") or "").strip():
                return "a promise needs something to do and a day not yet gone"
        if do == "note" and not str(a.get("text") or "").strip():
            return "an empty note"
        return None

    def _do(self, a: dict[str, Any], ctx: AgentContext, message: Message, who: str) -> str:
        do, kind = a["do"], a.get("kind")
        if do == "resolve":
            ctx.resolve(str(a.get("note") or "bill corrected"), kind="billing")
            return f"Day {message.day} {message.time}: corrected the bill"
        if do == "credit":
            amount = round(float(a["amount"]), 2)
            ctx.credit(amount, str(a.get("reason") or ""))
            self.credited[who] = self.credited.get(who, 0.0) + amount
            return f"Day {message.day} {message.time}: credited ${amount:.2f}"
        if do == "dispatch":
            at = " ".join(str(a["at"]).split())
            ctx.dispatch(at, kind=kind or "internet", note=str(a.get("note") or ""))
            d = int(WHEN.match(at).group(1))
            self.diary.setdefault(d, []).append(f"{at.split()[-1]} {_street(message.customer.get('address', ''))}")
            self.booked[who] = True
            return f"Day {message.day} {message.time}: engineer booked for {at}"
        if do == "promise":
            ctx.promise(str(a["what"]).strip(), int(a["by_day"]), kind=kind)
            return f"Day {message.day} {message.time}: promised {str(a['what']).strip()} by Day {int(a['by_day'])}"
        ctx.note(str(a["text"]))
        return f"Day {message.day} {message.time}: note - {str(a['text'])[:80]}"

    # One message

    async def handle(self, message: Message, ctx: AgentContext) -> Reply:
        cust = message.customer
        who = cust.get("number") or cust.get("name") or "?"
        street = _street(cust.get("address", ""))
        account = self._account(message)
        if account["line"] != "ok":
            self.street_faults.setdefault(street, set()).add(who)
        others = len(self.street_faults.get(street, set()) - {who})
        thread = message.thread[-self.thread_turns:]
        facts = {"first": (cust.get("name") or "").split()[0] if cust.get("name") else "there",
                 "day": message.day, "price": self.price, "channel": message.channel,
                 "bill_wrong": account["bill_wrong"], "line": account["line"],
                 "engineer_booked": self.booked.get(who, False),
                 "next_slot": self._next_slot(message.day, message.time)}
        system = SYSTEM.format(name=self.name, eng_open=self.eng_open, eng_close=self.eng_close,
                               max_credit=self.max_credit)
        user = USER.format(
            channel_line=CHANNEL.get(message.channel, message.channel), now=f"Day {message.day} {message.time}",
            text=message.text or "(nothing said)",
            thread="\n".join(f"  {'Customer' if t['from'] == 'customer' else 'You'}: {t['text']}"
                             for t in thread) or "  (nothing)",
            name=cust.get("name", ""), number=cust.get("number", ""), address=cust.get("address", ""),
            plan=self.plan, price=self.price, bill=account["bill"], line=account["line_text"],
            street=street or "their street",
            street_faults=f"{others} other customer{'s' if others != 1 else ''} with a fault on their line"
            if others else "none",
            history="; ".join(self.done.get(who, [])[-6:]) or "nothing yet",
            diary=self._diary_text(message.day))

        data, calls = None, []
        for attempt in (1, 2):
            prompt = user if attempt == 1 else user + "\n\nYour last answer was not one JSON object. Reply with the JSON object only."
            result = await self.chat(system, prompt, facts)
            calls.append({"attempt": attempt, "latency_s": round(result.latency_s, 2),
                          "tokens_in": result.tokens_in, "tokens_out": result.tokens_out, "model": result.model,
                          "usage_reported": result.usage_reported})
            data = extract_json(result.text)
            if isinstance(data, dict) and str(data.get("reply") or "").strip():
                break
            data = None
        record: dict[str, Any] = {"customer": who, "channel": message.channel, "calls": calls,
                                  "prompt": user, "response": result.text}
        if data is None:
            record["failed"] = "no usable JSON after a retry"
            ctx.log(record)
            raise AgentModelError(f"the helpdesk model gave no usable answer: {result.text[:120]!r}")

        refused, did = [], []
        raw_actions = data.get("actions") if isinstance(data.get("actions"), list) else []
        for a in raw_actions:
            why = self._check(a, message, who)
            if why:
                refused.append({"action": a, "why": why})
                continue
            did.append(self._do(a, ctx, message, who))
        self.done.setdefault(who, []).extend(did)
        record.update({"actions": raw_actions, "refused": refused})
        ctx.log(record)
        return Reply(str(data["reply"]).strip(), end=bool(data.get("end")) or message.channel == "text")


def make_agent(model_url: str | None = None, model: str | None = None, mock: bool = True,
               thinking_off: str | None = None, **_: Any) -> LlmHelpdesk:
    """What `--agent SERVICE=examples/llm_helpdesk.py` calls: the stand-in in
    mock, the run's own server (and `--thinking-off`) when there is one."""
    if mock or not model_url:
        return LlmHelpdesk(MockChat())
    return LlmHelpdesk(OpenAIChat(model_url, model=model or "populace", thinking_off=thinking_off))
