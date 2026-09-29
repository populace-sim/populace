"""Rebuild `tests/fixtures/run_small/`: one mock day of a 12-person town, and
the report it should produce.

    .venv/bin/python tests/fixtures/make_run_small.py            # dry run: say what would change
    .venv/bin/python tests/fixtures/make_run_small.py --write    # replace the fixture

Rebuild it when the engine or the report changes on purpose, read the diff of
`report.md`, and commit both. The prompts and replies are stripped from
`calls.jsonl` to keep the fixture small; nothing in the report reads them.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from populace.gen.generate import generate  # noqa: E402
from populace.observe.manifest import build_manifest  # noqa: E402
from populace.observe.report import render  # noqa: E402
from populace.sim.run import run_town, ticks_for_days  # noqa: E402

DESCRIPTION = "a hamlet of 12 people with a pub, a shop and a cafe"
SEED = 5
TARGET = HERE / "run_small"
KEEP = ("events.jsonl", "decisions.jsonl", "conversations.jsonl", "ticks.jsonl", "names.json", "snapshots",
        "injections.jsonl", "contacts.jsonl")


# A closure, a notice, an outage and a service, so the report's "Injected"
# section is part of the golden copy.
INJECTIONS = [
    {"kind": "service.register", "params": {"id": "northline", "name": "Northline Internet",
                                            "purpose": "home internet", "channels": ["text", "call"],
                                            "handles": ["internet"]}},
    {"kind": "place.close", "at": "Day 1 09:00", "params": {"place": "{cafe}", "days": 2, "reason": "a burst pipe"}},
    {"kind": "event.notice", "at": "Day 1 12:00", "params": {"place": "{bar}", "text": "Quiz night, Friday"}},
    {"kind": "event.outage", "at": "Day 1 07:00", "params": {"service": "internet", "neighbourhood": "{nb}",
                                                             "until": "Day 1 20:00"}},
]


async def build(work: Path) -> Path:
    from populace.inject import inject
    from populace.state.town import Town

    await generate(DESCRIPTION, work / "town", seed=SEED)
    town = Town.load(work / "town")
    nb = sorted({p.neighbourhood for p in town.world.places.values() if not p.public and p.residents_of})[0]
    by_kind = {p.kind: p.id for p in sorted(town.world.places.values(), key=lambda p: p.id) if p.public}
    for raw in INJECTIONS:
        text = json.dumps(raw).replace("{nb}", nb)
        for kind, pid in by_kind.items():
            text = text.replace("{" + kind + "}", pid)
        inject(town, json.loads(text))
    town.save(full=True)
    from populace.agents.basic import HelpdeskAgent
    out = await run_town(work / "town", ticks_for_days(1), mock=True, run_id="small",
                         agents={"northline": HelpdeskAgent("Northline Internet")})
    manifest = build_manifest(out)
    run_dir = Path(out["run_dir"])
    staged = work / "run_small"
    staged.mkdir()
    for name in KEEP:
        src = run_dir / name
        (shutil.copytree if src.is_dir() else shutil.copy2)(src, staged / name)
    calls = [json.loads(l) for l in (run_dir / "calls.jsonl").read_text(encoding="utf-8").splitlines()]
    with open(staged / "calls.jsonl", "w", encoding="utf-8") as f:
        for c in calls:
            c = {k: v for k, v in c.items() if k not in ("prompt", "response", "ts")}
            f.write(json.dumps(c, sort_keys=True) + "\n")
    manifest["wall_s"] = manifest["seconds_per_day"] = 0.0  # wall clock is not reproducible
    manifest["ticks_per_min"] = manifest["minutes_per_day"] = 0.0
    manifest["tick_wall_s"] = {"median": 0.0, "p90": 0.0}
    (staged / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (staged / "report.md").write_text(render(staged), encoding="utf-8")
    return staged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write", action="store_true", help="replace the fixture (default: dry run)")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        staged = asyncio.run(build(Path(tmp)))
        new = (staged / "report.md").read_text(encoding="utf-8")
        old = (TARGET / "report.md").read_text(encoding="utf-8") if (TARGET / "report.md").exists() else ""
        print(f"report.md: {'unchanged' if new == old else f'{len(old.splitlines())} -> {len(new.splitlines())} lines, changed'}")
        if not args.write:
            print("Dry run. Pass --write to replace tests/fixtures/run_small/.")
            return 0
        if TARGET.exists():
            shutil.rmtree(TARGET)
        shutil.copytree(staged, TARGET)
        print(f"Wrote {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
