# Hacker News: draft

**Not posted. The repo is private until the owner decides.** Every number
below is from a computed report section or a run's manifest, never from a
model-written retelling; the sources are listed at the bottom (not for
posting).

---

**Title:** Show HN: Populace - a town of 200 AI people to test your agent against

**URL:** https://github.com/populace-sim/populace

**Text:**

Populace turns a sentence ("a commuter suburb of 200 people with a high
street, a station and a school") into a town of AI residents who live for
days: they have homes, jobs, households, money, needs and people they know;
they remember what they saw and heard, talk to each other, and decide what to
do one model call at a time. While it runs you can drop things in - an outage,
a price rise, a notice, a newcomer, or your own AI agent that residents can
text, call or visit - and at the end you get a plain-language report of what
the town did about it, plus every log.

To try it, I put two support agents for an internet provider in front of the
same 200-person town for four in-game days, with the same trouble scheduled:
an outage on one street, twelve wrong bills, slow internet in 25 homes, the
outage coming back. Residents were Qwen3-32B on one RTX 4090, about 10
minutes per in-game day. One helpdesk was a deliberately simple rule-based
bot. The other was a language model (the same Qwen3-32B) with a support
prompt, the customer's account on screen and four actions: correct a bill,
credit, send an engineer, promise.

Neither won outright. The LLM helpdesk checked claims against the account and
turned away made-up outages ("I can see your line is currently working
normally"), which the rule-based bot can't do, and it fixed 7 problems on the
first day against 4. It also:

- broke 6 of the 8 promises that fell due, all same-day fixes the schedule
  didn't allow (the rule-based bot broke 2 of 30);
- told six customers an engineer was coming at 10:00 that day, when those
  visits were booked for other homes;
- invented an excuse for a visit never booked: "The engineer was scheduled
  for 10:00 AM today but couldn't make it";
- told one customer a $184.60 bill "includes your usual $39 plan fee plus any
  additional charges", in the same reply whose action corrected it.

The residents were the part I didn't expect. Verbatim: "Why did my bill jump
to $184.60 this month?"; "My line's been down since 07:00. Rose Grant already
raised a fault with you, but I just wanted to check in myself."; and one
resident to another: "I've had my share of trouble with Northline. Best to
get on to them quick."

What it doesn't do well, honestly:

- One run per agent. A live model drives the residents, so who gets in touch
  varies between runs (39 tried with one helpdesk, 48 with the other).
- The LLM helpdesk is a simple prompt on a 32B model, not a frontier model or
  a production agent. Yours should do better; that's the point.
- It needs a ~32B-class model for the residents. On the same day of the same
  town, Qwen2.5-7B made 0 helpdesk contacts on three separate days; Qwen3-32B
  made 14. So: a gaming GPU or a server.
- The simulated people get things wrong too, and the report keeps that apart
  from the agent's mistakes: 8 contacts in the LLM run were about problems
  nobody in that home had, and 24 of 57 came out of hours.
- The summary paragraph at the top of each report is model-written and gets
  numbers wrong, so every number in it is checked against the computed facts
  and mismatches are listed underneath.

It's built from the brain of a life-sim I've been working on, where the core
rule is that a character only knows what they saw, heard or were told. Mock
mode is free and deterministic; `populace demo isp` runs without a model in
about a minute. MIT.

If you're building an agent that talks to the public (support, sales,
booking), plug it in - any Python object or HTTP endpoint - and run it against
the same town. I'd love to see where yours beats these two.

---

## Sources (not for posting)

All from `docs/samples/isp-200-live-32b-report.md` (run `live-32b-4d`,
computed sections) unless noted.

| Claim | Where |
|---|---|
| Two runs, same town, seed, schedule, server | docs/results/pc-llm-helpdesk.md "What was run"; STATUS "Same town, seed and schedule" |
| About 10 minutes per in-game day | At a glance: 10.11 (LLM), 10.82 (rules) min per in-game day |
| Turned away made-up outages | LLM report appendix: Henry Murray Day 2 14:30, Raj Qureshi Day 3 15:00 |
| 7 problems on Day 1 against 4 | The service: "Problems the service fixed, by day", Day 1: 7 (LLM), 4 (rules) |
| Broke 6 of the 8 that fell due; 2 of 30 | The service: promises kept / broken / not yet due, 2 / 6 / 1 (LLM), 28 / 2 / 1 (rules); same-day dates: docs/results/pc-llm-helpdesk.md |
| Six customers told of other homes' 10:00 visits | LLM appendix, Charlie Harper, Kwesi Achebe, Abiodun Obi, Rob Moore, Yolanda García (Day 2), Jakub Sokolov (Day 3); bookings in agent_calls.jsonl |
| The invented excuse | LLM appendix, Kwesi Achebe Day 2 17:30 |
| The $184.60 bill defended and corrected | LLM appendix, Nancy Graham Day 1 10:00 (reply and `resolve` action) |
| Resident quotes | First run's appendix (live-32b-4d): Luis Vargas Day 1 18:00, Ximena Aguilar Day 1 18:30; Paul Shaw to Edward Shaw Day 4 17:00 |
| 39 and 48 tried | The service: "...who tried to get in touch" |
| 7B 0 contacts on three days; 32B 14 | docs/STATUS.md "Three live days"; docs/results/pc-32b-day-b.md |
| 8 invented, 24 of 57 out of hours | LLM report, The service: 8 from 6 residents; Got nowhere: they were closed 24; Contacts 33 / 57 |
