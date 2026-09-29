"""One call from a sentence to a saved town.

    spec (rules, or the model with the rules as fallback)
      -> skeleton (seeded, procedural)
      -> enrichment (persona prose, batched, cached, validated)
      -> locality (circles, places known, names from the circle only)
      -> validation (a town that does not validate is not saved)
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from ..config import Config
from ..observe.telemetry import Telemetry
from ..providers.costs import Meter
from ..providers.runner import ModelRunner
from ..state import locality
from ..state.town import Town
from . import enrich as E
from . import skeleton
from .spec import TownSpec, parse_description, spec_from_model


class GenerationError(Exception):
    pass


async def generate(
    description: str,
    out: str | Path,
    seed: int = 0,
    mock: bool = True,
    config: Config | None = None,
    overrides: dict[str, Any] | None = None,
    use_model_for_spec: bool = False,
    progress=None,
) -> tuple[Town, dict[str, Any]]:
    out = Path(out)
    config = config or Config.build()
    telemetry = Telemetry(out, run_id="generate", town_name="")
    meter = Meter(config)
    runner = ModelRunner(config, meter, telemetry, mock=mock, seed=seed)
    started = time.perf_counter()
    try:
        if use_model_for_spec:
            spec = await spec_from_model(description, seed, runner, overrides)
        else:
            spec = parse_description(description, seed, overrides)
        telemetry.town_name = spec.name
        town = skeleton.build(spec, config)
        town.root = out
        locality.refresh(town)
        counts = await E.enrich(town, runner, cache_dir=out / "cache" / "enrich",
                                on_batch=progress)
        locality.refresh(town)
        locality.seed_acquaintance(town)
        # Stages otherwise catch up only at night, and day one's prompts
        # would describe a partner as somebody who knows your face.
        from ..sim.reflection import settle_stages
        for r in town.residents.values():
            settle_stages(r, town)
    finally:
        await runner.aclose()
    problems = town.validate()
    if problems:
        raise GenerationError("the generated town does not validate:\n  " + "\n  ".join(problems[:20]))
    town.save(out, full=True)
    report = {
        "town": town.name,
        "population": len(town.residents),
        "dependents": sum(len(h.get("dependents", [])) for h in town.world.households.values()),
        "households": len(town.world.households),
        "places": len(town.world.places),
        "spec_source": spec.source,
        "persona_sources": counts,
        "model_calls": meter.calls_total,
        "seconds": round(time.perf_counter() - started, 1),
        "mock": mock,
    }
    telemetry.write_json("generation.json", report)
    return town, report


def spec_only(description: str, seed: int = 0, overrides: dict[str, Any] | None = None) -> TownSpec:
    return parse_description(description, seed, overrides)
