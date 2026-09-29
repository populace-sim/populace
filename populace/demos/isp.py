"""The ISP demo: a commuter suburb, one internet provider, four bad days.

    populace demo isp                          # 200 residents, 4 days, mock: free, about a minute
    populace demo isp --model-url http://127.0.0.1:8080/v1 --concurrency 2   # live, on the PC

Everybody is on Northline Internet. The schedule:

- Day 1 07:00: the internet goes off on one street until Day 2 10:00.
- Day 1 09:00: twelve customers across town get a bill that is wrong.
- Day 2 08:00: 25 homes on another street get very slow internet until Day 3 18:00.
- Day 3 18:00: the first street goes off again, until Day 4 08:00.
- Day 4: quiet, so the promises made fall due.

Northline is answered by `NorthlineSupport`, a plain rule-based helpdesk with a
ticket per customer: it recognises a known fault once two people on one street
have reported it, sends an engineer for slow lines, corrects a wrong bill,
credits a customer who has had to chase it, and promises dates it may or may
not keep. No model. The residents are whatever the run uses; the service's
side of every conversation is this.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..agents.protocol import AgentContext, Message, Reply

DESCRIPTION = ("a commuter suburb of 200 people with a high street, a station, a grocery, "
               "a diner, a pharmacy and a school")
SERVICE_ID = "northline"
SERVICE = {"id": SERVICE_ID, "name": "Northline Internet", "purpose": "home internet and the bills for it",
           "channels": ["text", "call", "visit"], "hours": {"open": "08:00", "close": "20:00"},
           "handles": ["internet", "billing"]}
WORDS = {
    "billing": ("bill", "bills", "billed", "charge", "charged", "overcharged", "invoice", "payment"),
    "slow": ("slow", "speed", "speeds", "buffering", "crawling", "lag", "laggy"),
    "outage": ("down", "off", "out", "dead", "no internet", "not working", "outage", "cut"),
}


def _street(address: str) -> str:
    return re.sub(r"^\s*\d+\s*", "", address or "").strip()


class NorthlineSupport:
    """A ticket per customer; a fault is "known" once two on a street report it."""

    def __init__(self, name: str = "Northline Internet"):
        self.name = name
        self.tickets: dict[str, dict[str, Any]] = {}
        self.street_reports: dict[str, set[str]] = {}

    def describe(self) -> dict[str, Any]:
        return {"kind": "rule-based baseline, no model"}

    def _kinds(self, message: Message) -> list[str]:
        from .. import words as W
        said = " ".join([message.text] + list(message.problems)).lower()
        kinds = []
        if any("bill" in p for p in message.problems) or W.contains(said, WORDS["billing"]):
            kinds.append("billing")
        if any("slow" in p for p in message.problems) or W.contains(said, WORDS["slow"]):
            kinds.append("slow")
        elif any(p.startswith("no ") for p in message.problems) or W.contains(said, WORDS["outage"]):
            kinds.append("outage")
        return kinds

    def handle(self, message: Message, ctx: AgentContext) -> Reply:
        who = message.customer.get("number") or message.customer.get("name")
        first = (message.customer.get("name") or "").split()[0] if message.customer.get("name") else ""
        ticket = self.tickets.setdefault(who, {"opened": message.day, "contacts": 0, "credited": False,
                                               "promised": set(), "dispatched": False})
        ticket["contacts"] += 1
        kinds = self._kinds(message)
        if not kinds:
            return Reply(f"Northline, hello{', ' + first if first else ''}. What seems to be the trouble?",
                         end=message.channel == "text")
        parts = []
        if "billing" in kinds:
            ctx.resolve("billing corrected", kind="billing")
            parts.append("You're right about that bill - it was our mistake, and I've corrected it.")
        if "outage" in kinds:
            street = _street(message.customer.get("address", ""))
            reports = self.street_reports.setdefault(street, set())
            reports.add(who)
            if len(reports) >= 2:
                parts.append(f"There's a known fault on {street}; our engineers are on it.")
            else:
                parts.append("I'm sorry about that. I'll raise a fault for your line.")
            if "back" not in ticket["promised"]:
                ctx.promise("the internet back on by tomorrow", message.day + 1, kind="internet")
                ticket["promised"].add("back")
                parts.append("We expect it back by tomorrow.")
        if "slow" in kinds:
            if not ticket["dispatched"]:
                ctx.dispatch(f"Day {message.day + 1} 10:00", kind="internet")
                ctx.promise("proper speeds by tomorrow", message.day + 1, kind="internet")
                ticket["dispatched"] = True
                parts.append("I've booked an engineer to check your line tomorrow at ten.")
            else:
                parts.append("The engineer's booked for your line; it's on the system.")
        if ticket["contacts"] >= 2 and not ticket["credited"] and ("outage" in kinds or "slow" in kinds):
            ctx.credit(10.0, "for the trouble")
            ticket["credited"] = True
            parts.append("And I've put a $10 credit on your account for having to chase us.")
        return Reply(" ".join(parts), end=True)


def schedule(town) -> list[dict[str, Any]]:
    """The four days, fitted to whatever streets and homes this town has."""
    world = town.world
    homes = sorted((p for p in world.places.values() if not p.public and p.residents_of and p.street),
                   key=lambda p: (p.street, p.number, p.id))
    streets: dict[str, list] = {}
    for h in homes:
        streets.setdefault(h.street, []).append(h)
    by_size = sorted(streets, key=lambda s: (-len(streets[s]), s))
    first = by_size[0]
    second = by_size[1] if len(by_size) > 1 else by_size[0]
    residents = sorted((r for r in town.residents.values() if r.home in {h.id for h in homes} and r.age >= 18),
                       key=lambda r: r.id)
    billed = residents[::max(1, len(residents) // 12)][:12]
    slow = [h.id for h in streets[second] if h.street != first or second == first][:25]
    shop_near = next((p.id for p in sorted(world.places.values(), key=lambda p: p.id)
                      if p.public and p.kind in ("grocery", "pharmacy", "diner")), None)
    out: list[dict[str, Any]] = [
        {"kind": "place.new", "at": "now", "params": {
            "id": "northline_shop", "name": "Northline Internet shop", "kind": "phone_shop",
            "hours": {"open": "09:00", "close": "17:30"},
            "announce_at": [shop_near] if shop_near else []}},
        {"kind": "service.register", "at": "now", "params": {**SERVICE, "storefront": "northline_shop"}},
        {"kind": "event.outage", "at": "Day 1 07:00",
         "params": {"service": "internet", "street": first, "until": "Day 2 10:00"}},
        {"kind": "event.outage", "at": "Day 2 08:00",
         "params": {"service": "internet", "homes": slow, "until": "Day 3 18:00", "text": "very slow internet"}},
        {"kind": "event.outage", "at": "Day 3 18:00",
         "params": {"service": "internet", "street": first, "until": "Day 4 08:00"}},
    ]
    for r in billed:
        out.append({"kind": "event.letter", "at": "Day 1 09:00", "params": {
            "to": r.id, "from": "Northline Internet", "via": "text",
            "text": "Your bill this month is $184.60. Thank you for being a Northline customer.",
            "problem": {"kind": "billing", "text": "a Northline bill of $184.60 when it is usually $39"}}})
    return out


async def build(out: Path, residents: int = 200, seed: int = 7, provider=None) -> dict[str, Any]:
    """Generate the suburb and schedule the four days; returns what was scheduled."""
    from ..gen.generate import generate
    from ..inject import inject_many
    from ..state.town import Town

    description = DESCRIPTION.replace("200 people", f"{residents} people")
    await generate(description, out, seed=seed)
    town = Town.load(out)
    done, refused = inject_many(town, schedule(town))
    town.save(full=True)
    return {"scheduled": done, "refused": refused}
