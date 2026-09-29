"""The one place an experimenter's view turns a resident id back into a name.

Resident ids are opaque (`r017`) so that no prompt can hand a stranger's name
to the model. People reading a run still want names. Everything written for a
person to read - the town listing, the report, a run's `names.json` beside its
JSONL streams - gets them from here, so there is exactly one mapping and it is
never consulted by anything a resident reads.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Mapping

if TYPE_CHECKING:  # pragma: no cover
    from ..state.town import Town

ID = re.compile(r"\[?\b(r\d{3,})\b\]?")
FILENAME = "names.json"


class NameBook:
    def __init__(self, names: Mapping[str, str]):
        self.names = dict(names)

    @classmethod
    def of(cls, town: "Town") -> "NameBook":
        return cls({rid: r.name for rid, r in town.residents.items()})

    @classmethod
    def load(cls, run_dir: str | Path) -> "NameBook":
        path = Path(run_dir) / FILENAME
        return cls(json.loads(path.read_text(encoding="utf-8")) if path.exists() else {})

    def save(self, run_dir: str | Path) -> Path:
        path = Path(run_dir) / FILENAME
        path.write_text(json.dumps(self.names, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        return path

    def name(self, rid: str | None) -> str:
        return self.names.get(rid or "", rid or "")

    def label(self, rid: str) -> str:
        """`Shu Yamada (r017)`: a name for the reader, the id for grep."""
        return f"{self.names[rid]} ({rid})" if rid in self.names else rid

    def restore(self, text: str) -> str:
        """Every id in a line of log text, bracketed or bare, as a name."""
        return ID.sub(lambda m: self.names.get(m.group(1), m.group(0)), text or "")

    def find(self, query: str) -> str | None:
        """An id from an id or a name, for command lines: `--resident "Shu Yamada"`."""
        if query in self.names:
            return query
        want = query.strip().lower()
        hits = [rid for rid, n in self.names.items() if n.lower() == want]
        return hits[0] if len(hits) == 1 else None
