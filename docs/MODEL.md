# The model

What populace runs on, and what a fine-tune would have to show before it
replaced the base model. The fine-tune below is parked.

## What is used today

- **Tests and gates:** the mock provider. No weights, no network.
- **Live checks on the owner's Mac:** the base
  `mlx-community/Qwen2.5-7B-Instruct-4bit` behind `mlx_lm.server`, compact
  prompt profile.
- **Live checks on the PC:** its `llama-server`, reached with `--model-url`,
  when it is up.

## The fine-tune

A LoRA on `Qwen/Qwen2.5-7B-Instruct` trained on Alive's calls (frontier
profile). None of the weights are in any git repository. **It is parked**: on
the same day of the same town it made 0 helpdesk contacts, like the base 7B,
where Qwen3-32B made 14 ([results/pc-32b-day-b.md](results/pc-32b-day-b.md)).
It was trained on a life-sim with no services, so contacting one is not in it.

### It saw name-style ids; populace no longer uses them

Every prompt the fine-tune was trained on listed people by ids made from their
names (`[boyle] ...`, and in populace's first scheme `[mariama_boateng] ...`).
On the first live populace day that shape leaked strangers' names: the model
read "Mariama" out of `[mariama_boateng]` and greeted a stranger by name.
Since step 2's approval, resident ids are opaque (`[r017] a stocky young
woman ...`), made at town creation, and names return only in what people read
(`populace/observe/names.py`).

So the fine-tune would meet an id shape it never saw. **Any eval of it must
compare the fine-tune against the base model on the new id scheme**,
on the same fixture town and ticks, and not rely on any score measured in
Alive. What to look at in particular:

- the share of replies whose `target` is a valid `r###` id rather than a name
  or a name-shaped guess;
- ids spoken aloud in dialogue ("Hey r017");
- names a speaker had no way to know, which should now be zero for both
  models, and any Alive name coming from the weights;
- JSON validity, latency and the voice metrics, as planned.

If the fine-tune does worse than base on targets under the new scheme, that is
a reason to keep base or retrain on regenerated prompts, not to go back to
name-built ids.
