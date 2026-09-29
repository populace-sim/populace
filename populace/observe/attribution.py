"""The fifth voice metric: putting words in somebody's mouth.

Ported from Alive, where the first fine-tuned adapter had a resident tell a
newcomer that a neighbour "said you came in yesterday" when the neighbour had
never mentioned them: valid JSON, no leak, no invented name, and a fact about
what somebody said, made up. None of the four counts in `voice` sees it.

A line that attributes speech to a named person ("Sam said...", "Jo told
me...", "according to Pat") is checked against what that person actually said
**within the speaker's hearing**: the conversations the speaker took part in
(`participants`) or stood in on (`overheard_by`), and only the lines said
before theirs. An attribution nothing they said supports is a
*misattribution*: either the person said nothing like it, or the speaker never
heard them say anything at all.

**Support is words, not meaning.** The attributed clause has to share `NEED`
of its own content words with one thing the person said, whole-word through
`populace.words`. It is a proxy like the other four, and the examples are kept
so a person can read what it counted.
"""

from __future__ import annotations

import re
from typing import Any

# Verbs that hand a line to somebody else's mouth. Whole-word, after a name.
VERBS = (
    "said", "says", "was saying", "kept saying", "keeps saying", "told me",
    "tells me", "told us", "tells us", "was telling me", "mentioned",
    "mentions", "reckons", "reckoned", "swears", "swore", "claims", "claimed",
    "admitted", "let slip", "asked me", "said to me", "says to me", "thinks",
    "thought", "figured", "figures",
)

# Function words, and the words of attribution themselves, which say nothing
# about *what* was attributed. Deliberately short: "yesterday" and "came" are
# exactly the words a made-up report is wrong about, so they stay.
NOISE = frozenset("""
a an the and or but so that this these those it its is was were be been being
to of in on at for with from by as about into over after before up down out
off than then there here he she they them his her their him you your me my we
our us i not no yes do does did have has had will would could should can may
might must just still yet too very quite rather some any all every each much
many more most also even ever what which who whom whose when where why how
said says say tell told telling mentioned thinks thought reckons claims
""".split())

# How many of the attributed clause's own words the person has to have said in
# one breath for the attribution to stand - or all of them, if it has fewer.
NEED = 2

_WORD = re.compile(r"[a-z0-9']+")


def _words(text: str) -> list[str]:
    return _WORD.findall(str(text or "").lower())


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", str(text or "").strip())
    return [p.strip() for p in parts if p.strip()]


def name_index(names_by_id: dict[str, str]) -> dict[str, str]:
    """Every way a person can be named in a line, lower-cased, to their id.

    Full names and first names of three letters or more. A first name two
    people share names nobody.
    """
    index: dict[str, str] = {}
    shared: set[str] = set()
    for cid, full in sorted(names_by_id.items()):
        full = str(full or "").strip()
        if not full:
            continue
        index[full.lower()] = cid
        first = full.split()[0].lower()
        if len(first) < 3:
            continue
        if first in index and index[first] != cid:
            shared.add(first)
        else:
            index[first] = cid
    for first in shared:
        index.pop(first, None)
    return index


def content_words(text: str, name_words: set[str]) -> list[str]:
    """The words of a clause worth checking against what somebody said."""
    return [w for w in _words(text)
            if w not in NOISE and w not in name_words and len(w) > 1]


def attributions_in(said: str, index: dict[str, str]) -> list[tuple[str, str]]:
    """Every (person id, attributed clause) a line hands to somebody's mouth.

    The clause is what follows the verb to the end of the sentence, with a
    leading "that" and any quotes taken off. A clause with no words worth
    checking - "Jo said so" - is dropped here rather than scored.
    """
    if not index:
        return []
    names = "|".join(re.escape(n) for n in sorted(index, key=len, reverse=True))
    verbs = "|".join(re.escape(v) for v in VERBS)
    direct = re.compile(
        rf"\b(?P<name>{names})\s+(?:just\s+|already\s+|even\s+|also\s+)?"
        rf"(?P<verb>{verbs})\b[,:]?\s*(?P<rest>.*)$",
        re.IGNORECASE,
    )
    according = re.compile(
        rf"\baccording to (?P<name>{names})\b[,:]?\s*(?P<rest>.*)$", re.IGNORECASE
    )
    name_words = set(index) | {w for n in index for w in n.split()}
    out: list[tuple[str, str]] = []
    for sentence in _sentences(said):
        found = direct.search(sentence) or according.search(sentence)
        if found is None:
            continue
        who = index.get(found.group("name").lower())
        if who is None:
            continue
        rest = found.group("rest").strip().strip("\"'“”‘’ ")
        rest = re.sub(r"^(?:that|to me that|me that|to me|me)\b[,\s]*", "", rest,
                      flags=re.IGNORECASE)
        rest = rest.strip("\"'“”‘’ .!?")
        if content_words(rest, name_words):
            out.append((who, rest))
    return out


def score(conversations: list[dict[str, Any]], names_by_id: dict[str, str]) -> dict[str, Any]:
    """Attributions of speech, checked against what was said within hearing.

    Conversations are taken in (day, tick) order. A line is heard by a
    conversation's `participants` and `overheard_by`; without a participants
    list, by its speakers alone. "Before" is an earlier tick, or an earlier
    line of the same conversation - a line in another conversation at the same
    tick is not before, because nobody is in two rooms at once.
    """
    from .. import words as W

    index = name_index(names_by_id)
    name_words = set(index) | {w for n in index for w in n.split()}
    ordered = sorted(
        enumerate(conversations),
        key=lambda pair: (pair[1].get("day", 0), pair[1].get("tick", 0), pair[0]),
    )
    # (when, conversation order, audience, speaker, text), in the order said.
    heard_log: list[tuple[tuple, int, set[str], str, str]] = []
    total = 0
    bad: list[dict[str, Any]] = []
    for order, (_, conv) in enumerate(ordered):
        lines = [l for l in (conv.get("lines") or []) if l.get("text")]
        audience = set(conv.get("participants") or [str(l.get("speaker")) for l in lines])
        audience |= set(conv.get("overheard_by") or [])
        when = (conv.get("day", 0), conv.get("tick", 0))
        for line in lines:
            speaker = str(line.get("speaker") or "")
            said = str(line.get("text") or "")
            for about, clause in attributions_in(said, index):
                if about == speaker:
                    continue
                total += 1
                wanted = tuple(dict.fromkeys(content_words(clause, name_words)))
                need = min(NEED, len(wanted))
                theirs = [
                    text for (w, o, aud, who, text) in heard_log
                    if who == about and speaker in aud and (w < when or o == order)
                ]
                record = {
                    "day": conv.get("day"), "who": names_by_id.get(speaker, speaker),
                    "about": names_by_id.get(about, about), "said": said,
                }
                if not theirs:
                    bad.append({**record, "kind": "never_heard_them", "closest": None})
                    continue
                best, closest = -1, ""
                for text in theirs:
                    hits = len(W.found(text, wanted))
                    if hits > best:
                        best, closest = hits, text
                if best < need:
                    bad.append({**record, "kind": "nothing_like_it", "closest": closest})
            heard_log.append((when, order, audience, speaker, said))
    return {
        "attributions": total,
        "misattributed": len(bad),
        "misattributed_pct_of_attributions": (
            round(100.0 * len(bad) / total, 1) if total else 0.0
        ),
        "examples": bad[:8],
    }


def select_days(conversations: list[dict[str, Any]], from_day: int = 0,
                to_day: int = 0) -> list[dict[str, Any]]:
    """The conversations of an inclusive day window; 0 at either end is open.

    A fortnight is read in halves to see whether a model drifts between its
    first days and its last, and the two halves have to be cut the same way.
    """
    return [
        c for c in conversations
        if (not from_day or int(c.get("day", 0)) >= from_day)
        and (not to_day or int(c.get("day", 0)) <= to_day)
    ]


# -- reading a transcript, for the runs that have nothing else ------------

_TRANSCRIPT_LINE = re.compile(r'^\s*(?P<star>\*)?\s*\[(?P<place>[^\]]+)\]\s+(?P<name>[^:"]+?):\s+"(?P<text>.*)"\s*$')
_DAY = re.compile(r"^##\s+Day\s+(?P<day>\d+)\b")


def conversations_from_transcript(text: str, names_by_id: dict[str, str],
                                  player_id: str = "player") -> list[dict[str, Any]]:
    """Conversations recovered from a `playtest.transcript.md`.

    The gate's recorder writes each conversation's lines together, so a
    conversation is a run of consecutive spoken lines at one place between
    one pair of speakers; a third speaker, another place, or anything that is
    not a spoken line (an event, a typed line, a day header) ends it. A run
    marked with `*` was at the player's location, so the player stood in on
    it. Ticks are not in a transcript: each conversation gets the next number,
    which keeps the order and nothing else.
    """
    by_name = {str(full).strip(): cid for cid, full in names_by_id.items() if full}
    convs: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    day = 0
    tick = 0

    def close():
        nonlocal current
        if current is not None and current["lines"]:
            convs.append(current)
        current = None

    for raw in text.splitlines():
        header = _DAY.match(raw)
        if header:
            close()
            day = int(header.group("day"))
            continue
        found = _TRANSCRIPT_LINE.match(raw)
        if not found:
            close()
            continue
        cid = by_name.get(found.group("name").strip())
        if cid is None:
            close()
            continue
        place = found.group("place")
        starred = bool(found.group("star"))
        speakers = set(current["participants"]) if current else set()
        if (current is None or current["place"] != place
                or (cid not in speakers and len(speakers) >= 2)):
            close()
            tick += 1
            current = {"day": day, "tick": tick, "place": place, "participants": [],
                       "overheard_by": [player_id] if starred else [], "lines": []}
        if cid not in current["participants"]:
            current["participants"].append(cid)
        if starred and player_id not in current["overheard_by"]:
            current["overheard_by"].append(player_id)
        current["lines"].append({"speaker": cid, "text": found.group("text")})
    close()
    return convs
