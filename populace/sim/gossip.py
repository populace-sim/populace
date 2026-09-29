"""How freely somebody passes a thing on.

Ported from Alive's `gossip.py`, the dispositions only. Each resident's comes
from generation (`persona.gossip`), so a town's pattern of who tells whom is
characterful rather than uniform: a single global nudge would make everybody
behave the same way, which is the failure this exists to avoid. The till and
officer lookups that went with it belonged to one street and stay behind.
"""

from __future__ import annotations

from ..state.resident import Resident

TALKER = "talker"
CONFIDER = "confider"
KEEPER = "keeper"
DEFAULT_DISPOSITION = CONFIDER

DISPOSITIONS: dict[str, str] = {
    TALKER: ("You are one of the people news travels through in this town. If you know a "
             "thing, saying it is the natural next move, and you do not need much of a reason."),
    CONFIDER: ("You do not broadcast, but you tell the one or two people you actually trust, "
               "and you tell somebody it was done to. What you know does not usually keep for long."),
    KEEPER: ("You keep things. Not out of loyalty exactly - it is that saying a thing out loud "
             "makes it yours to have said. It takes something real to get it out of you, and "
             "you are the exception here."),
}


def disposition(resident: Resident) -> str:
    value = str((resident.persona or {}).get("gossip") or "").strip().lower()
    return value if value in DISPOSITIONS else DEFAULT_DISPOSITION


def disposition_words(resident: Resident) -> str:
    return DISPOSITIONS[disposition(resident)]
