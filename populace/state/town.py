"""The town: its world, its residents, and how it is saved.

Ported from Alive's `persistence.py` (`GameState`, `Meta`, atomic writes,
nightly snapshots), without the step that re-applied one particular street to
every world on load.

**Saves scale.** Alive rewrote every character file every tick, which at 200
residents of 50-100 KB each is 10-20 MB a tick. Here anything that changes a
resident calls `town.touch(id)`, a tick saves only those residents plus the
world and meta, and the night saves everything.

A town directory:

    town.json            the spec it was generated from, and its seed
    config.json          preset and overrides
    world.json           places, positions, clock
    residents/<id>.json  one per resident
    saves/meta.json      counters and whatever the engine carries between ticks
    saves/day_NN/        a full copy at the end of each day
    runs/<run_id>/       logs, one directory per run
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .. import clock
from ..config import Config
from ..sim.events import NameIndex
from .place import World
from .resident import Resident

SCHEMA_VERSION = 1


class StateError(Exception):
    pass


def atomic_write_json(path: Path, data: Any) -> None:
    """Write via a temp file and os.replace, so a reader never sees half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def read_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@dataclass
class Meta:
    schema_version: int = SCHEMA_VERSION
    ticks_run: int = 0
    model_calls: int = 0
    runs: list[dict[str, Any]] = field(default_factory=list)
    # In-flight engine state that must survive a stop and resume mid-day.
    engine_carry: dict[str, Any] = field(default_factory=dict)
    injections: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(d: dict) -> "Meta":
        return Meta(
            schema_version=int(d.get("schema_version", SCHEMA_VERSION)),
            ticks_run=int(d.get("ticks_run", 0)), model_calls=int(d.get("model_calls", 0)),
            runs=list(d.get("runs", [])), engine_carry=dict(d.get("engine_carry", {})),
            injections=dict(d.get("injections", {})),
        )

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version, "ticks_run": self.ticks_run,
            "model_calls": self.model_calls, "runs": list(self.runs),
            "engine_carry": self.engine_carry, "injections": self.injections,
        }


class Town:
    """Everything that is true about one town at one moment."""

    def __init__(
        self,
        spec: dict[str, Any],
        world: World,
        residents: dict[str, Resident],
        config: Config,
        meta: Meta | None = None,
        root: Path | None = None,
    ):
        self.spec = spec
        self.world = world
        self.residents = residents
        self.config = config
        self.meta = meta or Meta()
        self.root = Path(root) if root else None
        self.names = NameIndex((r.id, r.name) for r in residents.values())
        self.dirty: set[str] = set()
        # Outside services residents can contact, registered by injection and
        # saved with the world.
        self.services: dict[str, Any] = world.services

    # -- queries ---------------------------------------------------------------

    @property
    def name(self) -> str:
        return str(self.spec.get("name", "Town"))

    @property
    def seed(self) -> int:
        return int(self.spec.get("seed", 0))

    def present(self) -> list[Resident]:
        """Residents still in town, in id order."""
        return [self.residents[k] for k in sorted(self.residents)
                if not self.residents[k].away]

    def secrets(self) -> dict[str, str]:
        return {rid: r.secret for rid, r in self.residents.items() if r.secret}

    def touch(self, resident_id: str) -> None:
        self.dirty.add(resident_id)

    def reindex_names(self) -> None:
        self.names.rebuild((r.id, r.name) for r in self.residents.values())

    def validate(self) -> list[str]:
        problems = self.world.validate()
        place_ids = set(self.world.places)
        resident_ids = set(self.residents)
        need_kinds = set(self.config.needs["kinds"])
        for rid in sorted(self.residents):
            problems += self.residents[rid].validate(place_ids, resident_ids, need_kinds)
            if rid not in self.world.positions and not self.residents[rid].away:
                problems.append(f"{rid} is not placed anywhere")
        for place in self.world.places.values():
            for rid in [place.owner, *place.hires]:
                if rid and rid not in resident_ids:
                    problems.append(f"{place.id}: owner or hirer {rid!r} is not a resident")
        return problems

    # -- saving ----------------------------------------------------------------------

    def save(self, root: str | Path | None = None, full: bool = False) -> Path:
        root = Path(root) if root else self.root
        if root is None:
            raise StateError("this town has no directory yet; pass one to save()")
        self.root = root
        atomic_write_json(root / "town.json", {"schema_version": SCHEMA_VERSION, **self.spec})
        atomic_write_json(root / "config.json", self.config.to_dict())
        atomic_write_json(root / "world.json", self.world.to_dict())
        atomic_write_json(root / "saves" / "meta.json", self.meta.to_dict())
        ids = sorted(self.residents) if full else sorted(self.dirty)
        for rid in ids:
            if rid in self.residents:
                atomic_write_json(root / "residents" / f"{rid}.json",
                                  self.residents[rid].to_dict())
        self.dirty.clear()
        return root

    def snapshot_day(self, day: int) -> Path:
        """A full copy of the town as it stood at the end of a day."""
        self.save(full=True)
        assert self.root is not None
        dest = self.root / "saves" / f"day_{day:02d}"
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        shutil.copy2(self.root / "world.json", dest / "world.json")
        shutil.copytree(self.root / "residents", dest / "residents")
        return dest

    @classmethod
    def load(cls, root: str | Path, preset: str | None = None,
             overrides: dict[str, Any] | None = None) -> "Town":
        root = Path(root)
        if not (root / "world.json").exists():
            raise StateError(f"no town in {root}: run `populace new` first")
        spec = read_json(root / "town.json")
        spec.pop("schema_version", None)
        config = (Config.load(root / "config.json", preset, overrides)
                  if (root / "config.json").exists() else Config.build(preset, overrides))
        clock.configure(**config.clock)
        world = World.from_dict(read_json(root / "world.json"))
        residents = {}
        for path in sorted((root / "residents").glob("*.json")):
            r = Resident.from_dict(read_json(path))
            residents[r.id] = r
        meta_path = root / "saves" / "meta.json"
        meta = Meta.from_dict(read_json(meta_path)) if meta_path.exists() else Meta()
        return cls(spec, world, residents, config, meta, root)
