"""The three conversation metrics, held to the lines that produced them.

Every example here is verbatim from the gate playtest's four days
(in Alive, the project populace came from). They are the reason the module exists, so they are what
it is tested against - and each one is paired with a line that must NOT count,
because a metric that fires on everything measures nothing.
"""

from __future__ import annotations

from populace.observe import voice as V

NAMES = {
    "castro": "Nora Castro", "moreno": "Helen Moreno",
    "pike": "Walter Pike", "marsh": "Leon Marsh",
    "kowal": "Eddie Kowal", "drake": "Owen Drake", "adeyemi": "Iris Adeyemi",
    "player": "Robin Hale",
}
ALL_NAME_WORDS = {w.lower() for n in NAMES.values() for w in n.split()}


# -- echo -----------------------------------------------------------------


def test_the_crossword_line_handed_straight_back():
    assert V.is_echo(
        "Morning, Nora. Still got the crossword numbers in?",
        "Morning, Mrs. M. Still got the crossword numbers in?",
        ALL_NAME_WORDS,
    )


def test_the_forty_dollars_handed_straight_back():
    assert V.is_echo(
        "Sure, Owen. What happened with Theo's forty dollars?",
        "Iris, got a minute? I need to know what happened with Theo's forty dollars.",
        ALL_NAME_WORDS,
    )


def test_two_different_greetings_are_not_an_echo():
    """"Morning, Nora" and "Morning, Leon" are the same greeting to two people."""
    assert not V.is_echo("Morning, Leon.", "Morning, Nora.", ALL_NAME_WORDS)


def test_a_real_answer_that_shares_words_is_not_an_echo():
    assert not V.is_echo(
        "He's good. Site's been steady since the rain stopped.",
        "How's Theo doing?",
        ALL_NAME_WORDS,
    )


def test_three_shared_words_is_a_phrase_and_four_is_a_parrot():
    names: set[str] = set()
    assert not V.is_echo("still got the milk", "still got the numbers", names)
    assert V.is_echo("still got the numbers in", "still got the numbers in", names)


# -- a speaker saying their own name --------------------------------------


def test_walter_calling_himself_walter():
    assert V.says_own_name("Sure, Walter. What's on your mind?", {"walter", "pike"})


def test_introducing_yourself_is_the_mechanic_working():
    """It is the only way anybody on this town learns a name."""
    assert not V.says_own_name("Morning, new one. I'm Leon.", {"leon", "marsh"})
    assert not V.says_own_name("The name's Leon.", {"leon", "marsh"})


def test_saying_somebody_else_s_name_is_just_talking():
    assert not V.says_own_name("Morning, Nora.", {"walter", "pike"})


# -- a question left on the floor -----------------------------------------


def test_ray_never_answered_whether_he_was_hiring():
    assert V.answers_nothing(
        "Morning, new one. I'm Leon. How's Theo holding up?", ALL_NAME_WORDS
    )


def test_a_greeting_on_its_own_answers_nothing():
    assert V.answers_nothing("Morning, Leon.", ALL_NAME_WORDS)


def test_an_actual_answer_counts_as_one():
    assert not V.answers_nothing("Not right now. Come back Monday.", ALL_NAME_WORDS)


def test_a_question_that_answers_first_is_an_answer():
    assert not V.answers_nothing("Yes - why, are you looking?", ALL_NAME_WORDS)


# -- the whole thing over a transcript ------------------------------------


def _conv(day: int, *lines: tuple[str, str]) -> dict:
    return {"day": day, "lines": [{"speaker": s, "text": t} for s, t in lines]}


def test_the_scene_that_produced_all_three_scores_all_three():
    result = V.score_conversations([
        _conv(1,
              ("castro", "Morning, Mrs. M. Still got the crossword numbers in?"),
              ("moreno", "Morning, Nora. Still got the crossword numbers in?")),
        _conv(1,
              ("player", "Are you taking anyone on?"),
              ("marsh", "Morning, new one. I'm Leon. How's Theo holding up?")),
        _conv(2,
              ("pike", "Got a minute? I need to talk about something."),
              ("castro", "Sure, Walter. What's on your mind?"),
              ("pike", "Sure, Walter. What's on your mind?")),
    ], NAMES)
    assert result["echoed_the_previous_line"] >= 1
    assert result["questions_left_on_the_floor"] >= 2
    # Walter calling himself Walter; Nora calling Walter Walter is not counted.
    assert result["said_their_own_name"] == 1
    assert result["examples"]["own_name"][0]["who"] == "Walter Pike"


def test_a_clean_exchange_scores_zero_on_all_three():
    """Or the numbers below are noise rather than a baseline."""
    result = V.score_conversations([
        _conv(1,
              ("marsh", "You back on the site tomorrow?"),
              ("kowal", "If the rain holds off. Otherwise Thursday."),
              ("marsh", "Thursday's no good. I need the frame up."),
              ("kowal", "Then I'll come wet.")),
    ], NAMES)
    assert result["echoed_the_previous_line"] == 0
    assert result["said_their_own_name"] == 0
    assert result["questions_left_on_the_floor"] == 0
    assert result["questions_asked"] == 1


def test_an_affirmation_answers_even_when_the_rest_is_a_question():
    assert not V.answers_nothing("Yeah, he's about. Why?", ALL_NAME_WORDS)
    assert not V.answers_nothing("No. Not this week.", ALL_NAME_WORDS)


def test_a_greeting_with_a_sentence_after_it_is_not_a_greeting():
    """The rule has to tell "Morning, Leon." from "Morning - he's gone."."""
    assert V.answers_nothing("Morning, Leon.", ALL_NAME_WORDS)
    assert not V.answers_nothing("Morning - he's gone.", ALL_NAME_WORDS)
    assert V.answers_nothing("Morning, new one.", ALL_NAME_WORDS)


def test_i_am_good_is_an_answer_and_i_am_ray_is_an_introduction():
    """Five words beginning with "I'm" ate a real answer the first time."""
    assert not V.answers_nothing(
        "Morning, Vic. Still on the crosswords, huh? I'm good, thanks for asking.",
        ALL_NAME_WORDS,
    )
    assert V.answers_nothing("Morning, new one. I'm Leon. How's Theo?", ALL_NAME_WORDS)


# -- the fourth, which the first three miss -------------------------------


def test_saying_the_same_thing_to_two_people_in_a_morning():
    """Verbatim from day 1. The prompt says not to; a 7B does it anyway."""
    result = V.score_conversations([
        {"day": 1, "tick": 18, "lines": [
            {"speaker": "adeyemi", "text": "Morning, Walter. Just here for the coffee, as usual."},
            {"speaker": "pike", "text": "It's the good stuff today."},
        ]},
        {"day": 1, "tick": 23, "lines": [
            {"speaker": "adeyemi", "text": "Morning, Nora. Just here for the coffee, as usual."},
            {"speaker": "castro", "text": "Then you're in luck."},
        ]},
    ], {**NAMES, "adeyemi": "Iris Adeyemi"})
    assert result["repeated_themselves"] == 1
    assert result["examples"]["repeated_themselves"][0]["who"] == "Iris Adeyemi"


def test_the_same_line_on_a_different_day_is_a_habit_and_not_a_repeat():
    """People do say the same thing every morning. The rule is per day."""
    result = V.score_conversations([
        {"day": 1, "tick": 18, "lines": [
            {"speaker": "adeyemi", "text": "Morning, Walter. Just here for the coffee, as usual."},
            {"speaker": "pike", "text": "It's the good stuff today."},
        ]},
        {"day": 2, "tick": 18, "lines": [
            {"speaker": "adeyemi", "text": "Morning, Walter. Just here for the coffee, as usual."},
            {"speaker": "pike", "text": "It's the good stuff today."},
        ]},
    ], {**NAMES, "adeyemi": "Iris Adeyemi"})
    assert result["repeated_themselves"] == 0


# -- how much was said, not only how bad it was ---------------------------


def test_the_counts_that_say_whether_a_rate_improved_by_talking_less():
    """Every other number is a percentage, and a percentage improves if the
    town simply says less. These are how you tell."""
    result = V.score_conversations([
        _conv(1,
              ("marsh", "You back tomorrow?"),
              ("kowal", "If the rain holds."),
              ("marsh", "It won't."),
              ("kowal", "Then I'll come wet.")),
        _conv(1,
              ("pike", "Cold one."),
              ("castro", "It is.")),
    ], NAMES)
    assert result["conversations"] == 2
    assert result["lines"] == 6
    assert result["lines_per_conversation"] == 3.0
    assert result["conversations_per_day"] == 2.0


def test_conversations_per_day_is_per_day_and_not_per_run():
    result = V.score_conversations([
        _conv(1, ("pike", "Cold one."), ("castro", "It is.")),
        _conv(2, ("pike", "Warmer."), ("castro", "Bit.")),
        _conv(2, ("pike", "Same again?"), ("castro", "Go on.")),
    ], NAMES)
    assert result["conversations_per_day"] == 1.5


def test_an_empty_run_does_not_divide_by_zero():
    """A 2.7-hour control once scored zero conversations. It must report that
    rather than raise, or the harness looks broken instead of the run."""
    result = V.score_conversations([], NAMES)
    assert result["conversations"] == 0
    assert result["lines_per_conversation"] == 0.0


# -- and whether anything actually landed ---------------------------------


def test_deals_asserted_and_deals_that_landed_are_different_numbers():
    """A deal somebody had no standing for is a thing they said and did not do,
    and the difference between the two counts is exactly that."""
    result = V.score_conversations([
        {"day": 1, "tick": 20, "lines": [
            {"speaker": "marsh", "text": "Start Monday. Bring a hammer."},
            {"speaker": "kowal", "text": "I'll be there."},
        ], "deals": [{"kind": "hire", "ok": True, "speaker": "marsh"},
                     {"kind": "hire", "ok": False, "speaker": "kowal",
                      "reason": "no work going"}]},
    ], NAMES)
    assert result["deals_asserted"] == 2
    assert result["deals_landed"] == 1
    assert result["deals_per_conversation"] == 2.0


def test_a_conversation_where_nothing_was_settled_scores_zero():
    result = V.score_conversations([
        _conv(1, ("pike", "Cold one."), ("castro", "It is."))
    ], NAMES)
    assert result["deals_asserted"] == 0
    assert result["deals_per_conversation"] == 0.0


def test_a_name_given_is_somebody_else_s_name_said_out_loud():
    """The one thing a conversation can hand over that costs nobody anything."""
    result = V.score_conversations([
        _conv(1,
              ("pike", "Nora, this is Leon. He's on the site."),
              ("castro", "Morning.")),
    ], NAMES)
    # Walter said two names that are not his: Nora's and Leon's.
    assert result["names_given"] == 2
    assert result["names_given_per_conversation"] == 2.0


def test_saying_your_own_name_is_not_giving_somebody_else_s():
    """It is counted under `said_their_own_name` and must not be double-counted
    as a name handed over - the man already had it."""
    result = V.score_conversations([
        _conv(1, ("pike", "Sure, Walter. What's on your mind?"),
                 ("castro", "Nothing.")),
    ], NAMES)
    assert result["said_their_own_name"] == 1
    assert result["names_given"] == 0


def test_shorter_is_fine_if_things_still_land():
    """The whole reason these two columns exist. Two profiles, one with half
    the lines, and the one that says less settles more."""
    talky = V.score_conversations([
        _conv(1, ("pike", "Cold one."), ("castro", "It is."),
                 ("pike", "Right."), ("castro", "Mm.")),
    ], NAMES)
    brief = V.score_conversations([
        {"day": 1, "tick": 20, "lines": [
            {"speaker": "marsh", "text": "Start Monday."},
            {"speaker": "kowal", "text": "I'll be there."},
        ], "deals": [{"kind": "hire", "ok": True, "speaker": "marsh"}]},
    ], NAMES)
    assert brief["lines_per_conversation"] < talky["lines_per_conversation"]
    assert brief["deals_per_conversation"] > talky["deals_per_conversation"]
