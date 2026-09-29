"""The fifth voice metric: putting words in somebody's mouth.

The adapter's friendship morning (in Alive, the project populace came from) had Nora say *"Iris said
you came in yesterday"* to a newcomer Iris had never mentioned. No name
outside town, no leak of the player's name, valid JSON - and a fact
about what a neighbour said, made up. This counts those: a line that
attributes speech to a named person is checked against what that person
actually said within the speaker's hearing, and an attribution nothing they
said supports is a misattribution.
"""

from __future__ import annotations

from populace.observe import voice as V

NAMES = {
    "castro": "Nora Castro", "adeyemi": "Iris Adeyemi", "pike": "Walter Pike",
    "marsh": "Leon Marsh", "player": "Robin Hale",
}


def _conv(day, tick, participants, *lines, overheard_by=()):
    return {
        "day": day, "tick": tick, "participants": list(participants),
        "overheard_by": list(overheard_by),
        "lines": [{"speaker": s, "text": t} for s, t in lines],
    }


def test_a_planted_misattribution_is_counted():
    """Iris only ever talked about the crossword; Nora says she said more."""
    result = V.score_conversations([
        _conv(1, 10, ["adeyemi", "castro"],
              ("adeyemi", "Morning. The crossword's done, finally."),
              ("castro", "Good for you.")),
        _conv(1, 20, ["castro", "player"],
              ("player", "Hello."),
              ("castro", "Iris said you came in yesterday, baby.")),
    ], NAMES)
    assert result["attributions"] == 1
    assert result["misattributed"] == 1
    example = result["examples"]["misattributed"][0]
    assert example["who"] == "Nora Castro" and example["about"] == "Iris Adeyemi"
    assert example["kind"] == "nothing_like_it"


def test_a_true_attribution_passes():
    """Iris did say it, to Nora, earlier that morning."""
    result = V.score_conversations([
        _conv(1, 10, ["adeyemi", "castro"],
              ("adeyemi", "That new one came in yesterday, didn't they?"),
              ("castro", "They did.")),
        _conv(1, 20, ["castro", "player"],
              ("player", "Hello."),
              ("castro", "Iris said you came in yesterday, baby.")),
    ], NAMES)
    assert result["attributions"] == 1
    assert result["misattributed"] == 0


def test_attributing_to_somebody_you_never_heard_is_a_misattribution():
    result = V.score_conversations([
        _conv(1, 20, ["castro", "player"],
              ("player", "Any work about?"),
              ("castro", "Leon told me the site's short-handed this week.")),
    ], NAMES)
    assert result["misattributed"] == 1
    assert result["examples"]["misattributed"][0]["kind"] == "never_heard_them"


def test_hearing_is_being_there_not_being_on_the_block():
    """Iris said it to Walter. Nora was not in the room - unless she was."""
    said_to_walter = _conv(1, 10, ["adeyemi", "pike"],
                          ("adeyemi", "The site's short-handed this week, Leon says."),
                          ("pike", "Is it."))
    nora = _conv(1, 20, ["castro", "player"],
                ("player", "Any work about?"),
                ("castro", "Iris said the site's short-handed this week."))
    absent = V.score_conversations([said_to_walter, nora], NAMES)
    assert absent["misattributed"] == 1
    present = V.score_conversations([
        {**said_to_walter, "overheard_by": ["castro"]}, nora,
    ], NAMES)
    assert present["misattributed"] == 0


def test_what_they_say_later_does_not_count():
    """The order matters: Iris saying it in the afternoon does not make Nora's
    morning line true."""
    result = V.score_conversations([
        _conv(1, 20, ["castro", "player"],
              ("player", "Hello."),
              ("castro", "Iris said you came in yesterday.")),
        _conv(1, 30, ["adeyemi", "castro"],
              ("adeyemi", "That new one came in yesterday, didn't they?"),
              ("castro", "They did.")),
    ], NAMES)
    assert result["misattributed"] == 1


def test_an_attribution_with_nothing_to_check_is_not_scored():
    """"Iris said so" carries no content to be wrong about."""
    result = V.score_conversations([
        _conv(1, 20, ["castro", "player"],
              ("player", "Is the shop open Sundays?"),
              ("castro", "Iris said so.")),
    ], NAMES)
    assert result["attributions"] == 0
    assert result["misattributed"] == 0


def test_a_line_with_no_attribution_in_it_is_left_alone():
    result = V.score_conversations([
        _conv(1, 20, ["castro", "player"],
              ("player", "Hello."),
              ("castro", "Iris was in earlier. She's well.")),
    ], NAMES)
    assert result["attributions"] == 0


def test_a_transcript_reads_back_as_conversations():
    """The three baselines exist only as `playtest.transcript.md`; the reader
    has to recover who spoke to whom, where, and whether the player was
    standing there, or the metric cannot be run on them at all."""
    text = """# Two weeks on Elm Street

## Day 1

    [depart] Walter Pike
  * [Castro's Grocery] Nora Castro: "Morning, baby."
  * [Castro's Grocery] Iris Adeyemi: "Morning. The crossword's done."
    [The Anchor] Walter Pike: "Leon said the site's short-handed."
    [The Anchor] Leon Marsh: "Did I."
    [arrive] Walter Pike

## Day 2

    [Castro's Grocery] Nora Castro: "Iris said the crossword's done."
    [Castro's Grocery] Robin Hale: "Good."
"""
    convs = V.conversations_from_transcript(text, NAMES)
    assert [c["day"] for c in convs] == [1, 1, 2]
    assert convs[0]["participants"] == ["castro", "adeyemi"]
    assert convs[0]["overheard_by"] == ["player"]       # starred: the player was there
    assert convs[1]["participants"] == ["pike", "marsh"]
    assert convs[1]["overheard_by"] == []
    assert convs[2]["participants"] == ["castro", "player"]
    assert convs[0]["tick"] < convs[1]["tick"] < convs[2]["tick"]
    scored = V.score_conversations(convs, NAMES)
    # Walter attributes to Leon something Leon never said; Nora attributes to
    # Iris something Iris did say to her on day 1.
    assert scored["attributions"] == 2
    assert scored["misattributed"] == 1
    assert scored["examples"]["misattributed"][0]["who"] == "Walter Pike"


def test_a_day_window_keeps_only_the_days_asked_for():
    """The fortnight is read in two halves to see whether the adapter drifts;
    the window is inclusive at both ends and 0 means no bound."""
    convs = [_conv(d, 10, ["castro", "adeyemi"], ("adeyemi", "Morning.")) for d in range(1, 13)]
    assert [c["day"] for c in V.select_days(convs, 1, 4)] == [1, 2, 3, 4]
    assert [c["day"] for c in V.select_days(convs, 9, 0)] == [9, 10, 11, 12]
    assert [c["day"] for c in V.select_days(convs, 0, 2)] == [1, 2]
    assert len(V.select_days(convs, 0, 0)) == 12
