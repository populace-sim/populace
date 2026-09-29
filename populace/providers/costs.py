"""Counting calls and tokens, and the two alarms that stop a run.

Ported from Alive's `costs.py` without the money: populace has no paid
provider, so there is no cap and no spend ledger. What stays is what the money
was never the point of:

* **`ValidationAlarm`**: too many malformed replies in a row window is a prompt
  regression, not bad luck.
* **`ProviderDown`**: a *run* of transport failures on one provider means the
  server has gone. In Alive a run carried on for four in-game days after its
  provider stopped answering, every resident on their schedule and nobody
  saying a word, and the transcript ended looking finished. Counted per
  provider, because a success on one backend says nothing about another.
"""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass

from ..config import Config


class RunStopped(Exception):
    """The run stopped itself. State is saved; the reason is in the message."""


class ValidationAlarm(RunStopped):
    """Too many malformed model responses: a prompt regression, not bad luck."""


class ProviderDown(RunStopped):
    """Every call to one provider is failing on the wire. The server is gone."""


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    @property
    def total_input(self) -> int:
        return self.input_tokens + self.cache_read_tokens + self.cache_write_tokens

    def to_dict(self) -> dict:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_write_tokens": self.cache_write_tokens,
        }


class Meter:
    """Counts every call, by role and by tick, and raises the two alarms."""

    def __init__(self, config: Config):
        self.config = config
        self.calls_total = 0
        self.calls_by_role: Counter[str] = Counter()
        self.tick_calls = 0
        self.tick_calls_by_role: Counter[str] = Counter()
        self.input_tokens = 0
        self.output_tokens = 0
        self.cache_reads = 0
        self.errors = 0
        self._recent_validations: deque[bool] = deque(
            maxlen=int(config.engine["validation_alarm_window"])
        )
        self._transport_failures: dict[str, int] = {}

    def start_tick(self) -> None:
        self.tick_calls = 0
        self.tick_calls_by_role = Counter()

    def record(self, role: str, usage: Usage, ok: bool) -> None:
        self.calls_total += 1
        self.calls_by_role[role] += 1
        self.tick_calls += 1
        self.tick_calls_by_role[role] += 1
        self.input_tokens += usage.input_tokens
        self.output_tokens += usage.output_tokens
        self.cache_reads += usage.cache_read_tokens
        if not ok:
            self.errors += 1

    def note_validation(self, ok: bool) -> None:
        """Track the malformed-reply rate over a window of decisions."""
        self._recent_validations.append(ok)
        window = self._recent_validations
        if len(window) < (window.maxlen or 0):
            return
        bad = sum(1 for v in window if not v) / len(window)
        if bad > float(self.config.engine["validation_alarm_frac"]):
            raise ValidationAlarm(
                f"{bad:.0%} of the last {len(window)} model replies failed validation "
                "- check the prompts before running further"
            )

    def note_transport(self, ok: bool, provider: str = "") -> None:
        """A run of wire failures on one provider, reset by one success on it."""
        runs = self._transport_failures
        if ok:
            runs[provider] = 0
            return
        runs[provider] = runs.get(provider, 0) + 1
        limit = int(self.config.engine.get("provider_down_after", 25))
        if limit and runs[provider] >= limit:
            raise ProviderDown(
                f"{runs[provider]} calls in a row failed on the wire"
                f"{' to ' + provider if provider else ''} - the model server is not "
                "answering. The town is saved; start the server (populace serve) "
                "or check --model-url, then resume."
            )
