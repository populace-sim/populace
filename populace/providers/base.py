"""The provider contract. Every model call goes through this shape."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..config import RoleConfig
from .costs import Usage


@dataclass
class ModelResult:
    text: str
    usage: Usage = field(default_factory=Usage)
    latency_ms: float = 0.0
    # How long this call waited for a slot before the backend was asked
    # anything. Kept apart from latency: latency says whether the model is fast
    # enough, the wait says whether the tick is too crowded for it.
    queue_wait_ms: float = 0.0
    model: str = ""
    request_id: str | None = None
    error: str | None = None
    # True when the server's reply carried a usage field; the mock's counts
    # are estimates, and some servers send none.
    usage_reported: bool = False

    @property
    def ok(self) -> bool:
        return self.error is None


class Provider(ABC):
    """A backend that can answer a prompt."""

    name = "base"

    @abstractmethod
    async def complete(
        self,
        role: RoleConfig,
        system_blocks: list[dict[str, Any]],
        messages: list[dict[str, Any]],
        meta: dict[str, Any],
    ) -> ModelResult:
        """Run one completion.

        `system_blocks` are ordered stable-to-volatile so a server's prefix
        cache can reuse them; providers must not reorder or rewrite them.
        """

    async def aclose(self) -> None:  # pragma: no cover - default no-op
        return None
