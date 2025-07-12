import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from parameters import Scenario
from main import BeatDMXShow


def test_scenario_mapping():
    show = BeatDMXShow(genre_model=None)
    assert show._scenario_from_label("rock") == Scenario.SONG_ONGOING_ROCK
    assert show._scenario_from_label("classical") == Scenario.SONG_ONGOING_SLOW


def test_ai_log_single_entry(tmp_path, monkeypatch):
    log_file = tmp_path / "ai.log"

    class DummyGC:
        def __init__(self, log_file=None, verbose=False):
            self.log_file = log_file

    import types, sys
    import src.audio as audio

    sys.modules["src.audio.genre_classifier"] = types.SimpleNamespace(GenreClassifier=DummyGC)
    audio.GenreClassifier = DummyGC
    show = BeatDMXShow(ai_log_path=str(log_file))
    show._ai_log("entry")
    show.ai_log_handle.close()
    contents = log_file.read_text().splitlines()
    assert contents == ["AI logging started", "entry"]
