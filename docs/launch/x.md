# X: draft thread

**Not posted. The repo is private until the owner decides.** Numbers only from
computed report sections (sources in [hn.md](hn.md): runs `live-32b-4d-llm` and `live-32b-4d-rules`, quotes from `live-32b-4d`).

---

**1/**
Populace: drop anything into a town of 200 AI people who live for days, remember, talk to each other and react together.

I put two support agents in front of the same town for 4 days. Neither won outright. 🧵

**2/**
You describe a town in one sentence. You get 200 residents with homes, jobs, households, money, needs and people they know.

They only know what they saw, heard or were told. News travels by people talking.

**3/**
The test: an internet provider's helpdesk. Scheduled trouble: an outage, 12 wrong bills, slow internet in 25 homes, the outage coming back.

Same town, same seed, same trouble. Only the helpdesk changed: a simple rule-based bot, or an LLM (Qwen3-32B) with the account on screen.

**4/**
The residents got in touch in their own words:

"Why did my bill jump to $184.60 this month?"

"My line's been down since 07:00. Rose Grant already raised a fault with you, but I just wanted to check in myself."

**5/**
The LLM helpdesk:
+ checked the line and turned away made-up outages ("I can see your line is currently working normally")
+ fixed 7 problems on day 1 vs 4
- broke 6 of 8 promises that fell due (the rules bot: 2 of 30)
- told 6 customers about engineer visits booked for other homes
- invented an excuse: "The engineer ... couldn't make it"

**6/**
Honest limits:
- one run per agent; residents vary between runs
- the LLM helpdesk is a simple prompt on a 32B, not a frontier model or a production agent
- the residents need a ~32B model: a 7B made 0 contacts on 3 separate days

**7/**
Plug in your own agent (any Python object or HTTP endpoint) and run it against the same town. Mock mode is free. MIT.

github.com/populace-sim/populace
