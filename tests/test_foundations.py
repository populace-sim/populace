"""The clock and the config: small things everything else stands on."""

from __future__ import annotations

import pytest

from populace import clock
from populace.config import Config, ConfigError, PRESETS


def test_time_advances_across_midnight():
    t = clock.GameTime(day=1, tick=47).advance()
    assert (t.day, t.tick, t.weekday) == (2, 0, "Tuesday")
    assert clock.GameTime(day=1, tick=15).hhmm == "07:30"


def test_the_day_must_be_a_day():
    with pytest.raises(ValueError):
        clock.configure(48, 20)


def test_every_preset_builds_and_quick_says_it_is_low_fidelity():
    for name in PRESETS:
        assert Config.build(name).preset == name
    assert Config.build("quick").low_fidelity
    assert not Config.build("laptop").low_fidelity
    assert Config.build("quick").scheduler["calls_per_tick"] == 2
    assert Config.build("gpu").reflection["nightly_cap"] is None


def test_an_override_reaches_the_section_that_is_read():
    """In Alive a config override for two sections never reached the prompt,
    because the prompt read the defaults table. Here the only way to read a
    number is through a loaded Config."""
    config = Config.build("laptop", {"needs": {"kinds": {"hunger": {"rate": 3.0}}}})
    assert config.needs["kinds"]["hunger"]["rate"] == 3.0
    assert config.needs["kinds"]["hunger"]["urgent_above"] == 70.0  # untouched siblings kept


def test_a_model_url_points_the_local_provider_somewhere_else():
    config = Config.build("gpu", {"providers": {"local": {"base_url": "http://pc:8080/v1"}}})
    assert config.provider_settings("local") == {"base_url": "http://pc:8080/v1", "max_concurrency": 8}


def test_nonsense_is_refused_loudly():
    with pytest.raises(ConfigError):
        Config.build("turbo")
    with pytest.raises(ConfigError):
        Config.build("laptop", {"scheduler": {"calls_per_tick": 0}})
    with pytest.raises(ConfigError):
        Config.build("laptop", {"needs": {"kinds": {"thirst": {"rate": 1, "words": ["a", "b"]}}}})


def test_one_name_book_turns_ids_back_into_names(tmp_path):
    from populace.observe.names import NameBook

    book = NameBook({"r001": "Shu Yamada", "r002": "Yumi Yamada"})
    assert book.restore("[r001] talked to r002; r999 was not there") == \
        "Shu Yamada talked to Yumi Yamada; r999 was not there"
    assert book.label("r001") == "Shu Yamada (r001)"
    assert book.find("yumi yamada") == "r002" and book.find("r001") == "r001"
    assert book.find("Nobody") is None
    book.save(tmp_path)
    assert NameBook.load(tmp_path).names == book.names
