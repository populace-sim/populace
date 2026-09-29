# Plugging in an agent

An agent is something outside the town that residents can contact: a helpdesk,
a shop's order line, a council office, a bot you are testing. Residents reach
it with their own `contact` action, by text, phone call or a visit to its
counter, when something in their life gives them a reason. Nothing makes them.

## Five minutes

```python
# my_agent.py
from populace.agents import Reply

class MyHelpdesk:
    def handle(self, message, ctx):
        if message.problems:
            ctx.dispatch(f"Day {message.day + 1} 09:00")        # somebody goes round
            ctx.promise("fixed by tomorrow", message.day + 1)   # judged that night
            return Reply("Sorry about that - an engineer is booked for tomorrow morning.")
        return Reply("Thanks for getting in touch.", end=True)
```

```python
import asyncio
from populace.inject import inject
from populace.sim.run import run_town, ticks_for_days
from populace.state.town import Town
from my_agent import MyHelpdesk

town = Town.load("towns/x")
inject(town, {"kind": "service.register", "params": {
    "id": "northline", "name": "Northline Internet", "purpose": "home internet",
    "channels": ["text", "call"], "hours": {"open": "08:00", "close": "20:00"},
    "handles": ["internet"]}})
inject(town, {"kind": "event.outage", "at": "Day 1 07:00", "params": {
    "service": "internet", "street": "Harbour Way", "until": "Day 2 12:00"}})
town.save()
asyncio.run(run_town("towns/x", ticks_for_days(1), mock=True, run_id="try",
                     agents={"northline": MyHelpdesk()}))
```

```bash
.venv/bin/populace report towns/x/runs/try      # "Injected" has the contacts; the appendix has every transcript
```

`examples/run_with_agent.py` does all of that in one go with the built-in
`HelpdeskAgent`. `examples/llm_helpdesk.py` is a helpdesk that is a language
model, on the same server as the residents:

```bash
.venv/bin/populace demo isp --agent northline=examples/llm_helpdesk.py            # mock: a stand-in writes the JSON
.venv/bin/populace demo isp --agent northline=examples/llm_helpdesk.py \
    --model-url http://127.0.0.1:8080/v1 --concurrency 2 --profile compact       # live
```

`--agent SERVICE=path/to/file.py` works on `run` and `demo` for any file with
`make_agent(model_url, model, mock)`; it is handed the run's own server. Over HTTP, in any language: `HttpAgent("http://host:port/")`,
and `examples/http_agent_server.py` shows the other end.

## What the agent gets

`message` (a `populace.agents.Message`):

| Field | |
|---|---|
| `service` | the service id |
| `channel` | `text`, `call` or `visit` |
| `customer` | what a service would know: `name`, `number`, `address` - nothing else about them |
| `text` | what they said this turn |
| `thread` | earlier turns with this customer, `{"from": "customer" or "agent", "text"}` |
| `day`, `time` | in-town time |
| `problems` | open problems at their address, e.g. `["no internet"]` |

It returns a string, a `Reply(text, end=False)`, or `None` for silence. A text
is one exchange; on a call or at the counter the resident answers (a model
call, within the tick's budget) until either side ends it or three turns pass.

## What the agent can do

Through `ctx` (a `populace.agents.AgentContext`); each becomes events in the
town and is listed in the run's `contacts.jsonl`:

| Call | In the town |
|---|---|
| `ctx.resolve(note)` | the customer's open problems of the kinds in the service's `handles` are fixed |
| `ctx.credit(amount, reason)` | money to the customer, on the record |
| `ctx.dispatch("Day N HH:MM", fixes=True)` | somebody comes round then; the household sees them |
| `ctx.promise(what, by_day)` | judged that night: kept if the problem is fixed by then; the customer remembers either way |
| `ctx.note(text)` | for the record only |
| `ctx.log(record)` | the agent's own working (a model call, an action it declined) to the run's `agent_calls.jsonl`; changes nothing |

It cannot touch a mind, and it only ever hears from residents who chose to
get in touch.

## When it fails

Every failure is said to the resident and kept in their memory: no agent
attached ("nobody answered"), out of hours (the recording gives the hours), an
exception or a timeout ("the line went dead"). An `async def handle` is
awaited for 10 s, or for the agent's own `timeout_s` if it sets one (a
model-backed agent needs longer). `HttpAgent` has a hard timeout (5 s by
default). A plain synchronous `handle` that blocks will block the run, so keep
it quick, make it async, or put it behind HTTP. An agent with a `describe()`
method is named in the report by what it returns.
