"""A free, deterministic stand-in for the model.

Shape ported from Alive's mock: one RNG per call, keyed on (seed, role,
resident, day, tick, sub-call), so running calls concurrently can never change
what any of them says. Alive's 500 lines of behaviour scripted for one particular street do
not come; behaviour here is generic and lives in role handlers that read only
the small `mock_state` dict the engine attaches to a call's meta. The mock
never parses a prompt.

**It is imperfect on purpose.** A configured share of replies are garbage (not
JSON at all), so the engine's retry, fallback and validation-alarm paths run in
every free test. In Alive nine mock gates never found a name leak, because the
mock never did anything a real model does wrong.

Handlers are registered per role with `@handler(role)`; each takes
`(rng, mock_state, meta)` and returns a Python object (serialised to JSON) or a
string. Modules that own a role register its handler, so the mock grows with
the engine instead of knowing about it.
"""

from __future__ import annotations

import hashlib
import json
import random
from typing import Any, Callable

from ..config import RoleConfig
from .base import ModelResult, Provider
from .costs import Usage

# Replies a model really produces when it goes wrong.
GARBAGE = [
    "I think I'll head over there.",
    '{"action": "move", "target": ',
    "```json\n{\"action\": \"wait\"\n```",
    "Sure! Here is my decision: wait.",
]

Handler = Callable[[random.Random, dict[str, Any], dict[str, Any]], Any]
_HANDLERS: dict[str, Handler] = {}


def handler(role: str) -> Callable[[Handler], Handler]:
    def register(fn: Handler) -> Handler:
        _HANDLERS[role] = fn
        return fn
    return register


def handlers() -> dict[str, Handler]:
    return dict(_HANDLERS)


class MockProvider(Provider):
    name = "mock"

    def __init__(self, seed: int = 0, garbage_rate: float = 0.03):
        self.seed = int(seed)
        self.garbage_rate = float(garbage_rate)

    def rng(self, role: str, meta: dict[str, Any]) -> random.Random:
        key = "|".join(
            str(x)
            for x in (
                self.seed,
                role,
                meta.get("char_id", ""),
                meta.get("day", 0),
                meta.get("tick", 0),
                meta.get("sub_idx", 0),
                meta.get("attempt", 1),
            )
        )
        digest = hashlib.sha256(key.encode()).hexdigest()
        return random.Random(int(digest[:16], 16))

    async def complete(self, role: RoleConfig, system_blocks, messages, meta) -> ModelResult:
        rng = self.rng(role.name, meta)
        state = meta.get("mock_state") or {}
        fn = _HANDLERS.get(role.name)
        # Garbage only where a retry exists to catch it: never on the first
        # attempt of a role that has no handler, and never when told not to.
        allow_garbage = fn is not None and not meta.get("mock_no_garbage")
        if allow_garbage and rng.random() < self.garbage_rate:
            text = rng.choice(GARBAGE)
        elif fn is None:
            text = json.dumps({"note": f"the mock has no behaviour for role {role.name!r}"})
        else:
            reply = fn(rng, state, meta)
            text = reply if isinstance(reply, str) else json.dumps(reply)
        return self._result(role, system_blocks, messages, text)

    @staticmethod
    def _result(role: RoleConfig, system_blocks, messages, text: str) -> ModelResult:
        """Plausible token counts, so the numbers a report prints have a shape."""
        system_chars = sum(len(b.get("text", "")) for b in system_blocks)
        other_chars = sum(len(str(m.get("content", ""))) for m in messages)
        return ModelResult(
            text=text,
            usage=Usage(
                input_tokens=other_chars // 4,
                output_tokens=max(1, len(text) // 4),
                cache_read_tokens=system_chars // 4,
            ),
            latency_ms=0.0,
            model="mock",
        )
