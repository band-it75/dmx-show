"""Audio utilities for DMX show.

This module lazily imports heavier dependencies so tests that only rely on
``DebouncedFlag`` do not require audio libraries like PortAudio.  Accessing any
of the exported classes will load the appropriate module on first use.  A
lightweight ``SongState`` enum is defined here so importing it does not pull in
the full beat detection stack.
"""

from enum import Enum

class SongState(Enum):
    """Simple states derived from audio volume."""

    INTERMISSION = "Intermission"
    STARTING = "Starting"
    ONGOING = "Ongoing"
    ENDING = "Ending"

__all__ = ["BeatDetector", "SongState", "DebouncedFlag", "GenreClassifier"]


def __getattr__(name: str):
    if name in {"BeatDetector", "SongState"}:
        from .beat_detection import BeatDetector, SongState
        globals().update({"BeatDetector": BeatDetector, "SongState": SongState})
        return globals()[name]
    if name == "DebouncedFlag":
        from .debounce import DebouncedFlag
        globals()["DebouncedFlag"] = DebouncedFlag
        return DebouncedFlag
    if name == "GenreClassifier":
        from .genre_classifier import GenreClassifier
        globals()["GenreClassifier"] = GenreClassifier
        return GenreClassifier
    raise AttributeError(name)
