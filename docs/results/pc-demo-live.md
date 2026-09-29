# The ISP demo, live on the PC's 32B

> **Corrections (Mac, after the step 5 reviewer):** the hours-to-contact
> figures here read a day too long; "41 got in touch" includes 13 who only
> heard the recording; "the second outage, 21 of 43" repeats the first's
> figure; "9 came back" is not chasing; both broken promises were artefacts.
> Details in [../../demo/isp/NOTES.md](../../demo/isp/NOTES.md), "Corrections".

Step 5's live run, done on the Windows 4090 on 28 September 2026 with the
commands in `docs/STATUS.md` ("Commands for the PC"), in order. Every number
is copied from the run's `manifest.json` / `report.md` or counted from its
logs. The full report, with the model's retelling, is
[../samples/isp-200-live-32b-report.md](../samples/isp-200-live-32b-report.md);
the realism checklist is filled in
[../../demo/isp/NOTES.md](../../demo/isp/NOTES.md).

## What was run

| | |
|---|---|
| Code | `ecc6f86` (main after the Mac's step 5 commits) |
| Tests on Windows | 249 passed, 222 s, nothing changed |
| Server | llama.cpp b10955, `Qwen3-32B-Q4_K_M.gguf` (SHA256 checked, see [pc-32b-day-b.md](pc-32b-day-b.md)), `--host 127.0.0.1`, 2 slots of 9,216 tokens, q8_0 KV, `--cache-reuse 256`, thinking off |
| Demo | `worldsim demo isp --out towns\isp-200 --days 4 --model-url http://127.0.0.1:8080/v1 --concurrency 2 --profile compact --run-id live-32b-4d` |
| Report | `worldsim report ... --narrate --provider local --model-url http://127.0.0.1:8080/v1` |

Nothing broke on Windows and no code was changed.

## Headline numbers

| | Live, 32B | Mock (for reference) |
|---|---|---|
| Residents / days | 200 / 4 | 200 / 4 |
| **Minutes per in-game day** | **10.4** (41.7 min in all) | 40 s in all |
| Calls | 807 (486 decisions, 241 dialogue, 80 reflections) | - |
| Decisions valid first try | 94.1% (30 retries, 2 fallbacks) | - |
| Residents with a problem Northline handles | 100 | 100 |
| **...who got in touch** | **41** | 19 |
| Contacts | 59 (58 text, 1 call) | 21 |
| Out of hours (got the recording) | 24 of 59 | 5 of 21 |
| Hours from problem to first contact, median / longest | 35.5 / 102 | 33.5 median |
| **Homes that reported, and of those more than once** | **29, 6** | 16, 3 |
| **Contacts from residents with no such problem** | **6** | 0 |
| **Promises kept / broken / broken then chased** | **21 / 2 / 0** | 10 / 3 / - |
| Came back more than once | 9 | - |
| What the agent did | promise 26, dispatch 11, resolve 7, credit 2 | - |
| Problems fixed by day | 4 / 44 / 48 / 43 | 1 / 44 / 47 / 44 |
| Still broken at the end | 6 | 9 |
| Talk of switching provider (proxy) | 0 | - |
| Conversations / lines / texts | 98 / 317 / 64 | - |
| Refusals | 58 | - |
| **Flags** | repeated_line 3, echo 3, stuck 3, no_reaction 1; claim_unfounded 0 | repeated 7, echo 4, stuck 2, no reaction 5 |

Who got in touch, by problem: the first outage street 21 of 43, the wrong
bills 8 of 12, slow internet 13 of 47, the second outage (same street) 21 of
43.

## news_in_talk

**Day B, the 32B (`towns/proof50-pc32b/runs/live-32b-dayB`, the logs from
before `b76b924`):**

```
event.outage (i4c002193d6), words internet: 12 knew
  conversation calls by knowers after knowing: 8; prompts carrying the news: 8
  talk decisions by knowers after knowing: 6; openers using its words: 1
  their talks refused as already talked today: 1
place.close (if2c770455f), words burst, pipe, kitchen: 5 knew
  conversation calls by knowers after knowing: 2; prompts carrying the news: 2
  talk decisions by knowers after knowing: 2; openers using its words: 0
  their talks refused as already talked today: 0
event.notice (i6b33fa0afb), words quiz: 18 knew
  conversation calls by knowers after knowing: 26; prompts carrying the news: 16
  talk decisions by knowers after knowing: 17; openers using its words: 4
  their talks refused as already talked today: 3
```

**Neither of the two suspected causes was the main one on day B.**

- The news did reach the prompts: the quiz was in 16 of 26, the outage in all 8.
- Only 3 talks were refused under the once-a-day rule.
- The 32B did talk about the quiz: "You seen the notice at Valley Foods? Quiz
  night at the bar Friday." and "I saw the notice at the grocery. Quiz night,
  Friday. You in?".
- Every listener had already seen the notice themselves. The report's "passed
  on" proxy counts only lines to somebody who did not know, so it said "no
  sign of it".

The fixes in `b76b924` are still right, but on day B the silence was mostly
the listeners already knowing. The proxy measures word of mouth to new people,
not talk about the news.

**The demo (`live-32b-4d`, with the fixes):**

| Injection | Knew | Conversation prompts carrying it | Openers using its words | Refused, already talked |
|---|---|---|---|---|
| Northline shop opens | 8 | 6 of 15 | 0 | 0 |
| Outage, Day 1 | 43 | 38 of 45 | 4 | 3 |
| Wrong bills (12 letters) | 1 each | 17 of 25 in all | 0 | 0 |
| Slow internet, Day 2 | 47 | 30 of 37 | 2 | 2 |
| Outage again, Day 3 | 43 | 20 of 21 | 2 | 3 |

With the fixes the news is in most prompts, and the once-a-day rule refuses
almost nobody. People do talk about the outages, but on the affected street,
with people who already know. The report counts two passes, both about the
wrong bill (Day 4, Alejandra Medina to Sofía Medina; Paul Shaw to Edward
Shaw). The shop's opening was never mentioned.

## Ten moments, good and bad

1. **Good: a clean wrong-bill call.** Luis Vargas made the only phone call of
   the run, Day 1 18:00: "Why did my bill jump to $184.60 this month?" It was
   corrected on the spot. Neha Joshi: "It was $39 last time."
2. **Good: chasing a promise that did not seem to land.** Will Ward, Day 3:
   "The internet's still down. It was supposed to be back by tomorrow." The
   helpdesk credited him $10. **Bad, the same man:** Will Ward never had a
   problem. His home is on Clover Street, which nothing touched. He invented the
   outage on Day 2, the helpdesk believed him, and he complained about it to a
   neighbour on Day 4: "They've had my money for two days. That's not my
   habit."
3. **Bad: six contacts from people with no problem.** Four invented an internet
   outage. Henry Murray texted the ISP about "the forms I submitted last week".
   Edward Shaw texted about his washing machine ("I've been having internet
   issues and suspect it's something to do with the line") straight after Paul
   Shaw said "I've had my share of trouble with Northline. Best to get
   on to them quick." The helpdesk trusts every report, so two invented reports
   from the building at 5 Clover Street, which is named Clover Court, produced
   "There's a known fault on Clover Court".
4. **Good: households now know somebody has reported it.** 6 of 29 reporting
   homes reported twice, against every multi-adult home on day B before the
   fix. Keith Moore to Beth Moore, Day 3 23:30: "I gave it a few hours after
   the shift. I'll head over to the office in the morning." (He did not; it
   came back at 08:00.)
5. **Bad: 41% of attempts out of hours.** 24 of 59 contacts came before 08:00
   or after 20:00, most between 20:00 and 23:30. Ruth Palmer texted about her
   wrong bill at 22:30 on Day 2 and again at 22:30 on Day 4, got the
   recording both times, and never got through. Her bill is still wrong.
6. **Good: an engineer visit that residents remember and pass on.** Julia
   Burton, Day 4: "You had Northline out yesterday, then?" Zoe Burton: "Aye,
   they came yesterday and fixed it up." Julia: "I was going to ask if they
   said when they'd get to us next door." And Jane Parker, Day 2: "I heard the
   engineer's coming tomorrow at ten. Fingers crossed."
7. **Mixed: advice given, not taken.** Matt Webb, Day 3: "I hear Northline
   Internet dropped by... I've been wrestling with mine again this morning."
   Valeria Vega: "You'd better get on to them quick." Matt never contacted
   them.
8. **Good: money talk in character, and nothing invented.**
   `claim_unfounded` is 0 over four days, where day B had 4. Owen Moore to Gary
   Moore: "You got the money for the internet sorted out yet?" / "Not yet.
   Watch this space." / "You say that every time, Gary. I'm starting to think
   you're keeping it."
9. **Bad: the helpdesk's rules show through.** Natalia Kovac's third contact
   is about slow speed, but it mentions the bill in passing, so the bill was
   "corrected" a second time. Every outage reply is the same template. The
   helpdesk is rule-based by design; these are its limits, not the model's.
10. **Bad: the retelling misses the story.** The model-written summary at the
    top of the report does not mention an outage, the slow internet or
    Northline at all. It turns the twelve wrong-bill texts into "several people
    in the city noticed something", calls the next day "three days later", and
    leads with the town's $62,445 in wages. The report labels it as possibly
    wrong, and the sections below it are right. As a demo summary, it fails.

## For the Mac session

- **Invented problems** are the new realism question. The helpdesk could check
  a claimed fault against the customer's open problems, as a real ISP checks
  the line. The resident prompt could also make clearer that the outage is on
  other people's streets. Neither was changed here.
- **Street from a named building:** `_street()` in `worldsim/demos/isp.py`
  takes the street from the customer's address, and for a named block that
  address is the block's name ("Clover Court"), not "5 Clover Street". So
  "known fault" counts reports per building there, not per street.
- **Retelling:** the narrator's input or prompt should put the injections and
  the service section first.
- **The passed-on proxy** only counts lines to somebody who did not know. That
  is the right measure of word of mouth, but the report should say so, or it
  reads as silence.
- The reviewer subagent over this report and NOTES.md, the step 5 hand-off,
  was not run here. It is left for the Mac session.
