"""Town time. By default one tick is 30 minutes and a day is 48 ticks.

Ported from Alive's `clock.py`. The one change: the day's length can be set
once per process with `configure`, because in Alive the config keys that
claimed to set it were read by nothing.
"""

from __future__ import annotations

from dataclasses import dataclass

TICKS_PER_DAY = 48
MINUTES_PER_TICK = 30

WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def configure(ticks_per_day: int = 48, minutes_per_tick: int = 30) -> None:
    """Set the day's length. Must describe exactly 24 hours."""
    global TICKS_PER_DAY, MINUTES_PER_TICK
    if ticks_per_day * minutes_per_tick != 24 * 60:
        raise ValueError(
            f"{ticks_per_day} ticks of {minutes_per_tick} minutes is not a day"
        )
    TICKS_PER_DAY = int(ticks_per_day)
    MINUTES_PER_TICK = int(minutes_per_tick)


def ticks_for_hours(hours: float) -> int:
    """How many ticks a span of hours covers, rounded to the nearest tick."""
    return int(round(hours * 60 / MINUTES_PER_TICK))


@dataclass(frozen=True)
class GameTime:
    """A point in town time. Day is 1-based; tick runs 0..TICKS_PER_DAY-1."""

    day: int
    tick: int

    def __post_init__(self) -> None:
        if self.day < 1:
            raise ValueError(f"day must be >= 1, got {self.day}")
        if not 0 <= self.tick < TICKS_PER_DAY:
            raise ValueError(f"tick must be 0..{TICKS_PER_DAY - 1}, got {self.tick}")

    def advance(self, n: int = 1) -> "GameTime":
        total = self.total_ticks + n
        return GameTime(day=total // TICKS_PER_DAY + 1, tick=total % TICKS_PER_DAY)

    @property
    def total_ticks(self) -> int:
        """Ticks elapsed since the start of day 1."""
        return (self.day - 1) * TICKS_PER_DAY + self.tick

    @property
    def weekday_index(self) -> int:
        return (self.day - 1) % 7

    @property
    def weekday(self) -> str:
        return WEEKDAYS[self.weekday_index]

    @property
    def hhmm(self) -> str:
        return tick_to_hhmm(self.tick)

    @property
    def is_last_tick_of_day(self) -> bool:
        return self.tick == TICKS_PER_DAY - 1

    def label(self) -> str:
        return f"Day {self.day} ({self.weekday}), {self.hhmm}"

    def to_dict(self) -> dict:
        return {"day": self.day, "tick": self.tick, "weekday": self.weekday}

    @staticmethod
    def from_dict(d: dict) -> "GameTime":
        return GameTime(day=int(d["day"]), tick=int(d["tick"]))


def ticks_between(earlier: GameTime, later: GameTime) -> int:
    return later.total_ticks - earlier.total_ticks


def tick_to_hhmm(tick: int) -> str:
    """Format a within-day tick index as a clock time (the day's end renders as 24:00)."""
    minutes = tick * MINUTES_PER_TICK
    return f"{minutes // 60:02d}:{minutes % 60:02d}"
