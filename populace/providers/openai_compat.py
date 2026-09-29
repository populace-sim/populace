"""One client for every real model: any server that speaks the OpenAI protocol.

Ported from Alive's `providers/openai.py`. It reaches `mlx_lm.server` on this
machine (`populace serve`), llama-server on another machine over the LAN, or
vLLM anywhere, by `base_url`. No API key is ever sent: every endpoint populace
talks to is one the user runs.

The prompt arrives as (system_blocks, messages); the blocks are joined into one
system message in a fixed order, which is what lets the server's prefix cache
reuse the shared rules on every call.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from ..config import Config, RoleConfig
from .base import ModelResult, Provider
from .costs import Usage


def build_messages(
    system_blocks: list[dict[str, Any]], messages: list[dict[str, Any]]
) -> list[dict[str, str]]:
    """Flatten the engine's prompt shape into chat messages."""
    system_text = "\n\n".join(b.get("text", "") for b in system_blocks if b.get("text"))
    out: list[dict[str, str]] = []
    if system_text:
        out.append({"role": "system", "content": system_text})
    for message in messages:
        content = message.get("content")
        if not isinstance(content, str):
            content = "\n".join(
                part.get("text", "") for part in content if isinstance(part, dict)
            )
        role = message.get("role", "user")
        out.append({"role": "assistant" if role == "assistant" else "user", "content": content})
    return out


class OpenAICompatProvider(Provider):
    def __init__(self, config: Config, settings_key: str = "local"):
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:  # pragma: no cover - install-time problem
            raise RuntimeError("the openai package is not installed: pip install openai") from exc
        self.name = settings_key
        settings = config.provider_settings(settings_key)
        base_url = settings.get("base_url")
        if not base_url:
            raise RuntimeError(f"providers.{settings_key}.base_url is not set")
        self.base_url = str(base_url)
        self.client = AsyncOpenAI(
            api_key="not-needed",
            base_url=self.base_url,
            timeout=float(config.engine["request_timeout_s"]),
            max_retries=2,
        )
        # A laptop serves one request at a time: two in flight made each of
        # them four times slower on the M1 in Alive's measurements. A GPU
        # server with parallel slots raises this.
        limit = int(settings.get("max_concurrency", 0) or 0)
        self._gate = asyncio.Semaphore(limit) if limit > 0 else None

    async def complete(self, role: RoleConfig, system_blocks, messages, meta) -> ModelResult:
        if self._gate is None:
            return await self._complete(role, system_blocks, messages)
        queued = time.perf_counter()
        async with self._gate:
            waited = (time.perf_counter() - queued) * 1000
            result = await self._complete(role, system_blocks, messages)
        result.queue_wait_ms = waited
        return result

    async def _complete(self, role: RoleConfig, system_blocks, messages) -> ModelResult:
        started = time.perf_counter()
        try:
            extra = {"extra_body": role.extra_body} if role.extra_body else {}
            response = await self.client.chat.completions.create(
                model=role.model,
                max_tokens=role.max_tokens,
                messages=build_messages(system_blocks, messages),
                **extra,
            )
        except Exception as exc:
            return ModelResult(
                text="",
                latency_ms=(time.perf_counter() - started) * 1000,
                model=role.model,
                error=f"{type(exc).__name__}: {exc}",
            )
        choice = response.choices[0] if response.choices else None
        usage = getattr(response, "usage", None)
        details = getattr(usage, "prompt_tokens_details", None)
        cached = getattr(details, "cached_tokens", 0) or 0
        prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
        return ModelResult(
            text=(choice.message.content or "") if choice else "",
            usage=Usage(
                input_tokens=max(0, prompt_tokens - cached),
                output_tokens=getattr(usage, "completion_tokens", 0) or 0,
                cache_read_tokens=cached,
            ),
            latency_ms=(time.perf_counter() - started) * 1000,
            model=getattr(response, "model", role.model) or role.model,
            request_id=getattr(response, "id", None),
        )

    async def aclose(self) -> None:
        await self.client.close()
