import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import parameters
from main import BeatDMXShow


def test_vu_to_level_scale():
    zero = BeatDMXShow._vu_to_level(0.0)
    threshold = BeatDMXShow._vu_to_level(parameters.VU_PULSE_THRESHOLD)
    full = BeatDMXShow._vu_to_level(parameters.VU_FULL)
    above = BeatDMXShow._vu_to_level(parameters.VU_FULL * 2)
    low = BeatDMXShow._vu_to_level(parameters.VU_FULL / 10)
    mid = BeatDMXShow._vu_to_level(parameters.VU_FULL / 2)
    high = BeatDMXShow._vu_to_level(
        (parameters.VU_FULL + parameters.VU_PULSE_THRESHOLD) / 2
    )
    assert zero == 25
    assert threshold == 25
    assert full == 175
    assert above == 175
    assert low == 25
    assert mid == 25
    assert 25 < high < full


import numpy as np
from src.audio.beat_detection import SongState

class DummyDetector:
    def __init__(self) -> None:
        self.state = SongState.ONGOING
        self.snare_hit = True
        self.is_chorus = False
        self.is_drum_solo = False
        self.is_crescendo = False
        self.kick_hit = False

    def process(self, samples, now):
        return False, 0, False, parameters.VU_FULL

class DummyCtrl:
    def update(self):
        pass

    def reset(self):
        pass


def test_snare_resets_smoothed_dimmer():
    show = BeatDMXShow(genre_model=None)
    show.controller = DummyCtrl()
    show.detector = DummyDetector()
    show.smoothed_vu_dimmer = 255
    show.last_vu_dimmer = 255
    show.scenario.events = {
        "snare_hit": {"Overhead Effects": {"dimmer": 255, "duration": 100}}
    }
    show._process_samples(np.zeros(512))
    assert show.smoothed_vu_dimmer == BeatDMXShow._vu_to_level(parameters.VU_FULL)
    # last_vu_dimmer is left unchanged so the next VU update triggers
    # a DMX refresh back to the expected level

class BeatDummyDetector:
    def __init__(self) -> None:
        self.state = SongState.ONGOING
        self.snare_hit = False
        self.is_chorus = False
        self.is_drum_solo = False
        self.is_crescendo = False
        self.kick_hit = False

    def process(self, samples, now):
        return True, 120, False, parameters.VU_FULL


def test_beat_resets_smoothed_dimmer():
    show = BeatDMXShow(dashboard=False, genre_model=None)
    show.controller = DummyCtrl()
    show.smoke = None
    show.smoke_on = False
    show.smoke_gap_ms = 0
    show.smoothed_vu_dimmer = 255
    show.last_vu_dimmer = 255
    show.detector = BeatDummyDetector()
    show.current_vu = parameters.VU_FULL
    show.scenario.events = {
        "beat": {"Overhead Effects": {"duration": 100}}
    }
    show._handle_beat(120, 0.0)
    assert show.smoothed_vu_dimmer == 255
