"""The mock gate: a town run twice must come out the same, and must do things.

Generates a town from one sentence and one seed, twice, in two directories;
runs each for the same number of days in mock; and checks:

1. **Determinism.** The two runs' events, conversations, and final residents
   are byte-identical. A mock that is not deterministic cannot tell a change
   in the engine from noise.
2. **Required kinds.** Every event kind a town is supposed to produce happened
   at least once. A check that has never fired is not a passing check, so the
   gate also reports how many of each it saw.
3. **Budget.** No tick spent more calls than its budget plus its retries.

`tests/test_gate.py` runs the gate on a deliberately broken run and watches
each check fail.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Callable

from ..gen.generate import generate
from .run import run_town, ticks_for_days

DEFAULT_DESCRIPTION = "a small town of 50 people with a diner, a grocery, a cafe and a workshop"

# Each entry is a set: any one of its kinds satisfies it.
REQUIRED: list[tuple[str, ...]] = [
    ("conversation",), ("wage",), ("buy",), ("rent_paid",), ("hired",), ("fired", "quit"),
    ("loan",), ("repay",), ("promise",), ("promise_kept", "promise_broken"), ("invite",),
    ("together",), ("text_sent",), ("refused",), ("sleep",), ("arrive",),
    # Step 4: an outage lands, people notice it, and somebody contacts the service.
    ("changed",), ("noticed",), ("contact",),
]


def _set_up_outside(town_dir: Path) -> dict:
    """A helpdesk and an outage on one street, the same for both runs."""
    from ..agents.basic import HelpdeskAgent
    from ..inject import inject
    from ..state.town import Town

    town = Town.load(town_dir)
    street = sorted({p.street for p in town.world.places.values() if not p.public and p.street})[0]
    inject(town, {"kind": "service.register", "params": {
        "id": "helpline", "name": "Town Helpline", "purpose": "home internet",
        "channels": ["text", "call"], "handles": ["internet"]}})
    inject(town, {"kind": "event.outage", "at": "Day 1 07:00", "params": {
        "service": "internet", "street": street, "until": "Day 3 12:00"}})
    town.save(full=True)
    return {"helpline": HelpdeskAgent("Town Helpline")}


def _digest(run_dir: Path, town_dir: Path) -> dict[str, str]:
    out = {}
    for name in ("events.jsonl", "conversations.jsonl"):
        path = run_dir / name
        out[name] = hashlib.sha256(path.read_bytes() if path.exists() else b"").hexdigest()
    residents = hashlib.sha256()
    for path in sorted((town_dir / "residents").glob("*.json")):
        residents.update(path.read_bytes())
    out["residents"] = residents.hexdigest()
    return out


async def run_gate(description: str = DEFAULT_DESCRIPTION, seed: int = 7, days: float = 7,
                   workdir: Path | None = None, mutate: Callable[[Path, Path], None] | None = None,
                   second_seed: int | None = None) -> dict[str, Any]:
    """Run the gate. `mutate(run_dir, town_dir)` and `second_seed` exist so the
    tests can break a run on purpose and watch the gate notice."""
    base = Path(workdir or tempfile.mkdtemp(prefix="populace-gate-"))
    runs = []
    for label, s in (("a", seed), ("b", seed if second_seed is None else second_seed)):
        town_dir = base / label
        if town_dir.exists():
            shutil.rmtree(town_dir)
        await generate(description, town_dir, seed=s)
        agents = _set_up_outside(town_dir)
        out = await run_town(town_dir, ticks_for_days(days), mock=True, run_id="gate", agents=agents)
        if mutate and label == "a":
            mutate(out["run_dir"], town_dir)
        runs.append((out, town_dir))
    (a, a_dir), (b, b_dir) = runs
    digest_a, digest_b = _digest(a["run_dir"], a_dir), _digest(b["run_dir"], b_dir)
    events = [json.loads(l) for l in open(a["run_dir"] / "events.jsonl", encoding="utf-8")]
    counts = Counter(e["kind"] for e in events)
    missing = [" or ".join(group) for group in REQUIRED if not any(counts.get(k) for k in group)]
    over_budget = [r.to_dict() for r in a["reports"] if r.calls > r.budget + r.retries]
    stopped = a["reports"][-1].stopped if a["reports"] else "no ticks ran"
    failures = []
    if digest_a != digest_b:
        failures.append("the two runs differ: " + ", ".join(k for k in digest_a if digest_a[k] != digest_b[k]))
    if missing:
        failures.append("never happened: " + ", ".join(missing))
    if over_budget:
        failures.append(f"{len(over_budget)} ticks spent more than their budget")
    if stopped:
        failures.append(f"the run stopped: {stopped}")
    return {
        "passed": not failures, "failures": failures, "days": days, "seed": seed,
        "description": description, "events": len(events),
        "kinds": {" or ".join(g): sum(counts.get(k, 0) for k in g) for g in REQUIRED},
        "signature": digest_a["events.jsonl"][:16], "workdir": str(base),
        "wall_s": round(a["wall_s"] + b["wall_s"], 1),
    }
