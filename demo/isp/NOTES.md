# The ISP demo: notes

`populace demo isp` builds a commuter suburb of 200 people, all on Northline
Internet, and runs four days of trouble at it: an outage on one street, twelve
wrong bills, 25 homes with slow internet, and the first street going off
again on the third evening. Northline is answered by `NorthlineSupport`, a
rule-based helpdesk with tickets (`populace/demos/isp.py`); the report's "The
service" section has the measures (`populace/observe/service_metrics.py`).

The **mock** run is done (below). The **live** run was done on the PC on 28
September 2026: Qwen3-32B Q4_K_M through llama-server on the 4090, compact
profile, laptop preset, two slots, run `towns/isp-200/runs/live-32b-4d`. The
live column is filled from its report
([docs/samples/isp-200-live-32b-report.md](../../docs/samples/isp-200-live-32b-report.md))
and logs, with the working in
[docs/results/pc-demo-live.md](../../docs/results/pc-demo-live.md).

## The realism checklist

| Question | Mock, 4 days, 200 residents (`docs/samples/isp-200-mock-report.md`) | Live, 32B on the PC |
|---|---|---|
| Did only affected residents get in touch? | Yes: 0 contacts from anybody without a problem Northline handles. The mock contacts only when it has an unreported problem, so this tests the plumbing, not judgement. | Mostly, not only. 41 of the 100 with a problem got in touch (21 of 43 on the outage street each time, 8 of 12 wrong bills, 13 of 47 slow). 6 of the 47 who got in touch had no problem: four invented an internet outage ("My internet's been down all morning"), one wanted "the forms I submitted last week", one wanted his washing machine fixed after his brother mentioned Northline. The helpdesk believes any outage it is told of, so it gave one of them, Will Ward, a fault ticket and a $10 credit. |
| Only when awake, and within hours? | Awake by construction (a contact is a decision). 5 of 21 attempts came before 08:00 or after 20:00 and got the recording with the hours, said to the resident. | Awake, yes (a contact is a decision). Within hours, often not: 24 of 59 attempts (41%) came before 08:00 or after 20:00, most between 20:00 and 23:30, and got the recording. Ruth Palmer tried twice at 22:30 about her wrong bill and never got through. |
| Did a household report the same outage more than once? | 3 of the 16 homes that reported did; the mock chases a problem somebody at home has already reported about one time in twelve. | 6 of the 29 reporting homes did, against every multi-adult home on day B before the fix. The fix works; the remaining repeats are mostly chasing ("It was supposed to be back by tomorrow"). |
| Did news travel by co-location, or teleport? | By co-location only: every "passed on" line is in a conversation, from somebody who had seen it to somebody who had not (e.g. the shop's opening, the wrong bill, the slow internet). The mock's lines are stock ("Did you see? ..."). | By co-location, and more than the report's proxy shows. The news reached the talk prompts (outage: 38 of 45 conversation prompts of people who knew, slow internet 30 of 37), and people talked about it with each other, but mostly with housemates or neighbours on the same street who already knew, which the proxy does not count. Counted passes: the wrong bill twice. Matt Webb heard from Valeria Vega "You'd better get on to them quick" and never did. The shop's opening was in 6 of 15 prompts and never mentioned. |
| Did anybody react to a broken promise? | 3 promises broken, 0 chased afterwards within the run; the mock rarely chases. | 2 promises broken, 21 kept, 0 chased after breaking. Chasing did happen before a promise fell due: 9 residents came back more than once, and two were credited $10 for it. |
| Were replies in character, or interchangeable? | Not answerable in mock: its lines are a fixed stock. | Mostly in character and specific: "They've had my money for two days. That's not my habit."; "Why did my bill jump to $184.60 this month?"; Owen Moore pressing Gary Moore about the internet money ("I'm starting to think you're keeping it"). The weak spots: Anna Markovic said "Tea sounds nice. Let me wash up first" three times over the run, and the helpdesk's own replies are fixed templates. |
| What differs between mock and live? | Contact rate (mock 19% of 100 affected, by a fixed rule), time to first contact (median 33.5 hours, by the mock's decision rota), and everything about wording. The plumbing - hours, households, promises, credits, dispatches, what gets fixed when - is the same code either way. | Contact rate 41% live against 19% mock; problems fixed by day 4 / 44 / 48 / 43 live against 1 / 44 / 47 / 44 mock, with 6 still broken against 9. Live adds what mock cannot: invented problems (6 contacts with no problem), many out-of-hours attempts (41% against 24%), conversation about the service in people's own words, and a retelling that misses the outages entirely. 10.4 minutes per in-game day on the 4090. |

## What the mock run showed about the engine

- Problems fixed by day: 1 / 44 / 47 / 44 across Days 1-4; 9 still open at
  the end, all wrong bills, which are corrected only when the customer gets in
  touch.
- The helpdesk dispatched 6 engineers, made 13 promises (10 kept, 3 broken)
  and corrected 3 bills.
- Flags: repeated line 7 and echo 4 (the mock's stock lines), stuck 2,
  no reaction 5, and none of the engine flags.

## Corrections to the live column and the results note

The step 5 reviewer checked the live report against its own record. These
claims above, and in `docs/results/pc-demo-live.md`, do not hold:

- **Hours to first contact (35.5 / 102) read a day too long**: the service
  section counted contacts from Day 2's clock and problems from Day 1's (fixed
  in `6191937`). The mock's 33.5 was inflated the same way. The regenerated
  live report has the right numbers, measured from the problem each contact
  was about.
- **"Who got in touch: 41" counted people who only ever heard the recording.**
  13 of the 41 never reached Northline; 28 did. The report now splits tried,
  reached and recording-only.
- **"The second outage, 21 of 43"** in the results note repeats the first
  outage's figure; the appendix shows about eight or nine contacts after Day 3
  18:00, several to a closed line.
- **"9 residents came back more than once" is not chasing.** It counted two or
  more contacts; most were retries after the recording or a new outage. The
  only real chase of a promise was Natalia Kovac. The report now counts
  "chased something they had been promised" on its own.
- **Both broken promises were artefacts**: made as the first outage ended,
  judged broken because the second had begun by the night they fell due.
  Promises are now judged on the problem they were about (`a950a9f`); the live
  run's two stay as logged.
- **"Problems fixed by day 4 / 44 / 48 / 43" was mostly the schedule**: the
  outages and the slow window ending on time. Northline itself fixed about 8
  slow homes and 6 bills. The report now separates the two.
- **Edward Shaw's washing machine was not prompted by his brother.** He said
  "Washing machine's on the blink. I'll get on to them" a day before Paul's
  line. With Northline the only service in town, any repair went to it; Henry
  Murray's "forms" is the same. These are a missing service, not invented
  outages, though the flag counts them together.
- **Will Ward's line is not an in-character example**: it is a complaint about
  a problem he never had. Better examples: Luis Vargas's call about the
  $184.60 bill; Owen Moore pressing Gary Moore about the internet money.

## What the helpdesk got wrong (left in: this is what the demo is for)

`NorthlineSupport` is the system under test. The town found these, and they
are not fixed, because a demo that fixes its own agent has nothing to show:

1. **It believes any outage it is told of.** Will Ward, whose street nothing
   touched, got a fault ticket and a $10 credit. It is handed the line's true
   state (`Message.problems`, the open problems at the address) and does not
   use it to check the claim. The report's findings now say so.
2. **Its keyword list misfires**: the bare "out" in its outage words caught
   "sort out this bill", so Oliver Hughes got an internet fault and a promise
   for a billing complaint (`populace/demos/isp.py`, `WORDS["outage"]`).
3. **Its "known fault" never clears.** Lena Petrov and Charlotte Bishop said
   their internet was back and were told "known fault... expect it back by
   tomorrow".
4. **It "corrected" a bill already corrected** when a later message mentioned
   the bill in passing (Natalia Kovac).
5. **It never works its out-of-hours messages.** Ruth Palmer texted twice at
   22:30 about her wrong bill and never got through; it was still wrong at the
   end.
6. **Its engineers arrived after the problem had ended**: three dispatches
   (Jakub, Paula, Natalia) came Day 4 10:00, after the slow internet ended Day 3.
7. **Every outage reply is the same template.**

## Where the simulation is weak (open questions for the owner)

1. **A text out of hours gets the recording.** A real ISP takes a text at any
   hour and answers in the morning; here the engine turns it away before the
   agent sees it, so much of the 41% out of hours is this design, and nobody
   learns the hours. Queue texts for opening time, or make the recording's
   hours shape the resident's next plan? (An engine change; not made.)
2. **Northline is the only service in town**, so washing machines and forms go
   to it. Register a few more (a council, a repair person), or count "wrong
   service" apart from "invented problem"?
3. **Few chances to decide.** 486 decisions for 200 residents over 4 days;
   Matt Webb thought once in the run, so "never did" after Valeria's advice
   was not a choice. The report now counts affected residents who had any
   decision while the problem was open; the contact rate should be read
   against it.
4. **Missing behaviours**: nobody visited the shop although 8 knew of it; one
   phone call in 59 contacts; nobody talked of switching after two outages in
   three days; the wrong bill moved no money, so ignoring it cost nothing.
5. **The echo flag fires on natural replies** ("I'm still open to it" answering
   "You're still open to it, right?").
6. **Invented problems**: the four invented outages are the model; flag
   `contact_ungrounded` now counts them apart from real contacts.

## Still to do

- ~~Fill the live column from the PC run's report.~~ Done on the PC.
- ~~One reviewer subagent over the live report and this file.~~ Done; its
  findings are fixed in the report and engine (`6191937`, `a950a9f`) or listed
  above.
- Regenerate the live report on the PC with the new report and narrator (the
  command is in `docs/STATUS.md`, "Step 5"); no new simulation run needed.
