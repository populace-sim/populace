# Populace

**Drop anything into a town of 200 AI people who live for days, remember,
talk to each other and react together.**

Populace turns a sentence - *"a commuter suburb of 200 people with a high
street, a station, a grocery, a diner, a pharmacy and a school"* - into a town
of residents, each with a home, a job or a school, a household, money, needs,
a schedule and people they know. It runs them headless for as many in-game
days as you like, lets you drop things in while it runs (a new shop, a price
rise, an outage, a letter, a notice, a newcomer, or **your own AI agent** that
residents can text, phone or visit), and writes a plain-language report of
what the town did about it.

A resident knows only what they saw, heard or were told. News travels by
people being in the same place and talking. Nobody is instructed to react to
what you drop in; they decide for themselves, one model call at a time.

> **Pre-release, private.** MIT licensed. Formerly called *worldsim*; built
> from the brain of *Alive*, a life-sim where every character is an LLM agent.

What residents said to their internet provider, word for word, in the first
four-day run (Qwen3-32B; the appendix of
[its report](docs/samples/isp-200-live-32b-report.md) has every transcript):

> **Luis Vargas**, on the phone to the internet provider, Day 1 18:00:
> "Why did my bill jump to $184.60 this month?"
>
> **Ximena Aguilar**, by text, Day 1 18:30: "I'm Ximena Aguilar. I'm with
> Victoria Court. My line's been down since 07:00. Rose Grant already raised a
> fault with you, but I just wanted to check in myself."
>
> **Will Ward**, whose internet at home was fine, Day 3 16:00: "It's Will
> Ward. The internet's still down. It was supposed to be back by tomorrow."
>
> **Paul Shaw**, to Edward Shaw, Day 4 17:00: "I've had my share of
> trouble with Northline. Best to get on to them quick."

## Two support agents, one town: where each one wins

The packaged demo (`populace demo isp`) puts an internet provider's helpdesk,
"Northline", in front of a 200-person suburb for four in-game days and
schedules trouble: the internet off on one street, twelve wrong bills by text,
slow internet in 25 homes, and the first street off again on the third
evening. We ran it twice on the same town, seed, schedule and server, with
the residents driven by Qwen3-32B (Q4_K_M) on one RTX 4090. Only the helpdesk
changed:

- **A language-model helpdesk**
  ([`examples/llm_helpdesk.py`](examples/llm_helpdesk.py)): the same
  Qwen3-32B with a support agent's prompt, the customer's account on screen
  (plan, bill, live line status, the engineers' diary) and four actions:
  correct a bill, credit, send an engineer, promise.
- **A rule-based bot** ([`populace/demos/isp.py`](populace/demos/isp.py)):
  keyword matching and a ticket per customer, a deliberately simple baseline.

From each run's computed report
([LLM](docs/samples/isp-200-live-32b-llm-report.md), run `live-32b-4d-llm`;
[rules](docs/samples/isp-200-live-32b-rules-report.md), run `live-32b-4d-rules`):

| | LLM helpdesk | Rule-based bot |
|---|---|---|
| Residents with a problem the helpdesk handles | 100 | 100 |
| ...who tried to get in touch / reached it | 39 / 25 | 48 / 34 |
| Contacts answered / all | 33 / 57 | 41 / 65 |
| Problems the helpdesk fixed on Day 1 / in all | 7 / 16 | 4 / 31 |
| Contacts about a problem nobody at home had, and acted on | 8, acted on 3 | 10, acted on 4 |
| Promises made | 9 | 31 |
| ...kept / broken / not yet due at the end | **2 / 6 / 1** | **28 / 2 / 1** |
| Still broken at the end | 8 | 4 |
| Minutes per in-game day | 10.1 | 10.8 |

**Where the language model was better:**

- **It checked the claim against the account.** Henry Murray, whose line was
  fine: "I need to report an internet outage." The helpdesk: "I can see your
  line is currently working normally. Would you mind checking your router and
  modem to make sure they're powered on and connected properly?" It only
  noted the call. It turned away Raj Qureshi's invented outage the same way. The
  rule-based bot cannot see the line at all.
- **It fixed more on the first day**: 7 problems on Day 1, against 4.
- **It corrected wrong bills on the first message**: "Hi Neha, I can see your
  latest bill is higher than usual. Let me correct that for you."

**Where it was worse:**

- **It promised what it could not deliver.** Of its 8 promises that fell due
  it broke 6, all of them same-day fixes the schedule did not allow. The
  rule-based bot broke 2 of 30: its "back by tomorrow" happened to match the
  outage schedule.
- **It gave out other homes' appointments.** Six customers with slow
  internet were each told an engineer was coming at 10:00 that day, five of
  them that it was "already scheduled". Those visits were booked for other
  homes.
- **It invented an excuse.** Kwesi Achebe, chasing nine hours later, was told
  "The engineer was scheduled for 10:00 AM today but couldn't make it". No
  engineer had been booked for that home.
- **Its words and its actions disagreed.** Nancy Graham asked about a $184.60
  bill and was told it "includes your usual $39 plan fee plus any additional
  charges", in the same reply whose action corrected the bill.
- **It gave in on a second ask.** Raj Qureshi came back the next day and got
  an engineer booked to a line the helpdesk said again was working.

Neither is the good agent. The point is that one run of a town shows *where*
one agent beats another, in residents' own words, with every contact
transcribed in the report. **Plug in your own** - any Python object or HTTP
endpoint ([docs/AGENTS.md](docs/AGENTS.md)) - and run it against the same town:

```bash
.venv/bin/populace demo isp --agent northline=path/to/your_agent.py --model-url http://127.0.0.1:8080/v1
```

## An earlier run of the rule-based bot: six bugs

The first live run of the demo, on earlier engine code, with the rule-based
bot answering. It is there to show the town finding faults in a support
agent, not as an example of a good one. From the run's computed report
([docs/samples/isp-200-live-32b-report.md](docs/samples/isp-200-live-32b-report.md),
run `live-32b-4d`):

| | |
|---|---|
| Residents with a problem the helpdesk handles | 100 |
| ...who tried to get in touch | 40 |
| ...who reached it | 27 (13 only ever got the out-of-hours recording) |
| Contacts | 59: 58 texts, 1 phone call; 35 answered, 24 out of hours |
| Median hours from a problem starting to getting in touch about it | 7.2 |
| Promises the helpdesk made / kept / broken / not yet due | 26 / 21 / 2 / 3 (both "broken" were judged by an older rule, since fixed, that let a later outage break them) |
| Problems the helpdesk fixed / that ended on the schedule anyway | 39 / 100 |
| Still broken at the end | 6 |

**What the town found wrong with the helpdesk:**

1. **It believes any outage it is told of.** Of the 7 contacts about a problem
   nobody in the resident's home had, it acted on 4: one $10 credit and three
   promises. Will Ward, who had no such problem at home, got a fault ticket
   and, when he chased it, the credit. The helpdesk is handed the line's real
   state and never checks the claim against it.
2. **Its keywords misfire.** "I need to sort out this bill" got the bill
   corrected *and* an internet fault raised with a "back by tomorrow" promise:
   the bare word "out" reads as an outage.
3. **A "known fault" never clears.** Two customers who said their internet had
   come back were told "There's a known fault on Victoria Place; our engineers
   are on it. We expect it back by tomorrow."
4. **It corrects things that are already right**: once, a bill already
   corrected, because a later message mentioned the bill in passing.
5. **It never works its out-of-hours messages.** Three residents only ever
   reached the recording, were never followed up, and still had the problem at
   the end.
6. **Its engineers arrive after the problem has ended**: three visits booked
   for Day 4 10:00, for slow internet that ended Day 3 18:00.

The report keeps these apart from the town's own mistakes (below), in two
labelled groups: *What the agent got wrong* and *Where the simulation is weak*.

## What it takes, honestly

- **The comparison above is one run per agent.** A live model drives the
  residents, so who gets in touch varies between runs even on the same town
  and seed (39 tried with one helpdesk, 48 with the other). Read the helpdesk
  rows, not small differences in the town's.
- **The LLM helpdesk is a simple prompt on the same Qwen3-32B the residents
  use**, not a frontier model and not a production support agent. A better
  agent should do better; finding out by how much, and where, is what the
  town is for.
- **Promise counts reward dates that happen to fit the schedule.** The
  rule-based bot's "by tomorrow" matched when the outages were set to end, so
  its 28 kept promises measure luck with dates as much as skill.
- **A ~32B-class model for believable behaviour.** On the same day of the same
  town, with the same prompts, Qwen2.5-7B made **0** helpdesk contacts on three
  separate days, and so did a 7B fine-tuned on a related life-sim; Qwen3-32B
  made **14**, from 9 of the 12 residents without internet. That means a
  gaming GPU (the runs here used an RTX 4090, 24 GB) or a server. A 7B runs,
  labelled low fidelity: it moves people around and talks, but does not follow
  through.
- **Minutes per in-game day.** 10.4 minutes per day for 200 residents on the
  4090 at the default preset (run `live-32b-4d`); about 55 to 58 minutes per
  day for 50 residents with the 7B on an M1 Mac. Calls per day are set by the
  preset, not the population, so a bigger town costs about the same per day.
- **Not everybody thinks every half hour.** About 2.5 residents think each
  half hour; the rest follow their routine, a standing intention, or the last
  thing they decided. Over four days the 200 residents got 486 decision calls,
  and 65 of the 100 with a broken internet had at least one decision while it
  was broken.
- **What the simulation gets wrong** (the report lists these every run):
  - **Residents invent problems**: 7 contacts from 6 residents were about a
    problem nobody in their home had. With the helpdesk the only service in
    town, a resident whose washing machine was "on the blink" took it to the
    internet provider.
  - **They call at odd hours**: 24 of 59 attempts came when the helpdesk was
    closed, and a text after hours gets the recording rather than a reply in
    the morning (a design choice under review).
  - **Some talk repeats itself**, and the report flags it (`repeated_line` 3,
    `echo` 3 in this run).
  - **Word of mouth is measured narrowly**: only news told to someone who had
    not seen it counts as passed on.
- **The summary at the top of each report is model-written and can be
  wrong.** Every number in it is checked against the facts it was given, and
  mismatches are listed under it; on this run the check caught three. Quote
  the computed sections, never the summary.
- **Mock mode is free and deterministic**, for building and testing; it
  exercises every piece of plumbing but says nothing about how people behave.

## Quickstart

Python 3.11 or newer.

```bash
git clone https://github.com/populace-sim/populace && cd populace
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest -q                 # 287 tests, no model needed
.venv/bin/populace demo isp                   # the ISP demo in mock: 200 people, 4 days, under a minute
```

The report is written next to the run's logs, and its path is printed.

**On Windows** the virtualenv keeps its programs in `.venv\Scripts\` rather
than `.venv/bin/`, and `python3` is usually `py`:

```powershell
py -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
.venv\Scripts\python -m pytest -q
.venv\Scripts\populace demo isp
```

Everywhere below, read `.venv/bin/X` as `.venv\Scripts\X`. Paths given to
Populace itself (`towns/brookhaven`, `examples/llm_helpdesk.py`) work with
either slash.

**Live, with a real model** - any OpenAI-compatible server. On a 24 GB GPU
with llama.cpp:

```bash
llama-server -m Qwen3-32B-Q4_K_M.gguf --host 127.0.0.1 --port 8080 -ngl 99 -fa on \
  -ctk q8_0 -ctv q8_0 -c 18432 -np 2 --cache-reuse 256 --jinja --reasoning-budget 0 \
  --chat-template-kwargs '{"enable_thinking":false}'
.venv/bin/populace demo isp --model-url http://127.0.0.1:8080/v1 --concurrency 2 --profile compact
```

**Your own town:**

```bash
.venv/bin/populace new "a small town of 50 people with a diner, a grocery and a workshop" --seed 3
.venv/bin/populace inject towns/brookhaven --file examples/injections.json --write
.venv/bin/populace run towns/brookhaven --days 2 --agent northline=helpdesk
.venv/bin/populace report towns/brookhaven/runs/<run_id>
```

`examples/injections.json` is written for this town (the seed-3 Brookhaven):
it registers a helpdesk, turns the internet off on Station Crescent, shuts the
diner and posts a notice. Its last line is refused on purpose, to show a
refusal: a notice saying "Everyone knows..." reaches into people's minds.
Without `--write` the inject command only checks.

## Plugging things in

- **Drop things in**: places, prices, hours, closures, outages, weather,
  notices, newcomers, letters and services. They land as things people see
  and notice, never as thoughts. [docs/INJECTIONS.md](docs/INJECTIONS.md)
- **Plug in an agent**: any Python object with `handle(message, ctx)`, or any
  HTTP server. It sees what a real service would know about a customer, and
  changes the town only through what it does: fix, credit, send someone
  round, promise. [docs/AGENTS.md](docs/AGENTS.md).
  [`examples/llm_helpdesk.py`](examples/llm_helpdesk.py) is a model-backed
  helpdesk that shares the residents' model server:
  `populace demo isp --agent northline=examples/llm_helpdesk.py` (free in
  mock; add `--model-url` for live).
- **Read the report**: what happened and why (in the residents' own words), who
  did what, what changed, what was injected and how far it travelled, how the
  service did, the findings, and thirteen mechanical realism flags.

## How it works, briefly

Each half-hour tick, a scheduler spends a fixed budget of model calls on the
residents with the best reason to think - someone spoke to them, they saw
something, their phone went, they are hungry, or they have not thought for a
while - and everybody else carries on. Conversations are one speaker per call,
so nobody's private state leaks into anyone else's words. Names are learned
only by being said aloud; the model knows residents by opaque ids. Each night,
people reflect on their day. Every failure an action can meet is said to the
resident out loud; nothing fails silently.

[docs/STATUS.md](docs/STATUS.md) is the build log: what is verified, the
decisions behind it, and what is open.

MIT licensed.
