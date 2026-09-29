"""`populace prompt-stats`: how big each part of a decision prompt is, measured.

Tokens are estimated at four characters each, which is what the engine's own
budget uses. The shared rules block is paid for once per server cache; the
character and dynamic blocks are paid for on every call, and on a laptop they
are what decides the seconds.
"""

from __future__ import annotations

from statistics import median

from ..state.town import Town
from .blocks import build_decision_prompt, shared_block


def measure(town: Town, sample: int | None = None) -> dict:
    ids = sorted(town.residents)
    if sample:
        ids = ids[:: max(1, len(ids) // sample)][:sample]
    char, dyn = [], []
    for rid in ids:
        system, messages, _ = build_decision_prompt(town.residents[rid], town, [])
        char.append(len(system[1]["text"]) // 4)
        dyn.append(len(messages[0]["content"]) // 4)
    return {
        "profile": town.config.prompt.get("profile"),
        "shared_rules_tokens": len(shared_block(town)) // 4,
        "character_tokens": {"min": min(char), "median": int(median(char)), "max": max(char)},
        "dynamic_tokens": {"min": min(dyn), "median": int(median(dyn)), "max": max(dyn)},
        "residents_measured": len(ids),
    }
