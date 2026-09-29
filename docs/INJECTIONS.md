# Injecting things into a town

An injection is something that happens to a town from outside: a new café, a
price rise, the diner shut for a burst pipe, the internet off on one street, a
notice on a board, rain, a newcomer, a letter, an outside service people can
contact. It changes the world. It never changes a mind.

```bash
.venv/bin/populace inject --kinds                                   # what can be injected
.venv/bin/populace new "a small town of 50 people with a diner, a grocery and a workshop" --seed 3
.venv/bin/populace inject towns/brookhaven --file examples/injections.json   # dry run: check only
.venv/bin/populace inject towns/brookhaven --file examples/injections.json --write
.venv/bin/populace run towns/brookhaven --days 1
.venv/bin/populace report towns/brookhaven/runs/<run_id>                     # see "Injected"
```

From Python:

```python
from populace.inject import inject
inject(town, {"kind": "place.close", "at": "Day 2 07:00",
              "params": {"place": "diner", "days": 3, "reason": "a burst pipe"}})
town.save()
```

## The shape

```json
{"kind": "event.outage", "at": "Day 1 07:00",
 "params": {"service": "internet", "street": "Harbour Way", "until": "Day 2 10:00"}}
```

`at` is `"now"`, `"Day N HH:MM"` or `{"day": N, "time": "HH:MM"}`, and never
in the past. Every injection gets an id made from its content, so the same one
twice is refused.

| Kind | Params | What people perceive |
|---|---|---|
| `place.new` | `name`, `kind`, optional `hours` {open, close}, `things` [{name, price, satiety}], `announce_at` [place ids], `owner`, `sign` | a sign at the announcing places and at the place itself; it joins a resident's places known only once they have seen it |
| `place.price` | `place`, `item`, `price` | new prices, at the place |
| `place.hours` | `place`, `open`, `close` | new hours, at the place |
| `place.close` | `place`, `days` (1-14), `reason` | a sign on the door until it reopens |
| `place.reopen` | `place` | "open again", at the place |
| `event.outage` | `service`, one of `homes` [ids] / `street` / `neighbourhood`, `until` | at each home, to the people who live there; a problem on their record until it ends, then "came back on" |
| `event.weather` | `text`, `until` | everybody up and about, wherever they are |
| `event.notice` | `place`, `text`, optional `until` | a posted notice, at the place |
| `event.arrival` | `name`, `age`, `descriptor`, `host` (a resident) or `home` (a place), optional `hangout`, `money` | a new face; known by name only to the household they stay with |
| `event.letter` | `to`, `from`, `text`, `via` (`letter` or `text`) | a letter waiting at home for that one person, or a text straight to them |
| `service.register` | `id`, `name`, `purpose`, `channels`, optional `hours`, `storefront`, `known_by` (`"everyone"`, a list of ids, or {neighbourhood}) | a "Services you know of" line in the prompts of those who know of it; step 4b lets them contact it |

## How it lands

- **As witnessed events.** Whoever is there, awake, sees it happen and
  remembers it in the ordinary way. Events carry `source: inject:<id>`.
- **As notices.** What stays up (a sign, a board, the weather, a letter) is
  noticed once by each person who comes by while it is up, and goes into their
  own memory as something they noticed.
- **In the prompt**, at most three "what changed" lines, only for what that
  resident has at home or has seen in the last two days, stated as facts.
- **Word of mouth is the residents' own.** Nothing tells anybody to pass it on.
  The report counts conversations where somebody who knew talked to somebody
  who did not and used the injection's own words, labelled as a keyword proxy.

## What is refused

Every refusal is said, with the reason, by the command, in the town's
`world.json` `refused` list, and in the report:

- an unknown kind, place or resident; a time already past; `until` before `at`;
- a closure longer than fourteen days; the same injection twice;
- any free text that names a resident (a stranger would learn the name from
  the sign) - use the id fields meant for people;
- anything that reaches into a mind: phrases like "you feel", "everyone knows",
  "will want to", and fields like `beliefs`, `memory`, `sentiment`, `goal`;
- at the time it falls due, anything that can no longer apply (the place has
  gone, the item is no longer sold).
