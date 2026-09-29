"""The smallest agent there is: it says back what it was told.

    from examples.echo_agent import Echo
    run_town(town_dir, ticks, agents={"northline": Echo()})

Any object with `handle(message, ctx)` is an agent. `message` carries the
channel, what a service would know about the customer (name, number, address),
their words, the thread so far, the time and their open problems. `ctx` is how
the agent changes the world: ctx.resolve(), ctx.credit(amount), ctx.dispatch("Day 2
09:00"), ctx.promise("fixed by Friday", by_day=5), ctx.note(text).
Return a string, a populace.agents.Reply(text, end=True), or None for silence.
"""

from populace.agents import Reply


class Echo:
    def handle(self, message, ctx):
        return Reply(f"You said: {message.text}", end=True)
