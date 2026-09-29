"""Anything the engine can do appears in a prompt, and the prompt's shape is frozen.

Alive lost four live runs to actions and deals that existed in the engine and
in no prompt: a model cannot choose what it is never told exists.
"""

from __future__ import annotations

from populace.prompt import profiles, rules
from populace.sim import actions as A


def test_every_action_is_described_in_your_reply():
    reply = rules.YOUR_REPLY
    options = reply.split('"action": one of', 1)[1].split(",", 1)[0]
    listed = {w.strip() for w in options.split("|")}
    assert listed == set(A.ACTION_TYPES)


def test_every_action_the_engine_validates_is_in_the_list():
    assert set(A.ACTION_TYPES) == set(rules.ACTION_TYPES)


def test_every_deal_in_the_menu_is_written_out():
    menu = rules._deal_menu()
    for kind in rules.DEAL_KINDS:
        assert f'"kind": "{kind}"' in menu


def test_your_reply_is_byte_identical_in_both_profiles():
    needs = {"kinds": {"hunger": {"urgent_above": 70, "words": ["a", "b"]}}}
    texts = {p: rules.world_rules(p, "T", "a town", needs) for p in profiles.PROFILES}
    for text in texts.values():
        assert rules.YOUR_REPLY in text


def test_the_section_order_is_the_fine_tunes():
    frontier = rules.section_names("frontier")
    compact = rules.section_names("compact")
    assert [s for s in frontier if s != "WORKED EXAMPLES"] == compact
    order = ["HOW YOU SEE THE WORLD", "HEARSAY", "TIME AND MOVEMENT", "NEEDS", "MONEY", "LOANS",
             "RENT", "WORK", "WHAT YOU CAN MAKE HAPPEN", "CONVERSATION", "HOW YOU FEEL ABOUT PEOPLE",
             "REMEMBERING", "WHAT PEOPLE DO WITH WHAT THEY KNOW", "VOICE", "HOW TO DECIDE",
             "YOUR REPLY", "WORKED EXAMPLES", "TRUST", "NEWCOMERS AND NEIGHBOURS", "NOTHING TO DO",
             "RULES ABOUT TARGETS"]
    assert frontier == order


def test_every_deal_in_the_menu_has_a_handler_and_no_handler_is_hidden():
    from populace.sim import deals
    assert sorted(rules.DEAL_KINDS) == deals.kinds()
