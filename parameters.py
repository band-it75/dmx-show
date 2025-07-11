# Default configuration parameters for DMX and beat detection
from __future__ import annotations

from enum import Enum
from pathlib import Path
import sys
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
from dmx.Prolights_LumiPar12UAW5_7ch import Prolights_LumiPar12UAW5_7ch
from dmx.Prolights_LumiPar7UTRI_8ch import Prolights_LumiPar7UTRI_8ch
from dmx.Prolights_LumiPar12UQPro_9ch import Prolights_LumiPar12UQPro_9ch
from dmx.Prolights_PixieWash_13ch import Prolights_PixieWash_13ch
from dmx.WhatSoftware_Generic_4ch import WhatSoftware_Generic_4ch


# Audio settings
SAMPLERATE = 44100

# Volume-based song state detection
AMPLITUDE_THRESHOLD = 0.02  # RMS amplitude considered "loud"
START_DURATION = 2.0        # seconds of sustained volume to mark song start
END_DURATION = 3.0          # seconds of quiet to mark song end

# DMX blink script defaults
UNIVERSE = 1
CHANNEL = 1

# How often to print BPM and genre summaries, in seconds
PRINT_INTERVAL = 10

# RMS level that results in full intensity for overhead effects
VU_FULL = 0.3

# Display a static dashboard instead of logging lines
SHOW_DASHBOARD = True

# DMX hardware port
COM_PORT = "COM4"

# List of (fixture class, start_address, name) tuples describing the rig
DEVICES = [
    #(Prolights_LumiPar12UAW5_7ch, 1, "House Lights"),
    #(Prolights_LumiPar7UTRI_8ch, 1, "House Lights"),
    #(Prolights_LumiPar12UAW5_7ch, 10, "House Lights"),
    #(Prolights_LumiPar12UAW5_7ch, 19, "House Lights"),
    #(Prolights_LumiPar7UTRI_8ch, 30, "Karaoke Lights"),
    #(Prolights_LumiPar7UTRI_8ch, 41, "Karaoke Lights"),
    #(Prolights_LumiPar12UQPro_9ch, 55, "Overhead Effects"),
    #(Prolights_LumiPar12UQPro_9ch, 69, "Overhead Effects"),
    #(Prolights_PixieWash_13ch, 85, "Moving Head"),
    #(WhatSoftware_Generic_4ch, 115, "Smoke Machine"),
    (Prolights_LumiPar7UTRI_8ch, 1, "Overhead Effects"),
]


# Programmatic show scenarios. Each update maps device groups to channel values
# ready for the DMX classes.

class Scenario(Enum):
    """Show states with BPM ranges and allowed transitions."""

    def __new__(
        cls,
        label: str,
        vu_level: float,
        bpm_range: tuple[int, int],
        predecessors: list[str],
        successors: list[str],
        updates: dict[str, dict[str, float]],
        beat: dict[str, dict[str, float]] | None = None,
    ):
        obj = object.__new__(cls)
        obj._value_ = label
        obj.vu_level = vu_level
        obj.bpm_range = bpm_range
        obj.predecessor_names = predecessors
        obj.successor_names = successors
        obj.updates = updates
        obj.beat = beat
        obj.predecessors: list["Scenario"] = []
        obj.successors: list["Scenario"] = []
        return obj

    INTERMISSION = (
        "Intermission",
        0.0,
        (0, 0),
        ["SONG_ENDING"],
        ["SONG_START"],
        {
            "House Lights": {"warm_white": 51, "dimmer": 51},
            "Moving Head": {"dimmer": 0},
            "Overhead Effects": {"dimmer": 0},
            "Karaoke Lights": {"dimmer": 0},
            "Smoke Machine": {"smoke_gap": 60000, "duration": 5000},
        },
    )
    SONG_START = (
        "Song Start",
        0.02,
        (0, 0),
        ["INTERMISSION"],
        [
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
        ],
        {
            "House Lights": {"dimmer": 0},
            "Moving Head": {"pan": 32768, "tilt": 49152, "dimmer": 255},
            "Overhead Effects": {"white": 77, "dimmer": 77},
            "Karaoke Lights": {"dimmer": 0},
            "Smoke Machine": {"smoke_gap": 30000, "duration": 3000},
        },
    )
    SONG_ONGOING_SLOW = (
        "Song Ongoing - Slow",
        0.02,
        (0, 80),
        [
            "SONG_START",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
        ],
        [
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
            "SONG_ENDING",
        ],
        {
            "House Lights": {"dimmer": 0},
            "Moving Head": {"dimmer": 255},
            "Overhead Effects": {"red": 255, "dimmer": 255},
            "Karaoke Lights": {"red": 26, "dimmer": 26},
            "Smoke Machine": {"smoke_gap": 15000, "duration": 2000},
        },
        {
            "Overhead Effects": {"red": 255, "dimmer": 255, "duration": 100},
        },
    )
    SONG_ONGOING_JAZZ = (
        "Song Ongoing - Jazz",
        0.02,
        (80, 110),
        [
            "SONG_START",
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
        ],
        [
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
            "SONG_ENDING",
        ],
        {
            "House Lights": {"dimmer": 0},
            "Moving Head": {"dimmer": 255},
            "Overhead Effects": {"red": 255, "green": 96, "dimmer": 255},
            "Karaoke Lights": {"red": 26, "green": 10, "dimmer": 26},
            "Smoke Machine": {"smoke_gap": 30000, "duration": 3000},
        },
        {
            "Overhead Effects": {
                "red": 255,
                "green": 96,
                "dimmer": 255,
                "duration": 100,
            },
        },
    )
    SONG_ONGOING_POP = (
        "Song Ongoing - Pop",
        0.02,
        (110, 130),
        [
            "SONG_START",
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
        ],
        [
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
            "SONG_ENDING",
        ],
        {
            "House Lights": {"dimmer": 0},
            "Moving Head": {"dimmer": 255},
            "Overhead Effects": {"red": 255, "blue": 96, "dimmer": 255},
            "Karaoke Lights": {"red": 26, "blue": 10, "dimmer": 26},
            "Smoke Machine": {"smoke_gap": 30000, "duration": 3000},
        },
        {
            "Overhead Effects": {
                "red": 255,
                "blue": 96,
                "dimmer": 255,
                "duration": 100,
            },
        },
    )
    SONG_ONGOING_ROCK = (
        "Song Ongoing - Rock",
        0.02,
        (130, 160),
        [
            "SONG_START",
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_METAL",
        ],
        [
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_METAL",
            "SONG_ENDING",
        ],
        {
            "House Lights": {"dimmer": 0},
            "Moving Head": {"dimmer": 255},
            "Overhead Effects": {"red": 255, "dimmer": 255},
            "Karaoke Lights": {"red": 26, "dimmer": 26},
            "Smoke Machine": {"smoke_gap": 30000, "duration": 3000},
        },
        {
            "Overhead Effects": {
                "red": 255,
                "dimmer": 255,
                "duration": 100,
            },
        },
    )
    SONG_ONGOING_METAL = (
        "Song Ongoing - Metal",
        0.02,
        (160, 999),
        [
            "SONG_START",
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
        ],
        [
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
            "SONG_ENDING",
        ],
        {
            "House Lights": {"dimmer": 0},
            "Moving Head": {"dimmer": 255},
            "Overhead Effects": {"white": 255, "dimmer": 255},
            "Karaoke Lights": {"white": 26, "dimmer": 26},
            "Smoke Machine": {"smoke_gap": 30000, "duration": 3000},
        },
        {
            "Overhead Effects": {
                "white": 255,
                "dimmer": 255,
                "duration": 100,
            },
        },
    )
    SONG_ENDING = (
        "Song Ending",
        0.02,
        (0, 0),
        [
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
        ],
        ["INTERMISSION"],
        {
            "House Lights": {"warm_white": 128, "dimmer": 128},
            "Moving Head": {"pan": 32768, "tilt": 16384, "dimmer": 255},
            "Overhead Effects": {"dimmer": 0},
            "Karaoke Lights": {"dimmer": 0},
            "Smoke Machine": {"smoke_gap": 30000, "duration": 3000},
        },
    )


def _resolve_transitions() -> None:
    lookup = {sc.name: sc for sc in Scenario}
    for sc in Scenario:
        sc.predecessors = [lookup[n] for n in sc.predecessor_names]
        sc.successors = [lookup[n] for n in sc.successor_names]
        del sc.predecessor_names
        del sc.successor_names


_resolve_transitions()

# Mapping for quick lookup by name
SCENARIO_MAP = {sc: sc for sc in Scenario}

def scenario_for_bpm(bpm: float) -> Scenario:
    """Return the scenario whose BPM range contains ``bpm``."""
    for scn in Scenario:
        low, high = scn.bpm_range
        if high > low and low <= bpm < high:
            return scn
    return Scenario.SONG_ONGOING_SLOW


def smoke_settings(scn: Scenario) -> tuple[int, int]:
    """Return smoke gap and duration in milliseconds for the scenario."""
    smoke = scn.updates.get("Smoke Machine", {})
    gap = int(smoke.get("smoke_gap", 30000))
    duration = int(smoke.get("duration", 3000))
    return gap, duration
