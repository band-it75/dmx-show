import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.audio.debounce import DebouncedFlag


def test_debounced_flag():
    flag = DebouncedFlag(0.2)
    now = 0.0
    # stable true for 0.1s should not trigger
    for _ in range(4):
        assert flag.update(True, now) is False
        now += 0.05
    # after 0.2s of true it should become True
    assert flag.update(True, now) is True
    now += 0.05
    # brief false shorter than debounce keeps state
    assert flag.update(False, now) is True
    now += 0.1
    # once false for >= debounce it resets
    now += 0.15
    assert flag.update(False, now) is False
