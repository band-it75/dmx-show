import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from parameters import Scenario
from main import BeatDMXShow
import log
import numpy as np


def test_scenario_mapping():
    show = BeatDMXShow(genre_model=None)
    assert show._scenario_from_label("rock") == Scenario.SONG_ONGOING_ROCK
    assert show._scenario_from_label("classical") == Scenario.SONG_ONGOING_CLASSICAL

    expected = {
        "0": Scenario.SONG_ONGOING_DISCO,
        "1": Scenario.SONG_ONGOING_METAL,
        "2": Scenario.SONG_ONGOING_REGGAE,
        "3": Scenario.SONG_ONGOING_BLUES,
        "4": Scenario.SONG_ONGOING_ROCK,
        "5": Scenario.SONG_ONGOING_CLASSICAL,
        "6": Scenario.SONG_ONGOING_JAZZ,
        "7": Scenario.SONG_ONGOING_HIPHOP,
        "8": Scenario.SONG_ONGOING_COUNTRY,
        "9": Scenario.SONG_ONGOING_POP,
    }
    for digit, scenario in expected.items():
        assert show._scenario_from_label(digit) == scenario


def test_ai_log_single_entry(monkeypatch):

    class DummyGC:
        def __init__(self, *args, **kwargs):
            self.log_file = kwargs.get("log_file")

    import types, sys
    import src.audio as audio

    sys.modules["src.audio.genre_classifier"] = types.SimpleNamespace(GenreClassifier=DummyGC)
    audio.GenreClassifier = DummyGC
    show = BeatDMXShow()
    show._ai_log("entry")
    contents = log.log_file.read_text().splitlines()
    assert any("AI logging started" in line for line in contents)
    assert "entry" in contents[-1]



