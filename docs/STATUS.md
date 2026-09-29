# Status

Where Populace stands, for a session that knows nothing. Kept current at every
hand-off. If it disagrees with the code, the code is right and this file needs
fixing, and a claim here that something works is checked against the code
before anything is built on it.

## Now

**Ready for launch day.** The LLM helpdesk ran live on the PC against the
rule-based baseline, same town, seed, schedule and server
([results/pc-llm-helpdesk.md](results/pc-llm-helpdesk.md), merged 29
September). The README and both launch drafts now lead with the comparison,
numbers from the two computed reports only: the LLM helpdesk checked claims
against the account and fixed 7 problems on Day 1 against 4, but broke 6 of
its 8 promises that fell due (the baseline 2 of 30), told six customers about
10:00 visits booked for other homes, invented an excuse for a visit never
booked, and defended a wrong bill in the reply that corrected it. The limits
say one run per agent, residents vary, and the LLM helpdesk is a simple prompt
on the same 32B. Report fixes since the run (tested): a service's line under
Injected shows its hours, and the number check accepts hours the report gives
for it, so "08:00"/"20:00" are no longer flagged; the invented-problem finding
no longer says "it never checked the claim" when some were answered without
action. The PC regenerated both sample reports with them (merged). The number check
then showed two more false flags, "000 while" and "490 with": money with a
thousands separator ("$62,000,") was split at the comma. Fixed and tested;
the two reports' flag lines were recomputed from their stored retellings, no
model call (the old parser reproduces the PC's lines exactly, so the method is
faithful). One false flag is left: "65 resident" in the rule-based retelling,
where "65 resident contacts" uses "resident" as an adjective.

**The PC's commits** still carry the old work email (`6bc4412`). In the PC
checkout, once: `git config user.email 314319750+shragi-presspay@users.noreply.github.com`.
The clean publish drops that history anyway.

**Step 6 is written and stopped short of going public.** The project is now
**Populace**: GitHub repo, Python package, CLI command and docs. The launch
README and the Hacker News and X drafts are in the repo, every number in them
from a computed report. **The repo is still private**; going public is the
owner's call after reading them.

| | |
|---|---|
| Step 1: extraction plan | Approved, including dropping "move out" |
| Step 2: the engine, milestones 1-9 | Approved, with all fourteen overnight defaults |
| Opaque resident ids (owner's decision at step 2) | Done: `r001`-style ids, one name lookup, guard reads ids |
| Step 3: observer and report | Approved |
| Step 4: claims flag, injection, agents | Done; the contact question answered on the PC: [results/pc-32b-day-b.md](results/pc-32b-day-b.md) |
| Step 5: the ISP demo | Done: mock, live on the PC, reviewer pass, live report regenerated on the PC |
| **Step 6: rename, launch README, launch drafts** | **Done, private. Waiting for the owner's decision to go public** |
| Model step | Parked (see "Decisions already made") |

**Tests: 287**, none needing a model, about two and a half minutes; the
week-long determinism gate is most of that.

## The LLM helpdesk (before launch)

**What it is.** `examples/llm_helpdesk.py`, class `LlmHelpdesk`: every reply is
one model call (a second if the first is not one JSON object) with a support
agent's system prompt. Under each customer message it sees what a helpdesk
screen shows: name, number, address; plan and price ($39); the latest bill;
the line's live status; how many other customers on that street have a fault
logged; what the desk already did for this customer; the engineers' diary
(8 visits a day, 08:00-18:00). It answers with
`{"reply", "actions": [...], "end"}`, and the actions are the ordinary
`AgentContext` calls: `resolve` (a bill only), `credit` (up to $25 a
customer), `dispatch`, `promise`, `note`. The code enforces only what a desk
cannot physically do (a line fixed from the desk, a credit over the cap, an
engineer out of hours, in the past or on a full day, a promise for a day
gone); each refusal goes to the run's `agent_calls.jsonl`. Judgement - whom to
believe, what to promise, when to credit - is the model's. Two unusable
answers in a row fail the contact out loud ("the line went dead").

**Sharing the server.** The engine runs contacts one at a time, after the
tick's decisions and conversations are finished, so the helpdesk's call never
competes with a resident's. The server stays exactly as for the baseline
(`-np 2`, same context), so only the helpdesk changes between the two runs.
The helpdesk also holds its own one-at-a-time gate, asks for JSON
(`response_format`), turns thinking off per request, and waits up to 110 s
(the engine now honours an agent's own `timeout_s`, 120 s here, instead of the
10 s default). Expect roughly 45-50 minutes for four days: the baseline's 42,
plus about 60 helpdesk calls.

**Same town, seed and schedule.** `demo isp` builds the town in mock from
seed 7, so it is identical whatever model runs it. Checked on the Mac: the
code the baseline ran on (`75edad1`) and today's build byte-identical
`town.json`, `world.json` (the schedule included) and all 200 resident files;
only the unused model-name label in `config.json` differs.

**New in the engine for it** (tested): `ctx.log(record)` writes an agent's
own working to `agent_calls.jsonl`; `timeout_s` on an agent; a `describe()`
the run records in `agents.json`, and the report says who answered and what
the agent's model cost; `--agent SERVICE=path/to/file.py` on `run` and
`demo`, calling the file's `make_agent(model_url, model, mock)`; a note on the
account no longer counts as acting on an invented problem.

**In mock** (60 residents, 2 days): 14 contacts, 12 answered, every reply
parsed first time, dispatch 11, promise 11, resolve 1. The mock "model" is a
stand-in that writes the same JSON; it says nothing about quality.

**On the PC.** Careful: `demo isp` deletes its `--out` folder unless given
`--keep`, so the old command would wipe `towns\isp-200` and the baseline's
logs. These use new folders.

```powershell
git pull
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m pytest -q

# The server, unchanged from the baseline, in its own window
llama-server -m Qwen3-32B-Q4_K_M.gguf --host 127.0.0.1 --port 8080 -ngl 99 -fa on -ctk q8_0 -ctv q8_0 -c 18432 -np 2 --cache-reuse 256 --jinja --reasoning-budget 0 --chat-template-kwargs '{"enable_thinking":false}'

# 1. Four days with the language-model helpdesk (about 45-50 minutes)
.venv\Scripts\populace.exe demo isp --out towns\isp-200-llm --days 4 --model-url http://127.0.0.1:8080/v1 --concurrency 2 --profile compact --agent northline=examples\llm_helpdesk.py --run-id live-32b-4d-llm
.venv\Scripts\populace.exe report towns\isp-200-llm\runs\live-32b-4d-llm --narrate --provider local --model-url http://127.0.0.1:8080/v1

# 2. Recommended: the rule-based baseline again on today's code (about 42 minutes).
#    The engine has changed since live-32b-4d (promises judged on their own
#    problem, households not buildings), so this is the fair comparison.
.venv\Scripts\populace.exe demo isp --out towns\isp-200-rules --days 4 --model-url http://127.0.0.1:8080/v1 --concurrency 2 --profile compact --run-id live-32b-4d-rules
.venv\Scripts\populace.exe report towns\isp-200-rules\runs\live-32b-4d-rules --narrate --provider local --model-url http://127.0.0.1:8080/v1
```

If a run stops early, do not restart it; bring back what it wrote. Bring back
to this repo: each `report.md` as `docs/samples/isp-200-live-32b-llm-report.md`
and `docs/samples/isp-200-live-32b-rules-report.md`, each run's
`manifest.json`, `agents.json` and `agent_calls.jsonl`. The README's
placeholder section and the HN headline are filled from the LLM run's
computed sections only.

## The name

**Populace**, from step 6 (owner's decision). It was **worldsim** from step 1
to step 5. The repository has moved twice: `shragi-presspay/worldsim`, renamed
`shragi-presspay/populace`, then transferred to the owner's organisation as
**`populace-sim/populace`** (private). GitHub redirects the old URLs, but a
checkout should point at the new one. Historical records keep the old name as
written: `docs/results/*.md` and the sample reports.
The Mac checkout is still at `~/worldsim` (a folder name only; its remote
points at `populace-sim/populace`).

**The PC's one-line remote update**, in its checkout:

```powershell
git remote set-url origin https://github.com/populace-sim/populace.git
```

Then `git pull` and `.venv\Scripts\python.exe -m pip install -e ".[dev]"`,
after which the command is `populace` (`.venv\Scripts\populace.exe`).

## Pre-launch checks

**Fresh-clone test**: clone, venv and install, the full test suite, and
`populace demo isp` in mock, following only the README, took **3 minutes 36
seconds** to a written report, no model. **CI** (`.github/workflows/ci.yml`)
runs the tests and a 40-person mock demo on Python 3.11 and 3.13. **License**:
MIT, "Copyright (c) 2026 Shragi Ritholtz".

## Step 6: the launch materials

- **[README.md](../README.md)** leads with "drop anything into a town of 200
  AI people who live for days, remember, talk to each other and react
  together", with the ISP demo as one example: the seven helpdesk bugs, each
  backed by the computed report's findings or its transcript appendix, and the
  key numbers from run `live-32b-4d`. Then the limits, plainly: a ~32B model
  and a gaming GPU for believable behaviour (the 7B made 0 contacts on three
  days, the 32B 14), 10.4 minutes per in-game day on a 4090, about 2.5
  residents thinking per half hour, invented problems, out-of-hours calling,
  the narrow word-of-mouth measure, and a model-written summary that is
  checked and not to be quoted.
- **[docs/launch/hn.md](launch/hn.md)** and **[docs/launch/x.md](launch/x.md)**:
  the same framing for Hacker News and X, with a source table mapping every
  number to the report line it came from. Not posted.
- **Before step 6, two checks on the retelling** (`5f45db9`): omissions are
  judged with word variants through the shared matcher ("billing" mentions
  the "bills"); and every count, day and time in the prose is checked against
  the facts, with mismatches listed under it. On the PC's regenerated
  retelling the omission check is now clean and the number check finds exactly
  its three errors: "47 households" (47 residents), "until 10:00" (the slow
  internet ran to Day 3 18:00), "called 24 times" (1 call, 58 texts). The
  sample report predates the check; the next regeneration prints them.
- **Going public** is not done: `gh repo edit populace-sim/populace
  --visibility public --accept-visibility-change-consequences`, when the owner
  says so.

## What to run

```bash
./.venv/bin/pip install -e ".[dev]"      # once
.venv/bin/python -m pytest -q
.venv/bin/populace new "a small town of 50 people with a diner, a grocery and a workshop" --seed 3
.venv/bin/populace show towns/brookhaven [--resident r017 | --resident "Full Name"]
.venv/bin/populace run towns/brookhaven --days 1                       # mock, seconds
.venv/bin/populace report towns/brookhaven/runs/<run_id>               # writes report.md there
.venv/bin/populace inject towns/brookhaven --file examples/injections.json [--write]   # dry run by default
.venv/bin/populace run towns/brookhaven --days 1 --agent northline=helpdesk           # or =echo, =http://...
.venv/bin/python examples/run_with_agent.py                              # 40 people, an outage, a helpdesk
.venv/bin/populace demo isp                                               # the ISP demo, 200 people, 4 days, mock
.venv/bin/python tools/news_in_talk.py <town>/runs/<run_id>               # why news did or did not travel
.venv/bin/populace gate --days 7 --seed 7                               # the determinism gate
.venv/bin/populace prompt-stats towns/brookhaven [--profile compact]
.venv/bin/python tests/fixtures/make_run_small.py [--write]             # rebuild the golden run
```

Live, against any OpenAI-compatible server (`mlx_lm.server` wants the repo id
as `--model`):

```bash
.venv/bin/populace run towns/brookhaven --days 1 --provider local \
  --model mlx-community/Qwen2.5-7B-Instruct-4bit --profile compact     # this Mac
.venv/bin/populace run towns/brookhaven --days 1 --model-url http://<pc>:8080/v1 --preset gpu
.venv/bin/populace report towns/brookhaven/runs/<run_id> --narrate --provider local \
  --model mlx-community/Qwen2.5-7B-Instruct-4bit                       # adds a model-written retelling
```

Every run writes `<town>/runs/<run_id>/`: `calls`, `systems`, `ticks`,
`events`, `decisions` and `conversations` as JSONL; `names.json`, the one
id-to-name lookup; `snapshots/start.json` and `snapshots/day_NN.json`; a day
transcript per day; and `manifest.json` with the realism flags counted. Every
number in this file is copied from a manifest or counted from those logs.

## Step 5: the ISP demo

`populace demo isp` builds a commuter suburb of 200 people, all on Northline
Internet, and runs four days: the internet off on one street (Day 1 07:00 to
Day 2 10:00), twelve wrong bills by text (Day 1 09:00), very slow internet in
25 homes on another street (Day 2 08:00 to Day 3 18:00), and the first street
off again (Day 3 18:00 to Day 4 08:00); Day 4 is quiet so promises fall due.
A Northline shop opens on the high street as the service's counter.
Northline is answered by `NorthlineSupport` (`populace/demos/isp.py`): a ticket
per customer, a "known fault on <street>" once two there have reported it, an
engineer for a slow line, a corrected bill, a $10 credit for having to chase,
and promises dated by kind. The report gains "The service"
(`populace/observe/service_metrics.py`): who had a problem, who got in touch
and after how long, by which channel, out-of-hours attempts, homes that
reported more than once, contacts from people with no problem, what got fixed
on which day, promises kept, broken and chased, and talk of switching
provider (a labelled keyword proxy). Notes and the realism checklist:
[../demo/isp/NOTES.md](../demo/isp/NOTES.md).

**Mock, 200 residents, 4 days** (`populace demo isp`, 40 s,
[samples/isp-200-mock-report.md](samples/isp-200-mock-report.md)): 100
residents had a problem Northline handles, 19 got in touch (21 contacts, 5 of
them out of hours), 0 contacts from anybody without a problem, 3 of 16
reporting homes reported more than once, problems fixed 1 / 44 / 47 / 44 by
day with 9 wrong bills still open at the end, promises 10 kept and 3 broken.
The mock's contact rate and timing are its own fixed rules; they test the
plumbing, not behaviour.

### The two problems the 32B showed, fixed (`b76b924`)

1. **A household knows who has already reported it.** The 32B had all three
   Masons and all three Sokolovs report one outage separately. A successful
   contact now marks the problem reported on the caller's record and posts a
   household-only notice at home: those in learn it at once, those out when
   they get in, and their "At home" line says who got on to the service, when,
   and what was said. They may still chase it; they are not told not to. On
   the way: a fix at home now fixes it for everybody who lives there (it
   fixed only the caller's record), and a fix, a dispatch or a promise can name
   the kind of problem it is about, so correcting a bill no longer "fixes" the
   internet.
2. **News in conversation.** Why did nothing injected pass on in the 32B's
   conversations when the 7B passed the quiz on twice? The PC's logs are on
   the PC, so the cause is not proven from here; the code had two gaps, both
   fixed with tests. The talk prompt carried only memories retrieved by
   relevance, so a notice seen at noon rarely reached an evening conversation;
   it now carries the same "what changed" facts decisions do, "yours to
   mention or not". And the pair rule (a second conversation the same day only
   with new business) did not count news: somebody who talked with their
   housemate in the morning and saw the notice at noon could not go back and
   tell them. Something seen or learned since two people last spoke now counts.
   The 32B's refusals were 13 of 14 "already talked with X today", which
   points at the second gap. `tools/news_in_talk.py` settles it from the PC's
   logs (first command below); on the 7B's day B it shows the quiz reached 7
   of the 15 conversation prompts of people who had seen it.

### Finishing step 5 (after the PC's live run)

The live run (`live-32b-4d`, 41.7 minutes for four days on the 4090) found three
real helpdesk bugs and one retelling that missed the whole story; the results
are in [results/pc-demo-live.md](results/pc-demo-live.md) and the checklist in
[../demo/isp/NOTES.md](../demo/isp/NOTES.md). What the owner asked for, done
(`6191937`):

1. **`contact_ungrounded`**, a realism flag for a resident getting in touch
   about a problem nobody in their household had. The service section counts
   real contacts and invented ones apart, and says what the agent did on the
   invented ones, so a reader can tell the town's inventions from the agent's
   mistakes. Tested on a broken fixture; a housemate's problem is grounds.
2. **The retelling leads with what was injected.** The narrator gets the
   injections first, then the service section, the findings and the flags
   that fired, and only then the day; its instructions ask it to lead with
   each injected thing and how the town and the service handled it. Under the
   prose the report lists any injection it leaves out (and anybody it names
   who is not in the facts). Still labelled model-written. Tested that the
   retelling mentions every injection, and that one skipping the outage is
   called out.
3. **Findings in two labelled groups**, "What the agent got wrong" (acted on
   problems customers did not have, fixed what was not broken, never worked its
   out-of-hours messages, broke promises) and "Where the simulation is weak"
   (invented problems, out-of-hours calling, the realism flags, the narrow
   word-of-mouth measure, the switching proxy).
4. **The reviewer pass**, one subagent over the live report, NOTES.md and the
   results note: 14 findings. Fixed in the report (`a950a9f`): tried vs
   reached vs recording-only; waits from the problem each contact was about;
   fixes by the service apart from the schedule's; promises to people with no
   problem and not yet due; "twice or more" and real chases; decisions while
   the problem was open; "What happened" leads with the injected things and
   says what people noticed. Fixed in the engine: promises judged on the
   problem they were about; who fixed a problem recorded; a household is the
   household, not the building (in the mock demo one report reached fifteen people in a block). Also fixed
   on the way: waits read a day too long; a named building's name went to the
   helpdesk as the address. **Listed, not fixed**, in NOTES.md: seven helpdesk
   bugs (left in; finding them is the demo's point), and five simulation
   questions for the owner, the first two being that a text out of hours is
   turned away instead of queued, and that Northline is the only service in
   town, so washing machines go to it.

### Regenerate the live report on the PC (no new run)

The live run's logs stay on the PC (towns are gitignored). With the 32B server
running as before, in the populace checkout:

```powershell
git pull
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\populace.exe report towns\isp-200\runs\live-32b-4d --narrate --provider local --model-url http://127.0.0.1:8080/v1
Copy-Item towns\isp-200\runs\live-32b-4d\report.md docs\samples\isp-200-live-32b-report.md
```

One call to the model (the retelling); everything else is recomputed from the
logs. Three things the old logs cannot show, and the regenerated report will
treat accordingly: who fixed each problem (inferred: a problem that ended when
its outage's schedule did counts as the schedule's), households in blocks of
flats (older snapshots have no household, so a building counts as one), and
the two artefact broken promises (judged when they were logged). Check the
retelling's first paragraph names the outages, the wrong bills and the slow
internet, and that no "It leaves out" line appears under it.

### Commands for the PC (the live run, done 28 September)

On the Windows 4090, in the populace checkout, with the 32B server as in
[results/pc-32b-day-b.md](results/pc-32b-day-b.md). About 40 minutes of model
time for four days at 200 residents, if a day costs what day B did (calls per
day are set by the preset, not the population).

```powershell
git pull
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m pytest -q

# 1. Settle why news did not travel on day B, from its existing logs (read-only)
.venv\Scripts\python.exe tools\news_in_talk.py towns\proof50-pc32b\runs\live-32b-dayB

# 2. The server (thinking off, two slots), in its own window
llama-server -m Qwen3-32B-Q4_K_M.gguf --host 127.0.0.1 --port 8080 -ngl 99 -fa on -ctk q8_0 -ctv q8_0 -c 18432 -np 2 --cache-reuse 256 --jinja --reasoning-budget 0 --chat-template-kwargs '{"enable_thinking":false}'

# 3. The demo, live: builds towns\isp-200 and runs four days
.venv\Scripts\populace.exe demo isp --out towns\isp-200 --days 4 --model-url http://127.0.0.1:8080/v1 --concurrency 2 --profile compact --run-id live-32b-4d

# 4. The report, with a retelling by the same model, and the news check
.venv\Scripts\populace.exe report towns\isp-200\runs\live-32b-4d --narrate --provider local --model-url http://127.0.0.1:8080/v1
.venv\Scripts\python.exe tools\news_in_talk.py towns\isp-200\runs\live-32b-4d
```

Bring back to this repo: `towns\isp-200\runs\live-32b-4d\report.md` as
`docs/samples/isp-200-live-32b-report.md`, its `manifest.json` numbers, and the
two `news_in_talk` outputs, in a results note like day B's. Then: fill the
live column of `demo/isp/NOTES.md`, and run the one reviewer subagent over the
live report and the notes (the plan's step 5 hand-off).

## Step 4: injection and external agents

Guides: [INJECTIONS.md](INJECTIONS.md) and [AGENTS.md](AGENTS.md).

**The missing check first.** `claim_unfounded` flags a line that speaks of
money owed, lent or borrowed between the speaker and somebody they are talking
to when nothing backs it: no debt either way, no landlord or employer tie, no
loan, repayment, gift or rent between them earlier in the run. Snapshots now
carry debts and rent so it can see. Shown firing on the golden fixture, quiet
on a backed claim and on talk about prices; on step 3's live day it catches
exactly the invented $900 and nothing else. Thirteen flags now.

**4a, injection** (`populace/inject/`, `populace inject`, dry run by default):
new places, prices, hours, closures of up to fourteen days, reopenings,
outages, weather, notices, arrivals, letters and outside services. Each lands
as witnessed events (`source: inject:<id>`) and as notices that whoever comes
by later notices once, in their own memory. An outage is a problem at home
until it ends. A new place joins a resident's places known only once they
have seen it (the nightly rebuild would otherwise have handed it to the whole
neighbourhood). Prompts get at most three "what changed" lines, facts only.
Refused on the record, with the reason: unknown kinds, places or residents,
past times, long closures, duplicates, free text naming a resident, anything
reaching into a mind ("everyone knows...", a `beliefs` field), and at landing
anything that no longer applies. Pending injections survive a save and land
after a resume.

**4b, agents** (`populace/agents/`, `populace run --agent`): any object with
`handle(message, ctx)` answers a registered service; `HttpAgent` posts the
same envelope to any server, with a hard timeout. Residents reach a service
with their own `contact` action by text, call or a visit to its counter (a new
optional `channel`); a call goes back and forth within the tick's budget. The
agent sees only what a service would know - name, number, address, the words,
the thread, open problems - and acts through `ctx`: resolve, credit, dispatch
somebody at a time, promise by a day (judged that night), note. Every failure
is said to the resident: nobody answering, out of hours, an error, a timeout.
`HelpdeskAgent` and `EchoAgent` ship; `examples/run_with_agent.py` runs a
40-person mock town with an outage and a helpdesk.

**The report** now has, per injection, who saw it, who noticed it later, who it
touched, when it ended, and the conversations it may have travelled through (a
labelled keyword proxy: a line by somebody who knew, to somebody who did not,
in the injection's own words); per service, contacts by channel, what the
agent did, repeat contacts and promises kept; and every contact transcript.
The gate now requires a notice noticed and a contact.

### Three live days

All on the step 2 proof town (seed 3, 50 residents), regenerated each time,
the base `mlx-community/Qwen2.5-7B-Instruct-4bit` on this Mac, preset laptop,
the same injections ([samples/live-day-injections.json](samples/live-day-injections.json)):
Northline Internet registered (text or call, 08:00-20:00) with the helpdesk
answering; the internet off on Station Crescent from 07:00 (twelve residents
in six homes); the diner shut for a burst pipe at 09:00; a quiz notice at the
grocery at noon.

| | Day A: compact | Day B: compact, with reasons | Day C: frontier, with reasons |
|---|---|---|---|
| Run | `proof50-v4/.../live-7b-day1` | `proof50-v5/.../live-7b-day1` | `proof50-v6/.../live-7b-frontier` |
| Minutes for the day | 55.9 | 57.5 | 55.5 |
| Decisions valid first try | 91.5% | 93.2% | 78.6% |
| Refusals | 26 | 10 | 6 |
| Decisions by the twelve without internet | 26 | 25 | 26 |
| ...whose reasoning mentions the internet | 2 | 4 | 10 |
| **Contacts with the helpdesk** | **0** | **0** | **0** |
| Realism flags | stuck 1 | repeated line 1, echo 5 | echo 1 |

The report of day B is [samples/brookhaven-50-live-7b-injected-report.md](samples/brookhaven-50-live-7b-injected-report.md).

**What landed.** Every injection was seen and noticed the way it should be:
the outage by all twelve at home, the diner's sign by five, the quiz notice by
fifteen. On day B the quiz travelled by word of mouth, unprompted: somebody
who had read the notice asked two people who had not, "Ready for the quiz
night?" and "How about that quiz night?". On day A, within households, the outage was
talked about ("Lucy, we should probably get that internet sorted").

**What did not: nobody contacted the service, three days running.** Day A:
every affected resident had "At home: no internet since 07:00" and the
helpdesk's name, number and hours in their prompt, and chose otherwise. For
day B, following the owner's rule for reticence (reasons and permission,
never orders), three moves went in (`9c8a8d8`): a world rule that what people
pay for comes with a number and getting on to them is what it is for, with
putting up with it as the less common choice; stakes in their own line (hours
off, and that they pay for it); and a disposition read off each persona -
straight away, give it a few hours, ask the neighbours first, or put up with
it (77 / 49 / 56 / 18 of 200 on the seed-7 suburb). Thinking about it doubled,
contacts stayed at zero. Day C isolated the prompt's missing worked example:
`compact` drops examples on purpose (Alive's finding that a 7B turns examples
into a script), `frontier` has one for contacting a service. Thinking about it
rose to 10 of 26 decisions, contacts stayed at zero, and not one reply even
named the service. What they did instead fits their dispositions and stops
short: "Waiting to see if the internet comes back on or if I need to do
something about it", "Haruto might know how to fix the internet or who to ask
about it", "she might be having the same issue".

So it is not the engine and not a missing reason: the base 7B takes the
permission as far as thinking about it and asking a neighbour, and never uses
`contact` for a service. The fine-tune was trained on Alive, which had no
services, so there is no reason to expect it to do better. **Options for the
owner**, cheapest first:

1. Run day B on a stronger local model on the PC's 4090 (free), to see
   whether this is the 7B or the design.
2. A "problem" trigger: a fresh problem at home, and the hour the service
   opens, each buy the resident a thought. It gives them the moment, not the
   answer; the data says the moment is not what is missing, so I would not
   lead with it.
3. Accept it for the 7B and say so in step 5: the ISP demo's live half would
   show word of mouth and patience, and its contact numbers would come from
   mock or a stronger model, labelled.

A frontier API would answer it fastest and is a paid run, so it is listed
only as a question.

**Answered (28 September, on the PC):** option 1. Qwen3-32B on the 4090, same
day and prompts: 14 contacts from 9 of the 12, 99.2% valid, 9.3 minutes a
day; the 14 September fine-tune: 0. It was the 7B. See
[results/pc-32b-day-b.md](results/pc-32b-day-b.md) and the decisions below.

**Fixed on the way through step 4**, each with a test:

- `"work"` from away was refused ("I wasn't at work to do it": 19 of 26
  refusals on day A); it now means going to work when the shift is on or
  within the hour, and well off shift the retry names the shift. Day B: 10
  refusals, day C: 6.
- A pupil's school in the city was refused as somebody's home (found at the
  step 3 hand-off, `3e4cb1f`).
- The mock now passes on news it has seen, and a mock caller says a line or
  two, so word of mouth and calls run free in tests.

## Step 3: the report

`populace report <run>` writes deterministic markdown from the run directory
alone, no model and no town needed: what kind of run it was (mock or live,
low fidelity or not), the numbers, the fifteen most important things that
happened with the reason each person gave when it was their own decision, who
did what, what changed between the start and the last night (work, money,
ties, names learned, beliefs, lives), anything injected (step 4), how well the
model did its job, the realism flags, and an appendix with every conversation
and every refusal. Every id comes back as a name through `names.json`.
`--narrate` puts a model-written retelling on top, labelled with the model's
name and "it can be wrong", and lists anybody it names who is not in the facts.

What the engine now logs to make that possible: `decisions.jsonl` (every
thought, its trigger, action and reasoning); on every event, its `source`
(`resident`, `intent`, `schedule` or `engine`) and the `decision` behind it; a
compact snapshot at the start of a run and each night.

**Twelve realism flags** (`populace/observe/flags.py`): repeated line, echo,
stuck, impossible move, sleepless, no reaction, ghost contact, money from
nowhere, promise ignored, provider down, id spoken, name unknown. Each is shown
firing on a deliberately broken copy of the golden fixture
(`tests/fixtures/run_small`, one mock day of a 12-person hamlet, with its
expected report compared byte for byte). A test fails if a flag is added
without one. The seven that mean the engine is wrong must be silent on the
clean fixture; the talk flags may fire on the mock, which repeats its stock
lines on purpose.

### The live day

`towns/proof50-v3/runs/live-7b-day1`: the same 50-person town as step 2's
proof, regenerated with opaque ids, one day on the base
`mlx-community/Qwen2.5-7B-Instruct-4bit` on this Mac, compact profile, preset
`laptop`. Its report, with a live retelling, is
[samples/brookhaven-50-live-7b-report.md](samples/brookhaven-50-live-7b-report.md).

| | Step 2's live day (name ids) | This live day (opaque ids) |
|---|---|---|
| Wall clock for the day | 63 min | 60.5 min |
| Calls | 194 | 169 |
| Residents thinking per tick / who thought at all | 2.42 / 50 | 2.44 / 50 |
| Decisions valid first try | 81.0% | **92.3%** |
| Retries / fallbacks to routine | 22 / 6 | 9 / 7 |
| Reflections landed / failed | 11 / 9 | **20 / 0** |
| Conversations / lines | 20 / 56 | 15 / 38 |
| Names used without having been given | 2 found by hand | **0** (the flag) |
| Realism flags | not built | **none fired** |
| Retelling | - | one call, 37 s |

**The first attempt stopped, and the stop was right.** At tick 21 the run's
validation alarm (35% of the last twenty replies failing) ended it. Every
failure was a pupil trying to get to school, which in a town without one is in
the city: the off-town place was refused as "somebody's home", "work" from a
pupil was refused as having no job, and "walk" with no place said "no place
called None". Fixed in `3e4cb1f` with four tests; the stopped run is kept in
`towns/proof50-v2-stopped`. The rerun above went through.

**Can a stranger read one day of a town and say what happened and why?**
Mostly yes, and the report is honest about the rest. From the sample: three
commuters and a diner worker missed shifts; one resident woke another in the
afternoon and the news went round three conversations in people's own words ("Adam, you
okay? I heard you woke Chris up last night.") - that is gossip travelling by
co-location, checked against the `woken` event; two people at home settled
what to do about the car over soup at the diner; a landlord took $551 in rent. The
reasons read like people: "I want to catch up with her after our falling-out."

**What the reader cannot yet see, and what the live day found:**

- **An invented debt went uncaught.** A pupil's persona secret is taking $900
  from their mum's wallet; the model turned it into "Yuri, you still haven't
  paid me back that $900", said to a housemate, and there is no such debt. No
  flag checks money claims in speech. A `claim_unfounded` flag (a spoken sum
  owed between two people with no obligation between them) is the next one to
  build.
- **22 of 28 refusals were residents trying to work off shift** ("it isn't my
  shift", "I wasn't at work to do it"). Each was said to them, as it must be;
  the rate says the 7B does not read shift times well. A question for the
  fine-tune eval, not a bug.
- **The retelling is faithful in outline and loose in detail**: it moves one
  conversation to the wrong hour and calls a resident absent who was not. The label
  says so; a stronger model would do better.
- **Talk is still thin**: 15 conversations, 38 lines, two deals asserted and
  one landed. That is the base 7B's register, the same as step 2.

**Fixed on the way through step 3**, each with a test watched failing first:

- A new town's trust stages were never settled before the first night, so
  every day-one prompt described a partner as somebody who "knows your face".
- A 12-person hamlet had three men called Julio; generation now draws the
  least-used first names in the pool.
- A boss facing a worker who keeps missing shifts had no reason to think; that
  is now "business", like a debtor in front of you.
- The mock creditor turned down repayments three times in ten; it now takes
  what it is owed. A mock boss may let somebody go after one missed shift.
  (The gate's week had stopped producing a firing, then a repayment, as the
  draws shifted.)
- The money-flow flag first counted events after the snapshot it compared
  against, and the sleepless flag could never fire on a run shorter than a
  calendar day; both found while writing their tests.

## The one-day proof (step 2)

Same town both times: `populace new "a small town of 50 people with a diner, a
grocery and a workshop" --seed 3` (Brookhaven, 50 residents, 23 households),
one in-game day from 06:00, preset `laptop` (6 calls a tick). The live run is
`towns/proof50/runs/live-7b-day1` on this Mac: `mlx_lm.server` on port 8080,
base `mlx-community/Qwen2.5-7B-Instruct-4bit`, compact profile, persona prose
from templates. The mock run is `towns/proof50-mock/runs/mock-day1`, rerun
after the hand-off fixes.

| | Mock | Live, base 7B on the M1 |
|---|---|---|
| Wall clock for the day | 1.9 s | **63 min** |
| Seconds per tick, median / p90 | 0.04 / 0.05 | 79 / 116 |
| Calls | 193 | 194 |
| Decisions / dialogue / reflections | 113 / 60 / 20 | 138 / 36 / 20 |
| Calls per tick, mean / max / budget | 4.02 / 6 / 6 | 4.04 / 6 / 6 |
| Ticks over budget | 0 | 0 |
| Residents thinking per tick, mean | 2.46 | 2.42 |
| Residents who thought at least once | 50 of 50 | 50 of 50 |
| Decision JSON valid first try | 95.4% | 81.0% |
| Decision retries / fallbacks to schedule | 6 / 0 | 22 / 6 |
| Call latency, decision / dialogue / reflection (median) | 0 | 18 s / 25 s / 22 s |
| Prompt cache share of input | 91% | 72% |
| Conversations / lines | 22 / 71 | 20 / 56 |
| Texts | 14 | 0 |
| Refusals, each said to the resident | 6 | 19 |
| Night: reflected / recapped / failed | 20 / 30 / 0 | 11 / 30 / 9 |
| Server errors | 0 | 0 |

So on this Mac, at the laptop preset, **a 50-person day is about an hour and
two to three residents think each half hour**. Nothing in the run depends on
population except who is chosen, so 200 residents would cost about the same
per day and think proportionally less each.

**What the live day found, and what was fixed before this hand-off** (each
with a test watched failing first):

- **Nine of twenty reflections were thrown away** because the model wrote
  `"delta": +1`. Our own schema says "-3 to +3". The JSON reader now accepts a
  plus on a number outside strings; all twenty replies parse. Worse, those nine
  residents got no recap either: see "Reflection has no retry" below, fixed too.
- **13 of the 22 decision retries were `"action": "home"` or `"walk"`.** The
  routine line reads "home at [willow_street_5]" and the model copies the
  activity back as the verb. "home" now means go home, or stay if already
  there; "walk" means move.
- **A stranger was described as "a stocky young woman with a neat beard".**
  Beards now go only to grown men.

**What the live day found about names, fixed after the hand-off: names leaked
through ids.** Every person in the room was listed as `[mariama_boateng] a
stocky young woman ...`, and the model read the first name out of the id: "Hey
Mariama, heard there's been some noise coming from the workshop." Alive has the
same leak with its surname ids. The owner chose opaque ids: residents are now
`r001`, `r002`, ... from town creation, and names return only in what people
read, through one lookup (`populace/observe/names.py`; every run directory gets
a `names.json`). The prompt guard now seats the whole town in crowds and looks
for any stranger's given and family name side by side, in a display name or an
id; a test swaps the old scheme back in and watches it fail. The fine-tune saw
name-style ids, so its eval has to be on the new scheme: see
[MODEL.md](MODEL.md). **Towns generated before this change keep their old ids
and should be regenerated.**

**How the live talk reads.** Plausible and flat, the base 7B's register. People
greet family and coworkers by name, answer the question asked, and mention
work, the park and dinner. The faults are the ones Alive saw: echoes ("Just got
back from the diner, same as you. How about you, Mariama?", said *by* Mariama),
five openings of "There we are.", one resident calling another by a third
person's name, and one pair saying the same two lines at 23:00 and midnight.
No deals landed live beyond two promises, and nobody texted. The fine-tune is
the next thing to ask these questions of.

The refusals were all about the rules and all heard: nine "it isn't my shift",
four "I wasn't at work to do it", six "I had already talked with them today".

## What the engine is

`populace/sim/engine.py` runs one tick in this order: needs rise and fall;
invitations are kept or stood up; anybody whose leaving day has come leaves;
rent falls due; the scheduler picks who is worth a call within the tick's
budget; those residents decide, concurrently, with one retry that tells the
model what was wrong; everybody else follows a standing intent or their
schedule for free; then sleep and waking, moves, work and wages, buying,
eating, giving; then conversations (one speaker per call, as many lines as the
budget still allows, the rest deferred and said free next tick) and texts;
then memories from the witnesses captured when each thing happened; then a save
of whatever changed. At midnight: promises judged, reflections within the
nightly cap and a free recap for everybody else, the weekly review, trust
stages settled, memories pruned, a full snapshot.

Everything a resident reads about another person goes through `known_as` or
`as_seen_by`. A guard sweeps every prompt of a generated 200-person town for a
stranger's name, and an AST guard fails the build if a prompt builder reads
`.name` outside that funnel. Resident ids are opaque (`r017`), because an id
made from a name leaked it: see under the one-day proof. Every action that cannot happen emits a `refused`
event and writes the reason into the actor's memory, so their next prompt knows.

## Decisions taken while the owner was asleep

The owner said to take the sensible default on anything open and log it here.
Every one of these is a config value or a few lines, and reversible.

1. **Children under 13 are named dependents, and the commuter share stays a
   spec number at 0.3.** These two are the owner's own decisions.
2. **The shared rules block is 5,599 tokens (frontier) and 4,607 (compact)**,
   not the 3,000 the plan hoped for. It keeps Alive's sections close to verbatim
   so a model tuned on Alive's calls sees familiar text, and it is the same bytes
   for every call in a town, so the server caches it once. What each call pays
   for is the character block (795-1,110 tokens in the proof town) and the
   dynamic block (218-473).
3. **No `use` action.** v1 has no items, so there is nothing to use. The verbs
   are move, talk, work, eat, sleep, buy, wait, give, contact and other.
4. **Where people may be.** Sleep is at home. Eating is at home or at work;
   anywhere else you buy food. A resident may walk into public places, their
   own home, and the homes of people they know, nowhere else.
5. **Who is worth a call.** `new_face` fires for arrivals only, and `scene` only
   for somebody you have a tie with outside your own household. With Alive's
   rules the first measurement spent 85 of 120 daily decisions on people
   watching their family come home, and 89 of 200 residents had never thought
   after four days.
6. **Nobody starves.** A resident who has not thought for two days (`owed`)
   outranks every routine reason. A test runs 200 people at the laptop preset
   for three days and requires every one to have thought.
7. **The laptop preset reflects 20 residents a night, not the plan's 60.** A
   reflection on the M1 is about a minute; everybody else gets a free recap
   written from their own memories. `gpu` reflects everybody.
8. **The quick preset cannot promise everybody thinks.** It buys one decision a
   tick, 48 a day, so in a 200-person town most people run their schedule all
   day. It is labelled low fidelity in the banner and the manifest.
9. **A pair talks at most twice a day, and the second time only if the opening
   puts something new on the table** (money, a request, an invitation, a deal).
   Once a day was Alive's rule; here it stopped people who meet daily from ever
   settling a debt.
10. **A deal that does not hold up tells the speaker**, in their memory, like
    any refused action. Alive only logged it.
11. **The second-call commitment judge is dropped** (in the plan); a line that
    sounds like a promise and declares none is simply not a promise.
12. **The gate requires a promise judged either way**, kept or broken, not both:
    in a mock week the loans land mid-week and a kept promise does not reliably
    fall due inside it.
13. **A worker's day off includes church only when Sunday is their only day
    off**, because one day-off routine serves all of a resident's days off.
14. **The live proof used the base Qwen2.5-7B with the compact profile on a
    town whose persona prose came from templates.** The fine-tune is not on this
    Mac, compact is what Alive measured best on the base model, and model prose
    for 50 people would have added about half an hour before the day began.

## Bugs found and fixed in step 2

Each has a test that was watched failing first.

- **Offers leaked between conversations.** An offer, request or invitation in
  an opening line was recorded before the conversation was granted, so one
  meant for one person turned up in another conversation the same tick.
- **Retries inside conversations were not counted**, and the gate found nine
  ticks over budget.
- **The owner's three generation bugs**: schedules ignoring opening hours;
  template personas ignoring age and role (pupils with work secrets); the same
  sentence across much of the town. Town-wide variety now redraws anything
  more than max(2, 2% of residents) share, and a batch refuses two people
  written the same.
- **Live persona generation came back all templates** (milestone 3): the model
  wrote a list as a sentence, the retry repeated the same prompt to a
  deterministic server, and the fallback was cached.
- **From Alive, not carried over**: `addressed` was checked after the phone; a
  second talk in a day was dropped silently; several prompt helpers named
  people raw.

## What is honestly not good yet

- **Reflection has no retry.** A garbled reflection costs that resident their
  real reflection for the night. Until the hand-off it also cost them the recap
  and their turn on the rota; now they get the free recap and stay first in line
  for tomorrow night, and the night's log counts them as `failed`. The live proof
  below started before this change.
- **Talk is budget-bound.** At 6 calls a tick an opening line is sometimes
  deferred a tick; it is said free then, but the conversation happens half an
  hour late.
- **`calls.per_tick` in a manifest includes the night's reflections** spread
  over the day's ticks; `calls.by_role` separates them.
- **Template prose is generic** by design, and the base 7B's is plausible and
  flat (see Generation).

## Generation (milestone 3 hand-off)

A sentence becomes a town in four passes in `populace/gen/`: a spec by keyword
rules (with an optional validated model reading), a seeded skeleton
(neighbourhoods, households, places with hours and staff, jobs, routines, ties,
money, rent, phones, descriptions), persona prose in batches of five (validated,
retried with the reasons, template fallback marked as such, cached), and
locality (circle of at most 20 people, at most 12 places known). Same
description and seed, same bytes.
[samples/westfield-200-mock.md](samples/westfield-200-mock.md) is the seed-7
suburb; [samples/hamlet-10-live-7b.md](samples/hamlet-10-live-7b.md) is live
prose from the base 7B. Live prose costs 150-185 s per batch of five on the
M1, so roughly two hours for 200 residents, once per town.

## Decisions already made (do not reopen without the owner)

- **$0.** No paid provider appears anywhere in populace's config.
- **Launch numbers come from the computed report, never the retelling**
  (owner, before step 6). The README and every launch material quote only
  numbers the deterministic report computed from a run's logs (At a glance,
  Findings, Injected, The service, Realism flags) or its manifest, and name the
  run. The model-written retelling is labelled and can be wrong: the live
  32B's regenerated retelling said "47 households" (47 residents), "until
  10:00" (the slow internet ran to Day 3 18:00) and "called 24 times" (58 of
  59 contacts were texts). The report now lists such mismatches under it.
- **The model is never a build dependency.** Mock is the default for every
  test and gate. `pip install` downloads no weights.
- **Believable follow-through needs a ~32B-class model** (owner, after the
  PC's day B: [results/pc-32b-day-b.md](results/pc-32b-day-b.md)). On the same
  day and prompts, Qwen3-32B on the 4090 made 14 helpdesk contacts from 9 of
  12 affected residents, 99.2% valid, 9.3 minutes a day; the base 7B and the
  14 September fine-tune made none.
- **Live runs happen on the PC**, against `llama-server` on the PC's own
  localhost with 2 slots, run by the PC session. The Mac does not reach it.
- **Development and mock stay on this Mac.** Behaviour questions are not
  answered with hour-long 7B days here; the exact commands for the PC go in
  this file instead.
- **The 7B is a labelled quick, low-fidelity mode**, never the source of a
  behaviour claim.
- **The fine-tune is parked.** It was trained on a life-sim with no
  services, so contacting a service is not in it.
- **A future idea, noted and not built:** distil the 32B's behaviour into a
  small model, so a laptop can run believable follow-through without the PC.
- **Private until step 6**, then public. MIT.
- **Stop after each step** and hand off; commit after every milestone.
- **Presets**: `quick` (2 calls a tick, low fidelity), `laptop` (6, the
  default), `gpu` (30).
- **No claim without telemetry.** The README states residents thinking per
  tick and minutes per in-game day per preset, copied from named runs.
- The weekly review offers keep, seek work, quit, leave town and make an offer;
  "move out" is dropped with the housing ladder.
- No subagents for building. One reviewer subagent after step 5.

## How to resume

Clone this repository. Nothing in the build needs a model, a GPU or mlx.

**Next: the owner reads the README and the launch drafts and decides on
going public.** Open design questions from step 5 are in `demo/isp/NOTES.md`.

## Standing rules (carried from Alive, all paid for)

- No bare `python` on the owner's Mac: `.venv/bin/python`.
- No silent no-ops: an action that cannot happen says so, as an event and a
  sentence in the actor's memory.
- Every name a resident reads goes through `known_as` / `as_seen_by`.
- Keyword matching goes through `populace/words.py`, whole words only.
- Anything the engine can do appears in a prompt; the deal menu equals the
  handlers.
- A check that has never fired is not a passing check.
- Write the failing test first, and watch it fail.
- Nothing that ships names Alive: `tests/guards/test_content_clean.py`.

## Git

Commits as `Shragi Ritholtz <314319750+shragi-presspay@users.noreply.github.com>`,
set as the repo-local `user.email`. Do not override it on the command line. With the co-author trailer the session gives. One commit per
milestone; tests green at every commit. CI (`.github/workflows/ci.yml`) runs
the tests and a 40-person mock demo on every push.
