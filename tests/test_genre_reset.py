import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parameters import Scenario
from main import BeatDMXShow
from src.audio.beat_detection import SongState

class DummyDashboard:
    def __init__(self):
        self.genre = None
        self.state = None
        self.groups = {}
    def set_genre(self, name):
        self.genre = name
    def set_state(self, state):
        self.state = state
    def set_group(self, name, vals):
        self.groups[name] = vals


class DummyCtrl:
    def update(self):
        pass

    def reset(self):
        pass


def test_genre_cleared_on_state_change():
    show = BeatDMXShow(dashboard=False, genre_model=None)
    show.dashboard_enabled = True
    show.dashboard = DummyDashboard()
    show.controller = DummyCtrl()
    show.last_genre = Scenario.SONG_ONGOING_ROCK
    show._handle_state_change(SongState.STARTING)
    assert show.last_genre is None
    assert show.dashboard.genre == ""
