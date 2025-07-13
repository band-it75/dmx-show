import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import parameters
from main import BeatDMXShow


def test_vu_to_level_log_scale():
    zero = BeatDMXShow._vu_to_level(0.0)
    full = BeatDMXShow._vu_to_level(parameters.VU_FULL)
    above = BeatDMXShow._vu_to_level(parameters.VU_FULL * 2)
    low = BeatDMXShow._vu_to_level(parameters.VU_FULL / 10)
    mid = BeatDMXShow._vu_to_level(parameters.VU_FULL / 2)
    assert zero == 0
    assert full == 255
    assert above == 255
    assert 0 < low < mid < full

