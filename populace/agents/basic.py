"""Two small agents that ship with populace, for trying the path and for the gate.

`EchoAgent` says back what it was told. `HelpdeskAgent` is a plain rule-based
helpdesk for one kind of problem: it apologises, books somebody round for the
next morning and promises it fixed by then; a customer who keeps coming back
gets a credit. Neither uses a model. The ISP demo in step 5 has a fuller one.
"""

from __future__ import annotations

from .protocol import AgentContext, Message, Reply


class EchoAgent:
    def handle(self, message: Message, ctx: AgentContext) -> Reply:
        return Reply(f"You said: {message.text}", end=True)


class HelpdeskAgent:
    def __init__(self, name: str, handles: tuple[str, ...] = ("internet",), credit_after: int = 3,
                 credit: float = 10.0):
        self.name = name
        self.handles = set(handles)
        self.credit_after = credit_after
        self.credit = credit

    def handle(self, message: Message, ctx: AgentContext) -> Reply:
        ours = [p for p in message.problems if any(h in p for h in self.handles)]
        earlier = sum(1 for t in message.thread if t["from"] == "customer")
        if not ours:
            return Reply(f"Thanks for getting in touch with {self.name}. Everything looks fine on "
                         "our side - is something not working?", end=True)
        if earlier == 0:
            ctx.dispatch(f"Day {message.day + 1} 09:00")
            ctx.promise("fixed by tomorrow", message.day + 1)
            return Reply(f"Sorry about that, {message.customer['name'].split()[0]}. There's a fault on "
                         "your line. An engineer will be with you tomorrow morning.")
        if earlier + 1 >= self.credit_after:
            ctx.credit(self.credit, "for the trouble")
            return Reply("I'm sorry it's still dragging on. I've put a credit on your account, "
                         "and the engineer is booked.", end=True)
        return Reply("It's logged, and the engineer is booked for tomorrow morning.", end=True)
