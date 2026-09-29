"""External agents: something outside the town that residents can contact.

A service is registered with an injection (`service.register`); an agent is
what answers it. An agent is any object with

    def handle(self, message: Message, ctx: AgentContext) -> Reply | str | None

(or an `async def handle`). `HttpAgent(url)` posts the same envelope as JSON to
any server; `populace.agents.http.serve(agent, port)` puts a Python agent
behind one. Nothing forces a resident to use a service: they reach it through
their own `contact` action, when a problem or a need gives them a reason.

What an agent can do to the world goes through `AgentContext`, and every one of
those is logged: resolve the resident's problem, credit them money, send
somebody round at a time, promise something by a day (judged that night), or
note something for the record. It never reaches into a mind.
"""

from .protocol import Agent, AgentContext, Message, Reply  # noqa: F401
from .http import HttpAgent  # noqa: F401
