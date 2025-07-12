import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import types
sys.modules['sounddevice'] = types.SimpleNamespace()
sys.modules['aubio'] = types.SimpleNamespace(
    tempo=lambda *a, **k: (lambda *_: False),
    onset=lambda *a, **k: (lambda *_: False),
)
sys.modules['librosa'] = types.SimpleNamespace(
    feature=types.SimpleNamespace(
        rms=lambda *a, **k: np.array([[0.0]]),
        spectral_flatness=lambda *a, **k: np.array([[0.0]]),
        spectral_centroid=lambda *a, **k: np.array([[0.0]]),
    ),
    stft=lambda *a, **k: np.zeros((1, 1)),
    decompose=types.SimpleNamespace(hpss=lambda S: (np.zeros_like(S), np.zeros_like(S))),
)

from src.audio.beat_detection import BeatDetector, SongState


def test_start_does_not_revert_before_end_duration():
    det = BeatDetector(amplitude_threshold=0.1, start_duration=1.0, end_duration=1.0)
    loud = np.ones(512, dtype=np.float32) * 0.2
    quiet = np.zeros(512, dtype=np.float32)

    det.process(loud, now=0.0)
    assert det.state is SongState.STARTING

    det.process(quiet, now=1.0)
    assert det.state is SongState.STARTING

    det.process(quiet, now=2.1)
    assert det.state is SongState.STARTING


def test_start_to_intermission_blocked():
    det = BeatDetector()
    det.state = SongState.STARTING
    changed = det._set_state(SongState.INTERMISSION, now=0.0)
    assert changed is False
    assert det.state is SongState.STARTING
