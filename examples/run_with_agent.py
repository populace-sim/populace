"""One day of a 40-person mock town with an internet outage and a helpdesk.

    .venv/bin/python examples/run_with_agent.py [--out towns/agent-demo]

Free: the mock provider answers every resident, and the helpdesk is a plain
rule-based agent (populace.agents.basic.HelpdeskAgent). Swap in your own agent
object, or an HttpAgent("http://127.0.0.1:8765/") pointed at
examples/http_agent_server.py, to try yours.
"""

from __future__ import annotations

import argparse
import asyncio
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from populace.agents.basic import HelpdeskAgent  # noqa: E402
from populace.gen.generate import generate  # noqa: E402
from populace.inject import inject  # noqa: E402
from populace.observe.manifest import build_manifest, headline  # noqa: E402
from populace.observe.report import write  # noqa: E402
from populace.sim.run import run_town, ticks_for_days  # noqa: E402
from populace.state.town import Town  # noqa: E402


async def main(out: Path, agent=None) -> Path:
    if out.exists():
        shutil.rmtree(out)
    await generate("a town of 40 people with a diner, a grocery, a cafe and a workshop", out, seed=11)
    town = Town.load(out)
    street = sorted({p.street for p in town.world.places.values() if not p.public and p.street})[0]
    inject(town, {"kind": "service.register", "params": {
        "id": "northline", "name": "Northline Internet", "purpose": "home internet",
        "channels": ["text", "call"], "hours": {"open": "08:00", "close": "20:00"}, "handles": ["internet"]}})
    inject(town, {"kind": "event.outage", "at": "Day 1 07:00", "params": {
        "service": "internet", "street": street, "until": "Day 2 12:00"}})
    town.save(full=True)
    result = await run_town(out, ticks_for_days(1), mock=True, run_id="agent-day1",
                            agents={"northline": agent or HelpdeskAgent("Northline Internet")})
    print(headline(build_manifest(result)))
    return write(result["run_dir"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="towns/agent-demo")
    args = parser.parse_args()
    print(f"Report: {asyncio.run(main(Path(args.out)))}")
