import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parameters import Scenario
from main import BeatDMXShow


class DummyCtrl:
    def update(self):
        pass

    def reset(self):
        pass


def test_intermission_to_start_allowed():
    show = BeatDMXShow(genre_model=None)
    show.controller = DummyCtrl()
    show.scenario = Scenario.INTERMISSION
    show._set_scenario(Scenario.SONG_START)
    assert show.scenario is Scenario.SONG_START


def test_start_to_intermission_blocked():
    show = BeatDMXShow(genre_model=None)
    show.controller = DummyCtrl()
    show.scenario = Scenario.SONG_START
    show._set_scenario(Scenario.INTERMISSION)
    assert show.scenario is Scenario.SONG_START
