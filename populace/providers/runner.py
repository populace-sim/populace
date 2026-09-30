"""Every model call goes through `ModelRunner.call`.

Ported from Alive's `providers/__init__.py`: resolve the role to a provider,
hold a global concurrency slot, make the call, turn any exception into an error
result (a dead call must not kill the tick), feed the two alarms, count it, and
log it with its full prompt. The system half is logged once per distinct
prefix, under the hash the call record cites.
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from typing import Any

from ..config import Config
from ..observe.telemetry import Telemetry
from .openai_compat import redact
from .base import ModelResult, Provider
from .costs import Meter
from .mock import MockProvider


def build_provider(name: str, config: Config) -> Provider:
    if name == "mock":
        return MockProvider()
    # Every other provider name is an OpenAI-compatible endpoint in `providers`.
    from .openai_compat import OpenAICompatProvider

    if name not in config.raw.get("providers", {}):
        raise RuntimeError(
            f"no provider {name!r} in config; the configured ones are "
            f"{', '.join(config.raw.get('providers', {})) or 'none'}"
        )
    return OpenAICompatProvider(config, settings_key=name)


class ModelRunner:
    def __init__(
        self,
        config: Config,
        meter: Meter,
        telemetry: Telemetry,
        mock: bool = False,
        seed: int = 0,
        garbage_rate: float = 0.03,
    ):
        self.config = config
        self.meter = meter
        self.telemetry = telemetry
        self.mock = mock
        self._providers: dict[str, Provider] = {}
        self._semaphore = asyncio.Semaphore(int(config.engine["concurrency"]))
        if mock:
            self._providers["mock"] = MockProvider(seed=seed, garbage_rate=garbage_rate)

    def provider_for(self, provider_name: str) -> Provider:
        if self.mock:
            return self._providers["mock"]
        if provider_name not in self._providers:
            self._providers[provider_name] = build_provider(provider_name, self.config)
        return self._providers[provider_name]

    async def call(
        self,
        role_name: str,
        system_blocks: list[dict[str, Any]],
        messages: list[dict[str, Any]],
        meta: dict[str, Any] | None = None,
    ) -> ModelResult:
        role = self.config.role(role_name)
        meta = dict(meta or {})
        provider = self.provider_for(role.provider)
        started = time.perf_counter()
        async with self._semaphore:
            try:
                result = await provider.complete(role, system_blocks, messages, meta)
            except Exception as exc:  # a dead call must not kill the tick
                result = ModelResult(
                    text="",
                    latency_ms=(time.perf_counter() - started) * 1000,
                    model=role.model,
                    error=f"{type(exc).__name__}: {exc}",
                )
        if not result.latency_ms:
            result.latency_ms = (time.perf_counter() - started) * 1000

        self.meter.record(role_name, result.usage, ok=result.ok)
        system_text = "".join(b.get("text", "") for b in system_blocks)
        system_hash = hashlib.sha256(system_text.encode()).hexdigest()[:12]
        self.telemetry.log_system(system_hash, system_blocks)
        self.telemetry.log_call(
            {
                "ts": time.time(),
                "day": meta.get("day"),
                "tick": meta.get("tick"),
                "role": role_name,
                "char_id": meta.get("char_id"),
                "call_id": meta.get("call_id"),
                "provider": provider.name,
                "model": result.model or role.model,
                "attempt": meta.get("attempt", 1),
                "latency_ms": round(result.latency_ms, 1),
                "queue_wait_ms": round(result.queue_wait_ms, 1),
                **result.usage.to_dict(),
                "usage_reported": result.usage_reported,
                "system_hash": system_hash,
                "system_tokens_est": len(system_text) // 4,
                "prompt": messages,
                "response": redact(result.text),
                "request_id": result.request_id,
                "error": redact(result.error) if result.error else None,
            }
        )
        # Last, so the failed call is on disk before the alarm stops the run.
        self.meter.note_transport(result.ok, provider.name)
        return result

    async def aclose(self) -> None:
        for provider in self._providers.values():
            await provider.aclose()
