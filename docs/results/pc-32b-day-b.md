# Day B on a 32B, on the PC's 4090

Option 1 from the step 4 hand-off: run day B on a stronger local model, to see
whether "nobody contacts the service" is the 7B or the design. Run on 28
September 2026 on the Windows 4090 box. Every number here is copied from the
run's `manifest.json` / `report.md` or counted from its logs.

**Answer: it was the 7B.** On the same town, the same injections, the same
prompts and the same agent, 9 of the 12 residents without internet contacted
Northline, 14 times, the first at 08:30, half an hour after it opened. The 7B
did it 0 times on three days. The owner's 14 September fine-tune of that 7B,
run the same way afterwards, also made 0 contacts (see "The fine-tune on the
same day").

## What was run

Everything as STATUS describes day B, except the model and where it ran.

| | |
|---|---|
| Code | `00e1f74` (only docs changed since `9c8a8d8`, the commit day B ran on) |
| Town | `worldsim new "a small town of 50 people with a diner, a grocery and a workshop" --seed 3` (Brookhaven, 50 residents, 23 households, persona prose from templates) |
| Injections | `docs/samples/live-day-injections.json`, all 4 scheduled, 0 refused |
| Run | `worldsim run <town> --days 1 --model-url http://127.0.0.1:8080/v1 --preset laptop --profile compact --agent northline=helpdesk --run-id live-32b-dayB` |
| Concurrency | `providers.local.max_concurrency: 2` in the town's `config.json` (default 1); no other config change |
| Model | `Qwen/Qwen3-32B-GGUF`, file `Qwen3-32B-Q4_K_M.gguf`, SHA256 `efd97156...d57d1f689` checked against Hugging Face |
| Server | llama.cpp b10955 CUDA, `llama-server --host 127.0.0.1 -ngl 99 -fa on -ctk q8_0 -ctv q8_0 -c 18432 -np 2 --cache-reuse 256 --jinja --reasoning-budget 0 --chat-template-kwargs {"enable_thinking":false}`: two slots of 9,216 tokens, thinking off, 22.4 of 24.5 GB VRAM |
| Run directory | `towns/proof50-pc32b/runs/live-32b-dayB` on the PC (towns are gitignored) |

Windows: `pip install -e ".[dev]"` and all 234 tests passed unchanged
(Python 3.13.15, 219 s). Nothing in worldsim needed a fix.

## Side by side

The first three columns are copied from STATUS ("Three live days"), base
`mlx-community/Qwen2.5-7B-Instruct-4bit` on the Mac, concurrency 1.

| | Day A: 7B compact | Day B: 7B compact, reasons | Day C: 7B frontier, reasons | **Day B: 32B, 4090** | **Day B: 7B + Sept 14 LoRA, 4090** |
|---|---|---|---|---|---|
| Minutes for the day | 55.9 | 57.5 | 55.5 | **9.3** | 5.3 |
| Calls | - | 174 | - | 200 | 187 |
| Decisions valid first try | 91.5% | 93.2% | 78.6% | **99.2%** (1 retry, 1 fallback) | 93.2% (8 retries, 5 fallbacks) |
| Refusals | 26 | 10 | 6 | 14 (13 "already talked with X today", 1 shift) | 13 (9 already talked, 4 shift) |
| Decisions by the twelve without internet | 26 | 25 | 26 | 25 | 22 |
| ...whose reasoning mentions the internet | 2 | 4 | 10 | 13 (see note) | 5 |
| **Contacts with the helpdesk** | **0** | **0** | **0** | **14, from 9 residents** (13 text, 1 call) | **0** |
| Realism flags | stuck 1 | repeated line 1, echo 5 | echo 1 | repeated_line 3, claim_unfounded 4 | stuck 1, claim_unfounded 1 |
| Conversations / lines / texts | - | 16 / 45 / 0 | - | 24 / 79 / 12 | 17 / 58 / 0 |
| Call latency, median / p90 | - | - | - | 3.6 s / 7.2 s | 2.1 s / 4.2 s |
| Prompt cache share of input | - | - | - | 70% | 72% |

Note on the internet row: counted here by a whole-word match on internet,
wifi, broadband, Northline or connection in the decision's reasoning and
dialogue. The 7B columns' method is not recorded, so treat the comparison as
approximate. For the 32B, 12 of the 13 are `contact` decisions; for the
LoRA, none of the 5 is.

The run is not identical to the Mac's in two ways besides the model: a
llama.cpp Q4_K_M GGUF instead of MLX 4-bit, and two calls at once instead of
one. The laptop preset's budget (6 calls a tick) is unchanged, so the
residents thinking per tick (2.58 against 2.44) are comparable.

## What the twelve did

The helpdesk answered 11 of the contacts. The other 3 came after 20:00 and
got the recording with the hours. It dispatched an engineer for Day 2 09:00
and promised a fix by Day 2 nine times, and four residents came back to chase
it up.

| Resident | Home | What they did | Reason, in their words |
|---|---|---|---|
| Molly Mason | 17 | texted 08:30; texted again 20:30 (closed) | "It's what I pay them for." / "I got tired of waiting" |
| Anna Sokolov | 11 | texted 09:00 | "down for two hours now, and I need it working for school" |
| Nick Mason | 17 | texted 09:30; chased 17:00 | "It's time I pushed for an update." |
| Sofía Acosta | 23 | **called** 10:00 | "check if there's a problem with the service" |
| Lucy Mason | 17 | texted 11:00 | "I'll give it until noon and then call the provider." |
| Marina Sokolov | 11 | texted 12:00 | "check if it's just me and then get it sorted" |
| Rocío Ortega | 23 | texted 12:30 | "It's something I pay for, and it's been down for hours." |
| Liam Fletcher | 7 | texted 14:00; chased 15:30; texted 23:00 (closed) | "It's what you pay them for." |
| Yuri Sokolov | 11 | worked; texted 16:00; texted 05:00 Day 2 (closed) | "better to get it sorted while I still have time" |
| Yusuf Agarwal | 19 | waited, then took a neighbour something he baked | "It happens sometimes. Give it a few hours." |
| Svetlana Wisniewski | 13 | at work in the city all day, then home to bed | - |
| Ivan Wisniewski | 13 | waited, then talked it over with Svetlana in the evening | "I need to know if it's just me or if there's something else going on." |

Where a household had more than one adult, several of them reported it
separately (all three Masons, all three Sokolovs at home). Real households do
that too, but not this often, so the next thing to look at is probably
whether a resident knows that somebody at home has already reported it.

The three who did not contact fit their dispositions ("give it a few hours")
or their day (a commuter out until the evening). The reasons use the step 4
wording almost word for word ("It's what I pay them for", "get on to
Northline"), so the permission lines are being read and taken up.

## What else the day showed

- **Word of mouth did not appear**: the outage, the diner's sign and the quiz
  notice were each "passed on in conversation: no sign of it" (the 7B's day B
  passed the quiz on twice). The 32B's conversations were about their own
  lives instead: a mother's overdue birthday money, a gift for a neighbour.
- **`claim_unfounded` fired 4 times**, all invented money between family or
  neighbours ("You owe me ten bucks from last week, right?"). The 32B makes
  up backstory debts more readily than the 7B did, and the flag catches every
  one.
- **`repeated_line` 3**, all in one late-night Simon/Adam conversation at
  Day 2 00:30.
- **Refusals changed character**: 13 of 14 are "I had already talked with X
  today" (the once-a-day conversation limit), and only 1 is a shift
  misreading, where the 7B's refusals were mostly shifts.
- **Speed**: 9.3 minutes for the day at the laptop preset, about 6× the M1.
  The `gpu` preset (30 calls a tick, 8 slots) would need a smaller context per
  slot on 24 GB. It was not tried.

## The fine-tune on the same day

Run the same way on the same evening: a fresh copy of the town (checked
identical to another fresh copy except for timestamps in the generation log),
the same injections, compact profile, laptop preset, helpdesk agent and
`max_concurrency: 2`. The only difference is the server:
`llama-server` with the official fp16 `Qwen/Qwen2.5-7B-Instruct-GGUF` and
`--lora` the 14 September adapter (r=16, step 488) converted with llama.cpp. Its `/lora-adapters`
reported scale 1.0. Same slots, context and KV cache type as the 32B, and no
thinking to switch off. Run `towns/proof50-pc-lora/runs/live-lora-dayB`. Its
manifest names only the base GGUF, because worldsim records the `-m` path and
not the adapter.

**Zero contacts, like the base 7B.** Nobody chose `contact` all day. Of the
twelve's 22 decisions, 5 mention the internet, and all 5 accept it: "the
internet is dead. Bed's the sensible place"; "The internet's still out, so
I'll just sit here"; "I'm at home and not working. The internet is dead ...
Time to eat". Two neighbours at 23 Station Crescent talked it over: "It's been
three hours. I need it fixed, and she's here. We can do it together." And one
of them reasoned "They gave me an answer, but it's still tomorrow", which is an
answer that never came, because nobody had contacted anyone.

The fine-tune's own strengths show elsewhere. Its lines are shorter and
plainer, and a burst pipe travelled once by word of mouth ("Pipe burst. Closed
for the weekend.", Nancy Holland to somebody who had not seen the sign). It
invented only one debt against the 32B's four.

Its weak points against the 32B:
- JSON validity is back at the base 7B's 93.2%, with 8 retries and 5
  fallbacks against 1 and 1.
- 4 of its refusals are shift misreadings, where the 32B had 1.
- 4 of 25 questions were left unanswered, against 1 of 26.

This fits what was expected at the step 4 hand-off. The adapter was trained
on Alive, which has no services, so it has never seen a `contact` to a
business. Its training prompts were also all Alive's `frontier` profile, so
under `compact` it is off-distribution
as well. **Contacting a service is the 32B's behaviour, not something the
fine-tune has.** A worldsim fine-tune would need examples of it in its data.

## Not done here

- No `--narrate` retelling.
- Day B was run once. One day is one sample. Rerunning it with a different
  seed would show how stable 9 of 12 is.
- STATUS.md is untouched; the Mac session owns it.
