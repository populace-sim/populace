"""The run manifest: the numbers a run can be held to, all from telemetry.

Nothing here is estimated. Wall clock, calls, residents thinking and JSON
validity are counted off the tick reports and the call log of the run itself,
and the preset is recorded so a low-fidelity run is never mistaken for a full
one.
"""

from __future__ import annotations

import json
from statistics import median
from typing import Any

from .. import clock
from ..clock import tick_to_hhmm
from ..config import LOW_FIDELITY_PRESETS


def build_manifest(out: dict[str, Any]) -> dict[str, Any]:
    reports = out["reports"]
    town = out["town"]
    engine = out["engine"]
    run_dir = out["run_dir"]
    calls = []
    calls_path = run_dir / "calls.jsonl"
    if calls_path.exists():
        calls = [json.loads(l) for l in open(calls_path, encoding="utf-8")]
    decisions = [c for c in calls if c["role"] == "npc_decision"]
    firsts = [c for c in decisions if c["attempt"] == 1]
    ticks = len(reports)
    wall = float(out["wall_s"])
    by_role: dict[str, int] = {}
    for c in calls:
        by_role[c["role"]] = by_role.get(c["role"], 0) + 1
    latencies = [c["latency_ms"] for c in calls if not c.get("error")]
    tick_walls = [r.wall_ms / 1000 for r in reports]
    thinking = [r.residents_thinking for r in reports]
    manifest = {
        "town": town.name,
        "residents": len(town.residents),
        "preset": town.config.preset,
        "low_fidelity": town.config.preset in LOW_FIDELITY_PRESETS,
        "profile": town.config.prompt.get("profile"),
        "mock": engine.runner.mock,
        "model": sorted({c["model"] for c in calls}) if calls else [],
        "from": f"Day {reports[0].day} {tick_to_hhmm(reports[0].tick)}" if reports else None,
        "ticks": ticks,
        "wall_s": round(wall, 1),
        "ticks_per_min": round(ticks / (wall / 60), 2) if wall else None,
        "minutes_per_day": round(wall / 60 / ticks * clock.TICKS_PER_DAY, 2) if ticks else None,
        "seconds_per_day": round(wall / ticks * clock.TICKS_PER_DAY, 1) if ticks else None,
        "tick_wall_s": {"median": round(median(tick_walls), 2) if tick_walls else 0,
                        "p90": round(sorted(tick_walls)[int(0.9 * (len(tick_walls) - 1))], 2) if tick_walls else 0},
        "budget_per_tick": reports[0].budget if reports else None,
        "calls": {
            "total": len(calls),
            "per_tick": round(len(calls) / ticks, 2) if ticks else 0,
            "per_tick_max": max((r.calls for r in reports), default=0),
            "over_budget_ticks": sum(1 for r in reports if r.calls > r.budget + r.retries),
            "by_role": by_role,
            "errors": sum(1 for c in calls if c.get("error")),
            "latency_s": {"median": round(median(latencies) / 1000, 2) if latencies else 0,
                          "p90": round(sorted(latencies)[int(0.9 * (len(latencies) - 1))] / 1000, 2)
                          if latencies else 0},
            "cache_read_share": round(sum(c.get("cache_read_tokens", 0) for c in calls) /
                                      max(1, sum(c.get("cache_read_tokens", 0) + c.get("input_tokens", 0)
                                                 for c in calls)), 3),
        },
        "tokens": _tokens(calls),
        "agent_calls": _agent_tokens(run_dir),
        "residents_thinking_per_tick": {"mean": round(sum(thinking) / ticks, 2) if ticks else 0,
                                        "max": max(thinking, default=0)},
        "distinct_residents_who_thought": len({c["char_id"] for c in decisions}),
        "decisions": {
            "made": sum(thinking),
            "json_valid_first_try_pct": round(100 * sum(r.json_first_try for r in reports) /
                                              max(1, len(firsts)), 1),
            "retries": sum(r.retries for r in reports),
            "fallbacks": sum(r.fallbacks for r in reports),
        },
        "free_actions": {"intent": sum(r.intent_actions for r in reports),
                         "schedule": sum(r.schedule_actions for r in reports)},
        "events": sum(r.events for r in reports),
        "refusals": sum(r.refusals for r in reports),
        "conversations": sum(r.conversations for r in reports),
        "lines": sum(r.lines for r in reports),
        "texts": sum(r.texts for r in reports),
        "stopped": reports[-1].stopped if reports else None,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    # The realism flags, counted, so a run's summary says whether to look.
    from . import flags as F
    from .report import load
    manifest["flags"] = {name: len(found) for name, found in F.run_all(load(run_dir)["run"]).items()}
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def _tokens(calls: list[dict[str, Any]]) -> dict[str, Any]:
    """What the model server said the run used, from each reply's usage field.
    Calls whose reply had none (the mock's are estimates) are counted apart."""
    reported = [c for c in calls if c.get("usage_reported")]
    return {
        "calls_with_usage": len(reported),
        "calls_without_usage": len(calls) - len(reported),
        "in": sum(c.get("input_tokens", 0) + c.get("cache_read_tokens", 0) + c.get("cache_write_tokens", 0)
                  for c in reported),
        "in_from_cache": sum(c.get("cache_read_tokens", 0) for c in reported),
        "out": sum(c.get("output_tokens", 0) for c in reported),
    }


def _agent_tokens(run_dir) -> dict[str, Any] | None:
    """An agent's own model calls, if it logged them (`ctx.log`)."""
    path = run_dir / "agent_calls.jsonl"
    if not path.exists():
        return None
    calls = [c for line in open(path, encoding="utf-8") if line.strip()
             for c in json.loads(line).get("calls", [])]
    reported = [c for c in calls if c.get("usage_reported", c.get("tokens_in", 0) > 0)]
    return {"calls": len(calls), "calls_with_usage": len(reported),
            "in": sum(c.get("tokens_in", 0) for c in reported),
            "out": sum(c.get("tokens_out", 0) for c in reported)}


def usage_line(m: dict[str, Any]) -> str:
    """What a run cost, in model calls and tokens, printed at the end of every run."""
    t = m.get("tokens") or {}
    calls = (m.get("calls") or {}).get("total", 0)
    if m.get("mock"):
        out = f"Model use: mock, no model called ({calls} mock calls; the mock's token counts are estimates, not shown)."
    elif not t.get("calls_with_usage"):
        out = f"Model use: {calls} calls; the server reported no token usage."
    else:
        out = (f"Model use: {calls} calls; tokens in {t['in']:,} (of them {t['in_from_cache']:,} from the "
               f"prompt cache), out {t['out']:,}"
               + (f"; {t['calls_without_usage']} calls reported no usage" if t.get("calls_without_usage") else "")
               + ".")
    a = m.get("agent_calls")
    if a and a.get("calls"):
        out += (f" The agent's own model: {a['calls']} calls"
                + (f", tokens in {a['in']:,}, out {a['out']:,}" if a.get("calls_with_usage") else ", no usage reported")
                + ".")
    return out


def headline(m: dict[str, Any]) -> str:
    fid = " LOW FIDELITY" if m["low_fidelity"] else ""
    return (f"{m['town']}: {m['residents']} residents, {m['ticks']} ticks in {m['wall_s']} s "
            f"({m['ticks_per_min']} ticks/min, "
            + (f"{m['minutes_per_day']} min" if m['minutes_per_day'] >= 1 else f"{m['seconds_per_day']} s")
            + " per in-game day), "
            f"preset {m['preset']}{fid}, {'mock' if m['mock'] else ', '.join(m['model'])}. "
            f"{m['calls']['per_tick']} calls/tick (budget {m['budget_per_tick']}), "
            f"{m['residents_thinking_per_tick']['mean']} residents thinking per tick, "
            f"{m['distinct_residents_who_thought']} distinct thinkers, "
            f"JSON valid first try {m['decisions']['json_valid_first_try_pct']}%, "
            f"{m['conversations']} conversations, {m['refusals']} refusals."
            + (" Flags: " + ", ".join(f"{k} {v}" for k, v in m["flags"].items() if v) + "."
               if any((m.get("flags") or {}).values()) else ""))
