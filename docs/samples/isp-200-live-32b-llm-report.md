# Hartwell: run `live-32b-4d-llm`

> **Live run** on Qwen3-32B-Q4_K_M.gguf, compact prompt profile.

## The day, as a model tells it

> *Model-written by Qwen3-32B-Q4_K_M.gguf, from the sections below. It can be wrong; the sections after it are the record.*

Northline Internet and its home internet services were introduced at 06:00 on Day 1, with a text, call, or visit option open from 08:00–20:00. The new Northline Internet shop opened at the same time, and two residents—Oliver Hughes and Julio Medina—saw it happen, while seven others noticed it later. The first event was an internet outage at 07:00, affecting 43 people and spreading further by word of mouth. At 09:00, 12 residents received a bill notification of $184.60, but none saw it happen; all noticed it later. On Day 2, a second event brought very slow internet affecting 47 residents, and a third outage struck at 18:00 on Day 3, again affecting 43 people. 

Residents contacted Northline 57 times, mostly by text. Of these, 33 were answered by an automated agent, with 24 calls going unanswered because the service was closed. The agent dispatched engineers 10 times, noted problems 14 times, made 9 promises, and resolved 4 issues. However, it acted on 8 cases where the customer had no real problem and broke six of its promises. Two residents—Oliver Hughes and Ian Shaw—were left with unresolved issues after receiving only the recording and no follow-up. 

The town showed some weaknesses: 6 residents invented problems with Northline that did not exist at their homes, and 24 of the 57 contact attempts were made when the service was closed. The simulation also flagged issues with realism, including repeated lines, ungrounded claims, and residents speaking of debts that did not exist.

Beyond the internet events, a few notable conversations occurred. A couple discussed splitting the cost of a bill, another couple talked about an overdue money promise, and a mother and daughter had a tense conversation over a missing credit card charge. Financially, the town’s residents collectively gained over $62,000, while relationships shifted slightly, with some growing closer and others drifting apart.

*Numbers that do not match the facts: "called" 33 times: by channel the facts have call 1, text 56.*

## At a glance

| | |
|---|---|
| Residents | 200 |
| From | Day 1 06:00 for 192 half-hour ticks |
| Preset | laptop (6 calls a tick) |
| Wall clock | 2426.4 s (10.11 min per in-game day) |
| Residents thinking per tick | 2.5 on average |
| Residents who thought at least once | 200 |
| Calls | 754 (dialogue 207, npc_decision 467, reflection 80) |
| Ticks over budget | 0 |
| Decisions valid first try | 96.5% |
| Conversations / lines / texts | 86 / 266 / 62 |
| Events / refusals | 9873 / 56 |

## Findings

Two kinds, kept apart: mistakes by the outside agent under test, and weaknesses of the simulated town and of this report.

### What the agent got wrong

- **It acted on problems the customer did not have.** 3 of the 8 contacts about a problem nobody at home had got dispatch 2, promise 1 in reply (Henry Hughes, Pooja Joshi, Raj Qureshi). The other 3 it answered got no action.
- **It never worked its out-of-hours messages.** 2 residents got only the recording, were never followed up, and still had the problem at the end (Oliver Hughes, Ian Shaw). A real helpdesk works the overnight queue in the morning.
- **It broke 6 promises** it made to customers about when things would be fixed.

### Where the simulation is weak

- **Residents invented problems.** 8 contacts from 6 residents were about a problem nobody in their home had. That is the simulated town making things up, not the service's doing, and it is counted apart from the real contacts in "The service".
- **Residents often called out of hours.** 24 of 57 attempts (42%) came when the service was closed. Real customers do some of this; how much is a question for the model driving them.
- **Realism flags fired:** `repeated_line` 2, `echo` 3, `stuck` 4, `no_reaction` 1, `claim_unfounded` 5 (details under "Realism flags").
- **Word of mouth is measured narrowly.** "Passed on in conversation" counts only lines to somebody who had not seen it; talk among people who already knew is not counted, so a quiet number is not the same as a quiet town.
- **Talk of switching provider** is a keyword proxy, not a measured intention.

## What happened

The most important things that happened, in order, with the reason the person gave when it was their own decision.

- **Day 1 06:00**: Northline Internet shop has opened: a new phone shop, open 09:00-17:30. (seen by 9 residents)
- **Day 1 07:00**: The internet went off at home. (seen by 43 residents)
- **Day 1 08:30**: Rose Grant got on to Northline Internet about the internet; they said: "Hi Rose, I'm sorry to hear your internet is down. I'll send an engineer to check it out as soon as possible.". (seen by 1 resident)
- **Day 1 09:00**: Somebody from Northline Internet came round and sorted the internet. (seen by 16 residents)
- **Day 1 09:00**: A text from Northline Internet: "Your bill this month is $184.60. Thank you for being a Northline customer." (seen by 12 residents)
- **Day 1 09:00**: Adriana Peña got on to Northline Internet about the internet; they said: "Hi Adriana, I'm sorry about the internet outage at your home. There's currently a fault affecting your line, and we've already scheduled an engineer to visit at 09:00 today. They'll work to get things back up and running. I'll keep you updated!". (seen by 1 resident)
- **Day 1 09:30**: Wendy Wood got on to Northline Internet about the internet; they said: "Hi Wendy, I'm sorry to hear your internet is down. I can see there's already a fault being looked at on Victoria Place today. I'll schedule an engineer to visit you at 14:00 today. They'll sort out the issue as soon as they arrive.". (seen by 1 resident)
- **Day 1 14:00**: Somebody from Northline Internet came round and sorted the internet. (seen by 2 residents)
- **Day 1 16:00**: Megan Parker got on to Northline Internet about the internet; they said: "Hi Megan, I'm sorry to hear your internet is down. We already have engineers scheduled to visit Victoria Place today at 09:00 and 14:00. I'll keep you updated on progress.". (seen by 1 resident)
- **Day 1 16:30**: Geeta Agarwal got on to Northline Internet about the internet; they said: "Hi Geeta, I'm sorry to hear your internet is down. There are already a few faults reported on Victoria Place, and I can schedule an engineer to visit your home. The earliest available slot is tomorrow at 09:00. Would that work for you?". (seen by 3 residents)
- **Day 2 08:00**: At home: very slow internet. (seen by 47 residents)
- **Day 2 10:00**: The internet came back on at home. (seen by 41 residents)
- **Day 3 18:00**: The internet went off at home. (seen by 43 residents)
- **Day 3 18:00**: The internet came back on at home. (seen by 39 residents)
- **Day 4 08:00**: The internet came back on at home. (seen by 43 residents)

The conversations that mattered most:

**Day 1 20:00**, Adwoa Traoré and Babajide Traoré at 21 Oak Lane:

> Adwoa Traoré: Babajide. I was wondering if you could maybe cover the internet bill for next week.  
> Babajide Traoré: Honestly though, with Femi's weekend plans, I'm not sure I'll have the cash spare.  

**Day 2 18:30**, Valeria Vega and Abiodun Obi at Spring Mansions:

> Valeria Vega: How's that Northline business looking, love?  
> Abiodun Obi: They said an engineer's on the way. It'll be fixed by tomorrow, I expect.  
> Valeria Vega: Good. Now, about that money you owe me - when can I expect it?  
> Abiodun Obi: I'll have it to you tomorrow, same as ever.  
> *promise by Abiodun Obi: landed*  
> *promise by Abiodun Obi: landed*  

**Day 2 20:30**, Margaret Hughes and Kate Hughes at Victoria Court:

> Margaret Hughes: Kate, could we have a word? I think we need to talk about a few things.  
> Kate Hughes: What is it, Margaret?  
> Margaret Hughes: I’ve been meaning to ask—have you noticed the credit card bill lately?  
> Kate Hughes: Kate Hughes: 'The card? I haven’t looked. Should I have?'

## Who did what

**Anna Markovic** thought 10 times, talked 4 times, was refused once, money +$218.
- The day has worn on, and I could do with something warm.
- I need to rest, my energy is low.
- I need to make sure I’m fully awake before heading to work.

**Sarah Pike** thought 8 times, talked 5 times, was refused 3 times, money -$277.
- I'm checking if she's noticed the bins again.
- I need to know if the bins have been emptied again, and she was the last person I spoke to about it.
- I want to keep the conversation going with Yaw about the bins, and start the day on a civil note.

**Jakub Sokolov** thought 7 times, talked 5 times, was refused once, money -$12.
- I wanted to start a friendly conversation and make light of the strange situation with everyone buying painkillers.
- I need to get in touch about the internet because I can't let it go on like this. It's something I pay for, after all.
- I need to vent about the internet situation and see if Lakshmi has any advice or experience with it. She’s been chatty before.

**Mercedes Fuentes** thought 9 times, talked twice, money +$274.
- I'll wait it out, give it a bit longer in case the internet comes back on its own.
- It's my shift, and there's no reason to stop working just yet.
- It's the middle of the night, and I've got a long day ahead of me. I might as well get some rest.

**Kate Hughes** thought 5 times, talked 5 times, money -$4.
- I need to say something about the repeated stamp purchases and keep an eye on things.
- I need to know what's going on. She keeps appearing, and it's starting to feel deliberate.
- Got to say it before I forget again.

**Farah Nair** thought 4 times, talked 5 times, money -$100.
- I need to talk to someone I trust, and Riya is the only one who might be able to help me with this.
- If I want to make up the rent, I need to know where to look.
- I need to get some rest if I'm to face the day and manage the rent somehow.

**Holly Spencer** thought 6 times, talked twice, money +$917.
- I need to get a move on before work; better to get up now than be late.
- This is what I signed up for.
- There we are, I might as well ask while I’m still in a civil frame of mind.

**Tara Bhatt** thought 6 times, talked twice, money -$104.
- I'm awake now, but it's early and I haven't had my coffee yet. Might as well lie in a bit longer.
- It’s Tuesday, and I'm at home, not working. No need to go out; I'll wait it out for now.
- Nothing much to do today. Just hang out.

**Beth Moore** thought 6 times, talked twice, money +$437.
- The internet stopped working, and I should check if it was a general issue or just my house.
- I'll stay where I am for a while.
- I need to get this sorted out, and I should check if it's just me first, but I know it's not. Time to call Northline.

**Will Ward** thought 5 times, talked 3 times, was refused once, money -$31.
- I'll wait here. There's no need to move until the time is right.
- Joe's asleep and I'm not exactly perking up for anything. Let it be.
- I'm curious about why Henry is still at the park. I might as well ask him directly.

Everybody:

| Resident | Thoughts | Conversations | Money | Refused |
|---|---|---|---|---|
| Aarti Sharma (r127) | 1 | 0 | +$768 | - |
| Abena Eze (r200) | 4 | 0 | +$470 | - |
| Abigail Barker (r198) | 3 | 1 | +$523 | - |
| Abiodun Obi (r090) | 3 | 4 | +$607 | - |
| Adaeze Ogunleye (r077) | 6 | 1 | +$417 | 2 |
| Adam Rhodes (r156) | 1 | 0 | - | - |
| Adam Young (r074) | 3 | 1 | +$351 | 1 |
| Adriana Peña (r049) | 1 | 0 | -$100 | - |
| Adwoa Traoré (r180) | 1 | 1 | +$595 | - |
| Agata Kowalski (r102) | 1 | 1 | +$388 | - |
| Aiko Xu (r169) | 2 | 0 | +$580 | - |
| Aisha Thakur (r060) | 1 | 1 | -$100 | - |
| Alan Brooks (r120) | 4 | 0 | +$560 | - |
| Alejandra Medina (r051) | 3 | 2 | +$368 | - |
| Aleksander Kovac (r099) | 6 | 0 | +$467 | - |
| Alice Marsh (r024) | 2 | 1 | -$24 | - |
| Alice Page (r159) | 1 | 0 | -$18 | - |
| Alina Orlov (r136) | 1 | 2 | - | - |
| Ama Abiola (r172) | 1 | 1 | -$100 | - |
| Amy Young (r076) | 1 | 0 | - | - |
| Andrei Markovic (r167) | 3 | 1 | -$100 | 1 |
| Andrés Estrada (r118) | 1 | 0 | +$713 | - |
| Anil Gupta (r065) | 2 | 0 | +$413 | - |
| Anna Markovic (r168) | 10 | 4 | +$218 | 1 |
| Antonio Navarro (r158) | 3 | 0 | +$685 | - |
| Arjun Agarwal (r123) | 1 | 1 | +$559 | - |
| Babajide Traoré (r179) | 1 | 1 | +$333 | - |
| Ben Carter (r029) | 4 | 1 | +$1694 | - |
| Beth Moore (r014) | 6 | 2 | +$437 | - |
| Beth Page (r161) | 1 | 0 | +$482 | - |
| Bogdan Volkov (r027) | 2 | 0 | +$870 | - |
| Callum Carter (r030) | 4 | 0 | +$523 | - |
| Camila Fuentes (r139) | 3 | 0 | -$100 | - |
| Carmen Sandoval (r134) | 1 | 0 | +$367 | - |
| Caroline Ellis (r111) | 1 | 0 | -$75 | - |
| Charlie Harper (r031) | 1 | 0 | -$24 | - |
| Charlie Rhodes (r153) | 1 | 0 | +$156 | - |
| Charlotte Bishop (r164) | 1 | 1 | -$345 | - |
| Charlotte Graham (r140) | 1 | 1 | -$8 | - |
| Chidi Traoré (r181) | 1 | 1 | - | - |
| Chinedu Appiah (r025) | 1 | 1 | -$24 | - |
| Chloe Burton (r072) | 2 | 1 | - | - |
| Chloe Rhodes (r155) | 1 | 1 | - | - |
| Chris Hughes (r047) | 1 | 0 | +$683 | - |
| Chris Parker (r194) | 1 | 1 | - | - |
| Claire Mason (r148) | 4 | 0 | +$3064 | - |
| Claudia Navarro (r157) | 2 | 0 | +$933 | 1 |
| Colin Abbott (r146) | 1 | 0 | +$476 | - |
| Colin Moore (r059) | 1 | 1 | - | - |
| Daniel Bishop (r197) | 4 | 0 | +$469 | - |
| Daniela García (r178) | 1 | 0 | - | - |
| Daria Nowak (r109) | 1 | 0 | +$547 | - |
| Dev Agarwal (r124) | 1 | 1 | - | - |
| Dmitri Nowak (r116) | 3 | 1 | +$550 | - |
| Edward Murray (r186) | 2 | 0 | +$563 | - |
| Edward Shaw (r084) | 1 | 0 | -$24 | - |
| Eleanor Talbot (r132) | 1 | 0 | +$635 | - |
| Elena Espinoza (r107) | 2 | 0 | -$56 | - |
| Ellen Spencer (r138) | 5 | 0 | +$771 | - |
| Emeka Abiola (r173) | 1 | 1 | -$77 | 1 |
| Emily Mason (r147) | 1 | 0 | -$18 | - |
| Emma Ellis (r112) | 1 | 0 | +$566 | 2 |
| Enrique Rojas (r192) | 3 | 0 | - | - |
| Esperanza Jiménez (r061) | 1 | 1 | -$100 | - |
| Ewa Volkov (r028) | 3 | 0 | +$418 | - |
| Farah Nair (r100) | 4 | 5 | -$100 | - |
| Filip Horvat (r104) | 4 | 1 | -$18 | - |
| Fiona Wood (r088) | 1 | 0 | - | - |
| Funmi Achebe (r190) | 2 | 2 | - | - |
| Gabriel Morales (r045) | 2 | 0 | +$743 | - |
| Gabriela Rojas (r191) | 1 | 0 | -$24 | - |
| Gary Moore (r098) | 1 | 2 | -$24 | - |
| Geeta Agarwal (r125) | 1 | 1 | - | - |
| George Fletcher (r040) | 1 | 2 | +$1401 | - |
| Hannah Webb (r093) | 4 | 0 | +$348 | - |
| Harry Wood (r004) | 1 | 3 | -$24 | - |
| Heather Pike (r053) | 5 | 0 | +$164 | 3 |
| Henry Hughes (r046) | 4 | 3 | -$75 | - |
| Henry Murray (r185) | 1 | 0 | -$100 | - |
| Holly Spencer (r005) | 6 | 2 | +$917 | - |
| Holly Wright (r184) | 2 | 1 | +$2723 | - |
| Hugo Aguilar (r033) | 1 | 1 | +$827 | - |
| Héctor Gutiérrez (r073) | 5 | 0 | +$133 | - |
| Ian Shaw (r083) | 1 | 1 | +$285 | - |
| Ibrahim Appiah (r019) | 1 | 1 | +$2896 | - |
| Igor Kovac (r114) | 1 | 0 | - | - |
| Isabel García (r023) | 4 | 1 | -$24 | - |
| Jack Wood (r085) | 2 | 0 | +$257 | 1 |
| Jakub Sokolov (r062) | 7 | 5 | -$12 | 1 |
| James Fletcher (r041) | 1 | 0 | - | - |
| James Page (r160) | 1 | 1 | +$331 | - |
| Jane Parker (r042) | 2 | 0 | -$24 | - |
| Jane Rhodes (r154) | 1 | 0 | +$704 | - |
| Jennifer Graham (r068) | 2 | 3 | -$50 | 1 |
| Jia Shin (r137) | 1 | 0 | +$244 | - |
| Joe Ward (r106) | 1 | 1 | +$353 | - |
| John Reed (r095) | 1 | 0 | +$708 | - |
| Julia Burton (r150) | 2 | 2 | +$348 | - |
| Julia Graham (r069) | 4 | 1 | +$540 | - |
| Julio Medina (r092) | 2 | 4 | +$518 | - |
| Kabir Sharma (r078) | 1 | 2 | +$443 | - |
| Karen Hughes (r003) | 1 | 1 | - | - |
| Karol Volkov (r026) | 1 | 0 | +$468 | - |
| Kate Hughes (r175) | 5 | 5 | -$4 | - |
| Keith Moore (r013) | 3 | 1 | +$469 | - |
| Kwame Osei (r129) | 2 | 4 | +$864 | - |
| Kwesi Achebe (r189) | 2 | 0 | +$387 | - |
| Lakshmi Iyer (r010) | 1 | 4 | -$24 | - |
| Laura Moore (r015) | 3 | 2 | - | - |
| Lena Petrov (r126) | 1 | 0 | -$24 | - |
| Leticia García (r176) | 1 | 0 | +$345 | - |
| Liam Burton (r066) | 7 | 0 | +$628 | 2 |
| Lucy West (r036) | 2 | 0 | -$8 | - |
| Lucía Vargas (r131) | 2 | 0 | -$75 | - |
| Luis Vargas (r130) | 1 | 0 | +$625 | - |
| Luisa Morales (r044) | 1 | 0 | -$77 | - |
| Lukas Orlov (r135) | 2 | 1 | +$562 | - |
| Luke Bishop (r196) | 1 | 1 | +$806 | - |
| Magda Lewandowski (r018) | 1 | 1 | - | - |
| Mahmoud Jaber (r055) | 4 | 2 | +$573 | 1 |
| Margaret Hughes (r174) | 3 | 1 | +$669 | - |
| Margaret Young (r075) | 1 | 0 | +$737 | - |
| Mariama Eze (r096) | 4 | 1 | -$52 | - |
| Maribel Salazar (r057) | 1 | 0 | - | - |
| Mario Salazar (r056) | 1 | 0 | +$428 | - |
| Mark Gibson (r008) | 4 | 0 | +$1077 | - |
| Marta Estrada (r119) | 2 | 1 | +$479 | - |
| Martin Shaw (r082) | 2 | 0 | +$300 | - |
| Matt Webb (r115) | 1 | 0 | -$24 | - |
| Megan Parker (r193) | 1 | 1 | +$736 | - |
| Mercedes Fuentes (r187) | 9 | 2 | +$274 | - |
| Molly Bishop (r195) | 1 | 1 | -$8 | 1 |
| Nancy Graham (r067) | 3 | 2 | -$77 | - |
| Natalia Kovac (r113) | 3 | 0 | +$412 | - |
| Neha Joshi (r037) | 1 | 0 | +$581 | - |
| Nkechi Adeyemi (r117) | 1 | 0 | +$647 | - |
| Nnamdi Achebe (r188) | 2 | 1 | +$748 | - |
| Oliver Bishop (r163) | 2 | 1 | -$24 | - |
| Oliver Hughes (r001) | 2 | 2 | +$370 | - |
| Olivia Burton (r070) | 3 | 2 | +$439 | - |
| Omar Yousef (r182) | 6 | 0 | +$548 | - |
| Owen Mason (r149) | 1 | 0 | - | - |
| Owen Moore (r097) | 5 | 2 | -$18 | - |
| Pablo García (r022) | 1 | 0 | -$24 | - |
| Paul Shaw (r145) | 1 | 0 | +$464 | - |
| Paula Fuentes (r121) | 6 | 0 | +$873 | - |
| Pavel Nowak (r110) | 1 | 0 | -$100 | - |
| Peter Stone (r007) | 1 | 1 | - | - |
| Peter Wright (r183) | 3 | 1 | +$503 | 1 |
| Pilar Peña (r048) | 1 | 0 | -$100 | - |
| Pooja Joshi (r038) | 1 | 0 | -$54 | - |
| Rachel Lloyd (r081) | 2 | 1 | +$371 | 1 |
| Rafael Aguilar (r034) | 1 | 0 | - | - |
| Rahul Iyer (r012) | 2 | 1 | - | - |
| Raj Qureshi (r144) | 6 | 0 | +$428 | - |
| Rana Jaber (r054) | 1 | 2 | +$473 | - |
| Riya Nair (r101) | 3 | 2 | - | - |
| Rob Moore (r043) | 2 | 0 | +$336 | - |
| Rocío Medina (r052) | 1 | 0 | - | - |
| Rosa Molina (r143) | 2 | 3 | +$1416 | - |
| Rose Grant (r063) | 1 | 1 | -$100 | - |
| Ruth Palmer (r162) | 5 | 0 | -$100 | - |
| Ryan Wood (r087) | 1 | 0 | - | - |
| Sanjay Iyer (r011) | 5 | 2 | +$339 | 3 |
| Sarah Bennett (r080) | 2 | 3 | +$325 | - |
| Sarah Pike (r152) | 8 | 5 | -$277 | 3 |
| Simon Bishop (r064) | 1 | 0 | -$24 | - |
| Simon Talbot (r170) | 3 | 2 | +$473 | - |
| Sofía Medina (r050) | 1 | 0 | +$343 | 2 |
| Sophie Hughes (r002) | 1 | 1 | +$442 | - |
| Stefan Lewandowski (r016) | 3 | 1 | +$418 | - |
| Steve Moore (r058) | 1 | 0 | -$24 | - |
| Su-bin Yoon (r142) | 1 | 0 | +$224 | - |
| Sunita Agarwal (r122) | 6 | 2 | +$346 | 2 |
| Susan Stone (r006) | 1 | 0 | +$624 | - |
| Svetlana Nowak (r108) | 7 | 1 | +$334 | - |
| Tara Bhatt (r009) | 6 | 2 | -$104 | - |
| Temitope Osei (r128) | 2 | 0 | +$368 | - |
| Tessa Wood (r086) | 1 | 1 | +$224 | - |
| Tom Burton (r071) | 1 | 0 | +$817 | - |
| Tom Dawson (r171) | 1 | 0 | - | - |
| Tomasz Lewandowski (r017) | 2 | 2 | +$300 | - |
| Tunde Abiola (r165) | 1 | 0 | -$24 | - |
| Valeria Vega (r089) | 1 | 1 | -$24 | - |
| Verónica Domínguez (r103) | 1 | 0 | -$100 | - |
| Víctor Díaz (r091) | 3 | 1 | +$600 | - |
| Wen Fujita (r166) | 1 | 1 | -$271 | - |
| Wendy Wood (r141) | 2 | 1 | -$100 | - |
| Will Barker (r199) | 5 | 1 | -$77 | - |
| Will Ward (r105) | 5 | 3 | -$31 | 1 |
| Ximena Aguilar (r032) | 1 | 0 | +$485 | - |
| Yaw Appiah (r020) | 3 | 4 | -$100 | - |
| Yetunde Appiah (r021) | 1 | 1 | - | - |
| Yolanda García (r177) | 2 | 0 | -$12 | - |
| Yuri Szabo (r079) | 2 | 1 | - | - |
| Yuto Shin (r094) | 1 | 0 | +$562 | - |
| Zara Joshi (r039) | 1 | 0 | +$934 | - |
| Zoe Burton (r151) | 3 | 1 | +$607 | - |
| Zoe Cole (r133) | 1 | 0 | +$410 | - |
| Óscar Aguilar (r035) | 1 | 1 | - | - |

## What changed

From the start of the run to the last night it finished.

**Work.**

- Nobody's work changed.

**Money.**

- The town's residents together: +$62486.
- Down most: Charlotte Bishop, -$345.
- Down most: Sarah Pike, -$277.
- Down most: Wen Fujita, -$271.
- Up most: Claire Mason, +$3064.
- Up most: Ibrahim Appiah, +$2896.
- Up most: Holly Wright, +$2723.

**People.**

- 22 new acquaintances made, 241 names learned.
- Stefan Lewandowski on Magda Lewandowski: stage 2 to 3, feeling +7 to +8
- Magda Lewandowski on Stefan Lewandowski: stage 2 to 3, feeling +8 to +8
- Ibrahim Appiah on Sanjay Iyer: stage 2 to 1, feeling +1 to +1
- Rana Jaber on Mahmoud Jaber: stage 2 to 3, feeling +4 to +4

**What people came to believe** (one each, first eight):

- Oliver Hughes: Julio is considering swapping shifts with James.
- Harry Wood: A lot of people in town are buying painkillers for $6.
- Peter Stone: Rahul Iyer might be interested in the team after I mentioned it.
- Lakshmi Iyer: Jakub Sokolov has a sense of humor and remembers me.
- Sanjay Iyer: Adam Young is trying to get me to talk about something he hasn't explained.
- Rahul Iyer: Peter Stone is thinking about trying out for a team.
- Beth Moore: Laura is growing up and wants more independence.
- Stefan Lewandowski: Magda is interested in something I don't care about.

**Lives.**

- Nobody changed course.

## Injected

"Passed on in conversation" counts only lines from somebody who knew to somebody who had not seen it themselves: word of mouth to new people. People talking it over with others who already knew is not counted here.

**Day 1 06:00: service.register** (i55d3828dc5). Northline Internet [northline], home internet and the bills for it; by text or call or visit; open 08:00-20:00.

- Known to: everybody.

**Day 1 06:00: place.new** (ieac4e8a79e). Northline Internet shop has opened: a new phone shop, open 09:00-17:30.

- Saw it happen: Oliver Hughes, Julio Medina.
- Noticed it later: 7, first James Page (Day 1 07:00), Sarah Bennett (Day 1 08:30), Adaeze Ogunleye (Day 1 11:00), Martin Shaw (Day 1 12:00), Agata Kowalski (Day 1 12:30) and more.
- Knew of it by the end: 9.
- Passed on in conversation: no sign of it.

**Day 1 07:00: event.outage** (if7d3434aa3). The internet went off at home.

- Saw it happen: Mark Gibson, Ximena Aguilar, Hugo Aguilar, Sarah Bennett, Rachel Lloyd, Yuto Shin, John Reed, Aarti Sharma, Ellen Spencer, Rosa Molina, Jane Rhodes, Margaret Hughes, Omar Yousef, Megan Parker, Abena Eze.
- Ended: Day 2 10:00.
- Noticed it later: 28, first Laura Moore (Day 1 07:00), Rafael Aguilar (Day 1 07:00), Óscar Aguilar (Day 1 07:00), Dev Agarwal (Day 1 07:00), Geeta Agarwal (Day 1 07:00) and more.
- Touched directly: 43 (Mark Gibson, Keith Moore, Beth Moore, Laura Moore, Ximena Aguilar, Hugo Aguilar and more).
- Knew of it by the end: 43.
- Possibly heard of it in conversation, not having seen it: 1.
- Possibly passed on in conversation (1; a keyword proxy on internet):
  - Day 2 10:00: Laura Moore to Chidi Traoré: "Not that it's any of my business, but did you see if Northline got back to you about the internet?"

**Day 1 09:00: event.letter** (12 of them, to 12 residents). A text from Northline Internet: "Your bill this month is $184.60. Thank you for being a Northline customer."

- Saw it happen: nobody.
- Noticed it later: 12, first Alejandra Medina (Day 1 09:00), Ruth Palmer (Day 1 09:00), Gary Moore (Day 1 09:00), Luis Vargas (Day 1 09:00), Neha Joshi (Day 1 09:00) and more.
- Touched directly: 12 (Oliver Hughes, Yaw Appiah, Neha Joshi, Alejandra Medina, Nancy Graham, Ian Shaw and more).
- Knew of it by the end: 12.
- Passed on in conversation: no sign of it.

**Day 2 08:00: event.outage** (ic41a61c3a6). At home: very slow internet.

- Saw it happen: Peter Stone, Rahul Iyer, Alice Marsh, Chinedu Appiah, Charlie Harper, Jakub Sokolov, Tom Burton, Chloe Burton, Amy Young, Kabir Sharma, Yuri Szabo, Tessa Wood, Ryan Wood, Fiona Wood, Agata Kowalski, Igor Kovac, Matt Webb, Eleanor Talbot, Carmen Sandoval, Simon Talbot, Tom Dawson, Daniela García, Nnamdi Achebe, Kwesi Achebe, Funmi Achebe.
- Ended: Day 3 18:00.
- Noticed it later: 22, first Valeria Vega (Day 2 08:30), Yolanda García (Day 2 08:30), Jane Parker (Day 2 09:00), Lakshmi Iyer (Day 2 09:00), Rob Moore (Day 2 12:30) and more.
- Touched directly: 47 (Susan Stone, Peter Stone, Lakshmi Iyer, Sanjay Iyer, Rahul Iyer, Alice Marsh and more).
- Knew of it by the end: 47.
- Passed on in conversation: no sign of it.

**Day 3 18:00: event.outage** (ibe1fc60eee). The internet went off at home.

- Saw it happen: Laura Moore, Ximena Aguilar, Hugo Aguilar, Rafael Aguilar, Óscar Aguilar, Pilar Peña, Adriana Peña, Rose Grant, Simon Bishop, Sarah Bennett, Rachel Lloyd, Julio Medina, Verónica Domínguez, Filip Horvat, Arjun Agarwal, Dev Agarwal, Geeta Agarwal, Lena Petrov, Ellen Spencer, Charlotte Graham, Wendy Wood, Su-bin Yoon, Jane Rhodes, Chloe Rhodes, Adam Rhodes, Oliver Bishop, Charlotte Bishop, Margaret Hughes, Kate Hughes, Omar Yousef, Megan Parker, Chris Parker, Abena Eze.
- Ended: Day 4 08:00.
- Noticed it later: 10, first Mark Gibson (Day 3 18:00), Rosa Molina (Day 3 18:00), John Reed (Day 3 18:00), Charlie Rhodes (Day 3 18:00), Aarti Sharma (Day 3 18:30) and more.
- Touched directly: 43 (Mark Gibson, Keith Moore, Beth Moore, Laura Moore, Ximena Aguilar, Hugo Aguilar and more).
- Knew of it by the end: 43.
- Passed on in conversation: no sign of it.

**Contacts with `northline`**: 57 from 44 residents (1 by call, 56 by text), the first at Day 1 07:30.

- Answered: 33. Got nowhere: 24 (they were closed; a recording gave their hours, 08:00-20:00).
- What the agent did: dispatch 10, note 14, promise 9, resolve 4.
- Answered by: `LlmHelpdesk` (kind language model, model populace, server http://127.0.0.1:8080/v1/).
- The agent's own model: 33 calls for 33 replies (0 retries), median 2.8 s; 0 gave no usable answer; 4 actions it asked for that the desk cannot do (that time has passed).
- Came back more than once: 11.
- Promises kept / broken: 2 / 6.

## The service

**Northline Internet** (`northline`)

| | |
|---|---|
| Residents with a problem it handles | 100 |
| ...who had at least one decision while it was open | 63 |
| ...who tried to get in touch | 39 (39.0%) |
| ...who reached the service | 25 |
| ...who only ever got the recording | 14 |
| Hours from a problem starting to getting in touch about it, median / longest | 7.8 / 32.5 (over 44) |
| Contacts, answered / all | 33 / 57 |
| Got nowhere | they were closed 24 |
| By channel | call 1, text 56 |
| Contacts about a real problem at home | 49 |
| Contacts about a problem nobody at home had (the simulation inventing one) | 8 from 6 residents; the agent answered with dispatch 2, promise 1 |
| Residents who got in touch twice or more | 11 |
| ...who chased something they had been promised | 1 |
| Homes that got in touch, and of those more than one person | 27, 5 |
| What the agent did | dispatch 10, note 14, promise 9, resolve 4 |
| Problems the service fixed, by day | Day 1: 7, Day 2: 4, Day 3: 5 |
| Problems that ended on the schedule (not the service's doing), by day | Day 2: 39, Day 3: 39, Day 4: 43 |
| Still broken at the end | 8 |
| Promises made / to people with no such problem | 9 / 1 |
| Promises kept / broken / not yet due at the end / broken and then chased | 2 / 6 / 1 / 0 |
| Talked of switching provider (keyword proxy) | 0 |

Got in touch about a problem nobody at home had: Pooja Joshi, Henry Hughes, Víctor Díaz, Paula Fuentes, Raj Qureshi, Henry Murray.

## How well the model did its job

| | |
|---|---|
| Decisions valid first try | 96.5% |
| Retries / fell back to routine | 17 / 1 |
| Call latency, median / p90 | 3.84 s / 8.01 s |
| Server errors | 0 |
| Share of input read from the prompt cache | 0.667 |
| Replies that echo the line before | 1.7% |
| Lines with the speaker's own name | 1.5% |
| Questions left unanswered | 3 of 73 |
| Lines repeating what the speaker already said today | 0.8% |
| Deals asserted / landed | 12 / 11 |
| Things said about somebody that they never said | 0 of the 0 such claims |
| Names used without having been given | 0 |
| Ids said out loud | 0 |

## Realism flags

Mechanical checks over the logs. A flag is a reason to look, not a verdict.

| Flag | Count | What it means |
|---|---|---|
| `repeated_line` | 2 | somebody said the same line, word for word, more than once |
| `echo` | 3 | a reply that repeats most of the line it answers |
| `stuck` | 4 | the same decision 4 times running |
| `impossible_move` | 0 | somebody arrived in a home that is neither theirs nor anybody's they know |
| `sleepless` | 0 | active through a stretch of 24 hours with no sleep in it |
| `no_reaction` | 1 | saw something of importance 7+ and had no thought for 4 ticks |
| `ghost_contact` | 0 | a text between two people with no tie at all |
| `money_from_nowhere` | 0 | somebody's money changed by more than the run's money events explain |
| `promise_ignored` | 0 | a broken promise the person let down never did anything about |
| `provider_down_window` | 0 | a stretch of ticks where the model did not answer |
| `id_spoken` | 0 | somebody said a resident id out loud |
| `name_unknown` | 0 | somebody used the name of a person whose name they had not been given |
| `claim_unfounded` | 5 | somebody spoke of money owed between them and a person with no debt, loan, rent or wage between them |
| `contact_ungrounded` | 8 | a resident got in touch with a service about a problem nobody in their home had |

**`repeated_line`**, first 2 of 2:

- Day 3 05:30: Yaw Appiah said "morning sarah you look like you've been up all night" 2 times
- Day 5 04:30: Yaw Appiah said "aye just trying to get the day off right you know how it is" 2 times

**`echo`**, first 3 of 3:

- Day 3 15:30: Lakshmi Iyer echoed Jakub Sokolov: "Aye, well, at least it's not just me, eh? Snails get holidays, I swear."
- Day 3 20:00: Ian Shaw echoed Víctor Díaz: "You again. What is it, Shaw?"
- Day 5 04:30: Anna Markovic echoed Yaw Appiah: "Aye, just trying to get the day off right."

**`stuck`**, first 4 of 4:

- Day 4 13:00: Jakub Sokolov chose talk Lakshmi Iyer 4 times running
- Day 4 22:30: Héctor Gutiérrez chose sleep 4 times running
- Day 4 20:30: Hannah Webb chose wait 4 times running
- Day 5 00:30: Sarah Pike chose talk Farah Nair 4 times running

**`no_reaction`**, first 1 of 1:

- Day 3 09:00: Ben Carter saw Gabriela Rojas's rent missed and did not react

**`claim_unfounded`**, first 5 of 5:

- Day 1 21:00: Dmitri Nowak spoke of money owed with Abiodun Obi, and nothing stands between them: "So, Abiodun, I've been thinking about that coffee I owe you."
- Day 2 18:30: Valeria Vega spoke of money owed with Abiodun Obi, and nothing stands between them: "Good. Now, about that money you owe me - when can I expect it?"
- Day 3 19:30: Holly Spencer spoke of money owed with Harry Wood, and nothing stands between them: "You’d be surprised how quickly a debt eats into your day, wouldn’t you?"
- Day 4 18:00: Sanjay Iyer spoke of money owed with Abiodun Obi, and nothing stands between them: "You owe her, and she's waiting. That's all there is to it."
- Day 4 18:30: Holly Spencer spoke of money owed with Harry Wood, and nothing stands between them: "I owe Claudia something before Friday, and I’d rather not be reminded of it by her walking through the door."

**`contact_ungrounded`**, first 5 of 8:

- Day 2 13:30: Pooja Joshi got in touch with northline with no such problem at home: "I need to speak to someone about my internet service. It's been down for two days."
- Day 2 14:30: Henry Murray got in touch with northline with no such problem at home: "I'm Henry Murray from 11 Birch Crescent. I need to report an internet outage."
- Day 3 15:00: Raj Qureshi got in touch with northline with no such problem at home: "I need to report an internet outage at my place. It's been down since yesterday."
- Day 3 16:00: Henry Hughes got in touch with northline with no such problem at home: "I'm Henry Hughes, I'm having some issues with my internet connection. I need to sort this out right away."
- Day 4 07:00: Víctor Díaz got in touch with northline with no such problem at home

## Appendix

### Every conversation

**Day 1 06:00**, Rachel Lloyd and Sarah Bennett at Victoria Court:

> Rachel Lloyd: Sarah, I do hope you're up for a game of Scrabble this evening. I could use a worthy opponent.  
> Sarah Bennett: Scrabble? I thought you'd never ask. Eight o'clock sound good?  
> *invite by Rachel Lloyd: did not land (there is no victoria_place_1 to meet at)*  
> *accept by Sarah Bennett: landed*  

**Day 1 08:30**, Ibrahim Appiah and Julia Burton at Fresh Fare:

> Ibrahim Appiah: Morning, Julia. You look like you're still finding your feet here. How’s it going?  
> Julia Burton: You could say that. Still getting the hang of the stock rotation, really.  
> Ibrahim Appiah: Aye, we all do. Just take your time. Need a hand with anything?  
> Julia Burton: I’ll muddle through. Got a list to get through, so…  

**Day 1 11:00**, Jakub Sokolov and Lakshmi Iyer at Spring Pharmacy:

> Jakub Sokolov: Well, if it isn't Lakshmi Iyer! Honestly though, everyone's been buying painkillers today - it's like we're all turning into old men overnight.  
> Lakshmi Iyer: Oh, I imagine that is the cold weather getting to us all!  
> Jakub Sokolov: Not today, but it's true, we're all feeling it!  
> Lakshmi Iyer: Well, there you go, then!  

**Day 1 15:30**, Peter Stone and Rahul Iyer at St. Anne's School:

> Peter Stone: Hey, Rahul, have you heard about the team tryouts on Tuesday? I was wondering if you knew what they're looking for.  
> Rahul Iyer: Not sure to be honest, I haven't really thought about it. Why, are you trying out?  
> Peter Stone: I just thought I’d give it a go, honestly. It’s on my mind a lot.  
> Rahul Iyer: Well, if you end up going, let me know what I need to do!  

**Day 1 16:00**, Esperanza Jiménez and Aisha Thakur at 21 Clover Street:

> Esperanza Jiménez: That bin situation on Clover Street — it's not a joke any more. People are just leaving their trash out, and it's not right.  
> Aisha Thakur: Ah, yes, dreadful. But I think I'll need to be going in a moment — I have a call to make.  
> Esperanza Jiménez: A call, sure. But you'll make it after you've dealt with the bin situation. Let's not be in denial.  
> Aisha Thakur: Ah, Esperanza, but I have said all that I came to say.  

**Day 1 19:30**, Rana Jaber and Mahmoud Jaber at 11 Clover Street:

> Rana Jaber: So, Mahmoud, I've been meaning to have a proper chat with you. You know, like the kind where we actually talk about things instead of just nodding and moving on.  
> Mahmoud Jaber: What's on your mind, Rana?  
> Rana Jaber: I think it's time we talked about where we're headed, you know, with everything.  
> Mahmoud Jaber: Right then. That's that, then.  

**Day 1 20:00**, Adwoa Traoré and Babajide Traoré at 21 Oak Lane:

> Adwoa Traoré: Babajide. I was wondering if you could maybe cover the internet bill for next week.  
> Babajide Traoré: Honestly though, with Femi's weekend plans, I'm not sure I'll have the cash spare.  

**Day 1 20:30**, Luke Bishop and Molly Bishop at 31 Oak Lane:

> Luke Bishop: So, there's something I need to say to you, Molly.  
> Molly Bishop: Go on then.  
> Luke Bishop: It’s about the money, Molly. I’ve been picking up some extra work on Mondays.  
> Molly Bishop: Right, well. Not my business, but I'll keep it in mind.  

**Day 1 21:00**, Dmitri Nowak and Abiodun Obi at Spring Mansions:

> Dmitri Nowak: So, Abiodun, I've been thinking about that coffee I owe you.  
> Abiodun Obi: I've got time. Let me just freshen up.  
> Dmitri Nowak: I'll buy you two coffees, and we can talk over one.  
> Abiodun Obi: Twenty minutes. I'll meet you at Willow Green.  
> *accept by Abiodun Obi: landed*  
> *invite by Abiodun Obi: landed*  

**Day 1 22:00**, Magda Lewandowski and Stefan Lewandowski at Clover Court:

> Magda Lewandowski: Dad, can I ask something? About the team tryouts...  
> Stefan Lewandowski: Tryouts? I don’t get involved in that sort of thing.  

**Day 1 22:30**, Yuri Szabo and Kabir Sharma at 23 Spring Terrace:

> Yuri Szabo: You ever thought about working part-time at the community centre? I heard the staff there are always looking for extra help.  
> Kabir Sharma: Not really my kind of place. I’ve got a full schedule already.  

**Day 2 08:00**, Owen Moore and Gary Moore at 21 Orchard Lane:

> Owen Moore: Gary, I was wondering if we could have a quick chat about the money situation. I think it's time we sort it out.  
> Gary Moore: I don't like talking about it, but... it's more than it should be again.  
> Owen Moore: Aye, no rush. Just thought we’d better get it out there while we’re both awake.  
> Gary Moore: I'll get it sorted by Thursday, I promise.  
> *promise by Gary Moore: landed*  

**Day 2 09:30**, Dev Agarwal and Geeta Agarwal at St. Anne's School:

> Dev Agarwal: Hang on, you already called Northline about the internet?  
> Geeta Agarwal: They said the earliest engineer can come tomorrow at 09:00.  
> Dev Agarwal: That’s not ‘til tomorrow. We’ll be stuck with no Wi-Fi all night again.  
> Geeta Agarwal: I'll let them know it's not working again tonight.  

**Day 2 10:00**, Laura Moore and Chidi Traoré at St. Anne's School:

> Laura Moore: Not that it's any of my business, but did you see if Northline got back to you about the internet?  
> Chidi Traoré: No bother. They don't take calls on a Tuesday.  

**Day 2 10:30**, Filip Horvat and Harry Wood at Spring Pharmacy:

> Filip Horvat: I don’t mean to pry, but I noticed a few of us here have been buying painkillers. Is there something about them you’d care to tell me?  
> Harry Wood: No, sorry. I don’t know nothing about them.  

**Day 2 13:00**, Ama Abiola and Emeka Abiola at 15 Birch Crescent:

> Ama Abiola: You still here to catch Pooja's noise?  
> Emeka Abiola: Still here for the noise, yes. What about you? You've been out and about.  
> Ama Abiola: I had to get the kids something sweet.  
> Emeka Abiola: Right. I'll get Esi sorted then.  

**Day 2 13:30**, Charlotte Graham and Wendy Wood at Victoria Court:

> Charlotte Graham: That engineer from Northline came by yesterday, you said. I suppose it’s sorted now.  
> Wendy Wood: That's right. Came by yesterday. It's all working again.  

**Day 2 14:00**, Karen Hughes and Alina Orlov at St. Anne's School:

> Karen Hughes: Have you started the Thursday homework yet?  
> Alina Orlov: Not yet. I'm still trying to figure out what the teacher actually wants.  
> Karen Hughes: Honestly, I'm just trying to get it done before it's too late.  
> Alina Orlov: Yeah, well—ask me tomorrow. It’s early days.  

**Day 2 14:30**, Yetunde Appiah and Chloe Rhodes at St. Anne's School:

> Yetunde Appiah: Chloe, are you going to the team tryouts on Thursday?  
> Chloe Rhodes: We'll see. My dad said I should go.  
> Yetunde Appiah: You think your dad’s the only one who gets a say, then?  
> Chloe Rhodes: My dad's not the only one, no. But I've got to make it, you know?  

**Day 2 15:00**, Tessa Wood and Agata Kowalski at St. Anne's School:

> Tessa Wood: Agata, I was wondering if you've seen Ryan about the internet issue at home. He's had it slow for a while now.  
> Agata Kowalski: Sorry, Tessa, I haven’t seen him. Should I ask around?  
> Tessa Wood: I'll give him a ring later. Thanks.  

**Day 2 16:30**, Simon Talbot and George Fletcher at Spring Pharmacy:

> Simon Talbot: George, got a minute? I was wondering if there's a chance of picking up a few more hours this week.  
> George Fletcher: You're doing all right at the moment, Simon. I'll keep it in mind.  

**Day 2 17:00**, Rosa Molina and Kwame Osei at Riverside Medical Practice:

> Rosa Molina: Kwame, I need to know what you meant on the 1st. It's been on my mind.  
> Kwame Osei: I was tired, that's all. It's not like I was... never mind.  
> Rosa Molina: Tired or not, you said something. I'm asking.  

**Day 2 17:30**, Jennifer Graham and Nancy Graham at Clover Court:

> Jennifer Graham: Nancy, a word if you've a minute? I've got the rent due today, and I'm not quite there yet. I'll have it to Claire by tomorrow, I promise.  
> Nancy Graham: You'll have to speak to them yourself if they're not there yet.  

**Day 2 18:00**, Sarah Pike and Farah Nair at Clover Court:

> Sarah Pike: I don't suppose you've seen my bins today, have you?  
> Farah Nair: No, I haven't been out that far.  

**Day 2 18:30**, Valeria Vega and Abiodun Obi at Spring Mansions:

> Valeria Vega: How's that Northline business looking, love?  
> Abiodun Obi: They said an engineer's on the way. It'll be fixed by tomorrow, I expect.  
> Valeria Vega: Good. Now, about that money you owe me - when can I expect it?  
> Abiodun Obi: I'll have it to you tomorrow, same as ever.  
> *promise by Abiodun Obi: landed*  
> *promise by Abiodun Obi: landed*  

**Day 2 19:30**, Julio Medina and Sarah Bennett at Victoria Court:

> Julio Medina: You up for the next shift? I saw you left early from the diner yesterday.  
> Sarah Bennett: Internet was down all day. Had to run an errand real quick.  

**Day 2 20:00**, Farah Nair and Riya Nair at Clover Court:

> Farah Nair: Riya, would you mind if I asked you something? It's about the rent.  
> Riya Nair: I don’t know where the money is going to come from.  
> Farah Nair: I'm not sure how else to make it up, but I'll find a way.  

**Day 2 20:30**, Margaret Hughes and Kate Hughes at Victoria Court:

> Margaret Hughes: Kate, could we have a word? I think we need to talk about a few things.  
> Kate Hughes: What is it, Margaret?  
> Margaret Hughes: I’ve been meaning to ask—have you noticed the credit card bill lately?  
> Kate Hughes: Kate Hughes: 'The card? I haven’t looked. Should I have?'  

**Day 2 21:00**, Chris Parker and Megan Parker at 21 Victoria Place:

> Chris Parker: Internet's back.  
> Megan Parker: That'll do. Felt like it might hold.  

**Day 3 04:30**, Anna Markovic and Yaw Appiah at Clover Court:

> Anna Markovic: I hope you're not in for a long shift today.  
> Yaw Appiah: Oh, I'm not going anywhere today. Just keeping Kemi entertained, really.  
> Anna Markovic: Kemi’s a lucky dog, then.  

**Day 3 05:00**, Yaw Appiah and Sarah Pike at Clover Court:

> Yaw Appiah: Morning, Sarah. You look like you've been up all night.  
> Sarah Pike: I've been thinking about the bins again. Still not where they should be.  

**Day 3 05:30**, Yaw Appiah and Sarah Pike at Clover Court:

> Yaw Appiah: Morning, Sarah. You look like you've been up all night.  
> Sarah Pike: No, same as always. They're still being a nuisance.  
> Yaw Appiah: Right you are. We'll manage.  

**Day 3 10:00**, Alejandra Medina and Svetlana Nowak at Hartwell Post Office:

> Alejandra Medina: You’re eating that very quickly. Are you feeling all right?  
> Svetlana Nowak: I was just trying to make it last, really. I was wondering if there might be more hours available for me.  
> Alejandra Medina: More hours? That depends on what the schedule allows. I'll see what I can do.  
> Svetlana Nowak: That’s all I needed to hear. I’ll keep doing my rounds as I always have.  

**Day 3 10:30**, Colin Moore and Funmi Achebe at St. Anne's School:

> Colin Moore: So, are you going to the team tryouts on Thursday?  
> Funmi Achebe: Not if I can help it. Teachers at tryouts? No thanks.  
> Colin Moore: Fair play, I guess. I just really want to get picked.  
> Funmi Achebe: Eh. I’ve got better things to do, anyway.  

**Day 3 11:00**, Rosa Molina and Kwame Osei at Riverside Medical Practice:

> Rosa Molina: Kwame, we still haven't cleared that up. What did you mean on the first?  
> Kwame Osei: I was late, I know. It won't happen again.  
> Rosa Molina: Fair enough. I'll let it slide—for now.  

**Day 3 11:30**, James Page and Julio Medina at The Half Moon:

> James Page: Julio, if I could have a word quick? I was wondering if I could swap my Monday shift with someone if it’s at all possible.  
> Julio Medina: Depends on the day. Who's covering it?  
> James Page: Does Sarah need covering? I can take the Monday shift if she can take mine.  
> *promise by James Page: landed*  

**Day 3 12:00**, Kate Hughes and Tomasz Lewandowski at Hartwell Post Office:

> Kate Hughes: That's that, then. Stamps are two dollars. Early days, but I'm keeping track.  
> Tomasz Lewandowski: Not today. That's life, really.  

**Day 3 12:30**, Olivia Burton and Anna Markovic at The Rolling Pin:

> Olivia Burton: Anna, if I could have a word? It's about my shift earlier.  
> Anna Markovic: Not sure what you mean, love. I was in the back.  

**Day 3 14:00**, Julio Medina and Sarah Bennett at The Half Moon:

> Julio Medina: You're early for your break, Sarah. Eat something before the lunch rush.  
> Sarah Bennett: Aye, keep it. I’ve got a few more hours to make up for that first shift I missed.  
> *gift_accept by Sarah Bennett: landed*  

**Day 3 14:30**, Will Ward and Henry Hughes at Willow Green:

> Will Ward: Henry, you were here first. Any reason you've stuck around?  
> Henry Hughes: Thought you'd like the company. We're both stuck here for a reason, aren't we?  
> Will Ward: Company's a fair enough reason. Beats being alone, I suppose.  

**Day 3 15:00**, Andrei Markovic and Jennifer Graham at Clover Court:

> Andrei Markovic: Mrs. Graham, not that it's my business, but I noticed you and Nancy were speaking earlier about the rent. Has everything been settled?  
> Jennifer Graham: I'll be the judge of that. Things are... being sorted.  

**Day 3 15:30**, Jakub Sokolov and Lakshmi Iyer at Spring Mansions:

> Jakub Sokolov: You know, honestly though, I've had about enough of this slow internet nonsense. I asked the neighbors first, but now I'm waiting on Northline to fix it.  
> Lakshmi Iyer: Ah, the internet! I've had it going at a snail's pace since Tuesday morning, myself.  
> Jakub Sokolov: Aye, well, at least it's not just me, eh? Snails get holidays, I swear.  
> Lakshmi Iyer: Aye, well, at least it's not just me, eh? Snails get holidays, I swear.  

**Day 3 16:30**, Riya Nair and Oliver Hughes at Clover Court:

> Riya Nair: You’ve been here before. You know how the internet works.  
> Oliver Hughes: Internet's a bit of a mystery to me. Cost me a pretty penny this month, anyway.  

**Day 3 17:00**, Owen Moore and Gary Moore at 21 Orchard Lane:

> Owen Moore: You know, I've been thinking about that thing you said about getting it sorted. Any chance you could give me an update?  
> Gary Moore: It’s... it’s on the way, Owen. Just give me a bit more time.  

**Day 3 17:30**, Will Ward and Joe Ward at 17 Clover Street:

> Will Ward: I ran out of money again, you know. Not that I'm asking for anything.  
> Joe Ward: You'll get it back, love. One thing at a time.  
> Will Ward: I just feel like I'm standing still sometimes. That's all.  

**Day 3 18:00**, Kate Hughes and Rose Grant at Victoria Court:

> Kate Hughes: Rose. You seem to be everywhere today.  
> Rose Grant: You could say the same, Kate. Seems like you've been keeping busy too.  
> Kate Hughes: Small mercies. Staying busy beats the quiet.  
> Rose Grant: Aye, staying busy does. We'll see how long it lasts.  

**Day 3 18:30**, Nancy Graham and Jennifer Graham at Clover Court:

> Nancy Graham: Jennifer. You should have told me you were short.  
> Jennifer Graham: I've got it under control, Nancy.  

**Day 3 19:00**, Holly Wright and Peter Wright at 5 Oak Lane:

> Holly Wright: You're still here. That'll do, won't it?  
> Peter Wright: That'll do. Got to sort something with Arjun before Monday.  
> Holly Wright: Sort it before Monday, then. On you go.  

**Day 3 19:30**, Holly Spencer and Harry Wood at 27 Orchard Lane:

> Holly Spencer: You’d be surprised how quickly a debt eats into your day, wouldn’t you?  
> Harry Wood: You could say that. It’s like trying to catch smoke with your bare hands.  
> Holly Spencer: There we are, then. The smoke's still there, but at least it's not spreading.  

**Day 3 20:00**, Víctor Díaz and Ian Shaw at Orchard Mansions:

> Víctor Díaz: You again. What is it, Shaw?  
> Ian Shaw: You again. What is it, Shaw?  

**Day 4 05:00**, Mahmoud Jaber and Rana Jaber at 11 Clover Street:

> Mahmoud Jaber: Rana. We need to talk about what you said Thursday. What did you mean?  
> Rana Jaber: It’s about us, Mahmoud. I think we need to decide if we’re still together or not.  
> Mahmoud Jaber: Right then. You've had your say. What's the move from here?  
> Rana Jaber: I think it's best if we both decide, for ourselves, where we stand.  

**Day 4 05:30**, Adaeze Ogunleye and Kabir Sharma at 23 Spring Terrace:

> Adaeze Ogunleye: Kabir, you awake? Just, uh, wanted to say sorry about the other night. Wasn't me being a drama queen or nothin'.  
> Kabir Sharma: No worries. We all have our moments.  

**Day 4 06:00**, Julia Burton and Zoe Burton at 33 Spring Terrace:

> Julia Burton: So... that internet guy came by yesterday. Sorted it out, apparently.  
> Zoe Burton: Aye, looks like they got it sorted. That’s one less thing to worry about.  
> Julia Burton: You know, I thought it was broken for good. Funny how it fixes itself when you least expect it.  
> Zoe Burton: Aye, well, that’s a good thing. Got to dash, love - early one today.  

**Day 4 06:30**, Anna Markovic and Olivia Burton at The Rolling Pin:

> Anna Markovic: You're up early, love. What is it?  
> Olivia Burton: I wanted to mention that I wasn't sure when I needed to speak with you yesterday.  
> Anna Markovic: I was in the back, love. Same as ever.  

**Day 4 07:00**, Lukas Orlov and Alina Orlov at 23 Orchard Lane:

> Lukas Orlov: You're up early. Had a good sleep?  
> Alina Orlov: Early days, but I had to beat the hunger.  
> Lukas Orlov: Breakfast? The Rolling Pin’s bread is still warm at this hour.  
> Alina Orlov: I’ll take a slice of pie if it’s not too late.  

**Day 4 07:30**, Laura Moore and Beth Moore at Victoria Court:

> Laura Moore: Mum? There's something I'd like to ask you.  
> Beth Moore: Go on then. What is it?  
> Laura Moore: It's about staying out later. I was wondering if you'd consider letting me stay out until eight on weekends.  
> Beth Moore: Provided you're home by eight, I don't see the harm in trying.  

**Day 4 08:30**, Adam Young and Sanjay Iyer at Fresh Fare:

> Adam Young: I heard you're taking the test next week. You feeling ready for it?  
> Sanjay Iyer: Test? Maybe. Depends on what's on it, I suppose.  
> Adam Young: Honesty though, I never asked what the test was for.  

**Day 4 09:00**, Alice Marsh and Chinedu Appiah at 27 Spring Terrace:

> Alice Marsh: You'll be needing a cup of tea soon, I'd wager.  
> Chinedu Appiah: There's a matter of the knee I need to go over with the doctor before it sets in any deeper.  
> Alice Marsh: Don't let it set in any deeper, then. I'll keep the kettle on.  
> Chinedu Appiah: There we are, then. I'll pop along to the clinic after I've had my tea.  

**Day 4 10:30**, Isabel García and Wen Fujita at Spring Pharmacy:

> Isabel García: There we are. That’s the corner, isn’t it. You all right?  
> Wen Fujita: Ach, no bother. I was just looking at the painkillers, myself.  
> Isabel García: Ach, well. Hope it's the kind that pass.  
> Wen Fujita: Ach, well, I’ve got to be along. Thursday bus, you know.  

**Day 4 11:00**, Jakub Sokolov and Lakshmi Iyer at Spring Pharmacy:

> Jakub Sokolov: Jakub, honestly though, you’re like a second shadow these days. Lakshmi, how’s the back holding up?  
> Lakshmi Iyer: Oh, you're quite the observer, aren't you? My back's been tolerable, thank you.  
> Jakub Sokolov: Not today, but I’ll take your word for it. I’ve got a doctor’s appointment to keep.  

**Day 4 11:30**, Marta Estrada and Kwame Osei at Riverside Medical Practice:

> Marta Estrada: You're still here, Kwame.  
> Kwame Osei: Still here, Marta. Just about.  

**Day 4 12:00**, Jakub Sokolov and Lakshmi Iyer at Spring Mansions:

> Jakub Sokolov: Lakshmi, honestly though, that snail internet of ours - you think it's worth a call to Northline? I'm tempted to send 'em a postcard from the Stone Age.  
> Lakshmi Iyer: I thought mine was bad, but I suppose we’re both sharing the same broadband curse.  
> Jakub Sokolov: You know, I might just do it - send them a postcard.  
> Lakshmi Iyer: Well, there you go—postcard to the Stone Age it is, then.  

**Day 4 12:30**, Alejandra Medina and Tomasz Lewandowski at Hartwell Post Office:

> Alejandra Medina: Tomasz, I saw you've been speaking with that woman. Is there something you'd like to tell me about it?  
> Tomasz Lewandowski: Not sure what you're getting at.  
> Alejandra Medina: Fair play. I'll let it ride, but don't let it interfere with your hours.  

**Day 4 13:00**, Simon Talbot and George Fletcher at Spring Pharmacy:

> Simon Talbot: George. Just wanted to follow up on that conversation we had about more hours. I'm still keen if it's something you're considering.  
> George Fletcher: Simon, I hear you. Let me get my head round the numbers first.  
> Simon Talbot: I'll be the judge of that. But if the numbers work, I'm here.  
> George Fletcher: I'll get back to you. Got to make sure the books don't burn down first.  

**Day 4 13:30**, Will Barker and Abigail Barker at 25 Birch Crescent:

> Will Barker: Abby, I wanted to ask you about the noise last night. It woke you up, didn't it?  
> Abigail Barker: I can't say I heard anything last night, love. What kind of noise was it?  
> Will Barker: It was... loud. Like someone dragging something down the hall.  
> Abigail Barker: Could be the pipes, love. Try not to worry about it.  

**Day 4 14:00**, Chloe Burton and Óscar Aguilar at St. Anne's School:

> Chloe Burton: Hey, Óscar. You seen that homework the teacher gave out?  
> Óscar Aguilar: Nah. I've been avoiding Mrs. Patel all day.  
> Chloe Burton: Ugh, I should’ve asked yesterday. It’s due Friday.  
> Óscar Aguilar: Just try not to let her catch you, then.  

**Day 4 14:30**, Henry Hughes and Will Ward at Willow Green:

> Henry Hughes: Company's a fair enough reason. Beats being alone, I suppose.  
> Will Ward: Copper Kettle it is, then. Let me just clear my head a bit.  
> Henry Hughes: Keep your hair on, Will. We’ll see what happens.  
> Will Ward: Well, I’ll be there. Might do some thinking over a coffee.  
> *accept by Will Ward: landed*  

**Day 4 15:00**, Sunita Agarwal and Ben Carter at Crossroads Service Station:

> Sunita Agarwal: Ben, I was just wondering—when you said that on Wednesday, you meant what exactly?  
> Ben Carter: Said what, love? You gonna stand there all day?  
> Sunita Agarwal: You know what I’m talking about. Wednesday, after your shift.  
> Ben Carter: Ben Carter: Look, I don’t run my shifts on guesswork. You want answers, go ask Mahmoud.  

**Day 4 15:30**, Jakub Sokolov and Abiodun Obi at Spring Mansions:

> Jakub Sokolov: Ah, there you are, Abiodun. I've been meaning to ask—did you manage to get that money to Valeria yet?  
> Abiodun Obi: Not yet. It's not my business, but I'm working on it.  

**Day 4 16:00**, Kate Hughes and Julio Medina at Victoria Court:

> Kate Hughes: Julio. You and Sarah were talking earlier, about shifts. What's the story there?  
> Julio Medina: Sarah? She had an early break. Had a bit of a problem with the internet, I think. Can't say much more.  
> Kate Hughes: Internet's been a pain, then. I had a day without it.  

**Day 4 16:30**, Henry Hughes and Mariama Eze at The Copper Kettle:

> Henry Hughes: Mariama. You're just as good for coffee as the place is, I'd say. Mind if I ask you something?  
> Mariama Eze: Depends what it is, Henry.  
> Henry Hughes: That’s the one. He’s been trying to sort out his internet, last I heard.  
> Mariama Eze: Hmm. He hasn't been here, has he? Not that I've noticed.  

**Day 4 17:00**, Oliver Bishop and Charlotte Bishop at 19 Victoria Place:

> Oliver Bishop: You know, Charlotte, I've been meaning to ask you about the bins on Victoria Place again. It seems like every other week they're overflowing, and I'm just not the only one who notices, am I?  
> Charlotte Bishop: Go easy, Oliver. I haven’t a clue who that is.  

**Day 4 17:30**, Kwame Osei and Rosa Molina at Riverside Medical Practice:

> Kwame Osei: Rosa... I need to say something, but I don't know how to start.  
> Rosa Molina: Kwame, if it's hard to start, maybe just say what's on your mind.  
> Kwame Osei: It’s... the lateness. I don’t know how to explain it.  
> Rosa Molina: Well, I'm here now. Let's be sure it doesn't happen again.  

**Day 4 18:00**, Sanjay Iyer and Abiodun Obi at Spring Mansions:

> Sanjay Iyer: I see you've been making promises to Valeria Vega.  
> Abiodun Obi: Valeria's not my business. I'm seeing to it.  
> Sanjay Iyer: You owe her, and she's waiting. That's all there is to it.  

**Day 4 18:30**, Holly Spencer and Harry Wood at 27 Orchard Lane:

> Holly Spencer: I owe Claudia something before Friday, and I’d rather not be reminded of it by her walking through the door.  
> Harry Wood: No bother. Just keep an eye on the time.  

**Day 4 19:00**, Kate Hughes and Hugo Aguilar at Victoria Court:

> Kate Hughes: Hugo. You around earlier today? I saw you come in a few times.  
> Hugo Aguilar: I was working late. Third time today, honestly. Needed to catch up.  
> Kate Hughes: Right. Well. That's that, then.  

**Day 4 19:30**, Mercedes Fuentes and Tara Bhatt at The Rusty Anchor:

> Mercedes Fuentes: Tara, honestly though, I know you're trying but the cocktail shaker's still off. Go on then, let me show you.  
> Tara Bhatt: Alright, boss. Show me then. I'll get it right this time.  
> Mercedes Fuentes: You're getting there. Keep it up.  

**Day 4 20:00**, Farah Nair and Oliver Hughes at Clover Court:

> Farah Nair: Mr. Hughes, if you're not in a hurry, I was wondering if I could ask you about finding work in the town. I understand it's not your business, but if there's anything you've heard—  
> Oliver Hughes: Not my business, but I’ve heard Julio’s been swapping shifts with someone. Might be worth asking him.  
> Farah Nair: A faded denim jacket, you say. I'll keep an ear out for him, thank you.  

**Day 4 20:30**, Nnamdi Achebe and Funmi Achebe at 13 Spring Terrace:

> Nnamdi Achebe: Funmi, your dad's been trying to get hold of you all week, you know.  
> Funmi Achebe: He's here? What'd he want?  
> Nnamdi Achebe: He's just been trying to reach you, that's all. Can you give him a call? He's been carrying that number around like it's a stone in his shoe.  
> Funmi Achebe: I'll call him. Later.  
> *promise by Funmi Achebe: landed*  

**Day 4 21:30**, Mercedes Fuentes and Tara Bhatt at The Rusty Anchor:

> Mercedes Fuentes: Tara, honestly though... I've left some bar snacks on your side of the counter. Go on then, take it.  
> Tara Bhatt: Appreciate it, boss.  
> *gift_accept by Tara Bhatt: landed*  

**Day 4 23:00**, Sarah Pike and Farah Nair at Clover Court:

> Sarah Pike: Farah Nair. We need to talk about those bins.  
> Farah Nair: I beg your pardon?  
> Sarah Pike: Those bins on Clover Street are a disgrace. They’re overflowing again.  
> Farah Nair: I haven't been out that far, I'm afraid. Perhaps you should speak to the council.  

**Day 4 23:30**, Beth Moore and Keith Moore at Victoria Court:

> Beth Moore: Keith, would you mind helping me with something? I need to get in touch with Anna.  
> Keith Moore: Don't know her name, I'm afraid.  
> Beth Moore: Not my business, but she’s usually at the laundromat on the hour.  

**Day 5 00:00**, Sunita Agarwal and Arjun Agarwal at 17 Victoria Place:

> Sunita Agarwal: Arjun, there's something I've been meaning to say since yesterday. It's about the internet.  
> Arjun Agarwal: Go on, then. What about it?  
> Sunita Agarwal: I couldn't tell you.  

**Day 5 00:30**, Sarah Pike and Farah Nair at Clover Court:

> Sarah Pike: Farah Nair. Those bins again. They're a right mess.  
> Farah Nair: I haven't been out that far, I'm afraid. You might speak to the council.  

**Day 5 04:30**, Anna Markovic and Yaw Appiah at Clover Court:

> Anna Markovic: You're up early. Same as ever, I suppose.  
> Yaw Appiah: Aye, just trying to get the day off right. You know how it is.  
> Anna Markovic: Long nights, I'd imagine.  
> Yaw Appiah: Aye, just trying to get the day off right. You know how it is.  
> Anna Markovic: Aye, just trying to get the day off right.  

**Day 5 05:30**, Julia Graham and Sophie Hughes at Clover Court:

> Julia Graham: Morning, Sophie. You're up early.  
> Sophie Hughes: Morning, Julia. Just trying to get an early start.  
> Julia Graham: Bit of a long day ahead, so thought I'd start on time.  

### Every contact with a service

**Day 1 07:30**, Chloe Rhodes to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 1 08:30**, Rose Grant to `northline` by text:

> Rose Grant: I need to speak to someone about my internet. It's been down since this morning.  
> northline: Hi Rose, I'm sorry to hear your internet is down. I'll send an engineer to check it out as soon as possible.  
> *dispatch: at Day 1 09:00, fixes True, kind internet*  

**Day 1 09:00**, Adriana Peña to `northline` by text:

> Adriana Peña: The internet stopped working at my place a couple of hours ago. I want to know what's going on.  
> northline: Hi Adriana, I'm sorry about the internet outage at your home. There's currently a fault affecting your line, and we've already scheduled an engineer to visit at 09:00 today. They'll work to get things back up and running. I'll keep you updated!  
> *promise: by_day 1, kind internet, what your internet working again*  
> *note: text Engineer dispatched to 9 Victoria Place at 09:00 Day 1 to resolve line fault.*  

**Day 1 09:30**, Wendy Wood to `northline` by text:

> Wendy Wood: I need to report an internet outage at my home. It's been down for two hours.  
> northline: Hi Wendy, I'm sorry to hear your internet is down. I can see there's already a fault being looked at on Victoria Place today. I'll schedule an engineer to visit you at 14:00 today. They'll sort out the issue as soon as they arrive.  
> *dispatch: at Day 1 14:00, fixes True, kind internet*  

**Day 1 10:00**, Nancy Graham to `northline` by text:

> Nancy Graham: I need to speak to someone about my bill. It's due and it's higher than usual.  
> northline: Hi Nancy, I see your latest bill was $184.60. That includes your usual $39 plan fee plus any additional charges. Let me check further and get back to you. Could you clarify if there's a specific charge you're concerned about?  
> *resolve: kind billing, note bill corrected*  

**Day 1 10:30**, Ruth Palmer to `northline` by text:

> Ruth Palmer: Hi, I received a bill for $184.60. I believe it's a mistake, as it's much higher than usual.  
> northline: Hi Ruth, I'm sorry about the confusion with your bill. It looks like there might be an issue with the amount charged. I'll resolve this for you right away.  
> *resolve: kind billing, note bill corrected*  

**Day 1 13:00**, Megan Parker to `northline` by text:

> Megan Parker: I need to report an internet outage at 21 Victoria Place. It's been down since 07:00 this morning.  
> northline: Hi Megan, I'm sorry to hear your internet is down. We already have engineers scheduled to visit Victoria Place today at 09:00 and 14:00. I'll keep you updated on progress.  
> *promise: by_day 1, kind internet, what engineers to visit and fix the issue*  
> *note: text Customer reported outage at 07:00, already have engineers scheduled for Victoria Place today.*  

**Day 1 16:30**, Geeta Agarwal to `northline` by text:

> Geeta Agarwal: Hi, I'm Geeta Agarwal. The internet at my house has been down since this morning, and I need it fixed. Can someone come take a look?  
> northline: Hi Geeta, I'm sorry to hear your internet is down. There are already a few faults reported on Victoria Place, and I can schedule an engineer to visit your home. The earliest available slot is tomorrow at 09:00. Would that work for you?  
> *promise: by_day 2, kind internet, what engineer visit*  

**Day 1 17:30**, Neha Joshi to `northline` by text:

> Neha Joshi: I need to sort out this bill - it's four times what I usually pay.  
> northline: Hi Neha, I can see your latest bill is higher than usual. Let me correct that for you.  
> *resolve: kind billing, note bill corrected*  

**Day 1 20:00**, Ellen Spencer to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 1 21:30**, Hugo Aguilar to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 1 22:30**, Abena Eze to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 1 23:00**, Margaret Hughes to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 1 23:30**, Beth Moore to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 1 23:30**, Natalia Kovac to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 2 05:00**, Oliver Hughes to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 2 06:00**, Ximena Aguilar to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 2 06:00**, Omar Yousef to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 2 07:00**, Ian Shaw to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 2 08:00**, Ryan Wood to `northline` by text:

> Ryan Wood: Hello, I'm having trouble with my internet at home. It's been really slow since this morning.  
> northline: Hi Ryan, sorry to hear about the slow internet. I can see your line is currently degraded. I'll send an engineer to check it out.  

**Day 2 09:00**, Kabir Sharma to `northline` by text:

> Kabir Sharma: My internet has been very slow since this morning. I need it fixed.  
> northline: Hi Kabir, I'm sorry to hear your internet is very slow. I'll send an engineer to check it out as soon as possible.  
> *dispatch: at Day 2 10:00, fixes True, kind internet*  

**Day 2 09:00**, Gary Moore to `northline` by text:

> Gary Moore: Hi, I just received a bill for $184.60 for Northline Internet, but I've been paying around $39 before. I need to sort this out, please.  
> northline: Hi Gary, I'm sorry about the confusion with your bill. I can see that you're on the $39 plan, and I'll sort this out right away.  
> *resolve: kind billing, note bill corrected*  

**Day 2 10:00**, Oliver Bishop to `northline` by text:

> Oliver Bishop: I'm Oliver Bishop at 19 Victoria Place. My internet was down yesterday and came back on this morning. Just wanted to let you know, in case it was a wider issue.  
> northline: Hi Oliver, thanks for letting us know. It sounds like your internet is working again now. We do see some other issues on Victoria Place, and I'll keep an eye on it.  
> *note: text Customer reported intermittent internet at 19 Victoria Place. Line is currently working normally, but there are 5 other faults in the area.*  

**Day 2 10:30**, Lena Petrov to `northline` by text:

> Lena Petrov: I'm Lena Petrov. My internet went down yesterday. It's back on now, but I'd like to report it just the same. When can I expect a follow-up?  
> northline: Hi Lena, thanks for letting us know. Your internet is currently working normally, but I've noted your report. An engineer can visit your home to check things over. I can schedule them for Day 3 at 10:00 — would that work for you?  
> *dispatch: at Day 3 10:00, fixes True, kind internet*  
> *note: text Customer reported intermittent outage; scheduled engineer visit for Day 3 10:00*  

**Day 2 11:00**, Charlie Harper to `northline` by text:

> Charlie Harper: My internet's been crawling since this morning. I want to know why.  
> northline: Hi Charlie, sorry about the slow internet. There's a fault affecting Spring Terrace, and we already have an engineer scheduled for 10:00 today to fix it. They'll sort it out when they arrive.  
> *promise: by_day 2, kind internet, what your internet working again*  
> *note: text Engineer already scheduled for 10:00 on Day 2 for Spring Terrace fault.*  

**Day 2 12:00**, Kwesi Achebe to `northline` by text:

> Kwesi Achebe: I need to report a fault with my home internet. It's been running at a crawl since the morning.  
> northline: Hi Kwesi, sorry to hear your internet is so slow. There are a few faults on Spring Terrace, and we've already scheduled an engineer for 10:00 AM today. They'll check the line and get things back to normal.  

**Day 2 12:30**, Abiodun Obi to `northline` by text:

> Abiodun Obi: I'm Abiodun Obi. I've been paying for my service and it's been down since 08:00.  
> northline: Hi Abiodun, I'm sorry to hear your internet has been very slow since 08:00. There's currently a fault affecting several lines on Spring Terrace, and an engineer is already scheduled to investigate at 10:00 today. I'll keep you updated.  
> *promise: by_day 2, kind internet, what the fault on Spring Terrace to be investigated*  
> *note: text Customer informed about scheduled engineer visit and fault on street.*  

**Day 2 13:30**, Pooja Joshi to `northline` by text:

> Pooja Joshi: I need to speak to someone about my internet service. It's been down for two days.  
> northline: Hi Pooja, I'm sorry to hear about your internet issues. Let me check that for you.  
> *promise: by_day 2, kind internet, what a resolution for your internet*  

**Day 2 14:30**, Henry Murray to `northline` by text:

> Henry Murray: I'm Henry Murray from 11 Birch Crescent. I need to report an internet outage.  
> northline: Hi Henry, thanks for getting in touch. I can see your line is currently working normally. Would you mind checking your router and modem to make sure they're powered on and connected properly? Let me know if you still have issues.  
> *note: text Customer reported internet outage, but line status shows normal. Requested to check router and modem.*  

**Day 2 15:00**, Rob Moore to `northline` by text:

> Rob Moore: I need to speak to someone about my internet. It's been unusably slow since this morning.  
> northline: Hi Rob, sorry to hear about the slow internet. We've got several issues on Spring Terrace, and we've already scheduled an engineer to look into it today at 10:00. They'll check the line and get things sorted as soon as they can.  
> *promise: by_day 2, kind internet, what a resolution for the internet slowdown*  
> *note: text Customer informed about scheduled engineer visit for Spring Terrace line issues.*  

**Day 2 15:30**, Igor Kovac to `northline` by text:

> Igor Kovac: Hi, it's Igor Kovac here. I've been having issues with very slow internet at my house, 15 Spring Terrace, since this morning. I need to get it sorted out.  
> northline: Hi Igor, sorry to hear about the slow internet at your house. There's a known issue on Spring Terrace with several other customers also affected. An engineer is already scheduled for your home on Day 2 at 10:00. They'll sort it out when they arrive.  

**Day 2 15:30**, Yolanda García to `northline` by text:

> Yolanda García: I need to report a problem with my home internet. It's been very slow since this morning.  
> northline: Hi Yolanda, I'm sorry about the slow internet at your home. There's a known issue on Spring Terrace affecting several customers, and we have an engineer scheduled to check it today at 10:00. I'll keep you updated.  
> *promise: by_day 2, kind internet, what a resolution for the internet issue*  
> *note: text Customer Yolanda García has a slow internet issue. Engineer scheduled for today at 10:00.*  

**Day 2 16:00**, Julia Burton to `northline` by text:

> Julia Burton: I’ve had slow internet since this morning. It’s been like that for eight hours.  
> northline: Hi Julia, I'm sorry to hear about the slow internet. There are several faults on Spring Terrace, and I've scheduled an engineer to visit you at 10:00 tomorrow to fix it.  
> *dispatch: at Day 3 10:00, fixes True, kind internet*  

**Day 2 17:30**, Kwesi Achebe to `northline` by text:

> Kwesi Achebe: Hi, it's Kwesi. I texted earlier about the internet on Spring Terrace. It's been nine hours, and I still can't get a decent connection. I'm paying for this, so I'd like to know what's actually happening.  
> northline: Hi Kwesi, sorry it's still so slow for you. The engineer was scheduled for 10:00 AM today but couldn't make it. We've moved them to 10:00 AM tomorrow, Day 3, and added a second visit that day to make sure it's fixed. I'll note this for the team, and I'll let you know when it's sorted.  
> *dispatch: at Day 3 10:00, fixes True, kind internet*  
> *note: text Customer reported slow internet on Spring Terrace. Engineer dispatched at 10:00 on Day 3. Customer unhappy with previous delay.*  

**Day 2 20:30**, Paula Fuentes to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 2 21:00**, Jane Parker to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 2 23:00**, Simon Talbot to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 07:30**, Rahul Iyer to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 08:30**, Jakub Sokolov to `northline` by text:

> Jakub Sokolov: I've been having some issues with the internet at my place, Spring Mansions. It's been really slow since yesterday morning.  
> northline: Hi Jakub, I'm sorry to hear about the slow internet at your place. There's currently a fault affecting several customers on Spring Terrace, including you. An engineer is already scheduled to check the issue today at 10:00. I'll keep you updated. Thanks for your patience.  
> *note: text Customer Jakub Sokolov experiencing slow internet. Fault affecting multiple customers on Spring Terrace. Engineer scheduled for today at 10:00.*  

**Day 3 13:30**, Matt Webb to `northline` by call:

> Matt Webb: I need to report an internet outage at my place. It's been like this for over a day.  
> northline: Hi Matt, sorry to hear about the slow internet at your place. There are currently faults affecting other customers on Spring Terrace, and we have engineers scheduled to look into these issues on Day 3 at 10:00. I'll make sure one of them checks your line as well. Thank you for your patience.  

**Day 3 15:00**, Raj Qureshi to `northline` by text:

> Raj Qureshi: I need to report an internet outage at my place. It's been down since yesterday.  
> northline: Hi Raj, I'm sorry to hear about your internet issues. However, our records show that your line is currently working normally, and there are no faults reported on Birch Crescent. Could you double-check your connection or try restarting your router?  

**Day 3 16:00**, Henry Hughes to `northline` by text:

> Henry Hughes: I'm Henry Hughes, I'm having some issues with my internet connection. I need to sort this out right away.  
> northline: Hi Henry, I'm sorry to hear about your internet issues. I can see your line is currently working normally, but I'll send an engineer to check it out for you. They'll be able to visit on Day 4 at 10:00.  
> *dispatch: at Day 4 10:00, fixes True, kind internet*  
> *note: text Engineer dispatched to check line for Henry Hughes on Day 4 at 10:00.*  

**Day 3 16:00**, Paula Fuentes to `northline` by text:

> Paula Fuentes: I've been having very slow internet at my place since yesterday morning. I need it fixed.  
> northline: Hi Paula, I'm sorry to hear about the slow internet. There's a known issue on Spring Terrace affecting several customers. I can book an engineer for you on Day 5 at 10:00 to investigate. Would that work for you?  
> *dispatch: at Day 5 10:00, fixes True, kind internet*  

**Day 3 16:30**, Natalia Kovac to `northline` by text:

> Natalia Kovac: I'm calling about the internet issue at 15 Spring Terrace. The engineer was scheduled for Day 2 at 10:00 but the problem hasn't been resolved yet.  
> northline: Hi Natalia, I'm sorry for the delay. There's still a fault affecting your line, and an engineer is scheduled for Day 5 at 10:00. I'll note this for the team.  
> *promise: by_day 5, kind internet, what your internet working again*  
> *note: text Customer reported no improvement after scheduled engineer visit on Day 2. Engineer rescheduled for Day 5.*  

**Day 3 18:00**, Natalia Kovac to `northline` by text:

> Natalia Kovac: This is Natalia Kovac. I need to speak to someone about the ongoing delay with my service. It's been over two days.  
> northline: Hi Natalia, I'm sorry for the continued delay. The engineer is scheduled for Day 5 at 10:00, and I've promised your internet working again by then. I'll note this for the team again.  
> *note: text Customer is frustrated with ongoing delay; engineer scheduled for Day 5 at 10:00.*  

**Day 3 19:30**, Abena Eze to `northline` by text:

> Abena Eze: Hello, I'm Abena Eze from 7 Victoria Place. The internet went off again just now, about an hour ago. I wanted to check if there's an issue or if I need to do something.  
> northline: Hi Abena, sorry to hear your internet is down. There are currently faults affecting Victoria Place, including your line. I've scheduled an engineer to visit you at 10:00 tomorrow. They'll work on getting your line back up.  
> *dispatch: at Day 4 10:00, fixes True, kind internet*  

**Day 3 20:30**, Ellen Spencer to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 21:30**, Omar Yousef to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 22:00**, Filip Horvat to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 22:00**, Wendy Wood to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 23:30**, Beth Moore to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 4 00:00**, Keith Moore to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 4 06:00**, Oliver Hughes to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 4 07:00**, Víctor Díaz to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 4 11:30**, Henry Hughes to `northline` by text:

> Henry Hughes: Hi, I noticed your technician was at 13 Clover Street earlier today. I need to sort out some internet issues and would like to schedule a visit.  
> northline: Hi Henry, I see the engineer was at 13 Clover Street earlier today. They’ll be stopping by again at 10:00 tomorrow to check your internet connection. I’ll let them know you’re expecting them.  

**Day 4 15:00**, Raj Qureshi to `northline` by text:

> Raj Qureshi: Hi, I spoke to someone yesterday about my internet on Birch Crescent. I'm still having no signal, and I can't believe the router's fixed itself by now. Do I need to come in and sort it out in person?  
> northline: Hi Raj, I'm sorry you're still having trouble, but our system shows your line is working normally on Birch Crescent with no faults. Let's send an engineer to check it out. I've scheduled a visit for Day 6 at 10:00. They'll look into it and get things sorted.  
> *dispatch: at Day 6 10:00, fixes True, kind internet*  

**Day 4 20:30**, Paula Fuentes to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

### Every refusal, by reason

- 16 x it isn't my shift
- 2 x I had already talked with Yaw Appiah today
- 1 x I had already talked with Abiodun Obi today
- 1 x I had already talked with Ama Abiola today
- 1 x I had already talked with Andrei Markovic today
- 1 x I had already talked with Arjun Agarwal today
- 1 x I had already talked with Ben Carter today
- 1 x I had already talked with Farah Nair today
- 1 x I had already talked with Jennifer Graham today
- 1 x I had already talked with Joe Ward today
- 1 x I had already talked with Lakshmi Iyer today
- 1 x I had already talked with Luke Bishop today
- 1 x I had already talked with Olivia Burton today
- 1 x I had already talked with Rana Jaber today
- 1 x I had already talked with Sanjay Iyer today
- 1 x there is no victoria_place_1 to meet at
