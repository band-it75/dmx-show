"""Simulated DMX show using generated beats.

LumiPar 12UAW5 units double as house lights. Overhead effects pulse with BPM.
Smoke bursts last 3 seconds with a 30-second gap. Genre-specific colors guide
stage lighting. The moving head stays on the artist during songs and points at
 the audience to end each song. Stage lights fade to black during songs and
return when the moving head faces the audience.
"""

from __future__ import annotations

import time
from typing import List

import numpy as np


def _compute_bpm(beat_times: List[float]) -> float:
    """Return the estimated BPM using recent beat intervals."""
    if len(beat_times) < 2:
        return 0.0
    recent = beat_times[-8:]
    intervals = np.diff(recent)
    if len(intervals) == 0:
        return 0.0
    return 60.0 / float(np.median(intervals))


def _detect_genre(bpm: float) -> str:
    if bpm >= 160:
        return "Metal"
    if bpm >= 130:
        return "Rock"
    if bpm >= 100:
        return "Pop"
    if bpm >= 80:
        return "Jazz"
    return "Slow"


def _genre_color(genre: str) -> str:
    mapping = {
        "Slow": "red",
        "Jazz": "amber",
        "Pop": "pink",
        "Rock": "red",
        "Metal": "white",
    }
    return mapping.get(genre, "white")


def _stage_light_color(genre: str) -> str:
    return "amber" if genre in ("Slow", "Jazz") else "white"


def simulate_show(bpm: float = 120.0, beats: int = 16) -> None:
    """Generate beats and print lighting cues."""
    interval = 60.0 / bpm
    beat_times: List[float] = []
    start = time.time()
    smoke_start = start
    for i in range(beats):
        target = start + i * interval
        time.sleep(max(0.0, target - time.time()))
        now = time.time()
        beat_times.append(now)
        est_bpm = _compute_bpm(beat_times)
        genre = _detect_genre(est_bpm)
        effect_color = _genre_color(genre).capitalize()
        stage_color = _stage_light_color(genre).capitalize()
        print(f"Beat {i + 1}: BPM {est_bpm:.1f} Genre {genre}")
        print("Change:")
        print("- Moving Light: Artist")
        print(f"- Stage Light: {stage_color}")
        print(f"- Overhead Effects: {effect_color} (80%) Pulsing")
        print(f"- Karaoke Lights: {effect_color} (10%)")
        if now - smoke_start >= 30.0:
            print("Smoke start")
            time.sleep(3.0)
            print("Smoke end")
            smoke_start = time.time()

    print("Change:")
    print("- Moving Light: Audience")
    print("Current:")
    print("- Moving Light: Audience")
    print("- Stage Light: Warm White (50%)")


if __name__ == "__main__":
    simulate_show()
