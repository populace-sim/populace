"""The bundled generation data, loaded once."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=None)
def load(name: str) -> dict[str, Any]:
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def names(culture: str) -> dict[str, list[str]]:
    return json.loads((DATA / "names" / f"{culture}.json").read_text(encoding="utf-8"))


def cultures() -> list[str]:
    return sorted(p.stem for p in (DATA / "names").glob("*.json"))


def kinds() -> dict[str, dict[str, Any]]:
    return load("place_kinds")["kinds"]


def composites() -> dict[str, list[str]]:
    return load("place_kinds")["composites"]
