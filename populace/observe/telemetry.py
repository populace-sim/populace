"""Append-only JSONL streams for one run, plus a readable transcript per day.

Ported from Alive's `telemetry.py`. Streams live under `<town>/runs/<run_id>/`:

* `calls.jsonl`: every model call, with its prompt, reply, tokens and latency
* `systems.jsonl`: each distinct system prefix once, under the hash calls cite
* `ticks.jsonl`: one line per tick
* `events.jsonl`: every event, with who witnessed it
* `conversations.jsonl`: every conversation, line by line

The transcript header carries the town's name, not a fixed one.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class Telemetry:
    def __init__(
        self,
        root: str | Path,
        run_id: str | None = None,
        enabled: bool = True,
        town_name: str = "Town",
    ):
        self.root = Path(root)
        self.enabled = enabled
        self.town_name = town_name
        self.run_id = run_id or time.strftime("%Y%m%d-%H%M%S")
        self.log_dir = self.root / "runs" / self.run_id
        self.transcript_dir = self.log_dir / "transcripts"
        self._systems_seen: set[str] = set()
        if self.enabled:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.transcript_dir.mkdir(parents=True, exist_ok=True)

    def _append(self, name: str, record: dict[str, Any]) -> None:
        if not self.enabled:
            return
        with open(self.log_dir / f"{name}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True, default=str) + "\n")

    def log_call(self, record: dict[str, Any]) -> None:
        self._append("calls", record)

    def log_system(self, system_hash: str, blocks: list[dict[str, Any]]) -> None:
        """Write a system prefix down once per run, under the hash calls refer to."""
        if not self.enabled or system_hash in self._systems_seen:
            return
        self._systems_seen.add(system_hash)
        self._append(
            "systems",
            {"system_hash": system_hash, "blocks": [b.get("text", "") for b in blocks]},
        )

    def log_tick(self, record: dict[str, Any]) -> None:
        self._append("ticks", record)

    def log_event(self, record: dict[str, Any]) -> None:
        self._append("events", record)

    def log_contact(self, record: dict[str, Any]) -> None:
        self._append("contacts", record)

    def log_agent_call(self, record: dict[str, Any]) -> None:
        self._append("agent_calls", record)

    def log_injection(self, record: dict[str, Any]) -> None:
        self._append("injections", record)

    def log_decision(self, record: dict[str, Any]) -> None:
        self._append("decisions", record)

    def log_conversation(self, record: dict[str, Any]) -> None:
        self._append("conversations", record)

    def write_json(self, name: str, data: Any) -> Path | None:
        if not self.enabled:
            return None
        path = self.log_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, sort_keys=True, default=str) + "\n",
                        encoding="utf-8")
        return path

    def read_stream(self, name: str) -> list[dict[str, Any]]:
        path = self.log_dir / f"{name}.jsonl"
        if not path.exists():
            return []
        with open(path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    # -- the readable transcript -------------------------------------------
    # Scenes go to a scratch file as they happen, so a run stopped and resumed
    # mid-day keeps everything said before the stop.

    def _parts_file(self, day: int) -> Path:
        return self.transcript_dir / f".day_{day:02d}.parts"

    def scene(self, text: str, day: int) -> None:
        if not text or not self.enabled:
            return
        with open(self._parts_file(day), "a", encoding="utf-8") as f:
            f.write(text.rstrip() + "\n")

    def write_day(self, day: int, header: str = "", footer: str = "") -> Path | None:
        if not self.enabled:
            return None
        parts = self._parts_file(day)
        body = parts.read_text(encoding="utf-8") if parts.exists() else ""
        path = self.transcript_dir / f"day_{day:02d}.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# {self.town_name} - Day {day}\n\n")
            if header:
                f.write(header.rstrip() + "\n\n")
            f.write(body.rstrip() + "\n")
            if footer:
                f.write("\n" + footer.rstrip() + "\n")
        parts.unlink(missing_ok=True)
        return path
