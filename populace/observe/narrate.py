"""`populace report --narrate`: the day retold as prose by a model, labelled.

The deterministic report is the record. This asks a model to turn it into a
few paragraphs somebody can read in a minute, leading with what was injected
and how the town and the service handled it, and puts them at the top of the
report under a heading that says which model wrote them and that they can be
wrong. The facts are fed in that order: the injections, the service, the
findings, the flags that fired, and only then the rest of the day. (The live
32B's first retelling led with the town's wages and never mentioned the
outages.)

Two cheap checks run on the prose, and anything they find is listed under it:
residents it names who are not in the facts (a narrator that invents people is
inventing events too), and injections it never mentions.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..providers.mock import handler

SYSTEM = """You write a short plain account of a simulation run, for somebody who \
was not there and has a minute to read it.

Lead with what was injected into the town, in the order given, and how the town \
and the service handled it: name each injected thing, who it touched, who got in \
touch and when, and what the service did - including what it got wrong, as the \
findings say. Keep the service's mistakes apart from the town's own weaknesses. \
Only then, briefly, anything else notable from the day.

Use only the facts you are given. Keep every name exactly as written. Do not add \
events, motives or feelings the facts do not state; where the facts give a \
person's own reason, you may use it, and say it was their reason. Write four \
short paragraphs, under 320 words in all, in the past tense. No headings, no lists."""

ENTRY = re.compile(r"^\*\*(Day \d+ \d\d:\d\d): ([\w.]+)\*\* \(([^)]*)\)\. (.*)$")
SECTIONS = ("## The service", "## Findings", "## What happened", "## What changed")
OUTAGE_WORDS = ("outage", "outages", "went off", "down", "cut", "off", "no internet", "offline")


def _section(report_markdown: str, heading: str) -> str:
    if heading not in report_markdown:
        return ""
    return heading + report_markdown.split(heading, 1)[1].split("\n## ", 1)[0]


def injected_entries(report_markdown: str) -> list[dict[str, str]]:
    """The report's own list of what was injected: when, what kind, what it said."""
    out = []
    for line in _section(report_markdown, "## Injected").splitlines():
        m = ENTRY.match(line.strip())
        if m:
            out.append({"when": m.group(1), "kind": m.group(2), "note": m.group(3), "text": m.group(4)})
    return out


def facts_from(report_markdown: str) -> str:
    """What the narrator may work from, most important first: what was
    injected, how the service handled it, the findings, the flags that fired,
    and only then the rest of the day."""
    entries = injected_entries(report_markdown)
    parts = []
    if entries:
        parts.append("WHAT WAS INJECTED, in order:\n" + "\n".join(
            f"{n}. {e['when']}, {e['kind']}"
            + (f" ({e['note']})" if not e["note"].startswith("i") else "") + f": {e['text']}"
            for n, e in enumerate(entries, 1)))
        parts.append(_section(report_markdown, "## Injected"))
    for heading in SECTIONS[:2]:
        parts.append(_section(report_markdown, heading))
    flags = _section(report_markdown, "## Realism flags")
    fired = [l for l in flags.splitlines() if l.startswith("| `") and not l.split("|")[2].strip() == "0"]
    if fired:
        parts.append("## Realism flags that fired\n" + "\n".join(fired))
    for heading in SECTIONS[2:]:
        parts.append(_section(report_markdown, heading))
    return "\n\n".join(p.strip() for p in parts if p.strip())


def _words(text: str) -> set[str]:
    from .report import COMMON
    from ..sim.memory import STOPWORDS
    return {w for w in re.findall(r"[a-z][a-z']{2,}", text.lower()) if w not in STOPWORDS and w not in COMMON}


def _own_words(entries: list[dict[str, str]]) -> dict[str, list[str]]:
    """Each distinct injected text's own words: those whose root no other
    injected text shares. The same outage twice counts once."""
    from .. import words as W

    texts = list(dict.fromkeys(e["text"] for e in entries))
    roots = {t: {W.stem(w) for w in _words(t)} for t in texts}
    out = {}
    for t in texts:
        others = set().union(*(roots[o] for o in texts if o != t)) if len(texts) > 1 else set()
        out[t] = sorted(w for w in _words(t) if W.stem(w) not in others)
    return out


def missing_injections(prose: str, entries: list[dict[str, str]]) -> list[str]:
    """Injected things the prose never mentions, judged by each one's own
    words in any of their common forms ("bills" is mentioned by "billing")."""
    from .. import words as W

    own = _own_words(entries)
    missing = []
    for text, e in {e["text"]: e for e in reversed(entries)}.items():
        words = own[text] or sorted(_words(text))
        if e["kind"] == "event.outage":
            words = sorted(set(words) | set(OUTAGE_WORDS))
        if words and not W.contains(prose, words, variants=True):
            missing.append(f"{e['when']} {e['kind']}")
    return sorted(missing, key=lambda m: entries.index(next(e for e in entries if f"{e['when']} {e['kind']}" == m)))


# -- the number check --------------------------------------------------------------------

NUMBER_WORDS = {w: n for n, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
    "sixteen seventeen eighteen nineteen twenty".split())}
UNIT_CLASSES = {
    "residents": ("resident", "people", "person", "customer", "neighbour"),
    "households": ("household", "home", "house", "flat"),
    "contacts": ("contact", "attempt"),
    "calls": ("call",),
    "texts": ("text", "message"),
    "days": ("day",),
    "hours": ("hour",),
}
CALL_VERBS = ("call", "phone", "rang", "ring")
TIME = re.compile(r"\b(\d{1,2}:\d{2})\b")
DAY = re.compile(r"\bDay (\d+)\b")
NUMBER = re.compile(r"(?<![\w:.$/])(?<!\d,)(\d[\d,]*(?:\.\d+)?)(?![\d:])(?:\s+([A-Za-z]+))?")


def _unit_class(word: str | None) -> str | None:
    from .. import words as W
    if not word:
        return None
    root = W.stem(word)
    for cls, members in UNIT_CLASSES.items():
        if any(W.stem(m) == root for m in members):
            return cls
    return None


def _numbers(text: str) -> list[tuple[str, str | None]]:
    """(number, the word after it) for every count in a text, digits or words;
    days, times and money are left to their own checks."""
    out = []
    clean = DAY.sub(" ", TIME.sub(" ", text))
    for m in NUMBER.finditer(clean):
        out.append((m.group(1).replace(",", ""), m.group(2)))
    for m in re.finditer(r"\b(" + "|".join(NUMBER_WORDS) + r")\s+([A-Za-z]+)", clean, re.IGNORECASE):
        out.append((str(NUMBER_WORDS[m.group(1).lower()]), m.group(2)))
    return out


def _blocks(report_markdown: str) -> list[dict[str, Any]]:
    """Each injected entry with the times and days it began and ended."""
    out = []
    body = _section(report_markdown, "## Injected")
    chunks = re.split(r"\n(?=\*\*Day \d+ \d\d:\d\d: )", body)
    for chunk in chunks:
        m = ENTRY.match(chunk.strip().splitlines()[0]) if chunk.strip() else None
        if not m:
            continue
        ended = re.search(r"- Ended: (Day \d+ \d\d:\d\d)", chunk)
        marks = [m.group(1)] + ([ended.group(1)] if ended else [])
        out.append({"when": m.group(1), "kind": m.group(2), "text": m.group(4), "marks": marks})
    return out


HOURS = re.compile(r"\b(?:hours|open)\b[^.\n]{0,20}?(\d{1,2}:\d{2})\s*[-\u2013]\s*(\d{1,2}:\d{2})", re.IGNORECASE)


def _hours_given(report_markdown: str, words) -> set[str]:
    """Opening hours the report gives for a thing anywhere ("a recording gave
    their hours, 08:00-20:00"), on lines that name it. Reports written before
    a service's line under Injected showed its hours need this."""
    from .. import words as W

    out: set[str] = set()
    for line in report_markdown.splitlines():
        if W.contains(line.lower(), [w.lower() for w in words], variants=True):
            for a, b in HOURS.findall(line):
                out |= {a, b}
    return out


def number_mismatches(prose: str, facts: str, report_markdown: str) -> list[str]:
    """Every count, day and time in the prose checked against the facts it was
    given. A count must exist there with the same kind of thing counted (47
    residents is not 47 households); a time or day in a sentence about an
    injected thing must be when that thing began or ended; "called" beside a
    number must fit how many contacts were calls."""
    from .. import words as W

    found: list[str] = []
    fact_numbers: dict[str, set[str]] = {}
    for n, word in _numbers(facts):
        fact_numbers.setdefault(n, set())
        cls = _unit_class(word)
        if cls:
            fact_numbers[n].add(cls)
    for line in facts.splitlines():            # "| Residents with a problem | 100 |"
        cells = [c.strip() for c in line.split("|")]
        if len(cells) >= 4 and re.fullmatch(r"\d+", cells[2] or ""):
            cls = next((c for c in (_unit_class(w) for w in re.findall(r"[A-Za-z]+", cells[1])) if c), None)
            fact_numbers.setdefault(cells[2], set())
            if cls:
                fact_numbers[cells[2]].add(cls)
    channels = dict((k, int(v)) for k, v in re.findall(r"\b(call|text|visit) (\d+)", _section(report_markdown, "## The service")))
    blocks = _blocks(report_markdown)
    own = _own_words(blocks)
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(prose.split()))
    for sentence in sentences:
        for n, word in _numbers(sentence):
            cls = _unit_class(word)
            known = fact_numbers.get(n)
            if known is None and n.rstrip("0").rstrip(".") not in fact_numbers:
                found.append(f"\"{n}{' ' + word if word else ''}\": no such number in the facts")
            elif cls and known and cls not in known:
                found.append(f"\"{n} {word}\": the facts have {n} {', '.join(sorted(known))}")
        about = [b for b in blocks if own.get(b["text"]) and W.contains(sentence, own[b["text"]], variants=True)]
        if about:
            # When it began and ended, and any time in its own words ("open 09:00-17:30").
            allowed_times = ({mark.split()[-1] for b in about for mark in b["marks"]}
                             | {t for b in about for t in TIME.findall(b["text"])}
                             | {t for b in about for t in _hours_given(report_markdown, own[b["text"]])})
            allowed_days = {mark.split()[1] for b in about for mark in b["marks"]}
            for t in TIME.findall(sentence):
                if t not in allowed_times:
                    spans = "; ".join(f"{b['text'].rstrip('.')} {' to '.join(b['marks'])}" for b in about)
                    found.append(f"\"{t}\": the facts give {spans}")
            for d in DAY.findall(sentence):
                if d not in allowed_days and not re.search(rf"\bDay {d}\b", facts):
                    found.append(f"\"Day {d}\": not a day in the facts")
        else:
            for t in TIME.findall(sentence):
                if t not in facts:
                    found.append(f"\"{t}\": no such time in the facts")
        if channels and W.contains(sentence, CALL_VERBS, variants=True):
            for n, _ in _numbers(sentence):
                if int(float(n)) > channels.get("call", 0):
                    found.append(f"\"called\" {n} times: by channel the facts have "
                                 + ", ".join(f"{k} {v}" for k, v in sorted(channels.items())))
                    break
    return list(dict.fromkeys(found))


@handler("narrator")
def _mock_narrator(rng, state: dict[str, Any], meta: dict[str, Any]) -> str:
    facts = state.get("facts", "")
    injected = [l.split(". ", 1)[1] for l in facts.split("\n\n", 1)[0].splitlines()[1:]
                if re.match(r"\d+\. ", l)] if facts.startswith("WHAT WAS INJECTED") else []
    lines = [l.strip("- ").split("  \n")[0] for l in facts.splitlines() if l.startswith("- **Day")]
    picked = [re.sub(r"\*\*(Day \d+ \d\d:\d\d)\*\*, ", r"On \1, at ", l) for l in lines[:2]]
    lead = ("(mock) Injected: " + " Then ".join(injected)) if injected else ""
    body = " ".join(picked) or "Nothing out of the ordinary happened."
    return "\n\n".join(x for x in (lead, f"(mock) {body}", "(mock) The rest ran on routine.") if x)


def invented_people(prose: str, facts: str, names: dict[str, str]) -> list[str]:
    return sorted(n for n in names.values() if re.search(rf"\b{re.escape(n)}\b", prose)
                  and not re.search(rf"\b{re.escape(n)}\b", facts))


def _model_name(run_dir, config) -> str:
    """The model that wrote it: the role's name, unless that is the placeholder
    a server ignores, in which case the model the run itself was served by."""
    import json
    name = config.role("narrator").model
    if name not in ("populace", "populace"):
        return name
    manifest = Path(run_dir) / "manifest.json"
    if manifest.exists():
        models = json.loads(manifest.read_text(encoding="utf-8")).get("model") or []
        if models:
            return Path(str(models[0])).name
    return "the local model"


async def narrate(run_dir: str | Path, report_markdown: str, config, mock: bool) -> str:
    from ..observe.telemetry import Telemetry
    from ..providers.costs import Meter
    from ..providers.runner import ModelRunner
    from .names import NameBook

    facts = facts_from(report_markdown)
    runner = ModelRunner(config, Meter(config), Telemetry(run_dir, enabled=False), mock=mock)
    try:
        result = await runner.call(
            "narrator", [{"type": "text", "text": SYSTEM}],
            [{"role": "user", "content": facts + "\n\nWrite the account now."}],
            {"char_id": "narrator", "mock_state": {"facts": facts}, "mock_no_garbage": True})
    finally:
        await runner.aclose()
    who = "the mock provider, which only strings facts together" if mock else _model_name(run_dir, config)
    head = ["## The day, as a model tells it", "",
            f"> *Model-written by {who}, from the sections below. It can be wrong; "
            "the sections after it are the record.*", ""]
    if not result.ok or not (result.text or "").strip():
        return "\n".join(head + [f"The narrator did not answer: {result.error or 'an empty reply'}."]) + "\n"
    prose = result.text.strip()
    invented = invented_people(prose, facts, NameBook.load(run_dir).names)
    left_out = missing_injections(prose, injected_entries(report_markdown))
    wrong = number_mismatches(prose, facts, report_markdown)
    tail = ([f"", f"*It names people the facts never mention: {', '.join(invented)}.*"] if invented else [])
    tail += ([f"", f"*It leaves out what was injected: {'; '.join(left_out)}.*"] if left_out else [])
    tail += ([f"", f"*Numbers that do not match the facts: {'; '.join(wrong)}.*"] if wrong else [])
    return "\n".join(head + [prose] + tail) + "\n"
