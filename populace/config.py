"""Every tunable number in one place, with presets on top.

A town's config is `DEFAULTS`, then a preset, then whatever the town or the
command line overrides, merged in that order. Nothing reads a default from
anywhere but a loaded `Config`: in Alive three prompt lines read the defaults
table directly, so a config override silently never reached the model.

There is no price table. populace spends nothing: every provider is local or
mock, and the meter counts tokens, not money.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROLES = ("npc_decision", "dialogue", "reflection", "chargen", "town_spec", "narrator")

DEFAULTS: dict[str, Any] = {
    "roles": {
        "npc_decision": {"provider": "local", "model": "populace", "max_tokens": 600},
        "dialogue": {"provider": "local", "model": "populace", "max_tokens": 500},
        "reflection": {"provider": "local", "model": "populace", "max_tokens": 1500},
        "chargen": {"provider": "local", "model": "populace", "max_tokens": 2500},
        "town_spec": {"provider": "local", "model": "populace", "max_tokens": 800},
        # `populace report --narrate`: the day retold as prose, labelled as such.
        "narrator": {"provider": "local", "model": "populace", "max_tokens": 700},
    },
    "providers": {
        # One OpenAI-compatible endpoint: `populace serve` on this machine, or
        # any `--model-url` (the PC's llama-server, vLLM, a cloud box).
        "local": {"base_url": "http://127.0.0.1:8080/v1", "max_concurrency": 1},
    },
    "clock": {"ticks_per_day": 48, "minutes_per_tick": 30},
    "engine": {
        "request_timeout_s": 300.0,
        "retry_limit": 1,
        "validation_alarm_window": 20,
        "validation_alarm_frac": 0.3,
        "provider_down_after": 25,
        "concurrency": 8,
    },
    "scheduler": {
        # The whole tick: decisions, dialogue lines, retries and phone replies.
        "calls_per_tick": 6,
        "decision_share": 0.5,
        "cooldown_ticks": 2,
        "staleness_ticks": 4,
        "staleness_ticks_idle": 8,
        "stale_max_days": 2,
        "scene_per_place": 1,
        "new_face_max_per_day": 2,
    },
    "dialogue": {"max_lines": 5, "min_bought_lines": 2, "transcript_window": 6},
    "reflection": {
        # Real reflections a night buys; everybody else gets a free recap. At
        # about a minute a reflection on a laptop, 20 is a third of an hour.
        "nightly_cap": 20,
        "prune_after_days": 3,
        "beliefs_cap": 40,
        "raw_memory_cap": 200,
        "review_every_days": 7,
    },
    "memory": {
        "retrieval_cap": 12,
        "w_recency": 1.0,
        "w_importance": 0.7,
        "w_relevance": 1.2,
        "recency_halflife_ticks": 48,
        "guaranteed_recent": 3,
        "guaranteed_high_importance": 3,
        "high_importance_threshold": 9,
    },
    "needs": {
        # Each need rises (or falls) per tick awake and per tick asleep, and is
        # urgent past a threshold. `words` are what the prompt says at each
        # band, low to high, so the model reads a state and not a number alone.
        "kinds": {
            "hunger": {
                "start": 20.0,
                "rate": 1.2,
                "sleep_rate": 0.5,
                "urgent_above": 70.0,
                "words": ["fed", "could eat", "hungry", "starving"],
            },
            "energy": {
                "start": 85.0,
                "rate": -2.5,
                "sleep_rate": 7.0,
                "urgent_below": 25.0,
                "words": ["worn out", "tired", "all right", "fresh"],
            },
        },
        "hysteresis": 10.0,
        "home_meal_satiety": 15.0,
    },
    "locality": {"people_cap": 20, "places_cap": 12},
    "prompt": {"profile": "frontier", "dynamic_budget_tokens": 1000},
    "trust": {
        "thresholds": [0, 5, 25, 60],
        "number_min_stage": 2,
        "introduce_min_stage": 2,
        "lately_window_days": 3,
        "lately_threshold": 2,
        "deltas": {
            "met": 2, "talked": 1, "heavy_talk": 2, "together": 3,
            "gift": 2, "gift_listened": 3, "gift_on_date_multiplier": 2,
            "loan_received": 2, "repaid_on_time": 4, "repaid_late": 2,
            "promise_kept": 3, "promise_broken": -4, "loan_overdue": -3,
            "no_show": -3, "fired": -4, "introduced": 4, "number": 1,
            "stood_up": -2, "threat": -8,
        },
    },
    "economy": {
        "loan_max": 250.0,
        "loan_cap_by_stage": [0, 0, 60, 200],
        "loan_min_reserve": 30.0,
        "loan_default_due_days": 7,
        "competence_gain_per_shift": 0.05,
        "wage_step": 0.5,
        "no_show_grace_ticks": 2,
    },
    "phone": {
        "send_cap_per_day": 3,
        "reply_cap_per_day": 40,
        "reply_cap_per_person_per_day": 3,
        "max_text_chars": 240,
    },
    "gen": {"enrich_batch": 5},
}

# The three presets. `quick` is low fidelity by design and says so wherever it
# appears; nothing measured on it stands for a full run.
PRESETS: dict[str, dict[str, Any]] = {
    "quick": {
        "scheduler": {"calls_per_tick": 2},
        "dialogue": {"max_lines": 3},
        "reflection": {"nightly_cap": 10},
    },
    "laptop": {
        "scheduler": {"calls_per_tick": 6},
        "dialogue": {"max_lines": 5},
        "reflection": {"nightly_cap": 20},
    },
    "gpu": {
        "scheduler": {"calls_per_tick": 30},
        "dialogue": {"max_lines": 6},
        # None means everybody reflects every night.
        "reflection": {"nightly_cap": None},
        "providers": {"local": {"max_concurrency": 8}},
        "engine": {"concurrency": 8},
    },
}
LOW_FIDELITY_PRESETS = {"quick"}
DEFAULT_PRESET = "laptop"


class ConfigError(ValueError):
    pass


def deep_merge(base: dict, over: dict | None) -> dict:
    """A copy of `base` with `over` laid on top, dict by dict."""
    out = copy.deepcopy(base)
    for key, value in (over or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


@dataclass(frozen=True)
class RoleConfig:
    name: str
    provider: str
    model: str
    max_tokens: int
    timeout_s: float | None = None
    # OpenAI-protocol servers only: fields the request body carries that the
    # protocol does not have, e.g. llama-server's per-request `lora` scale.
    extra_body: dict[str, Any] | None = None
    # Qwen3's soft switch: "/no_think" appended to the last user message, for
    # a hosted endpoint that offers no request field to turn thinking off.
    no_think: bool = False


# Turning a model's thinking off per request, for endpoints the user does not
# start themselves (a local llama-server is started with thinking off). Each
# host spells it differently; check the host's documentation.
THINKING_OFF: dict[str, dict[str, Any]] = {
    "openrouter": {"extra_body": {"reasoning": {"enabled": False}}},
    "no-think": {"no_think": True},
}


def thinking_off_overrides(name: str | None) -> dict[str, Any]:
    """Role overrides that turn thinking off in every role the model answers."""
    if not name:
        return {}
    if name not in THINKING_OFF:
        raise ConfigError(f"unknown --thinking-off {name!r}; choose from {', '.join(THINKING_OFF)}")
    return {"roles": {role: dict(THINKING_OFF[name]) for role in ROLES}}


class Config:
    """A merged, read-only view of one town's settings."""

    def __init__(self, raw: dict[str, Any], preset: str = DEFAULT_PRESET):
        self.raw = raw
        self.preset = preset
        self._validate()

    @classmethod
    def build(
        cls,
        preset: str | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> "Config":
        name = preset or DEFAULT_PRESET
        if name not in PRESETS:
            raise ConfigError(f"unknown preset {name!r}; choose from {', '.join(PRESETS)}")
        raw = deep_merge(deep_merge(DEFAULTS, PRESETS[name]), overrides)
        return cls(raw, preset=name)

    @classmethod
    def load(cls, path: str | Path, preset: str | None = None,
             overrides: dict[str, Any] | None = None) -> "Config":
        p = Path(path)
        if not p.exists():
            raise ConfigError(f"config file not found: {p}")
        stored = json.loads(p.read_text(encoding="utf-8"))
        return cls.build(preset or stored.pop("preset", None),
                         deep_merge(stored, overrides))

    @property
    def low_fidelity(self) -> bool:
        return self.preset in LOW_FIDELITY_PRESETS

    def _validate(self) -> None:
        for role in ROLES:
            if role not in self.raw.get("roles", {}):
                raise ConfigError(f"roles.{role} is missing")
        share = float(self.scheduler["decision_share"])
        if not 0 < share <= 1:
            raise ConfigError("scheduler.decision_share must be in (0, 1]")
        if int(self.scheduler["calls_per_tick"]) < 1:
            raise ConfigError("scheduler.calls_per_tick must be at least 1")
        for name, need in self.needs["kinds"].items():
            if "urgent_above" not in need and "urgent_below" not in need:
                raise ConfigError(f"needs.kinds.{name} has no urgent threshold")
            if len(need.get("words", [])) < 2:
                raise ConfigError(f"needs.kinds.{name} needs at least two words")

    def section(self, name: str) -> dict[str, Any]:
        return self.raw[name]

    def role(self, name: str) -> RoleConfig:
        spec = self.raw["roles"].get(name)
        if spec is None:
            raise ConfigError(f"no role {name!r}")
        return RoleConfig(
            name=name,
            provider=str(spec["provider"]),
            model=str(spec["model"]),
            max_tokens=int(spec["max_tokens"]),
            timeout_s=spec.get("timeout_s"),
            extra_body=dict(spec["extra_body"]) if isinstance(spec.get("extra_body"), dict) else None,
            no_think=bool(spec.get("no_think", False)),
        )

    def provider_settings(self, name: str) -> dict[str, Any]:
        return dict(self.raw.get("providers", {}).get(name, {}))

    def to_dict(self) -> dict[str, Any]:
        return {"preset": self.preset, **copy.deepcopy(self.raw)}

    # Named sections, so call sites read like the config file.
    engine = property(lambda self: self.raw["engine"])
    scheduler = property(lambda self: self.raw["scheduler"])
    dialogue = property(lambda self: self.raw["dialogue"])
    reflection = property(lambda self: self.raw["reflection"])
    memory = property(lambda self: self.raw["memory"])
    needs = property(lambda self: self.raw["needs"])
    locality = property(lambda self: self.raw["locality"])
    prompt = property(lambda self: self.raw["prompt"])
    trust = property(lambda self: self.raw["trust"])
    economy = property(lambda self: self.raw["economy"])
    phone = property(lambda self: self.raw["phone"])
    gen = property(lambda self: self.raw["gen"])
    clock = property(lambda self: self.raw["clock"])
