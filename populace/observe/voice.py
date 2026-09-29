"""Four ways a model's talking comes apart, counted from a transcript.

Ported from Alive, where a four-day run on a 7B model produced a town whose
mechanics all worked and whose talk was unreadable. Every measure here is a
proxy with a documented blind spot; the transcripts are still read by a person.

* **Echo**: a reply that hands the previous line straight back
  ("Morning, Sam. Still got the paper?" / "Morning, Jo. Still got the paper?").
* **Self-address**: a speaker using their own name as if it were the other
  person's ("Sure, Sam." said by Sam). Introducing yourself is exempt, because
  that is how names travel.
* **A question left on the floor**: a question the next line does not engage.
* **Repeating yourself**: saying again, to somebody else, a line you already
  said today.

Alive's base 7B scored 24.7% echo, 2.8% self-address, 33.8% questions dropped
and 29.5% self-repetition over four in-game days; a frontier model scored
under 3% on all four.
"""

from __future__ import annotations

import re
from typing import Any

# The fifth count, and the reader for runs that exist only as a transcript.
# Re-exported so every scorer keeps coming through this one module.
from .attribution import conversations_from_transcript, select_days  # noqa: F401

# Enough of a shared run to be a parrot rather than a coincidence.
ECHO_RUN = 4

# Saying the same thing twice in a day to two different people. A longer run
# than `ECHO_RUN` because a person's own turns of phrase genuinely recur -
# "same old" is somebody's voice, and "same old, just the coffee, how about
# you" twice in a morning is not.
SELF_REPEAT_RUN = 5

# Openers that carry no content. A reply made only of these is not an answer.
GREETINGS = (
    "morning", "evening", "afternoon", "hi", "hey", "hello", "yeah", "yep",
    "sure", "right", "alright", "all right", "ok", "okay", "well", "look",
    "listen", "thanks", "thank you", "cheers", "night", "goodnight", "bye",
)

# An answer can be one word, and then the rest of the line can be a question.
# "Yes - why, are you looking?" answers the thing it was asked.
AFFIRMATIONS = (
    "yes", "no", "nope", "nah", "aye", "never", "always", "maybe",
    "sometimes", "not", "course",
)

# What somebody is called to their face when it is not their name. Only used to
# decide whether "Morning, X" is a greeting or a greeting plus a sentence.
ADDRESS_FORMS = (
    "new one", "mrs", "mr", "ms", "miss", "dr", "man", "mate", "son", "kid",
    "love", "pal", "friend", "boss", "chief", "brother", "sister", "sir",
    "ma'am", "everyone", "everybody", "folks", "you two", "the new one",
)

_WORD = re.compile(r"[a-z0-9']+")


def _words(text: str) -> list[str]:
    return _WORD.findall(str(text or "").lower())


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", str(text or "").strip())
    return [p.strip() for p in parts if p.strip()]


def _contains_word(text: str, candidates: tuple[str, ...]) -> bool:
    from .. import words as W

    return W.contains(text, candidates)


def longest_shared_run(said: str, previous: str, names: set[str]) -> int:
    """The longest run of consecutive words this line takes from the last one.

    Names are dropped from both sides first: "Morning, Sam" and "Morning, Jo"
    are the same greeting to two different people and neither is a parrot.
    """
    a = [w for w in _words(said) if w not in names]
    b = [w for w in _words(previous) if w not in names]
    if not a or not b:
        return 0
    best = 0
    # Small lines; the quadratic is fine and the alternative is unreadable.
    table = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                table[i][j] = table[i - 1][j - 1] + 1
                best = max(best, table[i][j])
    return best


def is_echo(said: str, previous: str, names: set[str], run: int = ECHO_RUN) -> bool:
    return longest_shared_run(said, previous, names) >= run


def says_own_name(said: str, own_names: set[str]) -> bool:
    """Their own name in their own mouth - unless they are introducing it.

    Self-introduction is how every name in town travels, so "I'm Sam" and
    "the name's Sam" are the mechanic working rather than a model slipping.
    """
    low = f" {str(said or '').lower()} "
    for name in own_names:
        name = name.lower()
        if not name:
            continue
        for match in re.finditer(rf"\b{re.escape(name)}\b", low):
            before = low[max(0, match.start() - 24):match.start()]
            if re.search(r"\b(i'?m|i am|name'?s|call me|it'?s|this is)\s*$", before):
                continue  # introducing themselves
            return True
    return False


def _is_address(sentence: str, name_words: set[str]) -> bool:
    """"Morning, Sam." and "Morning, new one." carry nothing. "Morning - he's
    gone." and "Yeah, he's about." carry a fact.

    A greeting, optionally followed by what somebody is called - a name, or one
    of the things people say instead of a name. Anything else after the comma
    is a sentence and counts.
    """
    parts = [p.strip() for p in sentence.strip().strip(".!?").split(",")]
    if not parts or _words(parts[0]) == []:
        return False
    if not all(w in GREETINGS for w in _words(parts[0])):
        return False
    for part in parts[1:]:
        low = part.lower().strip(". ")
        if low in ADDRESS_FORMS:
            continue
        words = _words(part)
        if words and all(w in name_words or w in ADDRESS_FORMS or len(w) == 1
                         for w in words):
            continue
        return False
    return True


def _is_self_introduction(sentence: str) -> bool:
    """"I'm Sam." does not answer "are you taking anyone on?".

    A name has to follow, or this eats real answers: "I'm good, thanks for
    asking" is five words beginning with "I'm" and is an answer to how you are.
    """
    text = sentence.strip().rstrip(".!?")
    if len(_words(text)) > 4:
        return False
    # Case-insensitive opener, case-SENSITIVE name: "I'm good" is an answer
    # and "I'm Sam" is an introduction, and the capital is the whole difference.
    return bool(re.match(
        r"^(?i:i'?m|i am|the name'?s|name'?s|call me)\s+[A-Z][a-z]+\s*$", text
    ))


def answers_nothing(said: str, name_words: set[str]) -> bool:
    """The reply carries no answer: only greetings, a name, or more questions.

    A proxy, and it will be wrong sometimes - people do answer questions with
    questions. It is here to be a number that moves rather than a verdict on a
    line.
    """
    text = said.strip()
    stripped = re.sub(r"^\s*[a-z']+[,\s-]+", "", text.lower())
    first = (_words(stripped) or _words(text) or [""])[0]
    if first in AFFIRMATIONS or (_words(text) or [""])[0] in AFFIRMATIONS:
        return False
    for sentence in _sentences(text):
        if not _words(sentence):
            continue
        if _is_address(sentence, name_words):
            continue
        if _is_self_introduction(sentence):
            continue
        if sentence.rstrip().endswith("?"):
            continue
        return False  # a declarative that is not a greeting: something was said
    return True


def score_conversations(conversations: list[dict[str, Any]],
                        names_by_id: dict[str, str]) -> dict[str, Any]:
    """The three counts, over every reply in every conversation given.

    A "reply" is any line with a line before it by the other person. The first
    line of a conversation cannot echo anything and cannot leave a question, so
    it is counted in `openings` and nowhere else.
    """
    all_name_words: set[str] = set()
    for full in names_by_id.values():
        all_name_words |= {w.lower() for w in str(full).split()}

    replies = openings = 0
    deals_asserted = deals_landed = names_given = 0
    echoes: list[dict[str, Any]] = []
    self_named: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    repeats: list[dict[str, Any]] = []
    questions = 0
    # What each person has already said today, so saying it again to somebody
    # else can be counted. Conversations are taken in the order they happened.
    said_today: dict[tuple[Any, str], list[str]] = {}

    for conv in sorted(conversations, key=lambda c: (c.get("day", 0), c.get("tick", 0))):
        lines = [dict(l) for l in (conv.get("lines") or []) if l.get("text")]
        # **Did anything land?** Shorter conversations are fine if things still
        # happen in them, and a cost if they do not. A deal is the channel this
        # game moves the world through.
        #
        # `names_given` needs reading with care. It counts somebody else's name
        # said out loud, which is how a name is *handed over* - but only when
        # the listener did not already have it. In a run with no player,
        # everybody is a seeded resident who holds all nineteen from the first
        # morning, so **nothing is actually transferred and what this measures
        # is how often people reach for each other's names**. Which is worth
        # measuring for its own reason: the frontier prompt tells them to use
        # first names "as punctuation", and this is that instruction, counted.
        # Lower is not automatically worse.
        for deal in (conv.get("deals") or []):
            deals_asserted += 1
            if deal.get("ok"):
                deals_landed += 1
        for index, line in enumerate(lines):
            said = str(line.get("text") or "")
            speaker = str(line.get("speaker") or "")
            own = {w.lower() for w in str(names_by_id.get(speaker, "")).split()}

            key = (conv.get("day"), speaker)
            earlier = said_today.setdefault(key, [])
            for before in earlier:
                if longest_shared_run(said, before, all_name_words) >= SELF_REPEAT_RUN:
                    repeats.append({
                        "day": conv.get("day"),
                        "who": names_by_id.get(speaker, speaker),
                        "earlier": before, "again": said,
                    })
                    break
            earlier.append(said)

            # A name said by anybody but the person it belongs to. Whole-word,
            # through the same matcher every keyword match in this codebase
            # uses. This is an approximation of `dialogue.names_said`: that one
            # also refuses to count a name the speaker does not hold, which
            # needs live state - in these runs everybody is a seeded resident
            # and holds all nineteen, so the filter is a no-op and the count is
            # exact. With a player in it, it would be an over-count.
            for other_id, full in sorted(names_by_id.items()):
                if other_id == speaker or not full:
                    continue
                first = full.split()[0]
                candidates = (full, first) if len(first) > 2 else (full,)
                if _contains_word(said, candidates):
                    names_given += 1

            if says_own_name(said, own):
                self_named.append({
                    "day": conv.get("day"), "who": names_by_id.get(speaker, speaker),
                    "said": said,
                })

            if index == 0:
                openings += 1
                continue
            previous = str(lines[index - 1].get("text") or "")
            if lines[index - 1].get("speaker") == speaker:
                continue  # two of their own lines in a row is not a reply
            replies += 1

            shared = longest_shared_run(said, previous, all_name_words)
            if shared >= ECHO_RUN:
                echoes.append({
                    "day": conv.get("day"), "shared_words": shared,
                    "they_said": previous, "the_reply": said,
                    "who": names_by_id.get(speaker, speaker),
                })

            if "?" in previous:
                questions += 1
                if answers_nothing(said, all_name_words):
                    dropped.append({
                        "day": conv.get("day"),
                        "asked": previous, "got_back": said,
                        "who": names_by_id.get(speaker, speaker),
                    })

    # The fifth count lives in its own module: what was attributed to
    # somebody, checked against what they said within the speaker's hearing.
    from . import attribution as ATTR

    attributed = ATTR.score(conversations, names_by_id)

    def pct(n: int, of: int) -> float:
        return round(100.0 * n / of, 1) if of else 0.0

    # **How much was said, as well as how bad it was.** Every rate below is a
    # percentage, and a percentage improves if the town simply talks less -
    # so the two counts that say whether it did sit next to them. A profile
    # that halves the echo rate by halving the conversation is not an
    # improvement, and there is no way to tell from a rate alone.
    per_conversation = round(
        (replies + openings) / len(conversations), 2
    ) if conversations else 0.0
    days = len({c.get("day") for c in conversations}) or 1

    def per_conv(n: int) -> float:
        return round(n / len(conversations), 2) if conversations else 0.0

    return {
        "conversations": len(conversations),
        "conversations_per_day": round(len(conversations) / days, 1),
        # -- did anything land -------------------------------------------
        "deals_asserted": deals_asserted,
        "deals_landed": deals_landed,
        "deals_per_conversation": per_conv(deals_asserted),
        "names_given": names_given,
        "names_given_per_conversation": per_conv(names_given),
        # Per line as well as per conversation, because the two answer
        # different questions when conversations get shorter: per conversation
        # falls if people simply say less, and per line is the rate at which
        # they reach for a name when they do speak.
        "names_given_per_line": round(
            names_given / (replies + openings), 2
        ) if (replies + openings) else 0.0,
        "lines": replies + openings,
        "lines_per_conversation": per_conversation,
        "replies": replies,
        "echoed_the_previous_line": len(echoes),
        "echoed_pct_of_replies": pct(len(echoes), replies),
        "said_their_own_name": len(self_named),
        "said_their_own_name_pct_of_lines": pct(len(self_named), replies + openings),
        "questions_asked": questions,
        "questions_left_on_the_floor": len(dropped),
        "questions_left_pct": pct(len(dropped), questions),
        "repeated_themselves": len(repeats),
        "repeated_themselves_pct_of_lines": pct(len(repeats), replies + openings),
        "attributions": attributed["attributions"],
        "misattributed": attributed["misattributed"],
        "misattributed_pct_of_attributions": attributed["misattributed_pct_of_attributions"],
        "examples": {
            "echo": echoes[:8],
            "own_name": self_named[:8],
            "unanswered": dropped[:8],
            "repeated_themselves": repeats[:8],
            "misattributed": attributed["examples"],
        },
    }
