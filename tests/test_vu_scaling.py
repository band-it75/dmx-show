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
    assert zero == 0
    assert threshold == 0
    assert full == 255
    assert above == 255
    assert low == 0
    assert mid == 0
    assert 0 < high < full

