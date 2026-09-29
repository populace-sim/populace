"""Why did news not travel in a run's conversations? Read-only.

    .venv/bin/python tools/news_in_talk.py <town>/runs/<run_id>

For each injection, takes the residents who knew of it (saw it happen or
noticed it) and, from the moment each knew, counts:

- their conversation calls, and how many of those prompts contained the news
  (if almost none did, the talk prompt was the cause: fixed in b76b924);
- their talk decisions, and how many opening lines used the news's words;
- their talks refused as "already talked with X today" (if many, the pair
  rule was the cause: fixed in b76b924).

Written for the PC's 32B day B, whose logs are on the PC.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from populace import words as W  # noqa: E402
from populace.observe.report import _inj_words  # noqa: E402

TPD = 48


def rows(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()] if path.exists() else []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    run = Path(ap.parse_args().run_dir)
    events, calls = rows(run / "events.jsonl"), rows(run / "calls.jsonl")
    decisions = rows(run / "decisions.jsonl")
    for inj in rows(run / "injections.jsonl"):
        if inj.get("refused") or inj["kind"].startswith("_") or inj["kind"] == "service.register":
            continue
        src = f"inject:{inj['id']}"
        knew: dict[str, int] = {}
        for e in events:
            if e.get("source") != src or (e.get("tags") or [inj["kind"]])[0] != inj["kind"]:
                continue
            at = e["day"] * TPD + e["tick"]
            for rid in (e.get("witnesses") or []) if e["kind"] == "changed" else [e["actor"]]:
                knew.setdefault(rid, at)
        words = _inj_words(inj.get("params") or {})
        text_bits = [w for w in words if len(w) > 3]
        talk_calls = with_news = openers = openers_news = refused = 0
        for c in calls:
            if c.get("role") != "dialogue" or c.get("char_id") not in knew:
                continue
            if (c.get("day") or 0) * TPD + (c.get("tick") or 0) < knew[c["char_id"]]:
                continue
            talk_calls += 1
            prompt = json.dumps(c.get("prompt") or "")
            with_news += bool(text_bits) and W.contains(prompt, text_bits)
        for d in decisions:
            if d["resident"] in knew and d["day"] * TPD + d["tick"] >= knew[d["resident"]] and d["action"] == "talk":
                openers += 1
                openers_news += bool(words) and W.contains(d.get("dialogue") or "", words)
        for e in events:
            if e["kind"] == "refused" and e["actor"] in knew and "already talked" in (e.get("detail") or "") \
                    and e["day"] * TPD + e["tick"] >= knew[e["actor"]]:
                refused += 1
        print(f"{inj['kind']} ({inj['id']}), words {', '.join(words[:4]) or '-'}: {len(knew)} knew")
        print(f"  conversation calls by knowers after knowing: {talk_calls}; prompts carrying the news: {with_news}")
        print(f"  talk decisions by knowers after knowing: {openers}; openers using its words: {openers_news}")
        print(f"  their talks refused as already talked today: {refused}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
