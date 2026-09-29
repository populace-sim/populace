"""Running a town: build the engine, tick it, report what it cost.

`run_town` is what `populace run` calls. Every tick is saved, so a run can be
stopped at any point and resumed with the same command.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .. import clock
from ..config import Config
from ..observe.telemetry import Telemetry
from ..providers.costs import Meter
from ..providers.runner import ModelRunner
from ..state.town import Town
from . import mockbrain  # noqa: F401  (registers the mock's behaviour)
from ..observe import digest
from ..observe.names import NameBook
from .engine import Engine


def build_engine(town: Town, mock: bool, run_id: str | None = None, seed: int | None = None,
                 garbage_rate: float = 0.03) -> Engine:
    telemetry = Telemetry(town.root, run_id=run_id, town_name=town.name)
    meter = Meter(town.config)
    runner = ModelRunner(town.config, meter, telemetry, mock=mock,
                         seed=town.seed if seed is None else seed, garbage_rate=garbage_rate)
    engine = Engine(town, runner, telemetry)
    if telemetry.enabled:
        NameBook.of(town).save(telemetry.log_dir)
        # A resumed run keeps the start it had.
        digest.write(town, telemetry.log_dir, "start", overwrite=False)
    _wire(engine)
    return engine


def _wire(engine: Engine) -> None:
    """Attach the systems later milestones add, if they are there."""
    try:
        from . import dialogue, phone
        engine.converse = dialogue.converse
        engine.send_texts = phone.send_texts
    except ImportError:
        pass
    try:
        from . import nightly
        engine.night = nightly.night
    except ImportError:
        pass
    from ..inject import apply as INJ
    engine.prompt_extras = lambda r: INJ.prompt_lines(engine, r)
    from ..agents.contact import contact_service
    engine.contact_service = contact_service


async def run_town(
    root: str | Path,
    ticks: int,
    mock: bool = True,
    preset: str | None = None,
    overrides: dict[str, Any] | None = None,
    run_id: str | None = None,
    progress=None,
    agents: dict[str, Any] | None = None,
) -> dict[str, Any]:
    town = Town.load(root, preset=preset, overrides=overrides)
    engine = build_engine(town, mock=mock, run_id=run_id)
    engine.agents = dict(agents or {})
    if engine.agents:
        engine.telemetry.write_json("agents.json", {sid: describe_agent(a) for sid, a in engine.agents.items()})
    started = time.perf_counter()
    reports = []
    try:
        for _ in range(ticks):
            report = await engine.run_tick()
            reports.append(report)
            if progress:
                progress(report)
            if report.stopped:
                break
    finally:
        await engine.runner.aclose()
    wall = time.perf_counter() - started
    return {"town": town, "engine": engine, "reports": reports, "wall_s": wall,
            "run_dir": engine.telemetry.log_dir}


def describe_agent(agent: Any) -> dict[str, Any]:
    """What answered a service, for the report: an agent's own `describe()`
    if it has one, else its class."""
    described = getattr(agent, "describe", None)
    out = {"agent": f"{type(agent).__module__}.{type(agent).__name__}"}
    if callable(described):
        out.update(described())
    return out


def ticks_for_days(days: float) -> int:
    return int(round(days * clock.TICKS_PER_DAY))
