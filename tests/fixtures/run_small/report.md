# Upton Green: run `run_small`

> **Mock run.** Every call was answered by the mock provider, which is deterministic and deliberately imperfect. The numbers below test the engine; they say nothing about how a model behaves.

## At a glance

| | |
|---|---|
| Residents | 12 |
| From | Day 1 06:00 for 48 half-hour ticks |
| Preset | laptop (6 calls a tick) |
| Wall clock | 0.0 s (0.0 min per in-game day) |
| Residents thinking per tick | 2.06 on average |
| Residents who thought at least once | 12 |
| Calls | 166 (dialogue 55, npc_decision 99, reflection 12) |
| Ticks over budget | 0 |
| Decisions valid first try | 92.4% |
| Conversations / lines / texts | 20 / 67 / 11 |
| Events / refusals | 297 / 19 |

## Findings

Two kinds, kept apart: mistakes by the outside agent under test, and weaknesses of the simulated town and of this report.

### What the agent got wrong

- Nothing these checks can see.

### Where the simulation is weak

- **Realism flags fired:** `repeated_line` 6, `echo` 3, `stuck` 1, `claim_unfounded` 1 (details under "Realism flags").
- **Word of mouth is measured narrowly.** "Passed on in conversation" counts only lines to somebody who had not seen it; talk among people who already knew is not counted, so a quiet number is not the same as a quiet town.
- **Talk of switching provider** is a keyword proxy, not a measured intention.

## What happened

The most important things that happened, in order, with the reason the person gave when it was their own decision.

- **Day 1 06:00**, Porter House: Abigail Mills told Colin Mills they would: drop it round - by Day 2.  
  *Why, in Abigail Mills's words:* (mock) owed
- **Day 1 07:00**: The internet went off at home. (seen by 12 residents)
- **Day 1 07:30**, The Copper Kettle: Colin Mills did not turn up for their shift at The Copper Kettle.  
  *Why, in Colin Mills's words:* (mock) goal
- **Day 1 07:30**, Fresh Fare: Colin Mills lent Abigail Mills $30. Due back Day 6.  
  *Why, in Colin Mills's words:* (mock) goal
- **Day 1 09:00**: A sign on the door of The Copper Kettle: closed until Day 3 - a burst pipe. (seen by 8 residents)
- **Day 1 10:30**, Fresh Fare: Abigail Mills took Esperanza Silva on.
- **Day 1 11:30**, Fresh Fare: Abigail Mills took Andrew Harper on.
- **Day 1 12:00**: A notice at Bridge Tavern: "Quiz night, Friday" (seen by 4 residents)
- **Day 1 12:30**: Hugo Ortega got on to Northline Internet about the internet; they said: "Sorry about that, Hugo. There's a fault on your line. An engineer will be with you tomorrow morning.". (seen by 1 resident)
- **Day 1 12:30**, The Copper Kettle: Colin Mills took Oliver Hunt on.  
  *Why, in Colin Mills's words:* (mock) addressed
- **Day 1 14:30**: Margaret Harper got on to Northline Internet about the internet; they said: "Sorry about that, Margaret. There's a fault on your line. An engineer will be with you tomorrow morning.". (seen by 2 residents)
- **Day 1 15:00**: Ian Harper got on to Northline Internet about the internet; they said: "Sorry about that, Ian. There's a fault on your line. An engineer will be with you tomorrow morning.". (seen by 2 residents)
- **Day 1 16:30**: Abigail Mills got on to Northline Internet about the internet; they said: "Sorry about that, Abigail. There's a fault on your line. An engineer will be with you tomorrow morning.". (seen by 1 resident)
- **Day 1 20:00**: The internet came back on at home. (seen by 12 residents)
- **Day 1 20:00**, Fresh Fare: Abigail Mills took Aarti Desai on.

The conversations that mattered most:

**Day 1 10:30**, Esperanza Silva and Abigail Mills at Fresh Fare:

> Esperanza Silva: Any work going?  
> Abigail Mills: Come in tomorrow and we'll see how you get on.  
> Esperanza Silva: We've had no internet at home all day. Nightmare.  
> *hire by Abigail Mills: landed*  

**Day 1 11:30**, Andrew Harper and Abigail Mills at Fresh Fare:

> Andrew Harper: Any work going?  
> Abigail Mills: Come in tomorrow and we'll see how you get on.  
> Andrew Harper: Did you see? The internet went off at home.  
> Abigail Mills: Come in tomorrow and we'll see how you get on.  
> *hire by Abigail Mills: landed*  

**Day 1 12:30**, Oliver Hunt and Colin Mills at The Copper Kettle:

> Oliver Hunt: Any work going?  
> Colin Mills: Come in tomorrow and we'll see how you get on.  
> Oliver Hunt: We've had no internet at home all day. Nightmare.  
> *hire by Colin Mills: landed*

## Who did what

**Colin Mills** thought 16 times, talked 6 times, was refused 6 times, money +$8.
- (mock) owed
- (mock) addressed
- (mock) goal

**Andrew Harper** thought 9 times, talked 7 times, was refused twice, money +$25.
- (mock) owed
- following the usual home block
- (mock) goal

**Abigail Mills** thought 10 times, talked 5 times, was refused twice, money +$110.
- (mock) owed
- (mock) goal
- (mock) addressed

**Aarti Desai** thought 9 times, talked 5 times, was refused 3 times, money +$20.
- (mock) owed
- (mock) addressed
- (mock) goal

**Oliver Hunt** thought 9 times, talked 5 times, was refused twice, money +$21.
- following the usual home block
- (mock) goal
- (mock) addressed

**Ian Harper** thought 7 times, talked 4 times, was refused once, money +$10.
- (mock) owed
- (mock) addressed
- (mock) scene

**Julio Valdez** thought 8 times, talked twice, was refused 3 times, money -$10.
- (mock) owed
- (mock) goal
- (mock) scene

**Esperanza Silva** thought 7 times, talked 3 times, money +$6.
- (mock) owed
- (mock) stale
- (mock) scene

**Margaret Harper** thought 5 times, talked twice.
- (mock) owed
- (mock) stale
- (mock) goal

**Hugo Ortega** thought 5 times, talked once, money +$146.
- (mock) owed
- (mock) stale
- (mock) scene

Everybody:

| Resident | Thoughts | Conversations | Money | Refused |
|---|---|---|---|---|
| Aarti Desai (r006) | 9 | 5 | +$20 | 3 |
| Abigail Mills (r010) | 10 | 5 | +$110 | 2 |
| Alejandra Valdez (r004) | 5 | 0 | -$25 | - |
| Andrew Harper (r001) | 9 | 7 | +$25 | 2 |
| Colin Mills (r009) | 16 | 6 | +$8 | 6 |
| Esperanza Silva (r008) | 7 | 3 | +$6 | - |
| Hugo Ortega (r012) | 5 | 1 | +$146 | - |
| Ian Harper (r002) | 7 | 4 | +$10 | 1 |
| Julio Valdez (r005) | 8 | 2 | -$10 | 3 |
| Luis Ortega (r011) | 2 | 0 | +$113 | - |
| Margaret Harper (r003) | 5 | 2 | - | - |
| Oliver Hunt (r007) | 9 | 5 | +$21 | 2 |

## What changed

From the start of the run to the last night it finished.

**Work.**

- Andrew Harper: no job to Fresh Fare
- Aarti Desai: no job to Fresh Fare
- Oliver Hunt: no job to The Copper Kettle
- Esperanza Silva: no job to Fresh Fare

**Money.**

- The town's residents together: +$424.
- Down most: Alejandra Valdez, -$25.
- Down most: Julio Valdez, -$10.
- Up most: Hugo Ortega, +$146.
- Up most: Luis Ortega, +$113.
- Up most: Abigail Mills, +$110.

**People.**

- 7 new acquaintances made, 0 names learned.

**What people came to believe** (one each, first eight):

- Andrew Harper: (mock) Things are about the same as they were.
- Ian Harper: (mock) Things are about the same as they were.
- Margaret Harper: (mock) Things are about the same as they were.
- Alejandra Valdez: (mock) Things are about the same as they were.
- Julio Valdez: (mock) Things are about the same as they were.
- Aarti Desai: (mock) Things are about the same as they were.
- Oliver Hunt: (mock) Things are about the same as they were.
- Esperanza Silva: (mock) Things are about the same as they were.

**Lives.**

- Nobody changed course.

## Injected

"Passed on in conversation" counts only lines from somebody who knew to somebody who had not seen it themselves: word of mouth to new people. People talking it over with others who already knew is not counted here.

**Day 1 06:00: service.register** (i80368dc200). Northline Internet [northline], home internet; by text or call.

- Known to: everybody.

**Day 1 07:00: event.outage** (iea2110ef57). The internet went off at home.

- Saw it happen: Abigail Mills.
- Ended: Day 1 20:00.
- Noticed it later: 11, first Margaret Harper (Day 1 07:00), Alejandra Valdez (Day 1 08:00), Oliver Hunt (Day 1 08:00), Esperanza Silva (Day 1 08:00), Aarti Desai (Day 1 08:30) and more.
- Touched directly: 12 (Andrew Harper, Ian Harper, Margaret Harper, Alejandra Valdez, Julio Valdez, Aarti Desai and more).
- Knew of it by the end: 12.
- Possibly heard of it in conversation, not having seen it: 1.
- Possibly passed on in conversation (2; a keyword proxy on internet):
  - Day 1 12:30: Oliver Hunt to Colin Mills: "We've had no internet at home all day. Nightmare."
  - Day 1 15:00: Aarti Desai to Colin Mills: "We've had no internet at home all day. Nightmare."

**Day 1 09:00: place.close** (i54215bd581). A sign on the door of The Copper Kettle: closed until Day 3 - a burst pipe.

- Saw it happen: Colin Mills.
- Noticed it later: 7, first Oliver Hunt (Day 1 10:30), Aarti Desai (Day 1 13:30), Abigail Mills (Day 1 14:30), Esperanza Silva (Day 1 15:00), Margaret Harper (Day 1 16:30) and more.
- Knew of it by the end: 8.
- Possibly heard of it in conversation, not having seen it: 1.
- Possibly passed on in conversation (1; a keyword proxy on burst, pipe):
  - Day 1 18:30: Margaret Harper to Andrew Harper: "Did you see? A sign on the door of The Copper Kettle: closed until Day 3 - a burst pipe."

**Day 1 12:00: event.notice** (idf79260dbd). A notice at Bridge Tavern: "Quiz night, Friday"

- Saw it happen: nobody.
- Noticed it later: 4, first Julio Valdez (Day 1 16:00), Ian Harper (Day 1 16:30), Oliver Hunt (Day 1 18:30), Colin Mills (Day 2 05:30).
- Knew of it by the end: 4.
- Passed on in conversation: no sign of it.

**Contacts with `northline`**: 4 from 4 residents (4 by text), the first at Day 1 09:30.

- Answered: 4. Got nowhere: 0.
- What the agent did: dispatch 4, promise 4.
- Came back more than once: 0.

## The service

**Northline Internet** (`northline`)

| | |
|---|---|
| Residents with a problem it handles | 12 |
| ...who had at least one decision while it was open | 12 |
| ...who tried to get in touch | 4 (33.3%) |
| ...who reached the service | 4 |
| ...who only ever got the recording | 0 |
| Hours from a problem starting to getting in touch about it, median / longest | 5.0 / 8.0 (over 4) |
| Contacts, answered / all | 4 / 4 |
| Got nowhere | 0 |
| By channel | text 4 |
| Contacts about a real problem at home | 4 |
| Contacts about a problem nobody at home had (the simulation inventing one) | 0 from 0 residents |
| Residents who got in touch twice or more | 0 |
| ...who chased something they had been promised | 0 |
| Homes that got in touch, and of those more than one person | 3, 1 |
| What the agent did | dispatch 4, promise 4 |
| Problems the service fixed, by day | none |
| Problems that ended on the schedule (not the service's doing), by day | Day 1: 12 |
| Still broken at the end | 0 |
| Promises made / to people with no such problem | 4 / 0 |
| Promises kept / broken / not yet due at the end / broken and then chased | 0 / 0 / 4 / 0 |
| Talked of switching provider (keyword proxy) | 0 |

## How well the model did its job

*Mock run: these numbers describe the mock provider, which errs on purpose.*

| | |
|---|---|
| Decisions valid first try | 92.4% |
| Retries / fell back to routine | 8 / 0 |
| Call latency, median / p90 | 0.0 s / 0.0 s |
| Server errors | 0 |
| Share of input read from the prompt cache | 0.894 |
| Replies that echo the line before | 6.4% |
| Lines with the speaker's own name | 0.0% |
| Questions left unanswered | 0 of 21 |
| Lines repeating what the speaker already said today | 14.9% |
| Deals asserted / landed | 12 / 12 |
| Things said about somebody that they never said | 0 of the 0 such claims |
| Names used without having been given | 0 |
| Ids said out loud | 0 |

## Realism flags

Mechanical checks over the logs. A flag is a reason to look, not a verdict.

| Flag | Count | What it means |
|---|---|---|
| `repeated_line` | 6 | somebody said the same line, word for word, more than once |
| `echo` | 3 | a reply that repeats most of the line it answers |
| `stuck` | 1 | the same decision 4 times running |
| `impossible_move` | 0 | somebody arrived in a home that is neither theirs nor anybody's they know |
| `sleepless` | 0 | active through a stretch of 24 hours with no sleep in it |
| `no_reaction` | 0 | saw something of importance 7+ and had no thought for 4 ticks |
| `ghost_contact` | 0 | a text between two people with no tie at all |
| `money_from_nowhere` | 0 | somebody's money changed by more than the run's money events explain |
| `promise_ignored` | 0 | a broken promise the person let down never did anything about |
| `provider_down_window` | 0 | a stretch of ticks where the model did not answer |
| `id_spoken` | 0 | somebody said a resident id out loud |
| `name_unknown` | 0 | somebody used the name of a person whose name they had not been given |
| `claim_unfounded` | 1 | somebody spoke of money owed between them and a person with no debt, loan, rent or wage between them |
| `contact_ungrounded` | 0 | a resident got in touch with a service about a problem nobody in their home had |

**`repeated_line`**, first 5 of 6:

- Day 1 10:00: Oliver Hunt said "did you see the internet went off at home" 2 times
- Day 1 12:30: Oliver Hunt said "we've had no internet at home all day nightmare" 2 times
- Day 1 11:30: Abigail Mills said "come in tomorrow and we'll see how you get on" 4 times
- Day 1 13:00: Esperanza Silva said "we've had no internet at home all day nightmare" 3 times
- Day 1 13:30: Andrew Harper said "did you see the internet went off at home" 2 times

**`echo`**, first 3 of 3:

- Day 1 10:00: Oliver Hunt echoed Aarti Desai: "Did you see? The internet went off at home."
- Day 1 15:00: Aarti Desai echoed Colin Mills: "We've had no internet at home all day. Nightmare."
- Day 1 18:00: Julio Valdez echoed Ian Harper: "Did you see? A sign on the door of The Copper Kettle: closed until Day 3 - a burst pipe."

**`stuck`**, first 1 of 1:

- Day 1 22:00: Julio Valdez chose talk Ian Harper 4 times running

**`claim_unfounded`**, first 1 of 1:

- Day 1 16:30: Hugo Ortega spoke of money owed with Andrew Harper, and nothing stands between them: "You still owe me a coffee, you know."

## Appendix

### Every conversation

**Day 1 06:00**, Abigail Mills and Colin Mills at Porter House:

> Abigail Mills: You still owe me a coffee, you know.  
> Colin Mills: Can't complain.  
> Abigail Mills: I'll drop it round tomorrow.  
> *promise by Abigail Mills: landed*  

**Day 1 07:30**, Abigail Mills and Colin Mills at Fresh Fare:

> Abigail Mills: Could you spot me thirty till Friday?  
> Colin Mills: Go on. Friday, mind.  
> Abigail Mills: Thanks. I'll pay you back in a couple of days, promise.  
> *loan by Colin Mills: landed*  
> *promise by Abigail Mills: landed*  

**Day 1 09:30**, Oliver Hunt and Aarti Desai at Porter House:

> Oliver Hunt: Any work going?  
> Aarti Desai: Right, I'd better get on.  
> Oliver Hunt: Did you see? The internet went off at home.  
> Aarti Desai: Same as ever.  

**Day 1 10:00**, Aarti Desai and Oliver Hunt at Porter House:

> Aarti Desai: Any work going?  
> Oliver Hunt: We've had no internet at home all day. Nightmare.  
> Aarti Desai: Did you see? The internet went off at home.  
> Oliver Hunt: Did you see? The internet went off at home.  

**Day 1 10:30**, Esperanza Silva and Abigail Mills at Fresh Fare:

> Esperanza Silva: Any work going?  
> Abigail Mills: Come in tomorrow and we'll see how you get on.  
> Esperanza Silva: We've had no internet at home all day. Nightmare.  
> *hire by Abigail Mills: landed*  

**Day 1 11:30**, Andrew Harper and Abigail Mills at Fresh Fare:

> Andrew Harper: Any work going?  
> Abigail Mills: Come in tomorrow and we'll see how you get on.  
> Andrew Harper: Did you see? The internet went off at home.  
> Abigail Mills: Come in tomorrow and we'll see how you get on.  
> *hire by Abigail Mills: landed*  

**Day 1 12:00**, Oliver Hunt and Colin Mills at The Copper Kettle:

> Oliver Hunt: Any work going?  
> Colin Mills: We've had no internet at home all day. Nightmare.  
> Oliver Hunt: We'll see.  

**Day 1 12:30**, Oliver Hunt and Colin Mills at The Copper Kettle:

> Oliver Hunt: Any work going?  
> Colin Mills: Come in tomorrow and we'll see how you get on.  
> Oliver Hunt: We've had no internet at home all day. Nightmare.  
> *hire by Colin Mills: landed*  

**Day 1 13:00**, Andrew Harper and Esperanza Silva at Fresh Fare:

> Andrew Harper: Long time. How are you keeping?  
> Esperanza Silva: Tell me about it.  
> Andrew Harper: Could be worse.  
> Esperanza Silva: We've had no internet at home all day. Nightmare.  

**Day 1 13:30**, Esperanza Silva and Andrew Harper at Fresh Fare:

> Esperanza Silva: Could you spot me thirty till Friday?  
> Andrew Harper: Did you see? The internet went off at home.  
> Esperanza Silva: We've had no internet at home all day. Nightmare.  

**Day 1 14:30**, Aarti Desai and Colin Mills at The Copper Kettle:

> Aarti Desai: Any work going?  
> Colin Mills: We've had no internet at home all day. Nightmare.  
> Aarti Desai: Haven't heard, no.  

**Day 1 15:00**, Colin Mills and Aarti Desai at The Copper Kettle:

> Colin Mills: Let me get this one.  
> Aarti Desai: Go on then, thanks.  
> Colin Mills: We've had no internet at home all day. Nightmare.  
> Aarti Desai: We've had no internet at home all day. Nightmare.  
> *gift_accept by Aarti Desai: landed*  

**Day 1 15:30**, Andrew Harper and Ian Harper at 9 Bridge Street:

> Andrew Harper: Didn't expect to see you here.  
> Ian Harper: Did you see? The internet went off at home.  
> Andrew Harper: Right, I'd better get on.  

**Day 1 16:30**, Hugo Ortega and Andrew Harper at Upton Green Common:

> Hugo Ortega: You still owe me a coffee, you know.  
> Andrew Harper: Meet me later?  
> Hugo Ortega: We'll see.  
> *invite by Andrew Harper: landed*  

**Day 1 18:00**, Julio Valdez and Ian Harper at The Copper Kettle:

> Julio Valdez: Heard anything about the factory?  
> Ian Harper: Did you see? A sign on the door of The Copper Kettle: closed until Day 3 - a burst pipe.  
> Julio Valdez: Did you see? A sign on the door of The Copper Kettle: closed until Day 3 - a burst pipe.  

**Day 1 18:30**, Margaret Harper and Andrew Harper at 9 Bridge Street:

> Margaret Harper: Don't suppose you've got change?  
> Andrew Harper: You know how it is.  
> Margaret Harper: Did you see? A sign on the door of The Copper Kettle: closed until Day 3 - a burst pipe.  

**Day 1 19:30**, Ian Harper and Oliver Hunt at Bridge Tavern:

> Ian Harper: Let me get this one.  
> Oliver Hunt: No, you keep it.  
> Ian Harper: You know how it is.  
> Oliver Hunt: Did you see? A notice at Bridge Tavern: "Quiz night, Friday"  
> *gift_accept by Oliver Hunt: landed*  

**Day 1 20:00**, Aarti Desai and Abigail Mills at Porter House:

> Aarti Desai: Any work going?  
> Abigail Mills: Come in tomorrow and we'll see how you get on.  
> Aarti Desai: Same as ever.  
> Abigail Mills: Can't complain.  
> *hire by Abigail Mills: landed*  

**Day 1 21:30**, Andrew Harper and Margaret Harper at 9 Bridge Street:

> Andrew Harper: Heard anything about the factory?  
> Margaret Harper: Same as ever.  
> Andrew Harper: I'll drop it round tomorrow.  
> *promise by Andrew Harper: landed*  

**Day 1 22:00**, Julio Valdez and Ian Harper at Bridge Tavern:

> Julio Valdez: Let me get this one.  
> Ian Harper: Go on then, thanks.  
> Julio Valdez: Mind how you go.  
> *gift_accept by Ian Harper: landed*  

### Every contact with a service

**Day 1 09:30**, Abigail Mills to `northline` by text:

> Abigail Mills: Hi, I'm having trouble with my internet.  
> northline: Sorry about that, Abigail. There's a fault on your line. An engineer will be with you tomorrow morning.  
> *dispatch: at Day 2 09:00, fixes True, kind None*  
> *promise: by_day 2, kind None, what fixed by tomorrow*  

**Day 1 10:30**, Hugo Ortega to `northline` by text:

> Hugo Ortega: Hi, I'm having trouble with my internet.  
> northline: Sorry about that, Hugo. There's a fault on your line. An engineer will be with you tomorrow morning.  
> *dispatch: at Day 2 09:00, fixes True, kind None*  
> *promise: by_day 2, kind None, what fixed by tomorrow*  

**Day 1 13:30**, Margaret Harper to `northline` by text:

> Margaret Harper: Hi, I'm having trouble with my internet.  
> northline: Sorry about that, Margaret. There's a fault on your line. An engineer will be with you tomorrow morning.  
> *dispatch: at Day 2 09:00, fixes True, kind None*  
> *promise: by_day 2, kind None, what fixed by tomorrow*  

**Day 1 15:00**, Ian Harper to `northline` by text:

> Ian Harper: Hi, I'm having trouble with my internet.  
> northline: Sorry about that, Ian. There's a fault on your line. An engineer will be with you tomorrow morning.  
> *dispatch: at Day 2 09:00, fixes True, kind None*  
> *promise: by_day 2, kind None, what fixed by tomorrow*  

### Every refusal, by reason

- 5 x I had already talked with Colin Mills today
- 4 x I had already talked with Oliver Hunt today
- 2 x I had already talked with Aarti Desai today
- 2 x I had already talked with Abigail Mills today
- 2 x I had already talked with Ian Harper today
- 1 x I had already talked with Esperanza Silva today
- 1 x I had already talked with Julio Valdez today
- 1 x I had already talked with Margaret Harper today
- 1 x they weren't there to hand it to
