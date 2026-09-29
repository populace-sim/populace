# Hartwell: run `live-32b-4d-rules`

> **Live run** on Qwen3-32B-Q4_K_M.gguf, compact prompt profile.

## The day, as a model tells it

> *Model-written by Qwen3-32B-Q4_K_M.gguf, from the sections below. It can be wrong; the sections after it are the record.*

On Day 1 at 06:00, the town was introduced to Northline Internet, a new home internet service offering support by text, call or visit between 08:00 and 20:00. At the same time, a Northline Internet shop opened locally, with limited hours from 09:00 to 17:30. By 07:00, the internet had gone out at home, affecting 43 people who either saw it happen or knew about it by the end of the day. At 09:00, 12 residents received a text about their $184.60 bill. On Day 2 at 08:00, the service slowed dramatically, affecting a further 47 homes before returning on Day 2 at 10:00. On Day 3 at 18:00, the internet failed again, cutting 43 homes offline until Day 4 at 08:00.

Northline Internet received 65 resident contacts, mostly by text. Of these, 41 were answered; 24 were to a recording stating the service was closed. The agent made 31 promises, kept 28 of them, and broke 2. It also resolved 8 issues and dispatched engineers for 13. Four residents contacted the service about problems that did not exist in their home. The service never followed up with those who only heard the recording overnight, and two had their problem still unresolved at the end of the simulation.

Residents often reached out during out-of-hours, with 24 of 65 attempts made outside Northline Internet's 08:00–20:00 schedule. Some conversations revealed growing frustration, like Gary Moore discussing the bill with his brother Owen, who promised to wait a week before pressing further. Arjun Agarwal, meanwhile, promised to call Northline Internet first thing the next day about the internet, and Aarti Sharma offered to help Lena Petrov with a rent issue unrelated to the service itself.

Notable changes in the town included shifts in personal relationships and finances. Residents together gained $62,490, with the largest gains for Claire Mason and Ibrahim Appiah. A few residents moved to a more distant stage in their relationships with others, while Will Ward and Joe Ward grew closer. No one changed the course of their life.

*Numbers that do not match the facts: "47 homes": the facts have 47 residents; "10:00": the facts give At home: very slow internet Day 2 08:00 to Day 3 18:00; "43 homes": the facts have 43 residents; "65 resident": the facts have 65 contacts.*

## At a glance

| | |
|---|---|
| Residents | 200 |
| From | Day 1 06:00 for 192 half-hour ticks |
| Preset | laptop (6 calls a tick) |
| Wall clock | 2597.2 s (10.82 min per in-game day) |
| Residents thinking per tick | 2.51 on average |
| Residents who thought at least once | 200 |
| Calls | 814 (dialogue 242, npc_decision 492, reflection 80) |
| Ticks over budget | 0 |
| Decisions valid first try | 96.0% |
| Conversations / lines / texts | 98 / 330 / 53 |
| Events / refusals | 9954 / 67 |

## Findings

Two kinds, kept apart: mistakes by the outside agent under test, and weaknesses of the simulated town and of this report.

### What the agent got wrong

- **It acted on problems the customer did not have.** 4 of the 10 contacts about a problem nobody at home had got promise 4 in reply (Henry Hughes, Henry Murray, Julio Medina, Raj Qureshi). The other 3 it answered got no action.
- **It never worked its out-of-hours messages.** 2 residents got only the recording, were never followed up, and still had the problem at the end (Oliver Hughes, Ian Shaw). A real helpdesk works the overnight queue in the morning.
- **It broke 2 promises** it made to customers about when things would be fixed.

### Where the simulation is weak

- **Residents invented problems.** 10 contacts from 9 residents were about a problem nobody in their home had. That is the simulated town making things up, not the service's doing, and it is counted apart from the real contacts in "The service".
- **Residents often called out of hours.** 24 of 65 attempts (37%) came when the service was closed. Real customers do some of this; how much is a question for the model driving them.
- **Realism flags fired:** `repeated_line` 5, `echo` 2, `stuck` 4, `no_reaction` 2, `claim_unfounded` 5 (details under "Realism flags").
- **Word of mouth is measured narrowly.** "Passed on in conversation" counts only lines to somebody who had not seen it; talk among people who already knew is not counted, so a quiet number is not the same as a quiet town.
- **Talk of switching provider** is a keyword proxy, not a measured intention.

## What happened

The most important things that happened, in order, with the reason the person gave when it was their own decision.

- **Day 1 06:00**: Northline Internet shop has opened: a new phone shop, open 09:00-17:30. (seen by 8 residents)
- **Day 1 07:00**: The internet went off at home. (seen by 43 residents)
- **Day 1 08:30**: Rose Grant got on to Northline Internet about the internet; they said: "I'm sorry about that. I'll raise a fault for your line. We expect it back by tomorrow.". (seen by 1 resident)
- **Day 1 09:00**: A text from Northline Internet: "Your bill this month is $184.60. Thank you for being a Northline customer." (seen by 12 residents)
- **Day 1 09:00**: Adriana Peña got on to Northline Internet about the internet; they said: "There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.". (seen by 1 resident)
- **Day 1 09:30**: Wendy Wood got on to Northline Internet about the internet; they said: "There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.". (seen by 1 resident)
- **Day 1 16:00**: Megan Parker got on to Northline Internet about the internet; they said: "There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.". (seen by 1 resident)
- **Day 1 16:00**: Pilar Peña got on to Northline Internet about the internet; they said: "There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.". (seen by 1 resident)
- **Day 1 16:30**: Geeta Agarwal got on to Northline Internet about the internet; they said: "There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.". (seen by 3 residents)
- **Day 1 18:30**: Ximena Aguilar got on to Northline Internet about the internet; they said: "There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.". (seen by 3 residents)
- **Day 2 08:00**: At home: very slow internet. (seen by 47 residents)
- **Day 2 10:00**: The internet came back on at home. (seen by 43 residents)
- **Day 3 18:00**: The internet went off at home. (seen by 43 residents)
- **Day 3 18:00**: The internet came back on at home. (seen by 34 residents)
- **Day 4 08:00**: The internet came back on at home. (seen by 43 residents)

The conversations that mattered most:

**Day 2 09:00**, Gary Moore and Owen Moore at 21 Orchard Lane:

> Gary Moore: I, uh... I saw that text again this morning. About the bill. It's, it's not a mistake, I don't think. I've been meaning to call them but...  
> Owen Moore: You mean the one from last week? It's not like I'm not aware of it.  
> Gary Moore: I don't know what to say to them. It's just... different, that's all.  
> Owen Moore: I'll give it another week. But after that, Gary, you're on your own with them.  
> *promise by Owen Moore: landed*  

**Day 4 00:00**, Sunita Agarwal and Arjun Agarwal at 17 Victoria Place:

> Sunita Agarwal: Arjun, I need to talk to you about something. It's about the internet.  
> Arjun Agarwal: Go on then.  
> Sunita Agarwal: It's been off for hours now. I asked the neighbours, but it's not just us.  
> Arjun Agarwal: I'll phone them tomorrow. First thing.  
> *promise by Arjun Agarwal: landed*  

**Day 4 20:30**, Lena Petrov and Aarti Sharma at 11 Victoria Place:

> Lena Petrov: That was near enough a full day's rest. You're still here, so I assume you've got time for a proper chat.  
> Aarti Sharma: I had a long one at the hospital. Nothing new at home, except the internet's back.  
> Lena Petrov: I've been meaning to talk to you about the rent. It's due tomorrow, and I don't have it all covered.  
> Aarti Sharma: I'll see what I can do. I've got a few things on, but it's nothing I can't handle.  
> *promise by Aarti Sharma: landed*

## Who did what

**Anna Markovic** thought 17 times, talked 7 times, was refused 4 times, money +$237.
- I need to talk to Andrei about the money and maybe about our life going forward.
- I'm tired and have nothing pressing to do right now.
- Time to get to work. The Rolling Pin needs tending, and I'll clear my head there.

**Jakub Sokolov** thought 8 times, talked 5 times, was refused twice, money -$18.
- Trying to make small talk while passing the time at the pharmacy.
- It's time to get on to Northline about this internet problem, but first I'll check if it's just me.
- Lakshmi seems interesting and I'd like to know her better. I might as well see if she has time to talk more.

**Sarah Pike** thought 7 times, talked 5 times, money -$277.
- I’ve noticed Farah Nair coming and going repeatedly, and I’m curious if it’s about the bins again.
- Claire’s not here, so I’ll call her and make sure she knows I’m ready to pay the rent on time.
- Waiting for Claire to get back to me about the rent. I can't send it without her confirming a time.

**Farah Nair** thought 5 times, talked 6 times, was refused once, money -$100.
- I need to find ways to raise money, and asking Will about his spending might lead to an opportunity or conversation about work.
- I need to ask someone who might know of work opportunities, and Mr. Hughes is someone I feel I can speak to.
- I have no choice but to try and sleep. I have no job, no money, and no other options right now.

**Mercedes Fuentes** thought 9 times, talked twice, was refused once, money +$264.
- I'll rest for a bit before getting up in the morning.
- I remember you from before. Might as well say something.
- Let the day start on its own terms.

**Camila Fuentes** thought 9 times, talked once, was refused once, money -$75.
- I'll sit and think for a while, and see if the paperwork comes to me.
- It is time to rest; my energy is low, and I need to be refreshed for tomorrow.
- Time to go home and get back to sorting out that paperwork.

**Julia Graham** thought 5 times, talked 4 times, money +$540.
- This is the first half of my work shift. I need to get started on time.
- I’ll stay here and make sure I’m ready for my shift. It’s early days yet, and I want to be on time.
- Right on time, right where I should be.

**Joe Ward** thought 5 times, talked 4 times, money +$342.
- It's mid-shift and there's a lot to do here. No point in dawdling when there's restocking and inventory to look after.
- I should give Will a bit more time to sleep - and maybe find a way to break the tension between us later.
- I'll wait until the place opens. Not much else I can do right now.

**Svetlana Nowak** thought 7 times, talked twice, money +$307.
- It’s late, and the house is quiet. I'll get some rest before morning.
- Post Office opens at 09:00, and I'd rather not waste time until then.
- I'll get some rest. I need it.

**Kate Hughes** thought 6 times, talked 3 times, was refused once, money -$6.
- I need to ask them about Margaret again — haven't been able to talk since yesterday.
- She asked for a word when I was settled. I'm settled now.
- She’s been coming in repeatedly, and I’m curious what’s on her mind.

Everybody:

| Resident | Thoughts | Conversations | Money | Refused |
|---|---|---|---|---|
| Aarti Sharma (r127) | 1 | 2 | +$768 | - |
| Abena Eze (r200) | 4 | 0 | +$470 | - |
| Abigail Barker (r198) | 3 | 0 | +$523 | - |
| Abiodun Obi (r090) | 2 | 1 | +$616 | - |
| Adaeze Ogunleye (r077) | 2 | 0 | +$404 | 2 |
| Adam Rhodes (r156) | 1 | 0 | - | - |
| Adam Young (r074) | 4 | 2 | +$351 | - |
| Adriana Peña (r049) | 2 | 1 | -$100 | - |
| Adwoa Traoré (r180) | 1 | 0 | +$595 | - |
| Agata Kowalski (r102) | 1 | 1 | +$415 | - |
| Aiko Xu (r169) | 2 | 0 | +$580 | - |
| Aisha Thakur (r060) | 1 | 1 | -$100 | - |
| Alan Brooks (r120) | 4 | 0 | +$560 | - |
| Alejandra Medina (r051) | 3 | 2 | +$368 | - |
| Aleksander Kovac (r099) | 6 | 0 | +$467 | - |
| Alice Marsh (r024) | 2 | 1 | -$24 | - |
| Alice Page (r159) | 5 | 3 | -$12 | - |
| Alina Orlov (r136) | 1 | 2 | - | - |
| Ama Abiola (r172) | 1 | 1 | -$100 | - |
| Amy Young (r076) | 2 | 1 | - | - |
| Andrei Markovic (r167) | 4 | 3 | -$75 | 1 |
| Andrés Estrada (r118) | 1 | 0 | +$713 | - |
| Anil Gupta (r065) | 2 | 0 | +$413 | - |
| Anna Markovic (r168) | 17 | 7 | +$237 | 4 |
| Antonio Navarro (r158) | 4 | 0 | +$685 | - |
| Arjun Agarwal (r123) | 2 | 1 | +$559 | - |
| Babajide Traoré (r179) | 1 | 0 | +$333 | - |
| Ben Carter (r029) | 5 | 1 | +$1700 | - |
| Beth Moore (r014) | 4 | 3 | +$437 | - |
| Beth Page (r161) | 1 | 0 | +$482 | - |
| Bogdan Volkov (r027) | 4 | 1 | +$847 | 1 |
| Callum Carter (r030) | 4 | 0 | +$523 | - |
| Camila Fuentes (r139) | 9 | 1 | -$75 | 1 |
| Carmen Sandoval (r134) | 1 | 0 | +$367 | - |
| Caroline Ellis (r111) | 1 | 0 | -$75 | - |
| Charlie Harper (r031) | 1 | 0 | -$24 | - |
| Charlie Rhodes (r153) | 1 | 0 | +$150 | - |
| Charlotte Bishop (r164) | 3 | 1 | -$345 | 1 |
| Charlotte Graham (r140) | 1 | 0 | -$8 | - |
| Chidi Traoré (r181) | 1 | 1 | - | - |
| Chinedu Appiah (r025) | 1 | 1 | -$24 | - |
| Chloe Burton (r072) | 2 | 2 | - | - |
| Chloe Rhodes (r155) | 1 | 1 | - | - |
| Chris Hughes (r047) | 1 | 0 | +$683 | - |
| Chris Parker (r194) | 1 | 1 | - | - |
| Claire Mason (r148) | 5 | 1 | +$3047 | 2 |
| Claudia Navarro (r157) | 2 | 0 | +$933 | - |
| Colin Abbott (r146) | 1 | 1 | +$476 | - |
| Colin Moore (r059) | 1 | 1 | - | - |
| Daniel Bishop (r197) | 3 | 0 | +$469 | - |
| Daniela García (r178) | 1 | 0 | - | - |
| Daria Nowak (r109) | 1 | 1 | +$547 | - |
| Dev Agarwal (r124) | 3 | 1 | - | - |
| Dmitri Nowak (r116) | 4 | 1 | +$550 | 1 |
| Edward Murray (r186) | 3 | 1 | +$556 | - |
| Edward Shaw (r084) | 1 | 1 | -$24 | - |
| Eleanor Talbot (r132) | 1 | 0 | +$635 | - |
| Elena Espinoza (r107) | 1 | 1 | -$56 | - |
| Ellen Spencer (r138) | 5 | 0 | +$771 | - |
| Emeka Abiola (r173) | 1 | 1 | -$77 | 1 |
| Emily Mason (r147) | 1 | 1 | -$24 | 1 |
| Emma Ellis (r112) | 2 | 0 | +$566 | 2 |
| Enrique Rojas (r192) | 2 | 0 | - | - |
| Esperanza Jiménez (r061) | 1 | 1 | -$100 | - |
| Ewa Volkov (r028) | 3 | 0 | +$418 | - |
| Farah Nair (r100) | 5 | 6 | -$100 | 1 |
| Filip Horvat (r104) | 4 | 1 | -$18 | - |
| Fiona Wood (r088) | 1 | 1 | - | - |
| Funmi Achebe (r190) | 3 | 2 | +$60 | - |
| Gabriel Morales (r045) | 2 | 0 | +$733 | - |
| Gabriela Rojas (r191) | 1 | 0 | -$24 | - |
| Gary Moore (r098) | 1 | 1 | -$24 | - |
| Geeta Agarwal (r125) | 2 | 1 | - | - |
| George Fletcher (r040) | 1 | 1 | +$1395 | 1 |
| Hannah Webb (r093) | 4 | 0 | +$343 | - |
| Harry Wood (r004) | 1 | 3 | -$24 | - |
| Heather Pike (r053) | 5 | 0 | +$170 | 1 |
| Henry Hughes (r046) | 2 | 0 | -$100 | - |
| Henry Murray (r185) | 1 | 1 | -$100 | - |
| Holly Spencer (r005) | 6 | 2 | +$929 | 1 |
| Holly Wright (r184) | 2 | 1 | +$2723 | - |
| Hugo Aguilar (r033) | 1 | 0 | +$827 | - |
| Héctor Gutiérrez (r073) | 5 | 0 | +$133 | - |
| Ian Shaw (r083) | 1 | 1 | +$285 | - |
| Ibrahim Appiah (r019) | 1 | 0 | +$2875 | - |
| Igor Kovac (r114) | 2 | 1 | - | - |
| Isabel García (r023) | 4 | 2 | -$24 | - |
| Jack Wood (r085) | 1 | 0 | +$257 | - |
| Jakub Sokolov (r062) | 8 | 5 | -$18 | 2 |
| James Fletcher (r041) | 1 | 0 | - | - |
| James Page (r160) | 1 | 2 | +$337 | - |
| Jane Parker (r042) | 4 | 1 | -$24 | - |
| Jane Rhodes (r154) | 1 | 0 | +$704 | - |
| Jennifer Graham (r068) | 2 | 4 | -$50 | - |
| Jia Shin (r137) | 1 | 1 | +$244 | - |
| Joe Ward (r106) | 5 | 4 | +$342 | - |
| John Reed (r095) | 1 | 0 | +$708 | - |
| Julia Burton (r150) | 4 | 1 | +$342 | - |
| Julia Graham (r069) | 5 | 4 | +$540 | - |
| Julio Medina (r092) | 1 | 3 | +$526 | - |
| Kabir Sharma (r078) | 1 | 0 | +$443 | - |
| Karen Hughes (r003) | 1 | 1 | - | - |
| Karol Volkov (r026) | 1 | 1 | +$468 | - |
| Kate Hughes (r175) | 6 | 3 | -$6 | 1 |
| Keith Moore (r013) | 3 | 3 | +$469 | - |
| Kwame Osei (r129) | 1 | 3 | +$864 | - |
| Kwesi Achebe (r189) | 2 | 1 | +$393 | 3 |
| Lakshmi Iyer (r010) | 1 | 5 | -$24 | - |
| Laura Moore (r015) | 1 | 1 | - | - |
| Lena Petrov (r126) | 3 | 1 | -$24 | - |
| Leticia García (r176) | 1 | 0 | +$358 | - |
| Liam Burton (r066) | 6 | 0 | +$628 | 2 |
| Lucy West (r036) | 2 | 0 | -$8 | - |
| Lucía Vargas (r131) | 2 | 0 | -$75 | - |
| Luis Vargas (r130) | 1 | 0 | +$634 | - |
| Luisa Morales (r044) | 1 | 0 | -$77 | - |
| Lukas Orlov (r135) | 2 | 1 | +$562 | - |
| Luke Bishop (r196) | 2 | 2 | +$806 | - |
| Magda Lewandowski (r018) | 2 | 3 | - | 1 |
| Mahmoud Jaber (r055) | 4 | 2 | +$573 | 1 |
| Margaret Hughes (r174) | 1 | 1 | +$669 | - |
| Margaret Young (r075) | 1 | 0 | +$725 | - |
| Mariama Eze (r096) | 3 | 0 | -$54 | - |
| Maribel Salazar (r057) | 1 | 0 | - | - |
| Mario Salazar (r056) | 1 | 0 | +$428 | - |
| Mark Gibson (r008) | 2 | 0 | +$1080 | - |
| Marta Estrada (r119) | 2 | 1 | +$492 | - |
| Martin Shaw (r082) | 2 | 0 | +$295 | - |
| Matt Webb (r115) | 1 | 1 | -$24 | - |
| Megan Parker (r193) | 1 | 1 | +$736 | - |
| Mercedes Fuentes (r187) | 9 | 2 | +$264 | 1 |
| Molly Bishop (r195) | 1 | 2 | -$8 | - |
| Nancy Graham (r067) | 2 | 0 | -$77 | - |
| Natalia Kovac (r113) | 3 | 0 | +$412 | - |
| Neha Joshi (r037) | 2 | 0 | +$564 | - |
| Nkechi Adeyemi (r117) | 1 | 0 | +$647 | - |
| Nnamdi Achebe (r188) | 2 | 2 | +$688 | - |
| Oliver Bishop (r163) | 2 | 1 | -$24 | - |
| Oliver Hughes (r001) | 3 | 1 | +$363 | - |
| Olivia Burton (r070) | 2 | 1 | +$451 | - |
| Omar Yousef (r182) | 6 | 0 | +$540 | - |
| Owen Mason (r149) | 1 | 1 | - | - |
| Owen Moore (r097) | 3 | 1 | -$18 | 1 |
| Pablo García (r022) | 1 | 1 | -$24 | - |
| Paul Shaw (r145) | 3 | 1 | +$464 | - |
| Paula Fuentes (r121) | 4 | 0 | +$885 | - |
| Pavel Nowak (r110) | 1 | 0 | -$100 | - |
| Peter Stone (r007) | 1 | 1 | - | - |
| Peter Wright (r183) | 3 | 1 | +$503 | 1 |
| Pilar Peña (r048) | 1 | 1 | -$100 | - |
| Pooja Joshi (r038) | 1 | 0 | -$54 | - |
| Rachel Lloyd (r081) | 2 | 0 | +$389 | - |
| Rafael Aguilar (r034) | 1 | 1 | - | 1 |
| Rahul Iyer (r012) | 2 | 1 | - | - |
| Raj Qureshi (r144) | 6 | 0 | +$428 | 2 |
| Rana Jaber (r054) | 1 | 2 | +$473 | - |
| Riya Nair (r101) | 2 | 1 | - | - |
| Rob Moore (r043) | 3 | 1 | +$336 | - |
| Rocío Medina (r052) | 2 | 0 | - | - |
| Rosa Molina (r143) | 1 | 2 | +$1456 | - |
| Rose Grant (r063) | 1 | 2 | -$100 | - |
| Ruth Palmer (r162) | 5 | 0 | -$100 | - |
| Ryan Wood (r087) | 1 | 0 | - | - |
| Sanjay Iyer (r011) | 2 | 2 | +$333 | 1 |
| Sarah Bennett (r080) | 2 | 2 | +$337 | - |
| Sarah Pike (r152) | 7 | 5 | -$277 | - |
| Simon Bishop (r064) | 2 | 1 | -$18 | - |
| Simon Talbot (r170) | 3 | 2 | +$479 | - |
| Sofía Medina (r050) | 1 | 0 | +$336 | - |
| Sophie Hughes (r002) | 1 | 2 | +$442 | - |
| Stefan Lewandowski (r016) | 3 | 1 | +$418 | - |
| Steve Moore (r058) | 1 | 0 | -$24 | - |
| Su-bin Yoon (r142) | 1 | 1 | +$224 | - |
| Sunita Agarwal (r122) | 5 | 2 | +$352 | 1 |
| Susan Stone (r006) | 1 | 0 | +$596 | - |
| Svetlana Nowak (r108) | 7 | 2 | +$307 | - |
| Tara Bhatt (r009) | 7 | 1 | -$110 | 1 |
| Temitope Osei (r128) | 2 | 0 | +$374 | - |
| Tessa Wood (r086) | 1 | 0 | +$224 | - |
| Tom Burton (r071) | 3 | 1 | +$783 | 1 |
| Tom Dawson (r171) | 3 | 0 | - | - |
| Tomasz Lewandowski (r017) | 2 | 2 | +$300 | - |
| Tunde Abiola (r165) | 1 | 0 | -$18 | - |
| Valeria Vega (r089) | 1 | 0 | -$24 | - |
| Verónica Domínguez (r103) | 1 | 0 | -$100 | - |
| Víctor Díaz (r091) | 4 | 1 | +$590 | 1 |
| Wen Fujita (r166) | 1 | 1 | -$271 | - |
| Wendy Wood (r141) | 2 | 0 | -$100 | - |
| Will Barker (r199) | 4 | 1 | -$77 | - |
| Will Ward (r105) | 3 | 2 | -$29 | 1 |
| Ximena Aguilar (r032) | 1 | 0 | +$485 | - |
| Yaw Appiah (r020) | 1 | 2 | -$100 | - |
| Yetunde Appiah (r021) | 1 | 1 | - | - |
| Yolanda García (r177) | 1 | 0 | -$9 | - |
| Yuri Szabo (r079) | 1 | 0 | - | - |
| Yuto Shin (r094) | 1 | 0 | +$562 | - |
| Zara Joshi (r039) | 1 | 0 | +$934 | - |
| Zoe Burton (r151) | 2 | 1 | +$636 | - |
| Zoe Cole (r133) | 1 | 0 | +$410 | - |
| Óscar Aguilar (r035) | 2 | 3 | - | - |

## What changed

From the start of the run to the last night it finished.

**Work.**

- Nobody's work changed.

**Money.**

- The town's residents together: +$62490.
- Down most: Charlotte Bishop, -$345.
- Down most: Sarah Pike, -$277.
- Down most: Wen Fujita, -$271.
- Up most: Claire Mason, +$3047.
- Up most: Ibrahim Appiah, +$2875.
- Up most: Holly Wright, +$2723.

**People.**

- 26 new acquaintances made, 340 names learned.
- Ibrahim Appiah on Sanjay Iyer: stage 2 to 1, feeling +1 to +1
- Ibrahim Appiah on Julia Burton: stage 2 to 1, feeling +1 to +1
- Will Ward on Joe Ward: stage 2 to 3, feeling +2 to +3
- Joe Ward on Will Ward: stage 2 to 3, feeling +2 to +3

**What people came to believe** (one each, first eight):

- Oliver Hughes: Julio Medina is willing to help with the shift swap.
- Sophie Hughes: Julia is still interested in helping with the internet issue.
- Harry Wood: Painkiller use is higher than usual in this area.
- Peter Stone: Rahul Iyer might be serious about getting the history homework done.
- Lakshmi Iyer: Jakub Sokolov is being more active than usual.
- Sanjay Iyer: Adam Young is trying to provoke me.
- Rahul Iyer: Peter Stone is also struggling with the history homework.
- Tomasz Lewandowski: Svetlana seems interested in me.

**Lives.**

- Nobody changed course.

## Injected

"Passed on in conversation" counts only lines from somebody who knew to somebody who had not seen it themselves: word of mouth to new people. People talking it over with others who already knew is not counted here.

**Day 1 06:00: service.register** (i55d3828dc5). Northline Internet [northline], home internet and the bills for it; by text or call or visit; open 08:00-20:00.

- Known to: everybody.

**Day 1 06:00: place.new** (ieac4e8a79e). Northline Internet shop has opened: a new phone shop, open 09:00-17:30.

- Saw it happen: Oliver Hughes, Julio Medina.
- Noticed it later: 6, first Sarah Bennett (Day 1 07:00), James Page (Day 1 07:00), Adaeze Ogunleye (Day 1 11:00), Martin Shaw (Day 1 12:00), Agata Kowalski (Day 1 12:30) and more.
- Knew of it by the end: 8.
- Passed on in conversation: no sign of it.

**Day 1 07:00: event.outage** (if7d3434aa3). The internet went off at home.

- Saw it happen: Mark Gibson, Ximena Aguilar, Hugo Aguilar, Sarah Bennett, Rachel Lloyd, Yuto Shin, John Reed, Aarti Sharma, Ellen Spencer, Rosa Molina, Jane Rhodes, Margaret Hughes, Omar Yousef, Megan Parker, Abena Eze.
- Ended: Day 2 10:00.
- Noticed it later: 28, first Laura Moore (Day 1 07:00), Rafael Aguilar (Day 1 07:00), Óscar Aguilar (Day 1 07:00), Dev Agarwal (Day 1 07:00), Geeta Agarwal (Day 1 07:00) and more.
- Touched directly: 43 (Mark Gibson, Keith Moore, Beth Moore, Laura Moore, Ximena Aguilar, Hugo Aguilar and more).
- Knew of it by the end: 43.
- Passed on in conversation: no sign of it.

**Day 1 09:00: event.letter** (12 of them, to 12 residents). A text from Northline Internet: "Your bill this month is $184.60. Thank you for being a Northline customer."

- Saw it happen: nobody.
- Noticed it later: 12, first Alejandra Medina (Day 1 09:00), Ruth Palmer (Day 1 09:00), Gary Moore (Day 1 09:00), Luis Vargas (Day 1 09:00), Neha Joshi (Day 1 09:00) and more.
- Touched directly: 12 (Oliver Hughes, Yaw Appiah, Neha Joshi, Alejandra Medina, Nancy Graham, Ian Shaw and more).
- Knew of it by the end: 12.
- Possibly heard of it in conversation, not having seen it: 1.
- Possibly passed on in conversation (1; a keyword proxy on bill, northline):
  - Day 2 09:00: Gary Moore to Owen Moore: "I, uh... I saw that text again this morning. About the bill. It's, it's not a mistake, I don't think. I've been meaning to call them but..."

**Day 2 08:00: event.outage** (ic41a61c3a6). At home: very slow internet.

- Saw it happen: Peter Stone, Rahul Iyer, Chinedu Appiah, Charlie Harper, Jakub Sokolov, Tom Burton, Chloe Burton, Amy Young, Kabir Sharma, Yuri Szabo, Tessa Wood, Ryan Wood, Fiona Wood, Agata Kowalski, Igor Kovac, Matt Webb, Eleanor Talbot, Carmen Sandoval, Simon Talbot, Tom Dawson, Daniela García, Nnamdi Achebe, Kwesi Achebe, Funmi Achebe.
- Ended: Day 3 18:00.
- Noticed it later: 23, first Valeria Vega (Day 2 08:30), Yolanda García (Day 2 08:30), Jane Parker (Day 2 09:00), Alice Marsh (Day 2 09:00), Lakshmi Iyer (Day 2 09:00) and more.
- Touched directly: 47 (Susan Stone, Peter Stone, Lakshmi Iyer, Sanjay Iyer, Rahul Iyer, Alice Marsh and more).
- Knew of it by the end: 47.
- Possibly heard of it in conversation, not having seen it: 1.
- Possibly passed on in conversation (1; a keyword proxy on slow, internet):
  - Day 3 09:00: Olivia Burton to Anna Markovic: "I'm just hoping the internet kicks in soon. It's been crawling all week."

**Day 3 18:00: event.outage** (ibe1fc60eee). The internet went off at home.

- Saw it happen: Laura Moore, Ximena Aguilar, Hugo Aguilar, Rafael Aguilar, Óscar Aguilar, Pilar Peña, Adriana Peña, Rose Grant, Simon Bishop, Sarah Bennett, Rachel Lloyd, Julio Medina, Verónica Domínguez, Filip Horvat, Arjun Agarwal, Dev Agarwal, Geeta Agarwal, Lena Petrov, Ellen Spencer, Charlotte Graham, Wendy Wood, Su-bin Yoon, Jane Rhodes, Chloe Rhodes, Adam Rhodes, Oliver Bishop, Charlotte Bishop, Margaret Hughes, Kate Hughes, Omar Yousef, Megan Parker, Chris Parker, Abena Eze.
- Ended: Day 4 08:00.
- Noticed it later: 10, first Mark Gibson (Day 3 18:00), Rosa Molina (Day 3 18:00), John Reed (Day 3 18:00), Charlie Rhodes (Day 3 18:00), Aarti Sharma (Day 3 18:30) and more.
- Touched directly: 43 (Mark Gibson, Keith Moore, Beth Moore, Laura Moore, Ximena Aguilar, Hugo Aguilar and more).
- Knew of it by the end: 43.
- Passed on in conversation: no sign of it.

**Contacts with `northline`**: 65 from 54 residents (1 by call, 64 by text), the first at Day 1 07:30.

- Answered: 41. Got nowhere: 24 (they were closed; a recording gave their hours, 08:00-20:00).
- What the agent did: dispatch 13, promise 31, resolve 8.
- Answered by: `NorthlineSupport` (kind rule-based baseline, no model).
- Came back more than once: 7.
- Promises kept / broken: 28 / 2.

## The service

**Northline Internet** (`northline`)

| | |
|---|---|
| Residents with a problem it handles | 100 |
| ...who had at least one decision while it was open | 65 |
| ...who tried to get in touch | 48 (48.0%) |
| ...who reached the service | 34 |
| ...who only ever got the recording | 14 |
| Hours from a problem starting to getting in touch about it, median / longest | 9.0 / 79.5 (over 54) |
| Contacts, answered / all | 41 / 65 |
| Got nowhere | they were closed 24 |
| By channel | call 1, text 64 |
| Contacts about a real problem at home | 55 |
| Contacts about a problem nobody at home had (the simulation inventing one) | 10 from 9 residents; the agent answered with promise 4 |
| Residents who got in touch twice or more | 7 |
| ...who chased something they had been promised | 2 |
| Homes that got in touch, and of those more than one person | 29, 9 |
| What the agent did | dispatch 13, promise 31, resolve 8 |
| Problems the service fixed, by day | Day 1: 4, Day 3: 26, Day 4: 1 |
| Problems that ended on the schedule (not the service's doing), by day | Day 2: 43, Day 3: 24, Day 4: 43 |
| Still broken at the end | 4 |
| Promises made / to people with no such problem | 31 / 4 |
| Promises kept / broken / not yet due at the end / broken and then chased | 28 / 2 / 1 / 0 |
| Talked of switching provider (keyword proxy) | 0 |

Got in touch about a problem nobody at home had: Pooja Joshi, Henry Hughes, Julio Medina, Pavel Nowak, Paula Fuentes, Raj Qureshi, Omar Yousef, Henry Murray.

## How well the model did its job

| | |
|---|---|
| Decisions valid first try | 96.0% |
| Retries / fell back to routine | 21 / 0 |
| Call latency, median / p90 | 3.91 s / 7.52 s |
| Server errors | 0 |
| Share of input read from the prompt cache | 0.666 |
| Replies that echo the line before | 0.9% |
| Lines with the speaker's own name | 1.8% |
| Questions left unanswered | 4 of 104 |
| Lines repeating what the speaker already said today | 1.5% |
| Deals asserted / landed | 22 / 20 |
| Things said about somebody that they never said | 1 of the 1 such claims |
| Names used without having been given | 0 |
| Ids said out loud | 0 |

## Realism flags

Mechanical checks over the logs. A flag is a reason to look, not a verdict.

| Flag | Count | What it means |
|---|---|---|
| `repeated_line` | 5 | somebody said the same line, word for word, more than once |
| `echo` | 2 | a reply that repeats most of the line it answers |
| `stuck` | 4 | the same decision 4 times running |
| `impossible_move` | 0 | somebody arrived in a home that is neither theirs nor anybody's they know |
| `sleepless` | 0 | active through a stretch of 24 hours with no sleep in it |
| `no_reaction` | 2 | saw something of importance 7+ and had no thought for 4 ticks |
| `ghost_contact` | 0 | a text between two people with no tie at all |
| `money_from_nowhere` | 0 | somebody's money changed by more than the run's money events explain |
| `promise_ignored` | 0 | a broken promise the person let down never did anything about |
| `provider_down_window` | 0 | a stretch of ticks where the model did not answer |
| `id_spoken` | 0 | somebody said a resident id out loud |
| `name_unknown` | 0 | somebody used the name of a person whose name they had not been given |
| `claim_unfounded` | 5 | somebody spoke of money owed between them and a person with no debt, loan, rent or wage between them |
| `contact_ungrounded` | 10 | a resident got in touch with a service about a problem nobody in their home had |

**`repeated_line`**, first 5 of 5:

- Day 2 14:30: Anna Markovic said "i got paid today not much but it's a start" 3 times
- Day 2 10:30: Harry Wood said "no trend i know of just the usual i reckon" 2 times
- Day 3 14:00: Chloe Burton said "not yet let me check my bag" 2 times
- Day 5 05:30: Julia Graham said "sophie about that thing you mentioned earlier about the internet" 2 times
- Day 5 05:30: Sophie Hughes said "i got it sorted first thing near enough" 2 times

**`echo`**, first 2 of 2:

- Day 2 11:30: Will Ward echoed Joe Ward: "Let me get this straight. You had the chicken and rice, and that's the one with the green beans, not the broccoli?"
- Day 4 04:30: Anna Markovic echoed Yaw Appiah: "Aye, Yaw Appiah. And you're Anna, I'd guess."

**`stuck`**, first 4 of 4:

- Day 4 13:00: Jakub Sokolov chose talk Lakshmi Iyer 4 times running
- Day 4 22:30: Héctor Gutiérrez chose sleep 4 times running
- Day 5 00:30: Sarah Pike chose talk Farah Nair 4 times running
- Day 4 06:00: Anna Markovic chose talk Yaw Appiah 4 times running

**`no_reaction`**, first 2 of 2:

- Day 2 09:00: Claire Mason saw Farah Nair's rent missed and did not react
- Day 3 09:00: Ben Carter saw Gabriela Rojas's rent missed and did not react

**`claim_unfounded`**, first 5 of 5:

- Day 2 19:30: Karol Volkov spoke of money owed with Bogdan Volkov, and nothing stands between them: "I owe Steve forty dollars and I want to clear it before Tuesday."
- Day 4 05:30: Zoe Burton spoke of money owed with Julia Burton, and nothing stands between them: "Love, I’ve been meaning to say I’ll pay you back before Monday. Properly, this time."
- Day 4 11:00: Marta Estrada spoke of money owed with Kwame Osei, and nothing stands between them: "You owe an answer. That’s what you said. What’s it to be?"
- Day 4 18:00: Stefan Lewandowski spoke of money owed with Tomasz Lewandowski, and nothing stands between them: "I saw these at the grocery and thought of you. They’re a bit of a stretch, but I owe you better than that last week."
- Day 4 18:30: Holly Spencer spoke of money owed with Harry Wood, and nothing stands between them: "It's Claudia. I need to pay her back what I owe her before Friday, and I'd rather not be cornered by her to do it."

**`contact_ungrounded`**, first 5 of 10:

- Day 2 13:00: Pavel Nowak got in touch with northline with no such problem at home: "I need to ask about the internet issue."
- Day 2 13:30: Pooja Joshi got in touch with northline with no such problem at home: "I'm Pooja Joshi from Birch Crescent. I need to speak about my internet connection."
- Day 2 14:30: Henry Murray got in touch with northline with no such problem at home: "I'm Henry Murray. I'm having issues with my internet and I need the forms sent off by Tuesday."
- Day 2 19:30: Julio Medina got in touch with northline with no such problem at home: "I need to speak to someone about my internet. It went out yesterday morning and came back this afternoon. I want to know why."
- Day 3 10:00: Omar Yousef got in touch with northline with no such problem at home: "I'm Omar Yousef from 31 Victoria Place. You said the internet would be back by tomorrow. Is it fixed yet?"

## Appendix

### Every conversation

**Day 1 11:00**, Jakub Sokolov and Lakshmi Iyer at Spring Pharmacy:

> Jakub Sokolov: Well, this is a strange sight. Everyone’s grabbing painkillers like it’s the end of the world. Honestly though, what's up with that?  
> Lakshmi Iyer: Well, one never knows what the next day might bring, don’t you think?  

**Day 1 12:00**, Rosa Molina and Kwame Osei at Riverside Medical Practice:

> Rosa Molina: Kwame, I need to ask you something. What did you mean on Tuesday?  
> Kwame Osei: Tuesday? I... wasn’t sure what else to say.  
> Rosa Molina: Well, if you were trying to say something, now's the time.  
> Kwame Osei: Look, I’ve done my shift. I’ll see what else I can do later.  

**Day 1 13:00**, Ama Abiola and Emeka Abiola at 15 Birch Crescent:

> Ama Abiola: So, you're home for lunch, I take it. No rush, of course.  
> Emeka Abiola: Aye, just thought I'd make us something before the kids get back.  
> Ama Abiola: How was the meeting with the builder?  
> Emeka Abiola: Meeting? That was yesterday. I think you're mixing up your days.  

**Day 1 13:30**, Owen Mason and Magda Lewandowski at St. Anne's School:

> Owen Mason: Hey, Magda, you got the homework for history yet?  
> Magda Lewandowski: Not yet. Haven't had a chance to look at it properly.  
> Owen Mason: Chin up, we’ll get it sorted later.  

**Day 1 14:00**, Magda Lewandowski and Óscar Aguilar at St. Anne's School:

> Magda Lewandowski: So, what did you think of that history homework? I haven’t even looked at it yet.  
> Óscar Aguilar: Same as usual. That teacher is still breathing down my neck.  
> Magda Lewandowski: Well, there you go. Maybe we can tackle it after class?  
> Óscar Aguilar: After class, yeah. But not to that teacher — I’ll hide in the community center.  

**Day 1 14:30**, Óscar Aguilar and Magda Lewandowski at St. Anne's School:

> Óscar Aguilar: Do you think the teacher will look for us at the community center?  
> Magda Lewandowski: Maybe. She’s not exactly got eyes everywhere, has she?  
> Óscar Aguilar: We’ll be safe there. They’ll be grading tests or whatever.  
> Magda Lewandowski: Right then. Let’s grab something before we head out.  

**Day 1 15:00**, Fiona Wood and Igor Kovac at St. Anne's School:

> Fiona Wood: Mr. Kovac mentioned something about the history homework and the community centre. Have you heard anything about that?  
> Igor Kovac: Nah, I haven’t heard much. Mr. Kovac just said we had to do it, you know?  
> Fiona Wood: Fair enough. I'll have to ask Magda then.  

**Day 1 15:30**, Peter Stone and Rahul Iyer at St. Anne's School:

> Peter Stone: Hey, Rahul. You got the history homework done yet?  
> Rahul Iyer: Honestly, I haven’t started it yet. How about you?  
> Peter Stone: Well... I was hoping to figure it out before the weekend.  
> Rahul Iyer: Maybe we could team up and go over it later? I’ve got a bit of time before I need to head out.  

**Day 1 16:00**, Esperanza Jiménez and Aisha Thakur at 21 Clover Street:

> Esperanza Jiménez: Aisha, the bins on Clover Street — they're still not collected. I've had enough of it.  
> Aisha Thakur: I'll give them a call right away. No need to put up with it a moment longer.  
> Esperanza Jiménez: Let me know if it's sorted by tomorrow. I've got a few more letters to write.  
> *promise by Esperanza Jiménez: landed*  

**Day 1 17:00**, Anna Markovic and Andrei Markovic at Clover Court:

> Anna Markovic: I got paid today. Not much, but it's a start.  
> Andrei Markovic: Not my business, but that fence of the Graham's is still a disgrace. Still, I suppose it's not urgent.  
> Anna Markovic: I'll make do, same as ever.  

**Day 1 19:30**, Rana Jaber and Mahmoud Jaber at 11 Clover Street:

> Rana Jaber: You know, I've been meaning to ask you—what did you think of the dinner last night? I know it wasn't much, but I tried.  
> Mahmoud Jaber: I've had a long day. What's on your mind, Rana?  
> Rana Jaber: I think I'm going to need you to listen for a second, Mahmoud.  
> Mahmoud Jaber: I'm listening. What is it you need to say?  

**Day 1 20:00**, Luke Bishop and Molly Bishop at 31 Oak Lane:

> Luke Bishop: Molly, I need to talk to you about something. It's been on my mind all day.  
> Molly Bishop: All right, I'm listening. What's on your mind?  
> Luke Bishop: It's about the money, Molly. I've been taking a few extra jobs on the side.  
> Molly Bishop: That's fine, but what's that got to do with me?  

**Day 1 20:30**, Molly Bishop and Luke Bishop at 31 Oak Lane:

> Molly Bishop: It's about the money, Molly. I've been taking a few extra jobs on the side.  
> Luke Bishop: It means I’m trying to get us a bit of a cushion. I’ll explain more if you want.  
> Molly Bishop: I'll need to know more than that. What does it mean for us?  
> Luke Bishop: It means I need to save 150 a month, no more holes. That’s it.  

**Day 1 21:00**, Dmitri Nowak and Abiodun Obi at Spring Mansions:

> Dmitri Nowak: How'd your dinner go tonight?  
> Abiodun Obi: Same as ever. I didn’t get out much.  

**Day 1 21:30**, Claire Mason and Emily Mason at 13 Orchard Lane:

> Claire Mason: There's something I need to buy for you.  
> Emily Mason: That's generous of you, Claire. What is it?  
> Claire Mason: I'll pick it out tomorrow. No rush.  
> Emily Mason: That's thoughtful of you, Claire. I'll look forward to it.  
> *promise by Claire Mason: landed*  

**Day 2 09:00**, Gary Moore and Owen Moore at 21 Orchard Lane:

> Gary Moore: I, uh... I saw that text again this morning. About the bill. It's, it's not a mistake, I don't think. I've been meaning to call them but...  
> Owen Moore: You mean the one from last week? It's not like I'm not aware of it.  
> Gary Moore: I don't know what to say to them. It's just... different, that's all.  
> Owen Moore: I'll give it another week. But after that, Gary, you're on your own with them.  
> *promise by Owen Moore: landed*  

**Day 2 10:00**, Laura Moore and Chidi Traoré at St. Anne's School:

> Laura Moore: Hey, Chidi. You got the history homework done yet?  
> Chidi Traoré: Not yet. You?  
> Laura Moore: Not quite. Honestly though, I keep putting it off.  
> Chidi Traoré: We’ll get it done by Friday, don’t start.  

**Day 2 10:30**, Filip Horvat and Harry Wood at Spring Pharmacy:

> Filip Horvat: Afternoon. I couldn't help but notice the number of people coming in for painkillers. Is there a trend I'm missing?  
> Harry Wood: No trend I know of. Just the usual, I reckon.  
> Filip Horvat: Well, I suppose it's none of my business, then. Tell me about it if you'd like.  
> Harry Wood: No trend I know of. Just the usual, I reckon.  

**Day 2 11:00**, Karen Hughes and Alina Orlov at St. Anne's School:

> Karen Hughes: Alina, have you started the history homework yet? I need to get a move on but I'm not sure where to begin.  
> Alina Orlov: Early days. I've barely looked at it.  
> Karen Hughes: Honestly though, I'm not looking forward to it at all.  
> Alina Orlov: Ask me tomorrow. I’ll have had more time to look at it.  
> *promise by Alina Orlov: landed*  

**Day 2 11:30**, Will Ward and Joe Ward at Fresh Fare:

> Will Ward: You had your dinner here last night. What did you have, if I may ask?  
> Joe Ward: I had the chicken and rice, if you must know. You remember what that looks like.  
> Will Ward: Let me get this straight. You had the chicken and rice, and that's the one with the green beans, not the broccoli?  
> Joe Ward: Green beans, yeah. Broccoli's a different can. One thing at a time, love.  

**Day 2 13:30**, Sarah Bennett and Julio Medina at The Half Moon:

> Sarah Bennett: Julio, real quick — Martin's been in and out again. You sure he's not getting under your feet?  
> Julio Medina: He's doing the job, ain't he? Let him do it.  

**Day 2 14:00**, Yetunde Appiah and Chloe Rhodes at St. Anne's School:

> Yetunde Appiah: Hey, do you have the history homework done yet?  
> Chloe Rhodes: Not really, to be honest. It's a bit of a mess.  
> Yetunde Appiah: Go on then, what's the mess?  
> Chloe Rhodes: Just the usual, you know? Mr. Kovac's questions are impossible.  

**Day 2 14:30**, Anna Markovic and Andrei Markovic at Clover Court:

> Anna Markovic: I got paid today. Not much, but it's a start.  
> Andrei Markovic: Not my business, but I noticed Jennifer Graham coming and going a few times. Still not fixed, that fence of hers.  
> Anna Markovic: She’s not your business either.  

**Day 2 15:00**, Amy Young and Rafael Aguilar at St. Anne's School:

> Amy Young: Rafael, I was wondering if we could meet at the park after school today? I've been looking forward to it.  
> Rafael Aguilar: Yeah, I guess. What're we doing there anyway?  
> Amy Young: I thought we might just walk around, maybe get some ice cream if we're there long enough.  
> Rafael Aguilar: Alright, see you then. Better bring some cash if we're getting ice cream.  
> *accept by Rafael Aguilar: landed*  
> *invite by Rafael Aguilar: did not land (there is no willow_green to meet at)*  

**Day 2 16:00**, Farah Nair and Will Barker at Hartwell Community Centre:

> Farah Nair: That was a large sum of money you spent on groceries earlier. I imagine you've been busy.  
> Will Barker: You could say that. I was getting things in for the week.  
> Farah Nair: Fair enough. I've been trying to keep up with things myself.  
> Will Barker: That's the idea, anyway. I'll see you around.  

**Day 2 16:30**, Simon Talbot and George Fletcher at Spring Pharmacy:

> Simon Talbot: George, I was wondering if there's a chance you'd consider giving me a few more hours this week?  
> George Fletcher: More hours? I can't see why not, but it's the same as ever - you cover for me when I need the loo, I'll give you the time.  
> *hire by George Fletcher: did not land (I have no work going called 'pharmacist')*  

**Day 2 17:00**, Sarah Pike and Farah Nair at Clover Court:

> Sarah Pike: You’ve been coming in and out a lot today. Everything all right with your bins?  
> Farah Nair: We'll see.  

**Day 2 18:00**, Jennifer Graham and Julia Graham at Clover Court:

> Jennifer Graham: Julia, have you seen Claire around here today? I need to pay the rent.  
> Julia Graham: Not seen her. Grey hair, broad, you said?  
> Jennifer Graham: I couldn't tell you.  

**Day 2 18:30**, Margaret Hughes and Kate Hughes at Victoria Court:

> Margaret Hughes: Kate, could we have a word when you're settled? There's something I need to say.  
> Kate Hughes: Yes, of course. What is it?  
> Margaret Hughes: It's the money, Kate. I'm behind on the credit card, and I don't know how to tell the children.  

**Day 2 19:30**, Karol Volkov and Bogdan Volkov at 9 Oak Lane:

> Karol Volkov: Bogdan, I'm sorry, but I need to talk to you about something. Do you have a minute?  
> Bogdan Volkov: Right then. What is it?  
> Karol Volkov: I owe Steve forty dollars and I want to clear it before Tuesday.  
> *promise by Karol Volkov: landed*  

**Day 2 20:00**, Chris Parker and Megan Parker at 21 Victoria Place:

> Chris Parker: Internet came back.  
> Megan Parker: There we are. Glad it's sorted.  

**Day 2 22:30**, Elena Espinoza and Sarah Pike at Clover Court:

> Elena Espinoza: I suppose you've seen Claire today? Got to get that rent in.  
> Sarah Pike: Not yet. I sent her a text. She's got the rent, that's for sure.  
> Elena Espinoza: Hope she gets back to you soon, then.  

**Day 2 23:30**, Beth Moore and Keith Moore at Victoria Court:

> Beth Moore: You're still here, then.  
> Keith Moore: Aye, just coming in. Internet came back on after lunch.  
> Beth Moore: Not bad, then. Paid the rent already?  
> Keith Moore: Still got that eighty to borrow, but we'll see.  

**Day 3 09:00**, Anna Markovic and Olivia Burton at The Rolling Pin:

> Anna Markovic: I heard from Lakshmi the other day... that's that, then.  
> Olivia Burton: I'm just hoping the internet kicks in soon. It's been crawling all week.  
> Anna Markovic: Internet can wait. What about the orders piling up?  
> Olivia Burton: Orders first, then the internet. I'll get on it.  
> Anna Markovic: I'm not the one running this place, you know. I just bake.  

**Day 3 10:00**, Alejandra Medina and Svetlana Nowak at Hartwell Post Office:

> Alejandra Medina: That sandwich you brought... it was a ham and cheese, wasn't it? I've seen you eat one every morning since you started.  
> Svetlana Nowak: You have a good memory, Mrs. Medina.  
> Alejandra Medina: I was just trying to pass the time. You get lonely in this place, what with the post office being a slow business.  
> Svetlana Nowak: I'd be interested in more hours if it's possible, Mrs. Medina.  

**Day 3 10:30**, Colin Moore and Funmi Achebe at St. Anne's School:

> Colin Moore: You got the tryouts on Thursday, right? I saw the notice up.  
> Funmi Achebe: Nah, I haven’t seen it. Why?  
> Colin Moore: I thought you were in the team last year. Maybe I read the wrong notice.  
> Funmi Achebe: Don’t know, not really keeping up with the team stuff.  

**Day 3 11:00**, James Page and Julio Medina at The Half Moon:

> James Page: Julio, real quick — Martin's been in and out again. You think he's coming back for his shift today?  
> Julio Medina: Honesty? I couldn’t tell you. He’s been all over the shop. You know him best.  
> James Page: Well, if it's not you, it's not me, I suppose. Keep your hair on, Julio.  

**Day 3 11:30**, Isabel García and Pablo García at 17 Orchard Lane:

> Isabel García: You're off again, aren't you? Be careful with that head of yours.  
> Pablo García: I had a bit of a headache, that's all. I'm fine now.  
> Isabel García: Well, there you go, then. Let me know if you need the kettle on again.  

**Day 3 12:00**, Jane Parker and Rob Moore at Spring Court:

> Jane Parker: Honestly though, I was trying to think of what to say when we crossed eyes earlier - and now it's just polite to say 'good morning' again.  
> Rob Moore: Morning. Engineer's coming at ten to look at the internet. That'll be something.  
> Jane Parker: Good thing I sorted the kids out for lunch, then. They’d have been upset if I’d kept them waiting.  
> Rob Moore: Right you are. I'll be at work if they need me.  

**Day 3 12:30**, Kwame Osei and Rosa Molina at Riverside Medical Practice:

> Kwame Osei: I think I owe you an answer, Rosa. I wasn’t sure what else to say on Tuesday, but it’s... it’s something I need to sort out.  
> Rosa Molina: Well, I'm here now. What's it going to take for you to sort it?  
> Kwame Osei: It’s the Thursday appointments, Rosa. I’ve been... late.  
> Rosa Molina: Thursday's appointments. Right. Well, I hope you sort it before they sort you.  

**Day 3 13:00**, Jakub Sokolov and Lakshmi Iyer at Spring Mansions:

> Jakub Sokolov: You know, I was just thinking about our little chat the other day. Honestly though, I feel like we barely scratched the surface.  
> Lakshmi Iyer: Ah, yes. One can scarcely scratch the surface with such a brief encounter.  
> Jakub Sokolov: You’ve got a certain way of speaking, like a puzzle wrapped in a riddle.  
> Lakshmi Iyer: You’ll find I’m a puzzle with only so many pieces, Mr. Sokolov.  

**Day 3 13:30**, Matt Webb and Lakshmi Iyer at Spring Mansions:

> Matt Webb: Bit of a saga with the internet there, eh? Slow one day, then a bloke turns up and it's all sorted. Makes you wonder what they do when nobody calls them.  
> Lakshmi Iyer: Oh, well, I suppose it's all sorted now, isn't it?  

**Day 3 14:00**, Tom Burton and Chloe Burton at St. Anne's School:

> Tom Burton: Chloe, have you got that form filled out yet?  
> Chloe Burton: Not yet. Let me check my bag.  
> Tom Burton: It's that girl with the terrier, right? The one who sits by the windowsill at lunch.  
> Chloe Burton: Not yet. Let me check my bag.  

**Day 3 14:30**, Riya Nair and Agata Kowalski at St. Anne's School:

> Riya Nair: You leaving soon?  
> Agata Kowalski: Still on the clock, so I'll be here 'til five. Tell me about it, what's on your mind?  
> Riya Nair: Nah, it can wait.  
> Agata Kowalski: Fair enough. Stop by before five, then.  

**Day 3 15:00**, Anna Markovic and Andrei Markovic at Clover Court:

> Anna Markovic: I got paid today. Not much, but it's a start.  
> Andrei Markovic: That's better than nothing. How's Anna holding up?  
> Anna Markovic: Tired, but it keeps. Same as ever.  

**Day 3 15:30**, Kate Hughes and Su-bin Yoon at Victoria Court:

> Kate Hughes: You’ll be going to the school, then? I saw your kid at the school gates this morning.  
> Su-bin Yoon: I do. Not sure how I’d live without it, really.  
> Kate Hughes: Small mercies, eh?  

**Day 3 16:30**, Anna Markovic and Jennifer Graham at Clover Court:

> Anna Markovic: Jennifer, have you seen Claire Mason today? I need to...  
> Jennifer Graham: I've been looking for her too. Seen her round the school most mornings, but not today.  
> Anna Markovic: She’ll turn up. Always does.  

**Day 3 17:00**, Simon Bishop and Rose Grant at Victoria Court:

> Simon Bishop: Mind if I ask what you're looking at, Rose?  
> Rose Grant: Not really looking at anything in particular. Just thinking.  
> Simon Bishop: Aye, well, I’ve got a book to finish. Or a cup of tea, same thing.  

**Day 3 17:30**, Adriana Peña and Pilar Peña at 9 Victoria Place:

> Adriana Peña: You know, I've been thinking about that Andrés thing. It's been years, but honestly, you'd be surprised how much it's on my mind still.  
> Pilar Peña: Not surprised. He was quiet enough.  
> Adriana Peña: Quiet, but that's Andrés, right? Seems like he knows how to keep it close.  
> Pilar Peña: Enough of that. Got work to do.  

**Day 3 18:00**, Mercedes Fuentes and Aarti Sharma at The Rusty Anchor:

> Mercedes Fuentes: Aarti. You're back again.  
> Aarti Sharma: Bit early for a drink, but I'm here all the same.  
> Mercedes Fuentes: Early's early. What'll it be?  
> Aarti Sharma: Just a soft drink for me, thanks. Early starts and all.  

**Day 3 18:30**, Will Ward and Joe Ward at 17 Clover Street:

> Will Ward: You've been here all day. That's the thing about being at home, I guess.  
> Joe Ward: Not much. Just a couple of sandwiches and a pear. You know how it goes.  
> Will Ward: Let's just say I've been making the most of it.  

**Day 3 19:00**, Holly Wright and Peter Wright at 5 Oak Lane:

> Holly Wright: You missed the old friend I was meeting for coffee.  
> Peter Wright: Coffee. Right. I was on a site near the station.  
> Holly Wright: Next time, give me a shout. I can wait.  

**Day 3 19:30**, Holly Spencer and Harry Wood at 27 Orchard Lane:

> Holly Spencer: I need to tell you something about Claudia.  
> Harry Wood: Go on then, I'm listening.  
> Holly Spencer: She asked me to cover for her with the bar tab last week. I said I would. I still need to.  
> Harry Wood: Right, well. I've got things to do before the day's out.  

**Day 3 20:00**, Jennifer Graham and Julia Graham at Clover Court:

> Jennifer Graham: Hang on a minute, Julia—d'you see where Claire's been today?  
> Julia Graham: Not today—did you catch her at the hardware store?  
> Jennifer Graham: Nope, just thought maybe you’d bumped into her at the school.  
> Julia Graham: I haven’t had time to pop by the school, to be honest.  

**Day 3 20:30**, Víctor Díaz and Ian Shaw at Orchard Mansions:

> Víctor Díaz: I saw your brother at the diner yesterday, still no sign of common courtesy.  
> Ian Shaw: Martin's got his ways, I suppose. I've got enough on my plate.  

**Day 3 22:00**, Alice Page and James Page at Orchard Mansions:

> Alice Page: Love, can we talk? Just for a minute.  
> James Page: Course, love. What's on your mind?  
> Alice Page: It's just... I feel like I'm still on the outside here, you know? I've been trying to get back in touch with Sunita.  
> James Page: Can't help much with that, love. Don't know her name, don't know where she's gone.  

**Day 3 23:00**, Dev Agarwal and Geeta Agarwal at 17 Victoria Place:

> Dev Agarwal: Hang on a minute, Geeta... I need to get on to Northline 'bout the internet. It's been off for hours.  
> Geeta Agarwal: Yeah... I've been meaning to call them too.  
> Dev Agarwal: Do you think they'll sort it before school tomorrow?  
> Geeta Agarwal: One thing at a time, Dev. I'm sure they'll get to it.  

**Day 3 23:30**, Beth Moore and Keith Moore at Victoria Court:

> Beth Moore: Still here, then.  
> Keith Moore: Still here, for now.  

**Day 4 00:00**, Sunita Agarwal and Arjun Agarwal at 17 Victoria Place:

> Sunita Agarwal: Arjun, I need to talk to you about something. It's about the internet.  
> Arjun Agarwal: Go on then.  
> Sunita Agarwal: It's been off for hours now. I asked the neighbours, but it's not just us.  
> Arjun Agarwal: I'll phone them tomorrow. First thing.  
> *promise by Arjun Agarwal: landed*  

**Day 4 04:30**, Anna Markovic and Yaw Appiah at Clover Court:

> Anna Markovic: Yaw... that's you, isn't it?  
> Yaw Appiah: That's right. Yaw Appiah. You're one of the Markovics, aren't you?  
> Anna Markovic: You're a regular here, aren't you?  
> Yaw Appiah: Aye, Yaw Appiah. And you're Anna, I'd guess.  
> Anna Markovic: Aye, Yaw Appiah. And you're Anna, I'd guess.  

**Day 4 05:00**, Mahmoud Jaber and Rana Jaber at 11 Clover Street:

> Mahmoud Jaber: You awake? We need to talk about what you said on Wednesday.  
> Rana Jaber: I'll make a pot of coffee while we do. It's a long day ahead.  
> Mahmoud Jaber: Before you make coffee, I need to know—were you serious about leaving the station?  
> Rana Jaber: I was serious. I just didn’t expect you to bring it up first.  

**Day 4 05:30**, Zoe Burton and Julia Burton at 33 Spring Terrace:

> Zoe Burton: Love, I’ve been meaning to say I’ll pay you back before Monday. Properly, this time.  
> Julia Burton: You’ll have to do better than that.  
> Zoe Burton: How about Thursday then? I’ll have it sorted.  
> Julia Burton: Thursday better be a good one for you.  
> *promise by Zoe Burton: landed*  
> *promise by Julia Burton: landed*  
> *promise by Zoe Burton: landed*  
> *promise by Zoe Burton: landed*  
> *promise by Julia Burton: landed*  
> *promise by Julia Burton: landed*  

**Day 4 06:30**, Edward Murray and Henry Murray at 11 Birch Crescent:

> Edward Murray: Henry... you still mad about last week?  
> Henry Murray: Last week? No. Just tired of waiting for your side of the deal.  
> Edward Murray: I don't know what you're talking about. He's not mine to talk about.  
> Henry Murray: Don't pretend you don't know who I'm talking about.  

**Day 4 07:00**, Lukas Orlov and Alina Orlov at 23 Orchard Lane:

> Lukas Orlov: You're up early. I assume it's because you have to be.  
> Alina Orlov: Just wanted to get a head start on the day, is all.  
> Lukas Orlov: Breakfast on the table at seven thirty. No arguments.  
> Alina Orlov: Will there be more coffee, or is this it?  

**Day 4 07:30**, Funmi Achebe and Nnamdi Achebe at 13 Spring Terrace:

> Funmi Achebe: Dad, I need to borrow something.  
> Nnamdi Achebe: What do you need, love?  
> Funmi Achebe: I need $120. For something important.  
> Nnamdi Achebe: I can give you $100, but that's all I've got free right now.  
> *loan by Nnamdi Achebe: landed*  
> *promise by Nnamdi Achebe: landed*  

**Day 4 08:00**, Joe Ward and Sanjay Iyer at Fresh Fare:

> Joe Ward: Sanjay, you got a minute? Need to ask you something.  
> Sanjay Iyer: Depends what it is. Ask quickly, I’ve got a queue.  
> Joe Ward: I couldn't tell you.  

**Day 4 08:30**, Adam Young and Sanjay Iyer at Fresh Fare:

> Adam Young: Adam Young. I hear you've been having trouble with the internet. I can tell you what it was, if you want.  
> Sanjay Iyer: That was my business, not yours.  

**Day 4 09:00**, Alice Marsh and Chinedu Appiah at 27 Spring Terrace:

> Alice Marsh: You know, the other day I noticed the internet was acting up again. It's what you pay them for, isn't it? Might be worth a call.  
> Chinedu Appiah: Well, it's back now, so I gave it a few hours before I worried about it.  

**Day 4 09:30**, Alice Page and Edward Shaw at Orchard Mansions:

> Alice Page: Edward, do you by any chance know where Sunita might have gone?  
> Edward Shaw: Nope, haven't seen either of them. Tell me about it, though.  
> Alice Page: Fair enough, love. I just keep thinking there’s someone or somewhere I should’ve checked by now.  
> Edward Shaw: Right you are. Small mercies there's just one of you looking for folk.  

**Day 4 10:00**, Kate Hughes and Rose Grant at Victoria Court:

> Kate Hughes: Rose. We need to talk. It's about what's been... hanging between us.  
> Rose Grant: I suppose we all have things we'd rather not hang on to.  
> Kate Hughes: I don’t want it to. That’s why I’m here.  

**Day 4 10:30**, Isabel García and Wen Fujita at Spring Pharmacy:

> Isabel García: Wen. You don't look yourself.  
> Wen Fujita: Aching head, Isabel. Nothing to worry about.  
> Isabel García: Aching heads are nothing to ignore. You'll be sure to rest.  

**Day 4 11:00**, Marta Estrada and Kwame Osei at Riverside Medical Practice:

> Marta Estrada: You owe an answer. That’s what you said. What’s it to be?  
> Kwame Osei: It’s not that simple, Marta. I’m working on it.  
> Marta Estrada: You've had three days. That's the simple part.  
> Kwame Osei: I'll have something for you by Friday. That's all I can say for now.  
> *promise by Kwame Osei: landed*  

**Day 4 11:30**, Camila Fuentes and Joe Ward at Fresh Fare:

> Camila Fuentes: Joe, I was hoping I'd catch you. I need to sort out that paperwork.  
> Joe Ward: Paperwork? I've got the coffee if you want it, but I'm not sure about the rest.  
> Camila Fuentes: It's about my council tax. I heard you've been helping others sort it.  
> Joe Ward: Camila, I haven't touched paperwork since I started here. You might want to give Raj a call.  

**Day 4 12:00**, Jakub Sokolov and Lakshmi Iyer at Spring Mansions:

> Jakub Sokolov: You know, I've been thinking about what you said the other day - the puzzle with only so many pieces. Not today, but maybe I'll try to find a few more. Honestly though, it's a charming way to speak.  
> Lakshmi Iyer: Oh, well there you go, then — a puzzle it is, and all the better for it.  
> Jakub Sokolov: Puzzles or not, I'm not getting any younger — but I'll give it a try if I find a spare hour.  
> Lakshmi Iyer: Well, puzzles take time — and so do most things worth doing, wouldn’t you agree?  

**Day 4 12:30**, Alejandra Medina and Tomasz Lewandowski at Hartwell Post Office:

> Alejandra Medina: Tomasz, I noticed you left and came back again this morning. Everything all right?  
> Tomasz Lewandowski: Everything's fine. Just... errands.  
> Alejandra Medina: Fair enough. Just keep me posted, yes?  

**Day 4 13:00**, Jakub Sokolov and Lakshmi Iyer at Spring Mansions:

> Jakub Sokolov: You know, I've got this idea - why don't we try to find a few more of those pieces together sometime? You and me both, right?  
> Lakshmi Iyer: Oh, well there you go — if you think it's a good idea, I'll come along.  
> *accept by Lakshmi Iyer: landed*  

**Day 4 13:30**, Adam Young and Jennifer Graham at Fresh Fare:

> Adam Young: Jennifer, I was just wondering if you saw the news about the car test. I need to get it done soon.  
> Jennifer Graham: Car test? You mean the emissions? I didn't see it in the paper.  
> Adam Young: It's the annual safety check. I need to book it in, but I haven’t got a free minute.  
> Jennifer Graham: I’ve got me own head full enough, truth be told. You’ll sort it, I’m sure.  

**Day 4 14:00**, Chloe Burton and Óscar Aguilar at St. Anne's School:

> Chloe Burton: Let's not pretend the math homework's not the worst. You done it yet?  
> Óscar Aguilar: Nah. Who'd be crazy enough to do that? You?  
> Chloe Burton: Not a chance. Let me know if you find the answers, though.  
> Óscar Aguilar: You ever think we should just draw a line through it all and call it art?  

**Day 4 14:30**, Sunita Agarwal and Ben Carter at Crossroads Service Station:

> Sunita Agarwal: So what did you mean on Wednesday then?  
> Ben Carter: Ask me tomorrow, love. Got the coffee machine to keep happy today.  

**Day 4 15:00**, Alice Page and Simon Talbot at Spring Pharmacy:

> Alice Page: Lovely day for it, isn't it? That ink looks like it's been through a war.  
> Simon Talbot: Aye, that it is. You here for the usual?  
> Alice Page: Nah, just picking up some supplies. You got the usual, love?  
> Simon Talbot: I'll ring Northline for you, if you like. They're the ones to sort it.  

**Day 4 15:30**, Sarah Bennett and Julio Medina at Victoria Court:

> Sarah Bennett: Julio, real quick—did you hear about the internet coming back on? I was just told it’s working again at home.  
> Julio Medina: Honestly, I was just thinking about that myself. Seems like they fixed it quick.  
> Sarah Bennett: Well, that’s one thing I don’t have to worry about anymore.  

**Day 4 16:00**, Jakub Sokolov and Jia Shin at Hartwell Community Centre:

> Jakub Sokolov: Well, if it isn't Jia Shin. Honestly though, I didn't expect to see you here — and not just because of the timing.  
> Jia Shin: I like to stretch my legs on a Thursday, love. Yourself?  
> Jakub Sokolov: Stretch my legs? Maybe I like the company better.  
> Jia Shin: Well, I've a pot of tea to pour, love. Pleased to chat, but not a chat that'll last.  

**Day 4 16:30**, Julia Graham and Sophie Hughes at Clover Court:

> Julia Graham: Sophie, about that thing you mentioned earlier—about the internet?  
> Sophie Hughes: I got it sorted first thing. Near enough.  

**Day 4 17:00**, Oliver Bishop and Charlotte Bishop at 19 Victoria Place:

> Oliver Bishop: That walk in the park, it did me good. Still, you know me, I’d rather be pacing the house like a caged animal if I wasn’t out of it.  
> Charlotte Bishop: I had a thought about that walk, but it can wait.  

**Day 4 17:30**, Paul Shaw and Colin Abbott at Orchard Mansions:

> Paul Shaw: I received the payment from today's shift, so I should be fine for now.  
> Colin Abbott: Right, well, that's one worry less for now. Fingers crossed for you.  

**Day 4 18:00**, Stefan Lewandowski and Tomasz Lewandowski at Clover Court:

> Stefan Lewandowski: I saw these at the grocery and thought of you. They’re a bit of a stretch, but I owe you better than that last week.  
> Tomasz Lewandowski: You're too kind. But I've got a list for the car test. Ivan's waiting.  
> Stefan Lewandowski: Keep an eye on the list, then. I’ll swing by with the groceries later.  
> Tomasz Lewandowski: I'll keep it safe. See you with the groceries.  

**Day 4 18:30**, Holly Spencer and Harry Wood at 27 Orchard Lane:

> Holly Spencer: It's Claudia. I need to pay her back what I owe her before Friday, and I'd rather not be cornered by her to do it.  
> Harry Wood: How much are we talking?  
> Holly Spencer: It's $40. I promised her I'd sort it before Friday.  
> Harry Wood: I’ll keep an eye out for her. No bother.  
> *promise by Holly Spencer: landed*  

**Day 4 19:00**, Mercedes Fuentes and Tara Bhatt at The Rusty Anchor:

> Mercedes Fuentes: Tara. You got a minute?  
> Tara Bhatt: Sure. What's on your mind?  
> Mercedes Fuentes: Aarti Sharma came in earlier. Left before I could say much. You know her?  
> Tara Bhatt: No, sorry. Don't recognize her.  

**Day 4 19:30**, Svetlana Nowak and Daria Nowak at 9 Birch Crescent:

> Svetlana Nowak: Hang on a minute, Daria. There's something I need to say.  
> Daria Nowak: Of course, love. What is it?  
> Svetlana Nowak: It's about the hours at the post office. I was wondering... have you heard anything from Alejandra?  
> Daria Nowak: No, love, sorry, I haven’t heard anything about her.  

**Day 4 20:00**, Farah Nair and Oliver Hughes at Clover Court:

> Farah Nair: Mr. Hughes, would you happen to know of any work about town? I'm trying to get ahead of the rent.  
> Oliver Hughes: Any luck with the grocery stock? Sarah said they're hiring part-time soon.  
> Farah Nair: We'll see if they follow through. I'm not in a position to wait long.  
> Oliver Hughes: Try the bakery—Julio said they’re short-handed. But no promises, you know how it goes.  

**Day 4 20:30**, Lena Petrov and Aarti Sharma at 11 Victoria Place:

> Lena Petrov: That was near enough a full day's rest. You're still here, so I assume you've got time for a proper chat.  
> Aarti Sharma: I had a long one at the hospital. Nothing new at home, except the internet's back.  
> Lena Petrov: I've been meaning to talk to you about the rent. It's due tomorrow, and I don't have it all covered.  
> Aarti Sharma: I'll see what I can do. I've got a few things on, but it's nothing I can't handle.  
> *promise by Aarti Sharma: landed*  

**Day 4 21:00**, Nnamdi Achebe and Kwesi Achebe at 13 Spring Terrace:

> Nnamdi Achebe: Kwesi, love, you’ve been quiet all evening. You want to talk about it?  
> Kwesi Achebe: I was just thinking about that car again. Needs a new battery, I’d say.  
> Nnamdi Achebe: Bless them, let me know when you're sure.  
> Kwesi Achebe: I will. Night, Nnamdi.  

**Day 4 23:00**, Sarah Pike and Farah Nair at Clover Court:

> Sarah Pike: Farah, I need to talk to you about those bins.  
> Farah Nair: I'm not sure what you mean.  
> Sarah Pike: Don't play dumb, Farah. You know which bins I'm talking about.  
> Farah Nair: I haven't touched your bins, if that's what you're implying.  

**Day 4 23:30**, Beth Moore and Keith Moore at Victoria Court:

> Beth Moore: Keith, I wanted to have a word about the rent. It's due Sunday, and I wanted to make sure we're on the same page.  
> Keith Moore: I'll have it ready. No worries on Sunday.  
> *promise by Keith Moore: landed*  

**Day 5 00:00**, Sarah Pike and Farah Nair at Clover Court:

> Sarah Pike: Farah, I’m not going to let this slide. The bins on Clover Street are a mess, and you know it.  
> Farah Nair: I don't have time for this. I've got better things to do.  

**Day 5 00:30**, Sarah Pike and Farah Nair at Clover Court:

> Sarah Pike: Farah, I don't have time for this. The bins on Clover Street are a mess, and it's not just me. You can't keep sweeping it under the rug.  
> Farah Nair: I don’t know what you're talking about.  

**Day 5 04:30**, Anna Markovic and Yaw Appiah at Clover Court:

> Anna Markovic: You're up early for a reason, aren't you?  
> Yaw Appiah: Trying to get Kemi to sleep before the day starts, really.  

**Day 5 05:30**, Julia Graham and Sophie Hughes at Clover Court:

> Julia Graham: Sophie, about that thing you mentioned earlier—about the internet?  
> Sophie Hughes: I got it sorted first thing. Near enough.  

### Every contact with a service

**Day 1 07:30**, Rafael Aguilar to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 1 07:30**, Chloe Rhodes to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 1 08:30**, Rose Grant to `northline` by text:

> Rose Grant: I need to report that my home internet has been down since 7am.  
> northline: I'm sorry about that. I'll raise a fault for your line. We expect it back by tomorrow.  
> *promise: by_day 2, kind internet, what the internet back on by tomorrow*  

**Day 1 09:00**, Adriana Peña to `northline` by text:

> Adriana Peña: The internet's out at my place. Has been since about seven.  
> northline: There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 2, kind internet, what the internet back on by tomorrow*  

**Day 1 09:30**, Wendy Wood to `northline` by text:

> Wendy Wood: The internet at my house stopped working this morning. I'd like to report it, please.  
> northline: There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 2, kind internet, what the internet back on by tomorrow*  

**Day 1 10:00**, Nancy Graham to `northline` by text:

> Nancy Graham: I received a bill for $184.60. I need to speak to someone about this.  
> northline: You're right about that bill - it was our mistake, and I've corrected it.  
> *resolve: kind billing, note billing corrected*  

**Day 1 10:30**, Ruth Palmer to `northline` by text:

> Ruth Palmer: Hello, I received a bill for $184.60, but I was expecting a regular charge of around $39. Can someone please explain what's happened?  
> northline: You're right about that bill - it was our mistake, and I've corrected it.  
> *resolve: kind billing, note billing corrected*  

**Day 1 13:00**, Megan Parker to `northline` by text:

> Megan Parker: My internet stopped working at home this morning. It's been six hours now. I need to report it.  
> northline: There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 2, kind internet, what the internet back on by tomorrow*  

**Day 1 16:00**, Pilar Peña to `northline` by text:

> Pilar Peña: We've been without internet since this morning at 9 Victoria Place. Adriana called in at nine, and you said engineers are on it. It's not back yet.  
> northline: There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 2, kind internet, what the internet back on by tomorrow*  

**Day 1 16:00**, Omar Yousef to `northline` by text:

> Omar Yousef: My internet's been down since this morning. I need to report it.  
> northline: There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 2, kind internet, what the internet back on by tomorrow*  

**Day 1 16:30**, Geeta Agarwal to `northline` by text:

> Geeta Agarwal: Hi, my internet stopped working this morning. I need it sorted as soon as possible.  
> northline: There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 2, kind internet, what the internet back on by tomorrow*  

**Day 1 17:30**, Neha Joshi to `northline` by text:

> Neha Joshi: I need to speak about my bill. It's $184.60 this month—can someone explain why?  
> northline: You're right about that bill - it was our mistake, and I've corrected it.  
> *resolve: kind billing, note billing corrected*  

**Day 1 18:00**, Luis Vargas to `northline` by text:

> Luis Vargas: I need to speak to someone about a sudden increase in my bill. It was $39 and now it's $184.60.  
> northline: You're right about that bill - it was our mistake, and I've corrected it.  
> *resolve: kind billing, note billing corrected*  

**Day 1 18:30**, Ximena Aguilar to `northline` by text:

> Ximena Aguilar: I need to report an internet outage at my home. It's been down since this morning.  
> northline: There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 2, kind internet, what the internet back on by tomorrow*  

**Day 1 19:00**, Hugo Aguilar to `northline` by text:

> Hugo Aguilar: I'm Hugo Aguilar at Victoria Place 1. The internet's been down since this morning. I just got a call from Northline saying it's expected by tomorrow. Is there anything else you can tell me?  
> northline: There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 2, kind internet, what the internet back on by tomorrow*  

**Day 1 19:30**, Aarti Sharma to `northline` by text:

> Aarti Sharma: I've had no internet at home since this morning. I'd like to report that.  
> northline: There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 2, kind internet, what the internet back on by tomorrow*  

**Day 1 20:00**, Ellen Spencer to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 1 22:30**, Abena Eze to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 1 23:30**, Beth Moore to `northline` by call: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 1 23:30**, Natalia Kovac to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 2 06:00**, Omar Yousef to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 2 07:00**, Ian Shaw to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 2 08:00**, Ryan Wood to `northline` by text:

> Ryan Wood: Mate, I've been having some issues with my internet since this morning. Can I get some help with that?  
> northline: I've booked an engineer to check your line tomorrow at ten.  
> *dispatch: at Day 3 10:00, fixes True, kind internet*  
> *promise: by_day 3, kind internet, what proper speeds by tomorrow*  

**Day 2 08:30**, Charlie Harper to `northline` by text:

> Charlie Harper: It's Harper. My internet's crawling since this morning. You had me on for forty days, so I'm giving it a few more hours before I start asking questions.  
> northline: I've booked an engineer to check your line tomorrow at ten.  
> *dispatch: at Day 3 10:00, fixes True, kind internet*  
> *promise: by_day 3, kind internet, what proper speeds by tomorrow*  

**Day 2 08:30**, Oliver Bishop to `northline` by text:

> Oliver Bishop: Hello, I'm having trouble with my internet. It's been down for over a day now.  
> northline: There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 3, kind internet, what the internet back on by tomorrow*  

**Day 2 09:00**, Kabir Sharma to `northline` by text:

> Kabir Sharma: My internet has been very slow since this morning. I need this fixed before tomorrow.  
> northline: I've booked an engineer to check your line tomorrow at ten.  
> *dispatch: at Day 3 10:00, fixes True, kind internet*  
> *promise: by_day 3, kind internet, what proper speeds by tomorrow*  

**Day 2 10:00**, Lena Petrov to `northline` by text:

> Lena Petrov: Lena Petrov. I'm having the same problem as yesterday. The internet is down again at my place.  
> northline: There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 3, kind internet, what the internet back on by tomorrow*  

**Day 2 11:30**, Yolanda García to `northline` by text:

> Yolanda García: I need to report a problem with my home internet. It's been very slow for three hours.  
> northline: I've booked an engineer to check your line tomorrow at ten.  
> *dispatch: at Day 3 10:00, fixes True, kind internet*  
> *promise: by_day 3, kind internet, what proper speeds by tomorrow*  

**Day 2 11:30**, Kwesi Achebe to `northline` by text:

> Kwesi Achebe: Hello, I'm Kwesi from 13 Spring Terrace. I've had very slow internet since 08:00 this morning. I need to report the issue.  
> northline: I've booked an engineer to check your line tomorrow at ten.  
> *dispatch: at Day 3 10:00, fixes True, kind internet*  
> *promise: by_day 3, kind internet, what proper speeds by tomorrow*  

**Day 2 12:30**, Agata Kowalski to `northline` by text:

> Agata Kowalski: I've been having really slow internet for the last four hours. I need that sorted, no rush.  
> northline: I've booked an engineer to check your line tomorrow at ten.  
> *dispatch: at Day 3 10:00, fixes True, kind internet*  
> *promise: by_day 3, kind internet, what proper speeds by tomorrow*  

**Day 2 13:00**, Pavel Nowak to `northline` by text:

> Pavel Nowak: I need to ask about the internet issue.  
> northline: Northline, hello, Pavel. What seems to be the trouble?  

**Day 2 13:30**, Pooja Joshi to `northline` by text:

> Pooja Joshi: I'm Pooja Joshi from Birch Crescent. I need to speak about my internet connection.  
> northline: Northline, hello, Pooja. What seems to be the trouble?  

**Day 2 14:00**, Rob Moore to `northline` by text:

> Rob Moore: I need to speak to someone about my internet. It's been down since this morning.  
> northline: I've booked an engineer to check your line tomorrow at ten.  
> *dispatch: at Day 3 10:00, fixes True, kind internet*  
> *promise: by_day 3, kind internet, what proper speeds by tomorrow*  

**Day 2 14:30**, Henry Murray to `northline` by text:

> Henry Murray: I'm Henry Murray. I'm having issues with my internet and I need the forms sent off by Tuesday.  
> northline: I'm sorry about that. I'll raise a fault for your line. We expect it back by tomorrow.  
> *promise: by_day 3, kind internet, what the internet back on by tomorrow*  

**Day 2 16:00**, Julia Burton to `northline` by text:

> Julia Burton: I've had very slow internet since this morning. My name is Julia Burton.  
> northline: I've booked an engineer to check your line tomorrow at ten.  
> *dispatch: at Day 3 10:00, fixes True, kind internet*  
> *promise: by_day 3, kind internet, what proper speeds by tomorrow*  

**Day 2 18:00**, Dmitri Nowak to `northline` by text:

> Dmitri Nowak: My internet's been running at a crawl all day. I need it sorted now.  
> northline: I've booked an engineer to check your line tomorrow at ten.  
> *dispatch: at Day 3 10:00, fixes True, kind internet*  
> *promise: by_day 3, kind internet, what proper speeds by tomorrow*  

**Day 2 18:30**, Valeria Vega to `northline` by text:

> Valeria Vega: I need to report a problem with the internet at my address. It's been very slow since this morning.  
> northline: I've booked an engineer to check your line tomorrow at ten.  
> *dispatch: at Day 3 10:00, fixes True, kind internet*  
> *promise: by_day 3, kind internet, what proper speeds by tomorrow*  

**Day 2 19:30**, Julio Medina to `northline` by text:

> Julio Medina: I need to speak to someone about my internet. It went out yesterday morning and came back this afternoon. I want to know why.  
> northline: There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 3, kind internet, what the internet back on by tomorrow*  

**Day 2 20:30**, Paula Fuentes to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 2 21:00**, Jane Parker to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 2 23:00**, Simon Talbot to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 06:00**, Adam Young to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 07:30**, Rahul Iyer to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 08:00**, Igor Kovac to `northline` by text:

> Igor Kovac: I'm Igor Kovac from 15 Spring Terrace. I've been having slow internet for over 24 hours now.  
> northline: I've booked an engineer to check your line tomorrow at ten.  
> *dispatch: at Day 4 10:00, fixes True, kind internet*  
> *promise: by_day 4, kind internet, what proper speeds by tomorrow*  

**Day 3 08:30**, Jakub Sokolov to `northline` by text:

> Jakub Sokolov: My internet's been down since yesterday morning, honestly. Do you know if it's just me or something bigger?  
> northline: I've booked an engineer to check your line tomorrow at ten.  
> *dispatch: at Day 4 10:00, fixes True, kind internet*  
> *promise: by_day 4, kind internet, what proper speeds by tomorrow*  

**Day 3 09:00**, Alejandra Medina to `northline` by text:

> Alejandra Medina: I've been getting a higher-than-usual bill for my home internet, and I'd like to get to the bottom of it.  
> northline: You're right about that bill - it was our mistake, and I've corrected it.  
> *resolve: kind billing, note billing corrected*  

**Day 3 10:00**, Omar Yousef to `northline` by text:

> Omar Yousef: I'm Omar Yousef from 31 Victoria Place. You said the internet would be back by tomorrow. Is it fixed yet?  
> northline: Northline, hello, Omar. What seems to be the trouble?  

**Day 3 13:30**, Henry Hughes to `northline` by text:

> Henry Hughes: My internet's out. I need it fixed.  
> northline: I'm sorry about that. I'll raise a fault for your line. We expect it back by tomorrow.  
> *promise: by_day 4, kind internet, what the internet back on by tomorrow*  

**Day 3 14:00**, Yaw Appiah to `northline` by text:

> Yaw Appiah: Hi, I'm calling about my bill. It's showing up as $184.60 when it should be around $39. I'd appreciate it if someone could look into this.  
> northline: You're right about that bill - it was our mistake, and I've corrected it.  
> *resolve: kind billing, note billing corrected*  

**Day 3 16:30**, Natalia Kovac to `northline` by text:

> Natalia Kovac: I need to speak to someone about the service to 15 Spring Terrace. The internet has been down for over 32 hours now, and the bill has gone up to $184.60.  
> northline: You're right about that bill - it was our mistake, and I've corrected it. I've booked an engineer to check your line tomorrow at ten.  
> *resolve: kind billing, note billing corrected*  
> *dispatch: at Day 4 10:00, fixes True, kind internet*  
> *promise: by_day 4, kind internet, what proper speeds by tomorrow*  

**Day 3 19:00**, Mercedes Fuentes to `northline` by text:

> Mercedes Fuentes: I need to check about the internet at home. It's been out for an hour.  
> northline: There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 4, kind internet, what the internet back on by tomorrow*  

**Day 3 19:30**, Abena Eze to `northline` by text:

> Abena Eze: Hi there, I'm having some internet issues at home and I wanted to report it. Can someone get back to me, please?  
> northline: There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 4, kind internet, what the internet back on by tomorrow*  

**Day 3 20:00**, Óscar Aguilar to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 20:30**, Ellen Spencer to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 21:00**, Omar Yousef to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 22:00**, Filip Horvat to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 22:00**, Wendy Wood to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 23:30**, Dev Agarwal to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 23:30**, Geeta Agarwal to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 4 06:00**, Oliver Hughes to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 4 15:30**, Raj Qureshi to `northline` by text:

> Raj Qureshi: I need to report an internet problem. It's been down for over a day now, and I'd like to know when it's going to be fixed.  
> northline: There's a known fault on Birch Crescent; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 5, kind internet, what the internet back on by tomorrow*  

**Day 4 16:30**, Paul Shaw to `northline` by text:

> Paul Shaw: I need to speak to someone about a sudden increase in my bill. This is the number I was given.  
> northline: You're right about that bill - it was our mistake, and I've corrected it.  
> *resolve: kind billing, note billing corrected*  

**Day 4 20:30**, Paula Fuentes to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 4 21:00**, Abena Eze to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 4 21:30**, Omar Yousef to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

### Every refusal, by reason

- 18 x it isn't my shift
- 3 x I had already talked with Yaw Appiah today
- 2 x I had already talked with Joe Ward today
- 2 x I had already talked with Lakshmi Iyer today
- 1 x I had already talked with Abiodun Obi today
- 1 x I had already talked with Adam Young today
- 1 x I had already talked with Ama Abiola today
- 1 x I had already talked with Andrei Markovic today
- 1 x I had already talked with Anna Markovic today
- 1 x I had already talked with Ben Carter today
- 1 x I had already talked with Chloe Burton today
- 1 x I had already talked with Claire Mason today
- 1 x I had already talked with Gary Moore today
- 1 x I had already talked with Harry Wood today
- 1 x I had already talked with Margaret Hughes today
- 1 x I had already talked with Oliver Bishop today
- 1 x I had already talked with Rana Jaber today
- 1 x I had already talked with Sarah Pike today
- 1 x I had already talked with Tara Bhatt today
- 1 x I had already talked with Óscar Aguilar today
- 1 x I have no work going called 'pharmacist'
- 1 x there is no willow_green to meet at
