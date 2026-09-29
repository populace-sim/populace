"""A compact picture of a town at one moment, for the report's "what changed".

A run writes one at its start (`snapshots/start.json`) and one each night
(`snapshots/day_NN.json`). The town's own `saves/` keep full copies for
resuming; these keep only what a reader would ask about, so a report can diff
two of them without loading a town: money, work, where people are, how they
stand with each other, what they have come to believe, and where their lives
are heading.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from ..state.town import Town


def resident_digest(r, town: "Town") -> dict[str, Any]:
    return {
        "name": r.name,
        "money": round(float(r.money), 2),
        "job": ({"workplace": r.job.workplace, "title": r.job.title, "employer": r.job.employer_id}
                if r.job else None),
        "at": town.world.location_of(r.id),
        # Who owes whom, so a claim about money can be checked against it.
        "owes": [{"to": o.get("to"), "amount": o.get("amount"), "kind": o.get("kind")}
                 for o in (r.obligations or {}).get("owes", [])],
        "rent": ({"landlord": r.rent.get("landlord_id"), "amount": r.rent.get("amount"),
                  "owed": r.rent.get("owed", 0)} if r.rent else None),
        "home": r.home,
        "household": r.household,
        "gone": bool(r.away and r.away.get("kind") == "gone"),
        "arc": {k: (r.arc or {}).get(k) for k in ("stage", "goal", "leave_day")},
        "names_known": {rid: v.get("day", 0) for rid, v in sorted(r.names_known.items())},
        "ties": {
            rid: {"stage": rel.stage, "sentiment": rel.sentiment, "trust": rel.trust,
                  "label": rel.label, "number": rel.number_shared}
            for rid, rel in sorted(r.relationships.items())
        },
        "beliefs": [m.text for m in r.memory if m.kind == "belief"],
        "problems": [{k: p.get(k) for k in ("kind", "inj", "since", "resolved", "resolved_at", "resolved_by", "text")}
                     | {"reported_by": (p.get("reported") or {}).get("by")} for p in r.problems],
        "goals": list(r.goals_active),
    }


def town_digest(town: "Town") -> dict[str, Any]:
    world = town.world
    return {
        "town": town.name,
        "day": world.time.day,
        "tick": world.time.tick,
        "residents": {rid: resident_digest(r, town) for rid, r in sorted(town.residents.items())},
        "places": {
            pid: {"name": p.name, "kind": p.kind, "public": p.public, "owner": p.owner,
                  "hires": list(p.hires), "staff": list(p.workplace_of),
                  "residents": list(p.residents_of)}
            for pid, p in sorted(world.places.items())
        },
    }


def write(town: "Town", run_dir: str | Path, name: str, overwrite: bool = True) -> Path:
    path = Path(run_dir) / "snapshots" / f"{name}.json"
    if path.exists() and not overwrite:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(town_digest(town), sort_keys=True, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    return path


def load(run_dir: str | Path, name: str) -> dict[str, Any] | None:
    path = Path(run_dir) / "snapshots" / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def latest(run_dir: str | Path) -> dict[str, Any] | None:
    days = sorted((Path(run_dir) / "snapshots").glob("day_*.json"))
    return json.loads(days[-1].read_text(encoding="utf-8")) if days else None
