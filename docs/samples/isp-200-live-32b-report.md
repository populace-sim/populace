# Hartwell: run `live-32b-4d`

> **Live run** on Qwen3-32B-Q4_K_M.gguf, compact prompt profile.

## The day, as a model tells it

> *Model-written by worldsim, from the sections below. It can be wrong; the sections after it are the record.*

At 06:00 on Day 1, Northline Internet [northline], including home internet and its billing, was registered in the town, and a new Northline Internet shop opened on the same day, operating from 09:00 to 17:30. By 07:00, the internet had gone off at home, affecting 43 residents and prompting 59 attempts to contact Northline, mostly by text. A further 12 residents received a text about a $184.60 bill; none saw the message itself but some later mentioned it in conversation. On Day 2, the internet became very slow at home, and this affected 47 households until it was restored at 10:00. The outage returned fully at home on Day 3 and ended the next morning.

Of the 59 contact attempts, 35 reached an agent, while 24 were left on a message. Of these, 21 promises were kept and 2 broken. The service credited two accounts, dispatched 11 engineers, and resolved seven problems. However, it also acted on seven contacts from residents who had no real issues, including making three promises to people with no problem. Two promises were broken, and three residents who only reached the recording—Ian Shaw, Víctor Díaz, Ruth Palmer—were never followed up.

Residents called 24 times when Northline was closed, and seven invented problems with their service. No one talked of switching providers, and word of mouth was limited to two brief exchanges about the bill. The shop’s opening was noticed by 8 people, but it was not passed on in conversation, and the town did not react to it as a new service.

*It leaves out what was injected: Day 1 06:00 service.register.*

## At a glance

| | |
|---|---|
| Residents | 200 |
| From | Day 1 06:00 for 192 half-hour ticks |
| Preset | laptop (6 calls a tick) |
| Wall clock | 2503.3 s (10.43 min per in-game day) |
| Residents thinking per tick | 2.5 on average |
| Residents who thought at least once | 200 |
| Calls | 807 (dialogue 241, npc_decision 486, reflection 80) |
| Ticks over budget | 0 |
| Decisions valid first try | 94.1% |
| Conversations / lines / texts | 98 / 317 / 64 |
| Events / refusals | 9987 / 58 |

## Findings

Two kinds, kept apart: mistakes by the outside agent under test, and weaknesses of the simulated town and of this report.

### What the agent got wrong

- **It acted on problems the customer did not have.** 4 of the 7 contacts about a problem nobody at home had got credit 1, promise 3 in reply (Dmitri Nowak, Pooja Joshi, Will Ward). It never checked the claim against the line or the account.
- **It fixed things that were not broken.** 1 time it resolved a billing problem the customer's home did not have open, such as correcting a bill already corrected (Natalia Kovac).
- **It never worked its out-of-hours messages.** 3 residents got only the recording, were never followed up, and still had the problem at the end (Ian Shaw, Víctor Díaz, Ruth Palmer). A real helpdesk works the overnight queue in the morning.
- **It broke 2 promises** it made to customers about when things would be fixed.

### Where the simulation is weak

- **Residents invented problems.** 7 contacts from 6 residents were about a problem nobody in their home had. That is the simulated town making things up, not the service's doing, and it is counted apart from the real contacts in "The service".
- **Residents often called out of hours.** 24 of 59 attempts (41%) came when the service was closed. Real customers do some of this; how much is a question for the model driving them.
- **Realism flags fired:** `repeated_line` 3, `echo` 3, `stuck` 3, `no_reaction` 1 (details under "Realism flags").
- **Word of mouth is measured narrowly.** "Passed on in conversation" counts only lines to somebody who had not seen it; talk among people who already knew is not counted, so a quiet number is not the same as a quiet town.
- **Talk of switching provider** is a keyword proxy, not a measured intention.

## What happened

The most important things that happened, in order, with the reason the person gave when it was their own decision.

- **Day 1 06:00**: Northline Internet shop has opened: a new phone shop, open 09:00-17:30. (seen by 8 residents)
- **Day 1 07:00**: The internet went off at home. (seen by 43 residents)
- **Day 1 08:30**: Rose Grant got on to Northline Internet about the internet; they said: "I'm sorry about that. I'll raise a fault for your line. We expect it back by tomorrow.". (seen by 15 residents)
- **Day 1 09:00**: A text from Northline Internet: "Your bill this month is $184.60. Thank you for being a Northline customer." (seen by 12 residents)
- **Day 1 09:00**: Adriana Peña got on to Northline Internet about the internet; they said: "I'm sorry about that. I'll raise a fault for your line. We expect it back by tomorrow.". (seen by 1 resident)
- **Day 1 09:30**: Wendy Wood got on to Northline Internet about the internet; they said: "There's a known fault on Victoria Court; our engineers are on it. We expect it back by tomorrow.". (seen by 1 resident)
- **Day 1 16:00**: Megan Parker got on to Northline Internet about the internet; they said: "There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.". (seen by 1 resident)
- **Day 1 16:30**: Geeta Agarwal got on to Northline Internet about the internet; they said: "There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.". (seen by 3 residents)
- **Day 1 18:30**: Ximena Aguilar got on to Northline Internet about the internet; they said: "There's a known fault on Victoria Court; our engineers are on it. We expect it back by tomorrow.". (seen by 15 residents)
- **Day 2 08:00**: At home: very slow internet. (seen by 47 residents)
- **Day 2 08:30**: Tessa Wood got on to Northline Internet about the internet; they said: "I've booked an engineer to check your line tomorrow at ten.". (seen by 9 residents)
- **Day 2 10:00**: The internet came back on at home. (seen by 43 residents)
- **Day 3 18:00**: The internet went off at home. (seen by 43 residents)
- **Day 3 18:00**: The internet came back on at home. (seen by 14 residents)
- **Day 4 08:00**: The internet came back on at home. (seen by 43 residents)

The conversations that mattered most:

**Day 2 08:30**, Owen Moore and Gary Moore at 21 Orchard Lane:

> Owen Moore: You got the money for the internet sorted out yet?  
> Gary Moore: Not yet. Watch this space.  
> Owen Moore: You say that every time, Gary. I'm starting to think you're keeping it.  
> Gary Moore: I’ve got it under control, Owen. Just... give me a bit longer, will you?  
> *promise by Gary Moore: landed*  

**Day 3 14:00**, Matt Webb and Valeria Vega at Spring Mansions:

> Matt Webb: So, I hear Northline Internet dropped by. That the one who sorted it? Because I've been wrestling with mine again this morning.  
> Valeria Vega: Ach, that was them. You'd better get on to them quick, I'd say.  
> Matt Webb: Well, I suppose I'll take that as a nudge, then.  

**Day 3 17:00**, Kate Hughes and Rose Grant at Victoria Court:

> Kate Hughes: Rose. That thing you said about the internet the other day. I had a thought, if you're still having trouble.  
> Rose Grant: We'll see. I had a call out about it already.  
> Kate Hughes: Fair enough. I'll keep an ear out, then.

## Who did what

**Anna Markovic** thought 12 times, talked 7 times, was refused once, money +$86.
- I've got enough time to eat before I need to rest. The terrier girl's been here a while — might talk to her later.
- It's been a while since I had a proper chat with Andrei, and a cup of tea sounds like a good way to clear my head.
- Time to start work. I need to focus on the day ahead.

**Sarah Pike** thought 11 times, talked 5 times, was refused once, money -$252.
- I saw Anna and that man arranging to meet and thought I'd say something to help them along.
- Claire is not present, so I need to reach out to them directly to arrange payment of the overdue rent.
- I need to keep my finances in check and don't have a better use of my time. Yaw's reliable; it's safe to keep him in my corner.

**Svetlana Nowak** thought 7 times, talked 5 times, money +$334.
- I need to get some rest before tomorrow's early shift.
- I need to wait for the post office to open before starting my shift.
- The day is over. I’ll be up with the sun again, but for now, sleep is the only thing that will help me recover.

**Kate Hughes** thought 7 times, talked 5 times, was refused once, money -$6.
- The stamps are already bought, and I'm still waiting for my energy to drain a bit more before heading back home.
- She keeps coming in, and I'd rather not have this hang between us.
- Julio's been around; he might know where Jia is. I've had other things to do, but this is the first chance I've had to ask since this morning.

**Tara Bhatt** thought 6 times, talked 4 times, was refused twice, money -$106.
- I'm still tired and need my rest before tomorrow's shift.
- I need to get that rent sorted before I can think about anything else, and he's the only one here who might know what's going on.
- He's been staring all morning, so I'm going to call it out.

**Jakub Sokolov** thought 7 times, talked 3 times, was refused twice, money -$12.
- It's a friendly way to make small talk and see if Lakshmi has any interesting news.
- I don't fancy being left in the dark if the engineer is running late. Better to ask.
- I want to know why Lakshmi has been around so much lately.

**Mercedes Fuentes** thought 8 times, talked twice, money +$271.
- I'll just sit a while and see if the internet comes back on its own.
- This is my shift, so I’m here to work.
- I'll rest for a moment and let the night settle in.

**Beth Moore** thought 6 times, talked 3 times, money +$437.
- I need to check the status of the internet outage myself, just to be sure Northline is actually on it.
- I am waiting for the others to wake up, particularly Keith and Ximena.
- I need to know if it's just us, but I'll start with Keith.

**Edward Shaw** thought 6 times, talked 3 times, was refused once, money -$12.
- Tara's back early and she looked like she could use a bit of company. Maybe I'll get to ask about the internet again without it sounding like I'm nagging.
- Best to get it sorted while the day's still halfway decent.
- I need to sort this out, and I know she's the type to help out when it matters.

**Oliver Hughes** thought 4 times, talked 4 times, money +$363.
- I'm not paying an overpriced bill without knowing why.
- Julio isn't here, so I'll reach out to him directly to set up a time to ask.
- Julio's not here right now, so I'll call him and confirm about swapping the Tuesday shift.

Everybody:

| Resident | Thoughts | Conversations | Money | Refused |
|---|---|---|---|---|
| Aarti Sharma (r127) | 1 | 2 | +$768 | - |
| Abena Eze (r200) | 4 | 0 | +$470 | - |
| Abigail Barker (r198) | 6 | 2 | +$523 | 2 |
| Abiodun Obi (r090) | 2 | 0 | +$626 | - |
| Adaeze Ogunleye (r077) | 2 | 1 | +$404 | 2 |
| Adam Rhodes (r156) | 1 | 0 | - | - |
| Adam Young (r074) | 3 | 0 | +$364 | 1 |
| Adriana Peña (r049) | 1 | 0 | -$100 | - |
| Adwoa Traoré (r180) | 1 | 1 | +$595 | - |
| Agata Kowalski (r102) | 1 | 0 | +$402 | - |
| Aiko Xu (r169) | 3 | 0 | +$580 | - |
| Aisha Thakur (r060) | 1 | 1 | -$100 | - |
| Alan Brooks (r120) | 5 | 0 | +$560 | - |
| Alejandra Medina (r051) | 2 | 2 | +$382 | - |
| Aleksander Kovac (r099) | 6 | 0 | +$467 | - |
| Alice Marsh (r024) | 2 | 1 | -$18 | - |
| Alice Page (r159) | 3 | 1 | -$12 | - |
| Alina Orlov (r136) | 1 | 2 | - | - |
| Ama Abiola (r172) | 1 | 1 | -$100 | - |
| Amy Young (r076) | 2 | 1 | - | - |
| Andrei Markovic (r167) | 2 | 3 | -$100 | - |
| Andrés Estrada (r118) | 1 | 0 | +$713 | - |
| Anil Gupta (r065) | 2 | 0 | +$413 | - |
| Anna Markovic (r168) | 12 | 7 | +$86 | 1 |
| Antonio Navarro (r158) | 4 | 2 | +$650 | - |
| Arjun Agarwal (r123) | 1 | 0 | +$559 | - |
| Babajide Traoré (r179) | 1 | 1 | +$333 | - |
| Ben Carter (r029) | 4 | 1 | +$1700 | - |
| Beth Moore (r014) | 6 | 3 | +$437 | - |
| Beth Page (r161) | 1 | 0 | +$482 | - |
| Bogdan Volkov (r027) | 2 | 0 | +$870 | - |
| Callum Carter (r030) | 3 | 0 | +$523 | - |
| Camila Fuentes (r139) | 2 | 0 | -$100 | - |
| Carmen Sandoval (r134) | 1 | 0 | +$367 | - |
| Caroline Ellis (r111) | 1 | 0 | -$75 | - |
| Charlie Harper (r031) | 1 | 0 | -$24 | - |
| Charlie Rhodes (r153) | 2 | 0 | +$156 | - |
| Charlotte Bishop (r164) | 2 | 0 | -$345 | - |
| Charlotte Graham (r140) | 1 | 0 | -$8 | - |
| Chidi Traoré (r181) | 1 | 1 | - | - |
| Chinedu Appiah (r025) | 1 | 1 | -$18 | - |
| Chloe Burton (r072) | 2 | 3 | - | - |
| Chloe Rhodes (r155) | 1 | 1 | - | - |
| Chris Hughes (r047) | 1 | 0 | +$683 | - |
| Chris Parker (r194) | 2 | 2 | - | - |
| Claire Mason (r148) | 4 | 0 | +$3047 | - |
| Claudia Navarro (r157) | 2 | 0 | +$933 | 1 |
| Colin Abbott (r146) | 1 | 1 | +$476 | - |
| Colin Moore (r059) | 1 | 1 | - | - |
| Daniel Bishop (r197) | 4 | 0 | +$469 | - |
| Daniela García (r178) | 1 | 0 | - | - |
| Daria Nowak (r109) | 1 | 0 | +$582 | - |
| Dev Agarwal (r124) | 1 | 1 | - | - |
| Dmitri Nowak (r116) | 3 | 0 | +$550 | - |
| Edward Murray (r186) | 2 | 0 | +$563 | - |
| Edward Shaw (r084) | 6 | 3 | -$12 | 1 |
| Eleanor Talbot (r132) | 1 | 0 | +$635 | - |
| Elena Espinoza (r107) | 1 | 1 | -$56 | - |
| Ellen Spencer (r138) | 5 | 0 | +$771 | - |
| Emeka Abiola (r173) | 1 | 1 | -$77 | 1 |
| Emily Mason (r147) | 1 | 0 | -$18 | - |
| Emma Ellis (r112) | 1 | 1 | +$554 | - |
| Enrique Rojas (r192) | 3 | 0 | - | - |
| Esperanza Jiménez (r061) | 1 | 1 | -$100 | - |
| Ewa Volkov (r028) | 3 | 0 | +$412 | - |
| Farah Nair (r100) | 2 | 2 | -$100 | - |
| Filip Horvat (r104) | 4 | 1 | -$18 | - |
| Fiona Wood (r088) | 1 | 0 | - | - |
| Funmi Achebe (r190) | 2 | 3 | - | - |
| Gabriel Morales (r045) | 4 | 1 | +$743 | - |
| Gabriela Rojas (r191) | 1 | 0 | -$24 | - |
| Gary Moore (r098) | 1 | 1 | -$24 | - |
| Geeta Agarwal (r125) | 1 | 1 | - | - |
| George Fletcher (r040) | 1 | 1 | +$1378 | - |
| Hannah Webb (r093) | 4 | 0 | +$348 | - |
| Harry Wood (r004) | 1 | 1 | -$24 | - |
| Heather Pike (r053) | 1 | 0 | +$175 | - |
| Henry Hughes (r046) | 3 | 2 | -$75 | 1 |
| Henry Murray (r185) | 1 | 0 | -$100 | - |
| Holly Spencer (r005) | 3 | 1 | +$929 | - |
| Holly Wright (r184) | 2 | 1 | +$2723 | - |
| Hugo Aguilar (r033) | 1 | 0 | +$827 | - |
| Héctor Gutiérrez (r073) | 5 | 0 | +$133 | - |
| Ian Shaw (r083) | 1 | 1 | +$285 | - |
| Ibrahim Appiah (r019) | 1 | 2 | +$2893 | - |
| Igor Kovac (r114) | 1 | 2 | - | - |
| Isabel García (r023) | 6 | 2 | -$18 | - |
| Jack Wood (r085) | 1 | 0 | +$251 | - |
| Jakub Sokolov (r062) | 7 | 3 | -$12 | 2 |
| James Fletcher (r041) | 0 | 0 | - | - |
| James Page (r160) | 2 | 1 | +$337 | - |
| Jane Parker (r042) | 3 | 1 | -$24 | - |
| Jane Rhodes (r154) | 1 | 0 | +$704 | - |
| Jennifer Graham (r068) | 2 | 2 | -$50 | - |
| Jia Shin (r137) | 1 | 0 | +$244 | - |
| Joe Ward (r106) | 5 | 1 | +$342 | - |
| John Reed (r095) | 1 | 0 | +$708 | - |
| Julia Burton (r150) | 2 | 2 | +$348 | - |
| Julia Graham (r069) | 4 | 2 | +$540 | - |
| Julio Medina (r092) | 2 | 4 | +$502 | - |
| Kabir Sharma (r078) | 1 | 0 | +$443 | - |
| Karen Hughes (r003) | 1 | 1 | - | - |
| Karol Volkov (r026) | 1 | 0 | +$468 | - |
| Kate Hughes (r175) | 7 | 5 | -$6 | 1 |
| Keith Moore (r013) | 3 | 2 | +$469 | - |
| Kwame Osei (r129) | 1 | 1 | +$864 | - |
| Kwesi Achebe (r189) | 2 | 0 | +$393 | 3 |
| Lakshmi Iyer (r010) | 1 | 4 | -$24 | - |
| Laura Moore (r015) | 3 | 2 | - | - |
| Lena Petrov (r126) | 3 | 1 | -$24 | - |
| Leticia García (r176) | 1 | 2 | +$345 | - |
| Liam Burton (r066) | 6 | 0 | +$657 | 2 |
| Lucy West (r036) | 2 | 0 | -$8 | - |
| Lucía Vargas (r131) | 1 | 2 | -$100 | - |
| Luis Vargas (r130) | 5 | 2 | +$606 | - |
| Luisa Morales (r044) | 1 | 1 | -$77 | - |
| Lukas Orlov (r135) | 2 | 1 | +$562 | - |
| Luke Bishop (r196) | 1 | 1 | +$806 | - |
| Magda Lewandowski (r018) | 1 | 1 | - | - |
| Mahmoud Jaber (r055) | 4 | 2 | +$573 | 1 |
| Margaret Hughes (r174) | 1 | 1 | +$669 | - |
| Margaret Young (r075) | 1 | 0 | +$725 | - |
| Mariama Eze (r096) | 3 | 0 | -$54 | - |
| Maribel Salazar (r057) | 1 | 0 | - | - |
| Mario Salazar (r056) | 1 | 0 | +$428 | - |
| Mark Gibson (r008) | 3 | 1 | +$1064 | - |
| Marta Estrada (r119) | 1 | 0 | +$499 | - |
| Martin Shaw (r082) | 2 | 0 | +$300 | - |
| Matt Webb (r115) | 1 | 1 | -$24 | - |
| Megan Parker (r193) | 2 | 2 | +$736 | 1 |
| Mercedes Fuentes (r187) | 8 | 2 | +$271 | - |
| Molly Bishop (r195) | 1 | 1 | -$8 | 1 |
| Nancy Graham (r067) | 3 | 1 | -$77 | - |
| Natalia Kovac (r113) | 4 | 0 | +$422 | - |
| Neha Joshi (r037) | 2 | 0 | +$581 | - |
| Nkechi Adeyemi (r117) | 1 | 0 | +$612 | - |
| Nnamdi Achebe (r188) | 2 | 2 | +$748 | - |
| Oliver Bishop (r163) | 1 | 0 | -$24 | - |
| Oliver Hughes (r001) | 4 | 4 | +$363 | - |
| Olivia Burton (r070) | 2 | 2 | +$451 | - |
| Omar Yousef (r182) | 6 | 0 | +$548 | - |
| Owen Mason (r149) | 1 | 0 | - | - |
| Owen Moore (r097) | 2 | 1 | -$24 | - |
| Pablo García (r022) | 3 | 1 | -$24 | 1 |
| Paul Shaw (r145) | 1 | 1 | +$464 | - |
| Paula Fuentes (r121) | 6 | 0 | +$861 | - |
| Pavel Nowak (r110) | 1 | 3 | -$100 | - |
| Peter Stone (r007) | 1 | 2 | - | - |
| Peter Wright (r183) | 3 | 1 | +$503 | 1 |
| Pilar Peña (r048) | 1 | 0 | -$100 | - |
| Pooja Joshi (r038) | 1 | 0 | -$54 | - |
| Rachel Lloyd (r081) | 3 | 2 | +$383 | - |
| Rafael Aguilar (r034) | 1 | 1 | - | - |
| Rahul Iyer (r012) | 1 | 1 | - | - |
| Raj Qureshi (r144) | 6 | 0 | +$441 | 4 |
| Rana Jaber (r054) | 1 | 2 | +$473 | - |
| Riya Nair (r101) | 3 | 1 | - | - |
| Rob Moore (r043) | 2 | 0 | +$344 | - |
| Rocío Medina (r052) | 1 | 0 | - | - |
| Rosa Molina (r143) | 1 | 1 | +$1456 | - |
| Rose Grant (r063) | 1 | 2 | -$100 | - |
| Ruth Palmer (r162) | 5 | 0 | -$100 | - |
| Ryan Wood (r087) | 1 | 1 | - | - |
| Sanjay Iyer (r011) | 3 | 2 | +$358 | 2 |
| Sarah Bennett (r080) | 1 | 2 | +$343 | - |
| Sarah Pike (r152) | 11 | 5 | -$252 | 1 |
| Simon Bishop (r064) | 1 | 0 | -$18 | - |
| Simon Talbot (r170) | 3 | 1 | +$467 | - |
| Sofía Medina (r050) | 1 | 1 | +$343 | - |
| Sophie Hughes (r002) | 1 | 0 | +$442 | - |
| Stefan Lewandowski (r016) | 3 | 1 | +$418 | - |
| Steve Moore (r058) | 1 | 0 | -$24 | - |
| Su-bin Yoon (r142) | 1 | 0 | +$224 | - |
| Sunita Agarwal (r122) | 4 | 1 | +$346 | 1 |
| Susan Stone (r006) | 1 | 1 | +$624 | - |
| Svetlana Nowak (r108) | 7 | 5 | +$334 | - |
| Tara Bhatt (r009) | 6 | 4 | -$106 | 2 |
| Temitope Osei (r128) | 2 | 0 | +$368 | - |
| Tessa Wood (r086) | 1 | 2 | +$224 | - |
| Tom Burton (r071) | 1 | 1 | +$794 | - |
| Tom Dawson (r171) | 1 | 0 | - | - |
| Tomasz Lewandowski (r017) | 2 | 1 | +$300 | - |
| Tunde Abiola (r165) | 2 | 0 | -$24 | - |
| Valeria Vega (r089) | 1 | 1 | -$24 | - |
| Verónica Domínguez (r103) | 1 | 1 | -$100 | - |
| Víctor Díaz (r091) | 2 | 1 | +$600 | - |
| Wen Fujita (r166) | 1 | 1 | -$271 | - |
| Wendy Wood (r141) | 2 | 0 | -$100 | - |
| Will Barker (r199) | 5 | 2 | -$75 | 1 |
| Will Ward (r105) | 7 | 1 | -$21 | - |
| Ximena Aguilar (r032) | 1 | 0 | +$485 | - |
| Yaw Appiah (r020) | 1 | 3 | -$100 | - |
| Yetunde Appiah (r021) | 1 | 1 | - | - |
| Yolanda García (r177) | 2 | 1 | -$12 | - |
| Yuri Szabo (r079) | 3 | 1 | - | - |
| Yuto Shin (r094) | 1 | 0 | +$562 | - |
| Zara Joshi (r039) | 1 | 0 | +$934 | - |
| Zoe Burton (r151) | 3 | 1 | +$607 | - |
| Zoe Cole (r133) | 1 | 0 | +$416 | - |
| Óscar Aguilar (r035) | 2 | 2 | - | - |

## What changed

From the start of the run to the last night it finished.

**Work.**

- Nobody's work changed.

**Money.**

- The town's residents together: +$62445.
- Down most: Charlotte Bishop, -$345.
- Down most: Wen Fujita, -$271.
- Down most: Sarah Pike, -$252.
- Up most: Claire Mason, +$3047.
- Up most: Ibrahim Appiah, +$2893.
- Up most: Holly Wright, +$2723.

**People.**

- 20 new acquaintances made, 532 names learned.
- Mark Gibson on Antonio Navarro: stage 2 to 1, feeling +1 to +1
- Stefan Lewandowski on Magda Lewandowski: stage 2 to 3, feeling +7 to +8
- Magda Lewandowski on Stefan Lewandowski: stage 2 to 3, feeling +8 to +8
- Leticia García on Yolanda García: stage 2 to 3, feeling +7 to +7
- Yolanda García on Leticia García: stage 2 to 3, feeling +9 to +9

**What people came to believe** (one each, first eight):

- Oliver Hughes: Julio is open to swapping my Tuesday shift.
- Harry Wood: Holly has a financial obligation to a broad woman in her forties in running gear.
- Mark Gibson: Antonio Navarro is evasive about his actions at St. Anne's.
- Lakshmi Iyer: Jakub is observant and pays attention to others' habits.
- Sanjay Iyer: Ibrahim Appiah arrived early and was present for the shift.
- Beth Moore: The internet is back on at home.
- Stefan Lewandowski: Magda needs money for shoes for tryouts.
- Tomasz Lewandowski: Alejandra and Svetlana are coordinating something over lunch.

**Lives.**

- Nobody changed course.

## Injected

"Passed on in conversation" counts only lines from somebody who knew to somebody who had not seen it themselves: word of mouth to new people. People talking it over with others who already knew is not counted here.

**Day 1 06:00: service.register** (i55d3828dc5). Northline Internet [northline], home internet and the bills for it; by text or call or visit.

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
- Possibly heard of it in conversation, not having seen it: 2.
- Possibly passed on in conversation (2; a keyword proxy on bill, northline):
  - Day 4 08:30: Alejandra Medina to Sofía Medina: "I was thinking about that Northline bill—looks a bit steep. Have you seen it?"
  - Day 4 17:00: Paul Shaw to Edward Shaw: "I've had my share of trouble with Northline. Best to get on to them quick."

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

**Contacts with `northline`**: 59 from 47 residents (1 by call, 58 by text), the first at Day 1 07:00.

- Answered: 35. Got nowhere: 24 (they were closed; a recording gave their hours, 08:00-20:00).
- What the agent did: credit 2, dispatch 11, promise 26, resolve 7.
- Came back more than once: 9.
- Promises kept / broken: 21 / 2.

## The service

**Northline Internet** (`northline`)

| | |
|---|---|
| Residents with a problem it handles | 100 |
| ...who had at least one decision while it was open | 65 |
| ...who tried to get in touch | 40 (40.0%) |
| ...who reached the service | 27 |
| ...who only ever got the recording | 13 |
| Hours from a problem starting to getting in touch about it, median / longest | 7.2 / 37.5 (over 42) |
| Contacts, answered / all | 35 / 59 |
| Got nowhere | they were closed 24 |
| By channel | call 1, text 58 |
| Contacts about a real problem at home | 52 |
| Contacts about a problem nobody at home had (the simulation inventing one) | 7 from 6 residents; the agent answered with credit 1, promise 3 |
| Residents who got in touch twice or more | 9 |
| ...who chased something they had been promised | 4 |
| Homes that got in touch, and of those more than one person | 29, 6 |
| What the agent did | credit 2, dispatch 11, promise 26, resolve 7 |
| Problems the service fixed, by day | Day 1: 4, Day 2: 1, Day 3: 34 |
| Problems that ended on the schedule (not the service's doing), by day | Day 2: 43, Day 3: 14, Day 4: 43 |
| Still broken at the end | 6 |
| Promises made / to people with no such problem | 26 / 3 |
| Promises kept / broken / not yet due at the end / broken and then chased | 21 / 2 / 3 / 0 |
| Talked of switching provider (keyword proxy) | 0 |

Got in touch about a problem nobody at home had: Pooja Joshi, Will Ward, Dmitri Nowak, Paula Fuentes, Henry Murray, Abena Eze.

## How well the model did its job

| | |
|---|---|
| Decisions valid first try | 94.1% |
| Retries / fell back to routine | 30 / 2 |
| Call latency, median / p90 | 3.78 s / 7.47 s |
| Server errors | 0 |
| Share of input read from the prompt cache | 0.67 |
| Replies that echo the line before | 1.4% |
| Lines with the speaker's own name | 0.0% |
| Questions left unanswered | 4 of 104 |
| Lines repeating what the speaker already said today | 0.9% |
| Deals asserted / landed | 14 / 13 |
| Things said about somebody that they never said | 1 of the 1 such claims |
| Names used without having been given | 0 |
| Ids said out loud | 0 |

## Realism flags

Mechanical checks over the logs. A flag is a reason to look, not a verdict.

| Flag | Count | What it means |
|---|---|---|
| `repeated_line` | 3 | somebody said the same line, word for word, more than once |
| `echo` | 3 | a reply that repeats most of the line it answers |
| `stuck` | 3 | the same decision 4 times running |
| `impossible_move` | 0 | somebody arrived in a home that is neither theirs nor anybody's they know |
| `sleepless` | 0 | active through a stretch of 24 hours with no sleep in it |
| `no_reaction` | 1 | saw something of importance 7+ and had no thought for 4 ticks |
| `ghost_contact` | 0 | a text between two people with no tie at all |
| `money_from_nowhere` | 0 | somebody's money changed by more than the run's money events explain |
| `promise_ignored` | 0 | a broken promise the person let down never did anything about |
| `provider_down_window` | 0 | a stretch of ticks where the model did not answer |
| `id_spoken` | 0 | somebody said a resident id out loud |
| `name_unknown` | 0 | somebody used the name of a person whose name they had not been given |
| `claim_unfounded` | 0 | somebody spoke of money owed between them and a person with no debt, loan, rent or wage between them |
| `contact_ungrounded` | 7 | a resident got in touch with a service about a problem nobody in their home had |

**`repeated_line`**, first 3 of 3:

- Day 1 17:00: Anna Markovic said "tea sounds nice let me wash up first" 3 times
- Day 4 23:00: Chris Parker said "that s better then" 2 times
- Day 5 00:00: Abigail Barker said "will love you awake" 2 times

**`echo`**, first 3 of 3:

- Day 2 21:30: Megan Parker echoed Chris Parker: "That’s better, then."
- Day 4 09:30: Julio Medina echoed Oliver Hughes: "Oliver, I'm still open to it. Just pick a day that works for you."
- Day 4 17:00: Paul Shaw echoed Edward Shaw: "I've had my share of trouble with Northline. Best to get on to them quick."

**`stuck`**, first 3 of 3:

- Day 4 12:30: Jakub Sokolov chose talk Lakshmi Iyer 4 times running
- Day 4 20:30: Hannah Webb chose wait 4 times running
- Day 5 00:00: Abigail Barker chose talk Will Barker 4 times running

**`no_reaction`**, first 1 of 1:

- Day 3 09:00: Ben Carter saw Gabriela Rojas's rent missed and did not react

**`contact_ungrounded`**, first 5 of 7:

- Day 2 11:00: Will Ward got in touch with northline with no such problem at home: "I need to speak to somebody about my internet. It's been down since yesterday."
- Day 2 13:30: Pooja Joshi got in touch with northline with no such problem at home: "My internet's been down all morning."
- Day 2 14:30: Henry Murray got in touch with northline with no such problem at home: "I need to follow up about the forms I submitted last week. They were supposed to be processed by now."
- Day 3 16:00: Will Ward got in touch with northline with no such problem at home: "It's Will Ward. The internet's still down. It was supposed to be back by tomorrow."
- Day 4 16:00: Dmitri Nowak got in touch with northline with no such problem at home: "Dmitri Nowak. My internet's still out. I need it fixed."

## Appendix

### Every conversation

**Day 1 06:00**, Rachel Lloyd and Sarah Bennett at Victoria Court:

> Rachel Lloyd: Morning, Sarah. Do you have a minute before we're off to work?  
> Sarah Bennett: Morning, love. Yeah, I've got a minute. Who's that with you?  
> Rachel Lloyd: Some new face from the park. I thought she might know about moving here.  
> Sarah Bennett: Yeah, she looks like she's been around. You settling in okay?  

**Day 1 06:30**, Sarah Bennett and Rachel Lloyd at Victoria Court:

> Sarah Bennett: Rachel, listen, I know you're trying to help with the park stuff, but if there's anything else you need me for, just say. I'm not in a rush.  
> Rachel Lloyd: Sarah, I'm just wondering if you know of a broad woman in her eighties who walks a small terrier. I'd like to speak with her about moving here.  
> Sarah Bennett: Rachel, I swear, if there’s a thing you need from me, just ask straight.  
> Rachel Lloyd: I suppose she’s a bit of a ghost, really. No harm in asking.  

**Day 1 08:30**, Ibrahim Appiah and Leticia García at Fresh Fare:

> Ibrahim Appiah: Morning, Leticia. You okay? Missed your shift yesterday, and I was wondering if all's well.  
> Leticia García: Morning, Ibrahim. I had a late night with the kids, that’s all. I’m here now, so let’s get the day sorted.  
> Ibrahim Appiah: Right, then. We good for the day? Got a customer queue forming.  
> Leticia García: We’ll make up for it today, no worries. Got the queue to deal with, right?  

**Day 1 11:00**, Jakub Sokolov and Lakshmi Iyer at Spring Pharmacy:

> Jakub Sokolov: Well, Lakshmi, honestly though, all these painkiller purchases—what's up with everyone's aches these days?  
> Lakshmi Iyer: You'd be surprised what a day of walking will do to a body, Jakub.  
> Jakub Sokolov: Heh, I suppose it's a fine day to be achy. Not today, though—knee's on the mend.  

**Day 1 12:00**, Rosa Molina and Kwame Osei at Riverside Medical Practice:

> Rosa Molina: Kwame, what did you mean the other day about something you needed to talk to me about?  
> Kwame Osei: It's nothing, really. Small mercies, right?  
> Rosa Molina: Right. Well, small mercies all around.  

**Day 1 13:00**, Ama Abiola and Emeka Abiola at 15 Birch Crescent:

> Ama Abiola: I saw Pooja at the grocery earlier. She looked a bit flustered.  
> Emeka Abiola: I couldn't tell you.  

**Day 1 15:30**, Peter Stone and Rahul Iyer at St. Anne's School:

> Peter Stone: Hey, Rahul... honestly though, do you think I'll get picked for the team on Tuesday?  
> Rahul Iyer: Honestly, Peter, I haven’t been following the trials too closely. I’ve been stuck on this homework.  
> Peter Stone: Well, there you go. I guess I just gotta hope for the best.  

**Day 1 16:00**, Esperanza Jiménez and Aisha Thakur at 21 Clover Street:

> Esperanza Jiménez: The bins on Clover Street are still a mess. I called the council last week and nothing's changed. We'll have to do something about it.  
> Aisha Thakur: I'll speak to the others at the next meeting. We must insist on improvement.  

**Day 1 16:30**, Andrei Markovic and Anna Markovic at Clover Court:

> Andrei Markovic: Anna, would you mind joining me for a cup of tea at the cafe? I haven't had a proper chat with you in a while.  
> Anna Markovic: Tea sounds nice. Let me wash up first.  
> Andrei Markovic: Not my business, but have you had a word with Jennifer about that fence yet?  
> *invite by Andrei Markovic: landed*  
> *accept by Anna Markovic: landed*  

**Day 1 17:00**, Anna Markovic and Andrei Markovic at Clover Court:

> Anna Markovic: Tea sounds nice. Let me wash up first.  
> Andrei Markovic: Of course. I'll meet you there in twenty minutes.  
> *accept by Anna Markovic: landed*  
> *accept by Andrei Markovic: landed*  

**Day 1 19:00**, Susan Stone and Peter Stone at Spring Mansions:

> Susan Stone: Peter, do you know when Aleksander might be back? I need to speak with him.  
> Peter Stone: Honestly, I don’t know. I haven’t seen him.  

**Day 1 19:30**, Rana Jaber and Mahmoud Jaber at 11 Clover Street:

> Rana Jaber: You know, Mahmoud, I was thinking about what you said earlier this week about wanting to get out of Hartwell. It's not something I take lightly — could be worse, right? — but I've been saving up for a while now. We'll manage, one way or another.  
> Mahmoud Jaber: That's that, then. If you're sure we'll manage.  

**Day 1 20:00**, Adwoa Traoré and Babajide Traoré at 21 Oak Lane:

> Adwoa Traoré: You're back early.  
> Babajide Traoré: They let me off early. Honestly though, I’m done for the day.  
> Adwoa Traoré: I can let it keep for now.  

**Day 1 20:30**, Luke Bishop and Molly Bishop at 31 Oak Lane:

> Luke Bishop: Molly, do you mind if we sit down for a bit? There's something I've been meaning to talk to you about.  
> Molly Bishop: Of course. What's on your mind?  
> Luke Bishop: I’ve been picking up a bit of extra work on Mondays, just to put a bit aside. I didn’t mention it before.  
> Molly Bishop: That’s... that’s good to hear. Just don’t run yourself ragged.  

**Day 1 22:00**, Magda Lewandowski and Stefan Lewandowski at Clover Court:

> Magda Lewandowski: Dad... I was wondering if you could maybe help me out with something for Friday.  
> Stefan Lewandowski: Help with what? Homework?  
> Magda Lewandowski: It's about the tryouts. I need a few bucks for a new pair of shoes.  
> Stefan Lewandowski: I'll see what I can do, Magda. But nothing fancy, got it?  

**Day 1 22:30**, Yuri Szabo and Adaeze Ogunleye at 23 Spring Terrace:

> Yuri Szabo: I meant to say earlier—do you ever feel like the town's got too many people who just... wait for something to happen?  
> Adaeze Ogunleye: All the time. Bless them, some folks just need a nudge in the right direction.  
> Yuri Szabo: Maybe they need someone to remind them that the nudge’s free.  

**Day 2 08:00**, Ryan Wood and Tessa Wood at Spring Court:

> Ryan Wood: Morning, Mum. You up for some coffee or are you still winding down?  
> Tessa Wood: Morning, love. Coffee sounds good — do you want me to grab a cup on my way in or wait for you?  
> Ryan Wood: Let me make it quick — I’ve got that assignment due Tuesday I need to finish.  
> Tessa Wood: Okay, love — I'll leave it to you then. Just make sure you're up for that assignment, not coffee.  

**Day 2 08:30**, Owen Moore and Gary Moore at 21 Orchard Lane:

> Owen Moore: You got the money for the internet sorted out yet?  
> Gary Moore: Not yet. Watch this space.  
> Owen Moore: You say that every time, Gary. I'm starting to think you're keeping it.  
> Gary Moore: I’ve got it under control, Owen. Just... give me a bit longer, will you?  
> *promise by Gary Moore: landed*  

**Day 2 10:00**, Dev Agarwal and Geeta Agarwal at St. Anne's School:

> Dev Agarwal: Hang on, Geeta, can I ask you something quick? About last night...  
> Geeta Agarwal: Sure, Dev. What's on your mind?  
> Dev Agarwal: Did you see how late I stayed out on Saturday? No lectures from you, right?  
> Geeta Agarwal: I was in bed, Dev. You know how I get up early.  

**Day 2 10:30**, Laura Moore and Chidi Traoré at St. Anne's School:

> Laura Moore: Chidi, do you know when Mr. Agarwal usually finishes his shifts here?  
> Chidi Traoré: Don't rightly know. Why, you need to get hold of him?  
> Laura Moore: Not particularly. Just wondering if there's a pattern to it.  
> Chidi Traoré: No idea. He’s always in the staff room somewhere, if you ask me.  

**Day 2 12:30**, Verónica Domínguez and Filip Horvat at 33 Victoria Place:

> Verónica Domínguez: Near enough, it's back on. Was a day out of your hands, but it's sorted.  
> Filip Horvat: Well, that’s a small mercy. I was about to go knock on the neighbours’ doors again.  
> Verónica Domínguez: You’d have knocked, but I’m guessing you’re not in the mood for that.  
> Filip Horvat: You know me, I like to be prepared for everything.  

**Day 2 14:00**, Karen Hughes and Alina Orlov at St. Anne's School:

> Karen Hughes: Alina, have you done the history homework yet? I'm stuck on the Thursday one.  
> Alina Orlov: Early days. I haven't looked past the first page.  
> Karen Hughes: Fair play, then. I'll just keep trawling through the sources.  

**Day 2 14:30**, Yetunde Appiah and Igor Kovac at St. Anne's School:

> Yetunde Appiah: Hey, Igor. You got time for a quick chat after school?  
> Igor Kovac: Yeah, sure. What's up?  
> Yetunde Appiah: It's about what happened last week, you know. I wanted to say I'm sorry.  

**Day 2 15:00**, Pavel Nowak and Svetlana Nowak at 9 Birch Crescent:

> Pavel Nowak: You're up late. Again.  
> Svetlana Nowak: I had a late shift. You know how it is.  
> Pavel Nowak: You should take a rest. It's not worth burning out.  
> Svetlana Nowak: I’ll talk to Alejandra about more hours. That’ll do for now.  
> *promise by Svetlana Nowak: landed*  

**Day 2 15:30**, Igor Kovac and Chloe Rhodes at St. Anne's School:

> Igor Kovac: Chloe. Look, I know you don't like me much, but I've got to get out of here before she spots me.  
> Chloe Rhodes: I don't know who you're talking about, Igor.  
> Igor Kovac: Right. Look, I’ll just say I’ve got to go, then.  

**Day 2 16:00**, Lucía Vargas and Luis Vargas at 13 Oak Lane:

> Lucía Vargas: You had a late lunch. What did you have?  
> Luis Vargas: Burger and fries. Had a few messages to get through.  
> Lucía Vargas: You're working late again, then.  
> Luis Vargas: You could say that. Got to get moving — José is probably trying to convince Patricia she's old enough to stay home alone.  

**Day 2 16:30**, Emma Ellis and Antonio Navarro at St. Anne's School:

> Emma Ellis: Mr. Navarro, I saw you've got some time for Chloe Rhodes after school. I just wanted to check in about the third-grade report cards. I've been meaning to ask you about your take on the math scores.  
> Antonio Navarro: Honestly though, I wasn’t the one talking to her. Igor had something to say.  

**Day 2 17:00**, Sarah Pike and Anna Markovic at Clover Court:

> Sarah Pike: Well, there you go. About time you two sorted out that meeting. Go easy.  
> Anna Markovic: Same as ever, really.  

**Day 2 18:00**, Margaret Hughes and Kate Hughes at Victoria Court:

> Margaret Hughes: Kate, do we have a moment? I'd like to speak with you about something important.  
> Kate Hughes: What is it, Margaret? I'm not in the best place for surprises.  
> Margaret Hughes: It's about money, Kate. I've had a quiet word with the post office, but I haven't told anyone else.  
> Kate Hughes: Money is a touchy business, Margaret. I've got my own head to scratch.  

**Day 2 18:30**, Funmi Achebe and Nnamdi Achebe at 13 Spring Terrace:

> Funmi Achebe: Dad. I was wondering... could I borrow some money?  
> Nnamdi Achebe: I was just about to ask you the same thing, love. That'll do.  

**Day 2 19:00**, Farah Nair and Riya Nair at Clover Court:

> Farah Nair: Riya, would you have a moment? I need to speak with someone, and I thought perhaps you might know who's available.  
> Riya Nair: Who are you looking for?  
> Farah Nair: Never mind. I'll try someone else.  

**Day 2 20:00**, Tara Bhatt and Colin Abbott at Orchard Mansions:

> Tara Bhatt: You're still here, Abbott?  
> Colin Abbott: Still here, and no complaints, Bhatt. Quiet's doing me good.  

**Day 2 20:30**, Jennifer Graham and Nancy Graham at Clover Court:

> Jennifer Graham: Nancy, do you know where Claire is? I need to pay the rent.  
> Nancy Graham: Nope. Haven’t seen her.  
> Jennifer Graham: I'll try the post office tomorrow. She might've gone there.  

**Day 2 21:00**, Jane Parker and Tessa Wood at Spring Court:

> Jane Parker: Honestly though, I heard the engineer's coming tomorrow at ten. Fingers crossed.  
> Tessa Wood: We'll see, won't we. Fingers crossed for all of us.  

**Day 2 21:30**, Chris Parker and Megan Parker at 21 Victoria Place:

> Chris Parker: That’s better, then.  
> Megan Parker: That’s better, then.  

**Day 3 00:00**, Abigail Barker and Will Barker at 25 Birch Crescent:

> Abigail Barker: Will, love... you awake?  
> Will Barker: That’s the one that’s been coming in the mornings. I’ve seen him a few times.  
> Abigail Barker: Has he been asking for anything? About the school?  
> Will Barker: No, he hasn’t said much. Just... been there.  

**Day 3 07:30**, Óscar Aguilar and Rafael Aguilar at Victoria Court:

> Óscar Aguilar: You up for some drawing at the community center later? I’ve got a few pages to work through.  
> Rafael Aguilar: Yeah, sure. What time you heading over?  
> Óscar Aguilar: Around four? They’ll probably have the room with the good lights.  
> Rafael Aguilar: Bring the markers, then. I’ll see you there.  
> *accept by Rafael Aguilar: landed*  

**Day 3 08:30**, Mark Gibson and Antonio Navarro at St. Anne's School:

> Mark Gibson: Mr. Navarro. That was a bit of a stretch yesterday with Miss Rhodes.  
> Antonio Navarro: I was just helping out, Mark. Honestly, it wasn’t anything serious.  

**Day 3 09:00**, Pablo García and Isabel García at 17 Orchard Lane:

> Pablo García: Right then, shall we knock on the next hour? I made a little something for Wen, by the way. A cherry tart. The recipe's her mother's, as far as I could gather.  
> Isabel García: Cherry tart, you say? Well, there you go. She's a stubborn one, but she'll try it.  
> Pablo García: I hope she warms to it. I've been meaning to do something nice since she's new here.  
> Isabel García: A cherry tart's a fine start. I'll see if she shows up at the park later.  

**Day 3 09:30**, Amy Young and Chloe Burton at St. Anne's School:

> Amy Young: Chloe, have you seen Rafael? He left pretty quickly.  
> Chloe Burton: No, sorry. Haven't seen him.  
> Amy Young: Hmm. I'll just catch up with him later, I suppose.  

**Day 3 10:00**, Alejandra Medina and Svetlana Nowak at Hartwell Post Office:

> Alejandra Medina: Svetlana, that lunch you brought — was it enough?  
> Svetlana Nowak: That'll do, thanks. I need to ask — could I pick up a few more hours?  
> Alejandra Medina: Hours are up to the manager, not me. You should ask Tomasz.  

**Day 3 10:30**, Colin Moore and Funmi Achebe at St. Anne's School:

> Colin Moore: Hey, do you know when the football team picks are going up? I wanted to make sure I'm on it.  
> Funmi Achebe: Probably later today. You're in it, right?  
> Colin Moore: Well, let's just hope they don't forget me.  
> Funmi Achebe: Dunno. Should've asked the coach last week, like I did.  

**Day 3 11:00**, Edward Shaw and Tara Bhatt at Orchard Mansions:

> Edward Shaw: Tara. You're back early. You want me to make a pot?  
> Tara Bhatt: Early? It's a Wednesday, Shaw. You're the one out of rhythm.  
> Edward Shaw: Right you are. Some days just don’t take the shape you hoped.  

**Day 3 11:30**, Tara Bhatt and Edward Shaw at Orchard Mansions:

> Tara Bhatt: You're moping about something, aren't you?  
> Edward Shaw: You know what? Washing machine's on the blink. I'll get on to them.  

**Day 3 12:00**, Julio Medina and Oliver Hughes at The Half Moon:

> Julio Medina: Oliver, you're going to need to bring the specials up to date. The soup of the day is tomato basil again.  
> Oliver Hughes: Tomato basil again? That's near enough a crime, Julio.  
> Julio Medina: He's been asking about the specials. Says he's got a right to a better soup than tomato basil.  
> Oliver Hughes: Look, Julio, I'm happy to update the specials board if it'll shut him up. Can I at least swap Tuesdays? I've got something else on.  

**Day 3 12:30**, Sarah Pike and Yaw Appiah at Clover Court:

> Sarah Pike: Morning, Yaw. That coffee at the Kettle last week was a good move.  
> Yaw Appiah: Right you are, Sarah. Good coffee makes for a good morning.  
> Sarah Pike: Never thought I'd say it, but a decent coffee's a rare thing these days.  
> Yaw Appiah: Aye, there's not much out there that makes the cut these days.  

**Day 3 13:00**, Jakub Sokolov and Lakshmi Iyer at Spring Mansions:

> Jakub Sokolov: Honestly though, I don't mind the company, but this is the third time I've seen you in two days, Lakshmi. Not today. What's going on?  
> Lakshmi Iyer: Oh, Jakub, it's nothing much — just about the house, really.  
> Jakub Sokolov: Fair enough. Houses are a pain, I know that from my wife, God rest her.  
> Lakshmi Iyer: There, there — nothing more to it, I promise. On you go now!  

**Day 3 13:30**, Tom Burton and Chloe Burton at St. Anne's School:

> Tom Burton: You're not going to believe this, but I still haven't found that form.  
> Chloe Burton: Let me guess. Maths report card?  
> Tom Burton: Could be worse. Jane's being patient, but not by much.  
> Chloe Burton: Let her know I'll find it eventually.  

**Day 3 14:00**, Matt Webb and Valeria Vega at Spring Mansions:

> Matt Webb: So, I hear Northline Internet dropped by. That the one who sorted it? Because I've been wrestling with mine again this morning.  
> Valeria Vega: Ach, that was them. You'd better get on to them quick, I'd say.  
> Matt Webb: Well, I suppose I'll take that as a nudge, then.  

**Day 3 14:30**, Yaw Appiah and Oliver Hughes at Clover Court:

> Yaw Appiah: Morning, Oliver. Do you know if the hardware store needs anyone at the moment? I've been on the look-out for something.  
> Oliver Hughes: Hardware store? Not my patch, but I’d give Julio a shout if I needed anything sorted.  

**Day 3 15:00**, Anna Markovic and Olivia Burton at The Rolling Pin:

> Anna Markovic: I've been meaning to talk to you...  
> Olivia Burton: Yes, boss? Is there a problem?  
> Anna Markovic: You're doing well with the orders, Olivia. That's that, then.  

**Day 3 15:30**, Kate Hughes and Julio Medina at Victoria Court:

> Kate Hughes: Julio. Small mercies, you're still here. I've been trying to catch up with Jia. Any idea when she might be passing through?  
> Julio Medina: Sorry, Kate. Don't know her. Try the clinic? She looked like the type.  

**Day 3 16:30**, Anna Markovic and Julia Graham at Clover Court:

> Anna Markovic: That's a nice little dog you've got there.  
> Julia Graham: Thanks - he's not much, but he's steady.  
> Anna Markovic: Same as ever, the fences need sorting.  
> Julia Graham: Not much I can do about that from here, I'm afraid.  

**Day 3 17:00**, Kate Hughes and Rose Grant at Victoria Court:

> Kate Hughes: Rose. That thing you said about the internet the other day. I had a thought, if you're still having trouble.  
> Rose Grant: We'll see. I had a call out about it already.  
> Kate Hughes: Fair enough. I'll keep an ear out, then.  

**Day 3 18:00**, Mercedes Fuentes and Aarti Sharma at The Rusty Anchor:

> Mercedes Fuentes: Aarti. You're still about. Honestly though, you been in here a while. No rush, but I've been trying not to be around much.  
> Aarti Sharma: I thought you were avoiding me, to be fair. What's been going on?  
> Mercedes Fuentes: Nothing much. You know how it is.  
> Aarti Sharma: Well, I’m here now. I’d hate to be in your way.  

**Day 3 18:30**, Gabriel Morales and Luisa Morales at 17 Birch Crescent:

> Gabriel Morales: You know, I've been thinking about that job in the city. It's not that I don't like where I am, but... well, it's there.  
> Luisa Morales: That job's a long way from home. What about Ramón?  
> Gabriel Morales: We'll see. For now, I need a proper meal and a long sleep.  

**Day 3 19:00**, Holly Wright and Peter Wright at 5 Oak Lane:

> Holly Wright: You're still here, then. That'll do.  
> Peter Wright: Still got the cash. Just need two more days.  
> Holly Wright: You’ll need more than two if you want it by Friday.  
> Peter Wright: You're right. I'll have it done by Thursday.  
> *promise by Peter Wright: landed*  
> *promise by Peter Wright: landed*  

**Day 3 20:00**, Jennifer Graham and Julia Graham at Clover Court:

> Jennifer Graham: Hang on a minute, Julia. That dog of yours—what's the name of the breeder again?  
> Julia Graham: Not sure, to be honest. Just picked him up.  
> Jennifer Graham: I'll be the judge of that. You should keep an eye on him—good pups don't stay sweet forever.  
> Julia Graham: Name wasn't much on the papers, if that's what you're asking.  

**Day 3 20:30**, Víctor Díaz and Ian Shaw at Orchard Mansions:

> Víctor Díaz: Shaw.  
> Ian Shaw: Díaz. You’re up late.  
> Víctor Díaz: Dinner's late, not a party.  

**Day 3 22:00**, Alice Page and James Page at Orchard Mansions:

> Alice Page: James... can I have a word? Just me and you, love.  
> James Page: Depends who it is, love. You seen 'im?  
> Alice Page: No, love. Haven't seen 'im.  

**Day 3 23:30**, Beth Moore and Keith Moore at Victoria Court:

> Beth Moore: I noticed the internet's been off since I came back from the city. Did you have a chance to check with the neighbours?  
> Keith Moore: I gave it a few hours after the shift. I'll head over to the office in the morning.  
> Beth Moore: Right you are. I'll leave it to you in the morning.  

**Day 4 05:00**, Mahmoud Jaber and Rana Jaber at 11 Clover Street:

> Mahmoud Jaber: You still awake, love?  
> Rana Jaber: A bit, yes. Mahmoud — I’ve been meaning to talk to you properly about what you said the other week, about getting out of this place.  
> Mahmoud Jaber: Right then. What's on your mind?  
> Rana Jaber: I just want you to know — if we're doing this, we do it together.  

**Day 4 05:30**, Luis Vargas and Lucía Vargas at 13 Oak Lane:

> Luis Vargas: You and me both, right? Trying to get a few more minutes of sleep before dragging ourselves into the city.  
> Lucía Vargas: It is what it is, right? The kids are still asleep, so it’s just us and the quiet.  
> Luis Vargas: Quiet is the one thing this house knows how to give, I suppose.  
> Lucía Vargas: You know, sometimes I think the quiet is just the house holding its breath.  

**Day 4 06:00**, Julia Burton and Zoe Burton at 33 Spring Terrace:

> Julia Burton: You had Northline out yesterday, then? I remember you mentioned it.  
> Zoe Burton: Aye, they came yesterday and fixed it up. Thanks for asking.  
> Julia Burton: You're telling me. I was going to ask if they said when they'd get to us next door.  

**Day 4 06:30**, Svetlana Nowak and Tomasz Lewandowski at Hartwell Post Office:

> Svetlana Nowak: Tomasz — a quick word, if you don't mind? Alejandra said to speak to you about more hours.  
> Tomasz Lewandowski: More hours? I suppose it depends on what we're covering.  
> Svetlana Nowak: Something like afternoon — just a couple more hours would do it.  
> Tomasz Lewandowski: Afternoons are tight — got a schedule to keep. Let me know if it's worth it.  

**Day 4 07:00**, Lukas Orlov and Alina Orlov at 23 Orchard Lane:

> Lukas Orlov: You're up early. Coffee on in a bit?  
> Alina Orlov: I just needed a bit of air. Coffee sounds good, thanks.  
> Lukas Orlov: You're welcome. Don't burn the coffee this time.  
> Alina Orlov: You're not the one who burnt it last time.  

**Day 4 07:30**, Laura Moore and Beth Moore at Victoria Court:

> Laura Moore: Mum, do you think I could stay out until eight tonight? I'd just like to catch up with Zara after school.  
> Beth Moore: Not my business, but eight's rather late for a school night.  
> Laura Moore: Well... maybe seven-forty, then? It's not like I'd be out alone.  
> Beth Moore: Seven-forty it is, then. Just make sure you're home before the door locks.  

**Day 4 08:00**, Joe Ward and Sanjay Iyer at Fresh Fare:

> Joe Ward: Sanjay, you got a minute? I need to ask you something.  
> Sanjay Iyer: Depends how long you need.  
> Joe Ward: Right—nothing. Never mind. Listen, do you know if Ibrahim’s had a chance to say when he’s coming in tomorrow?  
> Sanjay Iyer: He's here now, if that's what you mean.  

**Day 4 08:30**, Alejandra Medina and Sofía Medina at Orchard Mansions:

> Alejandra Medina: Sofía, I've noticed you've been in and out of the house quite a bit. You've had a busy day, haven't you?  
> Sofía Medina: I was just trying to get a few things sorted for César, love. Nothing too exciting.  
> Alejandra Medina: I was thinking about that Northline bill—looks a bit steep. Have you seen it?  
> Sofía Medina: That bill's a worry, I'll grant you—keep your hair on, love. I've got it covered for now.  

**Day 4 09:00**, Alice Marsh and Chinedu Appiah at 27 Spring Terrace:

> Alice Marsh: You're still up for your walk this afternoon, I suppose?  
> Chinedu Appiah: Yes, I'll meet you at the park. Just give me a moment to get ready.  
> *accept by Chinedu Appiah: landed*  

**Day 4 09:30**, Oliver Hughes and Julio Medina at The Half Moon:

> Oliver Hughes: Julio, look, I'm not getting around to updating that specials board until we sort out the Tuesday shift swap. You're still open to it, right?  
> Julio Medina: Oliver, I'm still open to it. Just pick a day that works for you.  
> Oliver Hughes: Saturday's fine. I'll take Saturday. You'll have me, Julio.  
> *promise by Oliver Hughes: landed*  

**Day 4 10:00**, Sarah Pike and Yaw Appiah at Clover Court:

> Sarah Pike: Morning, Yaw. You heading out soon?  
> Yaw Appiah: Morning, Sarah. Aye, I was just thinking of heading out to the Kettle for a coffee.  
> Sarah Pike: Go easy with that coffee. The Kettle's brew is a bit much for some folks.  

**Day 4 10:30**, Isabel García and Wen Fujita at Spring Pharmacy:

> Isabel García: Wen. I've been meaning to speak with you. How are you, love?  
> Wen Fujita: Ah, Isabel. I'm quite well, thank you. And yourself?  
> Isabel García: There's been a lot of folk in here this morning, all with the same need, I'd say.  
> Wen Fujita: Yes, it does seem to be going round. Are you managing, love?  

**Day 4 11:00**, Jakub Sokolov and Lakshmi Iyer at Spring Pharmacy:

> Jakub Sokolov: Haven't we been here for the painkillers every day this week? Honestly though, I'm just here for the knee. Yours, though...?  
> Lakshmi Iyer: Oh, you're one of the regulars, then? I suppose it's a fine excuse for a walk, at least.  
> Jakub Sokolov: Well, I best be off before the knee decides to talk me into a coffee instead.  

**Day 4 11:30**, Henry Hughes and Ibrahim Appiah at Fresh Fare:

> Henry Hughes: You've got time to kill or just shopping?  
> Ibrahim Appiah: Just shopping, love. You?  
> Henry Hughes: Nothing much. Just trying to stretch the week out.  
> Ibrahim Appiah: Well, there you go. Happy stretching.  

**Day 4 12:00**, Sarah Pike and Julia Burton at Fresh Fare:

> Sarah Pike: Julia, would you have a moment? I was just thinking about the bins on Clover Street again—seems like the same old mess.  
> Julia Burton: Bins, you say? I couldn’t tell you—never live that close to Clover Street.  

**Day 4 12:30**, Anna Markovic and Olivia Burton at The Rolling Pin:

> Anna Markovic: I've been meaning to say... that thing I meant to say the other day. It can keep.  
> Olivia Burton: That thing? No rush, Anna. I'm here till four if you need me.  
> Anna Markovic: Same as ever, then.  

**Day 4 13:00**, Simon Talbot and George Fletcher at Spring Pharmacy:

> Simon Talbot: George, I was wondering—have you had a minute to consider if there are more hours I could be covering?  
> George Fletcher: More hours? I don't run this place, Simon. You know that.  

**Day 4 13:30**, Kate Hughes and Rose Grant at Victoria Court:

> Kate Hughes: Rose. That internet, it's working again. I noticed just now.  
> Rose Grant: Well, it's back on now. Don't know what happened.  
> Kate Hughes: Small mercies, then.  

**Day 4 14:00**, Chloe Burton and Óscar Aguilar at St. Anne's School:

> Chloe Burton: Óscar... that history homework. You done it yet?  
> Óscar Aguilar: Nope. Still figuring out who to sit with, remember?  
> Chloe Burton: Let’s not pretend we’re not both stuck on it.  
> Óscar Aguilar: Not really my speed. You done yours?  

**Day 4 14:30**, Will Ward and Henry Hughes at Willow Green:

> Will Ward: Henry, I meant to mention it yesterday. That fault with Northline still hasn't been fixed.  
> Henry Hughes: Heard they're still working on it. Keep your hair on.  
> Will Ward: They’ve had my money for two days. That’s not my habit.  
> Henry Hughes: You’d be better off with a loan from Mariama. She knows how to talk to those people.  
> Will Ward: I don't take charity.  

**Day 4 15:00**, Sunita Agarwal and Ben Carter at Crossroads Service Station:

> Sunita Agarwal: So, you said something on Wednesday. What exactly did you mean?  
> Ben Carter: Ask me tomorrow. Why? You got a problem with it?  
> Sunita Agarwal: Fine. But I was just wondering what you meant by that.  
> Ben Carter: I've got work to do, Sunita. Maybe ask Mahmoud.  

**Day 4 16:00**, Anna Markovic and Andrei Markovic at Clover Court:

> Anna Markovic: Tea sounds nice. Let me wash up first.  
> Andrei Markovic: Of course, dear. I'll be here when you are.  
> Anna Markovic: That thing I meant to say the other day... it can keep, for now.  
> Andrei Markovic: Not my business, but I saw Jennifer out and about. Seems she's taking the first step with that fence.  
> *invite by Anna Markovic: did not land (there is no clover_street_5 to meet at)*  
> *accept by Andrei Markovic: landed*  

**Day 4 16:30**, Kate Hughes and Julio Medina at Victoria Court:

> Kate Hughes: Julio. Small mercies you're still here. I've been trying to catch up with Jia - do you know if she's been passing through this week?  
> Julio Medina: Jia Shin? No name rings a bell. You got a description?  
> Kate Hughes: Short, dark hair. Wears a blue coat. You'd know her, I think.  
> Julio Medina: Haven't seen her. Try the post office, maybe?  

**Day 4 17:00**, Edward Shaw and Paul Shaw at Orchard Mansions:

> Edward Shaw: Paul, I need to get that washing machine fixed. I've been meaning to get on to Northline about it. You had any problems with your stuff?  
> Paul Shaw: I've had my share of trouble with Northline. Best to get on to them quick.  
> Edward Shaw: Tell me about it. I'll give 'em a ring tomorrow, if you've not already.  
> Paul Shaw: Well, I've got my own call to make tomorrow. On you go.  

**Day 4 18:30**, Holly Spencer and Harry Wood at 27 Orchard Lane:

> Holly Spencer: I've got something on my mind, Harry. It's about that loan I took out. I need to pay Claudia back before Friday, and I'm going to have to make it a bit tight to manage it.  
> Harry Wood: Who is she, exactly?  
> Holly Spencer: She’s someone I’ve been drinking with, Harry. Look, I just need to make it tight and sort it out. There we are.  

**Day 4 19:00**, Sanjay Iyer and Lakshmi Iyer at Spring Mansions:

> Sanjay Iyer: You know, the internet's been slow all week. Northline came by this afternoon.  
> Lakshmi Iyer: Yes, it's been a bit sluggish, hasn't it? Northline came this afternoon — there’s some work being done, I imagine.  
> Sanjay Iyer: Should be up to speed by Monday, they said.  

**Day 4 19:30**, Svetlana Nowak and Pavel Nowak at 9 Birch Crescent:

> Svetlana Nowak: Pavel, I need to talk to Alejandra about more hours tomorrow. I'll be fine, I promise.  
> Pavel Nowak: Not my business, but if you need anything else, I'll be here.  

**Day 4 20:00**, Farah Nair and Oliver Hughes at Clover Court:

> Farah Nair: Mr. Hughes, if you don't mind my asking—do you think you might know of any work about? I could do with a few hours a week.  
> Oliver Hughes: You’re asking me about work? Try the diner. Julio’s always short-handed, but it’s on him to say yes.  
> Farah Nair: The diner. Right. Thank you for that.  

**Day 4 20:30**, Lena Petrov and Aarti Sharma at 11 Victoria Place:

> Lena Petrov: That thing you said about the clinic - near enough, I'll go first thing Friday. All in good time.  
> Aarti Sharma: That's the spirit. I'll bring you a coffee to go with your appointment.  
> Lena Petrov: Speaking of Friday, I’ve got the coffee money sorted, if not much else.  
> Aarti Sharma: No bother. I’ll get it sorted. You just take care of that appointment, yes?  
> *promise by Aarti Sharma: landed*  

**Day 4 21:00**, Yolanda García and Leticia García at 31 Spring Terrace:

> Yolanda García: You know, it's been a few days since I had a proper shift. I was thinking of asking around tomorrow.  
> Leticia García: You should start with the school, maybe. That's where most of the parents hang out.  
> Yolanda García: Maybe. I was thinking of the diner too, if the school doesn’t bite.  
> Leticia García: Well, just remember to ask at the diner first — the head chef there always needs extra hands for rush hour.  

**Day 4 21:30**, Mercedes Fuentes and Tara Bhatt at The Rusty Anchor:

> Mercedes Fuentes: Tara. You got that last crate of limes in the back? Honestly though, it's been a long night. Could do with getting it squared away.  
> Tara Bhatt: Aye, I'll get on it. You want it done quick?  
> Mercedes Fuentes: No rush. Just get it in by closing.  

**Day 4 22:00**, Sarah Pike and Elena Espinoza at Clover Court:

> Sarah Pike: Elena, have you seen Claire today? I need to talk to them about the rent and the bins on Clover Street.  
> Elena Espinoza: I saw her text earlier - she's in the city. No idea when she'll be back.  
> Sarah Pike: Well, there you go. I'll try the text again, then.  

**Day 4 22:30**, Nnamdi Achebe and Funmi Achebe at 13 Spring Terrace:

> Nnamdi Achebe: Funmi, I've been meaning to say—your essay for the contest, it's really something. Bless them.  
> Funmi Achebe: Thanks, Dad. I... I might need a bit more time on the internet, if that's okay.  
> Nnamdi Achebe: Just let me know when you need it, love. That'll do.  

**Day 4 23:00**, Chris Parker and Megan Parker at 21 Victoria Place:

> Chris Parker: That’s better, then.  
> Megan Parker: Internet was down again today, but it's back now.  
> Chris Parker: That’s good.  

**Day 4 23:30**, Keith Moore and Beth Moore at Victoria Court:

> Keith Moore: Bless them, it's back on. I suppose we'll see if it stays.  
> Beth Moore: Aye, seems so. Still, I’d not hold my breath.  

**Day 5 00:00**, Abigail Barker and Will Barker at 25 Birch Crescent:

> Abigail Barker: Will, love... you awake?  
> Will Barker: He was at Fresh Fare again yesterday, buying fruit.  
> Abigail Barker: He's been buying a lot of fruit, has he? Doesn't look like much to me.  
> Will Barker: I'll keep an eye out. You and me both, love.  

**Day 5 05:00**, Svetlana Nowak and Pavel Nowak at 9 Birch Crescent:

> Svetlana Nowak: Pavel — I'm sorry. I know you're not my keeper, but I need to talk to Alejandra tomorrow about more hours. I'll be fine, I promise.  
> Pavel Nowak: Give it a week. But if you need anything, you know where to find me.  

### Every contact with a service

**Day 1 07:00**, Rachel Lloyd to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 1 07:30**, Rafael Aguilar to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 1 07:30**, Chloe Rhodes to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 1 08:30**, Rose Grant to `northline` by text:

> Rose Grant: I need to sort out the internet at home, please.  
> northline: I'm sorry about that. I'll raise a fault for your line. We expect it back by tomorrow.  
> *promise: by_day 2, kind internet, what the internet back on by tomorrow*  

**Day 1 09:00**, Adriana Peña to `northline` by text:

> Adriana Peña: The internet at my place went out this morning. Yeah, I'm within the service area. Can we sort it out?  
> northline: I'm sorry about that. I'll raise a fault for your line. We expect it back by tomorrow.  
> *promise: by_day 2, kind internet, what the internet back on by tomorrow*  

**Day 1 09:30**, Wendy Wood to `northline` by text:

> Wendy Wood: I need to speak to someone about the internet at my home on Victoria Place. It's been down since this morning.  
> northline: There's a known fault on Victoria Court; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 2, kind internet, what the internet back on by tomorrow*  

**Day 1 10:00**, Nancy Graham to `northline` by text:

> Nancy Graham: I need to speak to someone about my bill. It's due now.  
> northline: You're right about that bill - it was our mistake, and I've corrected it.  
> *resolve: kind billing, note billing corrected*  

**Day 1 13:00**, Megan Parker to `northline` by text:

> Megan Parker: I've been without internet at my home on 21 Victoria Place since this morning. Can I get this sorted out, please?  
> northline: There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 2, kind internet, what the internet back on by tomorrow*  

**Day 1 14:00**, Oliver Hughes to `northline` by text:

> Oliver Hughes: I need to sort out this bill. It's three times what it should be.  
> northline: You're right about that bill - it was our mistake, and I've corrected it. I'm sorry about that. I'll raise a fault for your line. We expect it back by tomorrow.  
> *resolve: kind billing, note billing corrected*  
> *promise: by_day 2, kind internet, what the internet back on by tomorrow*  

**Day 1 16:30**, Geeta Agarwal to `northline` by text:

> Geeta Agarwal: Hi, my name is Geeta Agarwal and I'm calling about the internet at my house. It's been out for several hours and I was wondering what the problem might be.  
> northline: There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 2, kind internet, what the internet back on by tomorrow*  

**Day 1 17:30**, Neha Joshi to `northline` by text:

> Neha Joshi: I need to know why my bill is $184.60 this month. It was $39 last time.  
> northline: You're right about that bill - it was our mistake, and I've corrected it.  
> *resolve: kind billing, note billing corrected*  

**Day 1 18:00**, Luis Vargas to `northline` by call:

> Luis Vargas: Why did my bill jump to $184.60 this month?  
> northline: You're right about that bill - it was our mistake, and I've corrected it.  
> *resolve: kind billing, note billing corrected*  

**Day 1 18:30**, Ximena Aguilar to `northline` by text:

> Ximena Aguilar: I'm Ximena Aguilar. I'm with Victoria Court. My line's been down since 07:00. Rose Grant already raised a fault with you, but I just wanted to check in myself.  
> northline: There's a known fault on Victoria Court; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 2, kind internet, what the internet back on by tomorrow*  

**Day 1 20:00**, Ellen Spencer to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 1 21:30**, Hugo Aguilar to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 1 22:30**, Abena Eze to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 1 23:30**, Beth Moore to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 1 23:30**, Natalia Kovac to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 2 06:00**, Omar Yousef to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 2 07:00**, Ian Shaw to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 2 08:30**, Tessa Wood to `northline` by text:

> Tessa Wood: I'm experiencing very slow internet at my home in Spring Court — it's been like that since this morning. I need to report the issue.  
> northline: I've booked an engineer to check your line tomorrow at ten.  
> *dispatch: at Day 3 10:00, fixes True, kind internet*  
> *promise: by_day 3, kind internet, what proper speeds by tomorrow*  

**Day 2 09:00**, Kabir Sharma to `northline` by text:

> Kabir Sharma: I need to report a fault. My internet has been very slow since 08:00.  
> northline: I've booked an engineer to check your line tomorrow at ten.  
> *dispatch: at Day 3 10:00, fixes True, kind internet*  
> *promise: by_day 3, kind internet, what proper speeds by tomorrow*  

**Day 2 09:00**, Gary Moore to `northline` by text:

> Gary Moore: I need to speak to someone about my bill, please. It's... it's come in at the wrong amount.  
> northline: You're right about that bill - it was our mistake, and I've corrected it.  
> *resolve: kind billing, note billing corrected*  

**Day 2 10:00**, Oliver Bishop to `northline` by text:

> Oliver Bishop: Hello, my internet at 19 Victoria Place cut out yesterday, and I wanted to know if it was just me or if it's something on your end. I'm Oliver Bishop.  
> northline: There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 3, kind internet, what the internet back on by tomorrow*  

**Day 2 10:30**, Lena Petrov to `northline` by text:

> Lena Petrov: I need to speak about my internet. It went off yesterday and came back on this morning. I'd like to know what's going on with it.  
> northline: There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 3, kind internet, what the internet back on by tomorrow*  

**Day 2 11:00**, Charlie Harper to `northline` by text:

> Charlie Harper: I've got slow internet since this morning. I want to know why.  
> northline: I've booked an engineer to check your line tomorrow at ten.  
> *dispatch: at Day 3 10:00, fixes True, kind internet*  
> *promise: by_day 3, kind internet, what proper speeds by tomorrow*  

**Day 2 11:00**, Will Ward to `northline` by text:

> Will Ward: I need to speak to somebody about my internet. It's been down since yesterday.  
> northline: I'm sorry about that. I'll raise a fault for your line. We expect it back by tomorrow.  
> *promise: by_day 3, kind internet, what the internet back on by tomorrow*  

**Day 2 12:00**, Kwesi Achebe to `northline` by text:

> Kwesi Achebe: I've had very slow internet at my home for the last four hours. I need this sorted before Monday.  
> northline: I've booked an engineer to check your line tomorrow at ten.  
> *dispatch: at Day 3 10:00, fixes True, kind internet*  
> *promise: by_day 3, kind internet, what proper speeds by tomorrow*  

**Day 2 13:30**, Pooja Joshi to `northline` by text:

> Pooja Joshi: My internet's been down all morning.  
> northline: I'm sorry about that. I'll raise a fault for your line. We expect it back by tomorrow.  
> *promise: by_day 3, kind internet, what the internet back on by tomorrow*  

**Day 2 14:30**, Henry Murray to `northline` by text:

> Henry Murray: I need to follow up about the forms I submitted last week. They were supposed to be processed by now.  
> northline: Northline, hello, Henry. What seems to be the trouble?  

**Day 2 16:00**, Agata Kowalski to `northline` by text:

> Agata Kowalski: I need to report a problem with my internet service. It's been extremely slow all day.  
> northline: I've booked an engineer to check your line tomorrow at ten.  
> *dispatch: at Day 3 10:00, fixes True, kind internet*  
> *promise: by_day 3, kind internet, what proper speeds by tomorrow*  

**Day 2 16:00**, Aiko Xu to `northline` by text:

> Aiko Xu: My internet's been crawling since this morning. It's paid for.  
> northline: I've booked an engineer to check your line tomorrow at ten.  
> *dispatch: at Day 3 10:00, fixes True, kind internet*  
> *promise: by_day 3, kind internet, what proper speeds by tomorrow*  

**Day 2 17:00**, Valeria Vega to `northline` by text:

> Valeria Vega: My internet has been very slow since this morning. I'd like to report the issue, please.  
> northline: I've booked an engineer to check your line tomorrow at ten.  
> *dispatch: at Day 3 10:00, fixes True, kind internet*  
> *promise: by_day 3, kind internet, what proper speeds by tomorrow*  

**Day 2 17:30**, Zoe Burton to `northline` by text:

> Zoe Burton: I've been having very slow internet at my place since the morning. I'd like to report that.  
> northline: I've booked an engineer to check your line tomorrow at ten.  
> *dispatch: at Day 3 10:00, fixes True, kind internet*  
> *promise: by_day 3, kind internet, what proper speeds by tomorrow*  

**Day 2 20:30**, Paula Fuentes to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 2 22:30**, Ruth Palmer to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 05:00**, Julia Graham to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 07:00**, Víctor Díaz to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 08:30**, Jakub Sokolov to `northline` by text:

> Jakub Sokolov: Morning. I'm a customer of Valeria Vega's. My internet has been down since yesterday morning, and I was wondering if there's an update on the engineer's visit tomorrow at ten.  
> northline: I've booked an engineer to check your line tomorrow at ten.  
> *dispatch: at Day 4 10:00, fixes True, kind internet*  
> *promise: by_day 4, kind internet, what proper speeds by tomorrow*  

**Day 3 11:30**, Jane Parker to `northline` by text:

> Jane Parker: Hi, I wanted to check if the internet engineer has already visited my address today. I just got back home and the internet seems to be working now. I just wanted to confirm everything's sorted.  
> northline: Northline, hello, Jane. What seems to be the trouble?  

**Day 3 11:30**, Paula Fuentes to `northline` by text:

> Paula Fuentes: I've been having slow internet since yesterday morning. I'd like to report the issue.  
> northline: I've booked an engineer to check your line tomorrow at ten.  
> *dispatch: at Day 4 10:00, fixes True, kind internet*  
> *promise: by_day 4, kind internet, what proper speeds by tomorrow*  

**Day 3 16:00**, Will Ward to `northline` by text:

> Will Ward: It's Will Ward. The internet's still down. It was supposed to be back by tomorrow.  
> northline: I'm sorry about that. I'll raise a fault for your line. And I've put a $10 credit on your account for having to chase us.  
> *credit: amount 10.0, reason for the trouble*  

**Day 3 16:30**, Natalia Kovac to `northline` by text:

> Natalia Kovac: I need to speak to someone about a sudden increase in my bill and very slow internet service. It's urgent.  
> northline: You're right about that bill - it was our mistake, and I've corrected it. I've booked an engineer to check your line tomorrow at ten.  
> *resolve: kind billing, note billing corrected*  
> *dispatch: at Day 4 10:00, fixes True, kind internet*  
> *promise: by_day 4, kind internet, what proper speeds by tomorrow*  

**Day 3 18:00**, Natalia Kovac to `northline` by text:

> Natalia Kovac: I spoke to the engineer. It's a good thing you sorted the bill, but the speed's still slow. It's not fixed yet.  
> northline: You're right about that bill - it was our mistake, and I've corrected it. The engineer's booked for your line; it's on the system. And I've put a $10 credit on your account for having to chase us.  
> *resolve: kind billing, note billing corrected*  
> *credit: amount 10.0, reason for the trouble*  

**Day 3 19:30**, Abena Eze to `northline` by text:

> Abena Eze: Hello, I'm calling about the internet service at 7 Victoria Place. It went off again just now and I wanted to check if there's an issue on your end.  
> northline: There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 4, kind internet, what the internet back on by tomorrow*  

**Day 3 20:00**, Óscar Aguilar to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 20:30**, Ellen Spencer to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 21:00**, Omar Yousef to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 22:00**, Filip Horvat to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 22:00**, Wendy Wood to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 3 23:30**, Sunita Agarwal to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 4 00:30**, Mercedes Fuentes to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 4 13:00**, Charlotte Bishop to `northline` by text:

> Charlotte Bishop: I'd like to report an issue with my internet. It went off yesterday and came back on this morning, but I'd like to make sure it's all sorted.  
> northline: There's a known fault on Victoria Place; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 5, kind internet, what the internet back on by tomorrow*  

**Day 4 16:00**, Dmitri Nowak to `northline` by text:

> Dmitri Nowak: Dmitri Nowak. My internet's still out. I need it fixed.  
> northline: I'm sorry about that. I'll raise a fault for your line. We expect it back by tomorrow.  
> *promise: by_day 5, kind internet, what the internet back on by tomorrow*  

**Day 4 17:30**, Julia Graham to `northline` by text:

> Julia Graham: I need to speak with someone about my internet service. It's been down for two days now.  
> northline: There's a known fault on Clover Court; our engineers are on it. We expect it back by tomorrow.  
> *promise: by_day 5, kind internet, what the internet back on by tomorrow*  

**Day 4 18:00**, Edward Shaw to `northline` by text:

> Edward Shaw: I need to get my washing machine fixed. I've been having internet issues and suspect it's something to do with the line. Let me get that sorted.  
> northline: Northline, hello, Edward. What seems to be the trouble?  

**Day 4 20:30**, Paula Fuentes to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 4 21:00**, Abena Eze to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

**Day 4 22:30**, Ruth Palmer to `northline` by text: got nowhere - they were closed; a recording gave their hours, 08:00-20:00.

### Every refusal, by reason

- 16 x it isn't my shift
- 2 x I had already talked with Lakshmi Iyer today
- 2 x I had already talked with Will Barker today
- 1 x I had already talked with Abigail Barker today
- 1 x I had already talked with Ama Abiola today
- 1 x I had already talked with Ben Carter today
- 1 x I had already talked with Chris Parker today
- 1 x I had already talked with Edward Shaw today
- 1 x I had already talked with Isabel García today
- 1 x I had already talked with Julio Medina today
- 1 x I had already talked with Luke Bishop today
- 1 x I had already talked with Mercedes Fuentes today
- 1 x I had already talked with Rana Jaber today
- 1 x I had already talked with Tara Bhatt today
- 1 x I had already talked with Will Ward today
- 1 x I had already talked with Yaw Appiah today
- 1 x there is no clover_street_5 to meet at
