"""Who witnesses what, what gets written, and what gets recalled later.

Ported from Alive's `memory.py`: the witness funnel, the three renderings a
single event produces (the actor's first person, the target's first person, and
the bystanders' public text, each passed through `as_seen_by`), and retrieval
by recency, importance and relevance with no embeddings and no extra call.

Left behind: object-state claims, and the theft, accusation and ownership
detectors, which belonged to systems populace does not have.

The off-town place is where nobody can see anybody: a commuter at their job in
the city is not in a room with the other commuters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..state.resident import Memory, Resident
from .events import Event, TARGET_REMEMBERS, as_seen_by, private_text, public_text, target_text

if TYPE_CHECKING:  # pragma: no cover
    from ..state.town import Town

# Things that reach you whether or not your eyes are open: your own body and
# your own books.
ALWAYS_REACHES_THE_ACTOR = {
    "woken", "sleep", "wake", "rent_paid", "rent_missed", "wage", "no_show",
    "debt_overdue", "hired", "fired", "date", "text_received",
}


@dataclass
class ObservationContext:
    """What the resident is looking at right now, used to rank memories."""

    location_id: str
    present_ids: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)


def witnesses(town: "Town", event: Event) -> list[str]:
    """Awake residents at the scene, excluding the actor. Sorted."""
    if event.is_private or town.world.is_offtown(event.location_id):
        return []
    return [
        rid for rid in town.world.occupants(event.location_id)
        if rid != event.actor and not town.residents[rid].asleep
    ]


def record(town: "Town", event: Event, actor_importance: int | None = None) -> list[str]:
    return record_with_witnesses(town, event, witnesses(town, event), actor_importance)


def record_with_witnesses(
    town: "Town",
    event: Event,
    witness_ids: list[str],
    actor_importance: int | None = None,
    skip_actor: bool = False,
) -> list[str]:
    """Fan one event out into memories. Returns who remembers it.

    Witnesses are captured at the instant the event happened and passed in:
    somebody who left before you arrived did not see you arrive.
    """
    place_name = town.world.place_by_id(event.location_id).name
    time = town.world.time
    remembered_by: list[str] = []

    actor = town.residents.get(event.actor) if not skip_actor else None
    if actor is not None and not (actor.asleep and event.kind not in ALWAYS_REACHES_THE_ACTOR):
        actor.remember(
            time,
            # Even your own account names the other person, and you only have
            # their name if somebody gave it to you.
            as_seen_by(private_text(event, actor, place_name), actor, town),
            importance=actor_importance if actor_importance is not None else event.base_importance,
            involved=event.involved(),
            location_id=event.location_id,
        )
        town.touch(actor.id)
        remembered_by.append(actor.id)

    # Nobody forms a durable memory of a stranger walking past. A background
    # event (importance under 3) is kept only when it involves somebody the
    # witness has dealings with.
    involved = set(event.involved())
    seen_by_others = [
        rid for rid in witness_ids
        if rid in town.residents and not town.residents[rid].asleep
        and (event.base_importance >= 3 or involved & set(town.residents[rid].relationships))
    ]
    text = public_text(event, place_name)
    for rid in seen_by_others:
        witness = town.residents[rid]
        if rid == event.target and event.kind in TARGET_REMEMBERS:
            written = as_seen_by(target_text(event, witness, place_name), witness, town)
        else:
            written = as_seen_by(text, witness, town)
        witness.remember(time, written, importance=event.base_importance,
                         involved=event.involved(), location_id=event.location_id)
        town.touch(rid)
        remembered_by.append(rid)

    if seen_by_others:
        entry = event.to_dict()
        entry["witnesses"] = seen_by_others
        town.world.log_public(entry)
    return remembered_by


STOPWORDS = frozenset(
    """a an and are as at be been but by came come for from get got had has have
    her here him his i in into is it its me my no not of on one only or our out
    over said she so some than that the their them then there they this to told
    too up was we went were what when where which who will with would you your""".split()
)

# Different words for the same kind of moment, so a memory about an argument
# surfaces when an argument is happening.
VERB_STEMS = {
    "argued": "conflict", "argue": "conflict", "arguing": "conflict",
    "fought": "conflict", "fight": "conflict", "yelled": "conflict",
    "shouted": "conflict", "row": "conflict", "snapped": "conflict",
    "paid": "money", "pay": "money", "owed": "money", "owe": "money",
    "rent": "money", "cash": "money", "short": "money", "bill": "money",
    "bought": "money", "buy": "money", "cost": "money", "borrowed": "money",
    "ate": "food", "eat": "food", "eating": "food", "hungry": "food",
    "meal": "food", "sandwich": "food", "coffee": "food", "breakfast": "food",
    "shift": "work", "working": "work", "worked": "work", "job": "work",
    "slept": "rest", "sleep": "rest", "tired": "rest", "woke": "rest",
    "talked": "talk", "told": "talk", "asked": "talk", "said": "talk",
    "texted": "talk", "called": "talk", "phoned": "talk",
}


def _content_words(text: str) -> set[str]:
    cleaned = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in text.lower())
    words = set()
    for word in cleaned.split():
        if word in STOPWORDS or len(word) < 3:
            continue
        words.add(VERB_STEMS.get(word, word))
    return words


def score_memory(memory: Memory, ctx: ObservationContext, now_ticks: int, weights: dict) -> float:
    """Recency, weight and relevance: no embeddings, no extra model call.

    Relevance is dominated by exact entities (who is here, where we are); word
    overlap only breaks ties between similar moments.
    """
    halflife = float(weights.get("recency_halflife_ticks", 48))
    ticks_ago = max(0, now_ticks - memory.total_ticks)
    recency = 0.5 ** (ticks_ago / halflife)

    ctx_entities = set(ctx.present_ids) | {ctx.location_id}
    mem_entities = set(memory.involved) | ({memory.location_id} if memory.location_id else set())
    entity_overlap = len(mem_entities & ctx_entities) / max(1, len(ctx_entities))

    ctx_words = _content_words(" ".join(ctx.keywords))
    mem_words = _content_words(memory.text)
    word_overlap = len(ctx_words & mem_words) / len(ctx_words) if ctx_words else 0.0

    relevance = min(1.0, 2.0 * entity_overlap + 0.5 * word_overlap)
    return (
        float(weights.get("w_recency", 1.0)) * recency
        + float(weights.get("w_importance", 0.7)) * (memory.importance / 10)
        + float(weights.get("w_relevance", 1.2)) * relevance
    )


def retrieve(
    resident: Resident,
    ctx: ObservationContext,
    cap: int = 12,
    now_ticks: int | None = None,
    weights: dict | None = None,
) -> list[Memory]:
    """The memories to put in front of the model this tick, oldest first.

    Beliefs and reflections are excluded: they already sit in the resident's
    own cached block, and repeating them would pay for the same text twice.
    """
    weights = weights or {}
    raw = [m for m in resident.memory if m.kind in {"observation", "dialogue"}]
    if not raw:
        return []
    if now_ticks is None:
        now_ticks = max(m.total_ticks for m in raw)
    chronological = sorted(raw, key=lambda m: (m.total_ticks, m.id))
    chosen: dict[int, Memory] = {}
    # Whatever just happened is always on your mind, however trivial.
    for mem in chronological[-int(weights.get("guaranteed_recent", 3)):]:
        chosen[mem.id] = mem
    # So is anything that genuinely shook you, however long ago.
    threshold = int(weights.get("high_importance_threshold", 9))
    heavy = sorted((m for m in raw if m.importance >= threshold),
                   key=lambda m: (-m.importance, -m.total_ticks, m.id))
    for mem in heavy[: int(weights.get("guaranteed_high_importance", 3))]:
        chosen[mem.id] = mem
    ranked = sorted(raw, key=lambda m: (-score_memory(m, ctx, now_ticks, weights),
                                        -m.total_ticks, m.id))
    for mem in ranked:
        if len(chosen) >= cap:
            break
        chosen.setdefault(mem.id, mem)
    return sorted(chosen.values(), key=lambda m: (m.total_ticks, m.id))[-cap:]


def enforce_raw_cap(resident: Resident, cap: int = 200) -> int:
    """Hard ceiling on raw memories: lowest importance and oldest go first.
    Reflections and beliefs are never dropped here."""
    raw = [m for m in resident.memory if m.kind in {"observation", "dialogue"}]
    excess = len(raw) - cap
    if excess <= 0:
        return 0
    doomed = {m.id for m in sorted(raw, key=lambda m: (m.importance, m.total_ticks, m.id))[:excess]}
    resident.memory = [m for m in resident.memory if m.id not in doomed]
    return len(doomed)
