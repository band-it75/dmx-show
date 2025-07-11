from parameters import Scenario
from main import BeatDMXShow


def test_scenario_mapping():
    show = BeatDMXShow(genre_model=None)
    assert show._scenario_from_label("rock") == Scenario.SONG_ONGOING_ROCK
    assert show._scenario_from_label("classical") == Scenario.SONG_ONGOING_SLOW
