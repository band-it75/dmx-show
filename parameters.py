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
from dmx.Fuzzix_PartyParUV_7ch import Fuzzix_PartyParUV_7ch


# Audio settings
SAMPLERATE = 44100

# Volume-based song state detection
AMPLITUDE_THRESHOLD = 0.02  # RMS amplitude considered "loud"
START_DURATION = 5.0        # seconds of sustained volume to mark song start
END_DURATION = 3.0          # seconds of quiet to mark song end

# DMX blink script defaults
UNIVERSE = 1
CHANNEL = 1

# How often to print BPM and genre summaries, in seconds
PRINT_INTERVAL = 10

# RMS level that results in full intensity for Stage Lights
VU_FULL = 0.3
# Ratio of VU_FULL that must be exceeded to trigger dimmer pulses
VU_PULSE_THRESHOLD = VU_FULL * 0.75

# Exponential smoothing factor for dimmer levels
VU_SMOOTHING = 0.8

# Display a static dashboard instead of logging lines
SHOW_DASHBOARD = True

# DMX hardware port
COM_PORT = "COM4"

# How many DMX frames to send per second
DMX_FPS = 60

# Seconds between automatic genre classification checks
GENRE_CHECK_INTERVAL = 15.0

# Mapping from numeric genre IDs to label strings
GENRE_ID_MAP = {
    "0": "disco",
    "1": "metal",
    "2": "reggae",
    "3": "blues",
    "4": "rock",
    "5": "classical",
    "6": "jazz",
    "7": "hiphop",
    "8": "country",
    "9": "pop",
}

# List of (fixture class, start_address, name) tuples describing the rig
DEVICES = [
    # House lights
    (Prolights_LumiPar12UAW5_7ch, 1, "Music Lights"),
    (Prolights_LumiPar12UAW5_7ch, 8, "Music Lights"),

    # Karaoke wall
    (Prolights_LumiPar7UTRI_8ch, 15, "Karaoke Lights"),
    (Prolights_LumiPar7UTRI_8ch, 23, "Karaoke Lights"),

    # Overhead pars used for stage wash and effects
    (Prolights_LumiPar12UQPro_9ch, 31, ("Stage Lights", "Overhead Effects")),
    (Prolights_LumiPar12UQPro_9ch, 40, ("Stage Lights", "Overhead Effects")),
    (Prolights_LumiPar12UQPro_9ch, 49, ("Stage Lights", "Overhead Effects")),

    # Moving head and smoke
    (Prolights_PixieWash_13ch, 58, "Moving Head"),
    (WhatSoftware_Generic_4ch, 71, "Smoke Machine"),

    # UV wash
    (Fuzzix_PartyParUV_7ch, 75, "UV Wash Left"),
    (Fuzzix_PartyParUV_7ch, 82, "UV Wash Right"),
]

# Names of every ongoing scenario
ONGOING_STATES = [
    "SONG_ONGOING_SLOW",
    "SONG_ONGOING_JAZZ",
    "SONG_ONGOING_POP",
    "SONG_ONGOING_ROCK",
    "SONG_ONGOING_METAL",
    "SONG_ONGOING_DISCO",
    "SONG_ONGOING_REGGAE",
    "SONG_ONGOING_BLUES",
    "SONG_ONGOING_CLASSICAL",
    "SONG_ONGOING_HIPHOP",
    "SONG_ONGOING_COUNTRY",
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
        events: dict[str, dict[str, dict[str, float]]] | None = None,
    ):
        obj = object.__new__(cls)
        obj._value_ = label
        obj.vu_level = vu_level
        obj.bpm_range = bpm_range
        obj.predecessor_names = predecessors
        obj.successor_names = successors
        obj.updates = updates
        obj.events = events or {}
        obj.predecessors = []  
        obj.successors = []    
        return obj

    INTERMISSION = (
        "Intermission",
        0.0,
        (0, 0),
        ["SONG_ENDING"],
        ["SONG_START"],
        {
            "Music Lights": {"warm_white": 51, "dimmer": 51},
            "Moving Head": {"dimmer": 0},
            "Stage Lights": {"dimmer": 0},
            "Karaoke Lights": {"red": 255, "green": 218, "blue": 185, "dimmer": 255},
            "Smoke Machine": {"smoke_gap": 60000, "duration": 5000},
        },
    )
    SONG_START = (
        "Song Start",
        0.02,
        (0, 0),
        ["INTERMISSION"],
        ONGOING_STATES,
        {
            "Music Lights": {"dimmer": 0},
            "Moving Head": {
                "pan": 32768,
                "tilt": 49152,
                "dimmer": 255,
                "red": 255,
                "green": 255,
                "blue": 255,
                "white": 255,
            },
            "Stage Lights": {"white": 77, "dimmer": 77},
            "Karaoke Lights": {"red": 255, "green": 218, "blue": 185, "dimmer": 50},
            "Smoke Machine": {"smoke_gap": 30000, "duration": 5000},
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
            "SONG_ONGOING_DISCO",
            "SONG_ONGOING_REGGAE",
            "SONG_ONGOING_BLUES",
            "SONG_ONGOING_CLASSICAL",
            "SONG_ONGOING_HIPHOP",
            "SONG_ONGOING_COUNTRY",
        ],
        [
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
            "SONG_ONGOING_DISCO",
            "SONG_ONGOING_REGGAE",
            "SONG_ONGOING_BLUES",
            "SONG_ONGOING_CLASSICAL",
            "SONG_ONGOING_HIPHOP",
            "SONG_ONGOING_COUNTRY",
            "SONG_ENDING",
        ],
        {
            "Music Lights": {"dimmer": 0},
            "Moving Head": {
                "dimmer": 255,
                "red": 255,
                "green": 255,
                "blue": 255,
                "white": 255,
            },
            "Stage Lights": {"red": 255},
            "Karaoke Lights": {"dimmer": 10},
            "Smoke Machine": {"smoke_gap": 15000, "duration": 5000},
        },
        {
            "beat": {
                "Stage Lights": {"red": 255, "duration": 100}
            },
            "chorus": {
                "Stage Lights": {"blue": 255, "dimmer": 255},
                "Moving Head": {
                    "pan": 30000,
                    "tilt": 40000,
                    "dimmer": 255,
                    "red": 255,
                    "green": 255,
                    "blue": 255,
                    "white": 255,
                },
            },
            "snare_hit": {
                "Stage Lights": {"white": 255, "dimmer": 255, "duration": 50}
            },
            "timer": {
                "after_seconds": 30,
                "Stage Lights": {
                    "from": {"red": 255},
                    "to": {"red": 128, "blue": 255},
                    "duration_ms": 45000,
                },
            },
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
            "SONG_ONGOING_DISCO",
            "SONG_ONGOING_REGGAE",
            "SONG_ONGOING_BLUES",
            "SONG_ONGOING_CLASSICAL",
            "SONG_ONGOING_HIPHOP",
            "SONG_ONGOING_COUNTRY",
        ],
        [
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
            "SONG_ONGOING_DISCO",
            "SONG_ONGOING_REGGAE",
            "SONG_ONGOING_BLUES",
            "SONG_ONGOING_CLASSICAL",
            "SONG_ONGOING_HIPHOP",
            "SONG_ONGOING_COUNTRY",
            "SONG_ENDING",
        ],
        {
            "Music Lights": {"dimmer": 0},
            "Moving Head": {
                "dimmer": 255,
                "red": 255,
                "green": 255,
                "blue": 255,
                "white": 255,
            },
            "Stage Lights": {"red": 255, "blue": 255},
            "Karaoke Lights": {"red": 26, "blue": 26, "dimmer": 10},
            "Smoke Machine": {"smoke_gap": 15000, "duration": 5000},
        },
        {
            "beat": {
                "Stage Lights": {"red": 255, "blue": 255, "duration": 100}
            },
            "chorus": {
                "Stage Lights": {"green": 255, "dimmer": 255},
                "Moving Head": {
                    "pan": 30000,
                    "tilt": 40000,
                    "dimmer": 255,
                    "red": 255,
                    "green": 255,
                    "blue": 255,
                    "white": 255,
                },
            },
            "snare_hit": {
                "Stage Lights": {"white": 255, "dimmer": 255, "duration": 50}
            },
            "timer": {
                "after_seconds": 30,
                "Stage Lights": {
                    "from": {"red": 255, "blue": 255},
                    "to": {"red": 128, "blue": 255},
                    "duration_ms": 45000,
                },
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
            "SONG_ONGOING_DISCO",
            "SONG_ONGOING_REGGAE",
            "SONG_ONGOING_BLUES",
            "SONG_ONGOING_CLASSICAL",
            "SONG_ONGOING_HIPHOP",
            "SONG_ONGOING_COUNTRY",
        ],
        [
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
            "SONG_ONGOING_DISCO",
            "SONG_ONGOING_REGGAE",
            "SONG_ONGOING_BLUES",
            "SONG_ONGOING_CLASSICAL",
            "SONG_ONGOING_HIPHOP",
            "SONG_ONGOING_COUNTRY",
            "SONG_ENDING",
        ],
        {
            "Music Lights": {"dimmer": 0},
            "Moving Head": {
                "dimmer": 255,
                "red": 255,
                "green": 255,
                "blue": 255,
                "white": 255,
            },
            "Stage Lights": {"green": 255},
            "Karaoke Lights": {"green": 26, "dimmer": 10},
            "Smoke Machine": {"smoke_gap": 15000, "duration": 5000},
        },
        {
            "beat": {
                "Stage Lights": {"green": 255, "duration": 100}
            },
            "chorus": {
                "Stage Lights": {"green": 255, "blue": 128, "dimmer": 255},
                "Moving Head": {
                    "pan": 30000,
                    "tilt": 40000,
                    "dimmer": 255,
                    "red": 255,
                    "green": 255,
                    "blue": 255,
                    "white": 255,
                },
            },
            "snare_hit": {
                "Stage Lights": {"white": 255, "dimmer": 255, "duration": 50}
            },
            "timer": {
                "after_seconds": 30,
                "Stage Lights": {
                    "from": {"green": 255},
                    "to": {"red": 128, "blue": 255},
                    "duration_ms": 45000,
                },
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
            "SONG_ONGOING_DISCO",
            "SONG_ONGOING_REGGAE",
            "SONG_ONGOING_BLUES",
            "SONG_ONGOING_CLASSICAL",
            "SONG_ONGOING_HIPHOP",
            "SONG_ONGOING_COUNTRY",
        ],
        [
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_METAL",
            "SONG_ONGOING_DISCO",
            "SONG_ONGOING_REGGAE",
            "SONG_ONGOING_BLUES",
            "SONG_ONGOING_CLASSICAL",
            "SONG_ONGOING_HIPHOP",
            "SONG_ONGOING_COUNTRY",
            "SONG_ENDING",
        ],
        {
            "Music Lights": {"dimmer": 0},
            "Moving Head": {
                "dimmer": 255,
                "red": 255,
                "green": 255,
                "blue": 255,
                "white": 255,
            },
            "Stage Lights": {"red": 255, "green": 64},
            "Karaoke Lights": {"red": 26, "green": 6, "dimmer": 10},
            "Smoke Machine": {"smoke_gap": 15000, "duration": 5000},
        },
        {
            "beat": {
                "Stage Lights": {"red": 255, "green": 64, "duration": 100}
            },
            "chorus": {
                "Stage Lights": {"red": 255, "blue": 64, "dimmer": 255},
                "Moving Head": {
                    "pan": 30000,
                    "tilt": 40000,
                    "dimmer": 255,
                    "red": 255,
                    "green": 255,
                    "blue": 255,
                    "white": 255,
                },
            },
            "snare_hit": {
                "Stage Lights": {"white": 255, "dimmer": 255, "duration": 50}
            },
            "timer": {
                "after_seconds": 30,
                "Stage Lights": {
                    "from": {"red": 255, "green": 64},
                    "to": {"red": 128, "blue": 255},
                    "duration_ms": 45000,
                },
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
            "SONG_ONGOING_DISCO",
            "SONG_ONGOING_REGGAE",
            "SONG_ONGOING_BLUES",
            "SONG_ONGOING_CLASSICAL",
            "SONG_ONGOING_HIPHOP",
            "SONG_ONGOING_COUNTRY",
        ],
        [
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_DISCO",
            "SONG_ONGOING_REGGAE",
            "SONG_ONGOING_BLUES",
            "SONG_ONGOING_CLASSICAL",
            "SONG_ONGOING_HIPHOP",
            "SONG_ONGOING_COUNTRY",
            "SONG_ENDING",
        ],
        {
            "Music Lights": {"dimmer": 0},
            "Moving Head": {
                "dimmer": 255,
                "red": 255,
                "green": 255,
                "blue": 255,
                "white": 255,
            },
            "Stage Lights": {"white": 255},
            "Karaoke Lights": {"white": 26, "dimmer": 10},
            "Smoke Machine": {"smoke_gap": 15000, "duration": 5000},
        },
        {
            "beat": {
                "Stage Lights": {"white": 255, "duration": 100}
            },
            "chorus": {
                "Stage Lights": {"white": 255, "dimmer": 255},
                "Moving Head": {
                    "pan": 30000,
                    "tilt": 40000,
                    "dimmer": 255,
                    "red": 255,
                    "green": 255,
                    "blue": 255,
                    "white": 255,
                },
            },
            "snare_hit": {
                "Stage Lights": {"white": 255, "dimmer": 255, "duration": 50}
            },
            "timer": {
                "after_seconds": 30,
                "Stage Lights": {
                    "from": {"white": 255},
                    "to": {"red": 128, "blue": 255},
                    "duration_ms": 45000,
                },
            },
        },
    )
    SONG_ONGOING_DISCO = (
        "Song Ongoing - Disco",
        0.02,
        (110, 130),
        [
            "SONG_START",
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
            "SONG_ONGOING_REGGAE",
            "SONG_ONGOING_BLUES",
            "SONG_ONGOING_CLASSICAL",
            "SONG_ONGOING_HIPHOP",
            "SONG_ONGOING_COUNTRY",
        ],
        [
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
            "SONG_ONGOING_REGGAE",
            "SONG_ONGOING_BLUES",
            "SONG_ONGOING_CLASSICAL",
            "SONG_ONGOING_HIPHOP",
            "SONG_ONGOING_COUNTRY",
            "SONG_ENDING",
        ],
        {
            "Music Lights": {"dimmer": 0},
            "Moving Head": {
                "dimmer": 255,
                "red": 255,
                "green": 255,
                "blue": 255,
                "white": 255,
            },
            "Stage Lights": {"red": 255, "blue": 255},
            "Karaoke Lights": {"red": 26, "blue": 26, "dimmer": 10},
            "Smoke Machine": {"smoke_gap": 15000, "duration": 5000},
        },
        {
            "beat": {
                "Stage Lights": {"red": 255, "blue": 255, "duration": 100}
            },
            "chorus": {
                "Stage Lights": {"green": 255, "blue": 255, "dimmer": 255},
                "Moving Head": {
                    "pan": 30000,
                    "tilt": 40000,
                    "dimmer": 255,
                    "red": 255,
                    "green": 255,
                    "blue": 255,
                    "white": 255,
                },
            },
            "snare_hit": {
                "Stage Lights": {"white": 255, "dimmer": 255, "duration": 50}
            },
            "timer": {
                "after_seconds": 30,
                "Stage Lights": {
                    "from": {"red": 255, "blue": 255},
                    "to": {"red": 128, "blue": 255},
                    "duration_ms": 45000,
                },
            },
        },
    )
    SONG_ONGOING_REGGAE = (
        "Song Ongoing - Reggae",
        0.02,
        (0, 80),
        [
            "SONG_START",
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
            "SONG_ONGOING_DISCO",
            "SONG_ONGOING_BLUES",
            "SONG_ONGOING_CLASSICAL",
            "SONG_ONGOING_HIPHOP",
            "SONG_ONGOING_COUNTRY",
        ],
        [
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
            "SONG_ONGOING_DISCO",
            "SONG_ONGOING_BLUES",
            "SONG_ONGOING_CLASSICAL",
            "SONG_ONGOING_HIPHOP",
            "SONG_ONGOING_COUNTRY",
            "SONG_ENDING",
        ],
        {
            "Music Lights": {"dimmer": 0},
            "Moving Head": {
                "dimmer": 255,
                "red": 255,
                "green": 255,
                "blue": 255,
                "white": 255,
            },
            "Stage Lights": {"red": 255, "green": 255},
            "Karaoke Lights": {"red": 26, "green": 26, "dimmer": 10},
            "Smoke Machine": {"smoke_gap": 15000, "duration": 5000},
        },
        {
            "beat": {
                "Stage Lights": {"red": 255, "green": 255, "duration": 100}
            },
            "chorus": {
                "Stage Lights": {"red": 255, "green": 128, "dimmer": 255},
                "Moving Head": {
                    "pan": 30000,
                    "tilt": 40000,
                    "dimmer": 255,
                    "red": 255,
                    "green": 255,
                    "blue": 255,
                    "white": 255,
                },
            },
            "snare_hit": {
                "Stage Lights": {"white": 255, "dimmer": 255, "duration": 50}
            },
            "timer": {
                "after_seconds": 30,
                "Stage Lights": {
                    "from": {"red": 255, "green": 255},
                    "to": {"red": 128, "blue": 255},
                    "duration_ms": 45000,
                },
            },
        },
    )
    SONG_ONGOING_BLUES = (
        "Song Ongoing - Blues",
        0.02,
        (0, 80),
        [
            "SONG_START",
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
            "SONG_ONGOING_DISCO",
            "SONG_ONGOING_REGGAE",
            "SONG_ONGOING_CLASSICAL",
            "SONG_ONGOING_HIPHOP",
            "SONG_ONGOING_COUNTRY",
        ],
        [
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
            "SONG_ONGOING_DISCO",
            "SONG_ONGOING_REGGAE",
            "SONG_ONGOING_CLASSICAL",
            "SONG_ONGOING_HIPHOP",
            "SONG_ONGOING_COUNTRY",
            "SONG_ENDING",
        ],
        {
            "Music Lights": {"dimmer": 0},
            "Moving Head": {
                "dimmer": 255,
                "red": 255,
                "green": 255,
                "blue": 255,
                "white": 255,
            },
            "Stage Lights": {"blue": 255},
            "Karaoke Lights": {"blue": 26, "dimmer": 10},
            "Smoke Machine": {"smoke_gap": 15000, "duration": 5000},
        },
        {
            "beat": {
                "Stage Lights": {"blue": 255, "duration": 100}
            },
            "chorus": {
                "Stage Lights": {"green": 255, "blue": 128, "dimmer": 255},
                "Moving Head": {
                    "pan": 30000,
                    "tilt": 40000,
                    "dimmer": 255,
                    "red": 255,
                    "green": 255,
                    "blue": 255,
                    "white": 255,
                },
            },
            "snare_hit": {
                "Stage Lights": {"white": 255, "dimmer": 255, "duration": 50}
            },
            "timer": {
                "after_seconds": 30,
                "Stage Lights": {
                    "from": {"blue": 255},
                    "to": {"red": 128, "blue": 255},
                    "duration_ms": 45000,
                },
            },
        },
    )
    SONG_ONGOING_CLASSICAL = (
        "Song Ongoing - Classical",
        0.02,
        (0, 80),
        [
            "SONG_START",
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
            "SONG_ONGOING_DISCO",
            "SONG_ONGOING_REGGAE",
            "SONG_ONGOING_BLUES",
            "SONG_ONGOING_HIPHOP",
            "SONG_ONGOING_COUNTRY",
        ],
        [
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
            "SONG_ONGOING_DISCO",
            "SONG_ONGOING_REGGAE",
            "SONG_ONGOING_BLUES",
            "SONG_ONGOING_HIPHOP",
            "SONG_ONGOING_COUNTRY",
            "SONG_ENDING",
        ],
        {
            "Music Lights": {"dimmer": 0},
            "Moving Head": {
                "dimmer": 255,
                "red": 255,
                "green": 255,
                "blue": 255,
                "white": 255,
            },
            "Stage Lights": {"white": 255},
            "Karaoke Lights": {"white": 26, "dimmer": 26},
            "Smoke Machine": {"smoke_gap": 15000, "duration": 5000},
        },
        {
            "beat": {
                "Stage Lights": {"white": 255, "duration": 100}
            },
            "chorus": {
                "Stage Lights": {"warm_white": 255, "dimmer": 255},
                "Moving Head": {
                    "pan": 30000,
                    "tilt": 40000,
                    "dimmer": 255,
                    "red": 255,
                    "green": 255,
                    "blue": 255,
                    "white": 255,
                },
            },
            "snare_hit": {
                "Stage Lights": {"white": 255, "dimmer": 255, "duration": 50}
            },
            "timer": {
                "after_seconds": 30,
                "Stage Lights": {
                    "from": {"white": 255},
                    "to": {"red": 128, "blue": 255},
                    "duration_ms": 45000,
                },
            },
        },
    )
    SONG_ONGOING_HIPHOP = (
        "Song Ongoing - HipHop",
        0.02,
        (0, 80),
        [
            "SONG_START",
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
            "SONG_ONGOING_DISCO",
            "SONG_ONGOING_REGGAE",
            "SONG_ONGOING_BLUES",
            "SONG_ONGOING_CLASSICAL",
            "SONG_ONGOING_COUNTRY",
        ],
        [
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
            "SONG_ONGOING_DISCO",
            "SONG_ONGOING_REGGAE",
            "SONG_ONGOING_BLUES",
            "SONG_ONGOING_CLASSICAL",
            "SONG_ONGOING_COUNTRY",
            "SONG_ENDING",
        ],
        {
            "Music Lights": {"dimmer": 0},
            "Moving Head": {
                "dimmer": 255,
                "red": 255,
                "green": 255,
                "blue": 255,
                "white": 255,
            },
            "Stage Lights": {"green": 255, "blue": 255},
            "Karaoke Lights": {"green": 26, "blue": 26, "dimmer": 10},
            "Smoke Machine": {"smoke_gap": 15000, "duration": 5000},
        },
        {
            "beat": {
                "Stage Lights": {"green": 255, "blue": 255, "duration": 100}
            },
            "chorus": {
                "Stage Lights": {"red": 255, "blue": 255, "dimmer": 255},
                "Moving Head": {
                    "pan": 30000,
                    "tilt": 40000,
                    "dimmer": 255,
                    "red": 255,
                    "green": 255,
                    "blue": 255,
                    "white": 255,
                },
            },
            "snare_hit": {
                "Stage Lights": {"white": 255, "dimmer": 255, "duration": 50}
            },
            "timer": {
                "after_seconds": 30,
                "Stage Lights": {
                    "from": {"green": 255, "blue": 255},
                    "to": {"red": 128, "blue": 255},
                    "duration_ms": 45000,
                },
            },
        },
    )
    SONG_ONGOING_COUNTRY = (
        "Song Ongoing - Country",
        0.02,
        (0, 80),
        [
            "SONG_START",
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
            "SONG_ONGOING_DISCO",
            "SONG_ONGOING_REGGAE",
            "SONG_ONGOING_BLUES",
            "SONG_ONGOING_CLASSICAL",
            "SONG_ONGOING_HIPHOP",
        ],
        [
            "SONG_ONGOING_SLOW",
            "SONG_ONGOING_JAZZ",
            "SONG_ONGOING_POP",
            "SONG_ONGOING_ROCK",
            "SONG_ONGOING_METAL",
            "SONG_ONGOING_DISCO",
            "SONG_ONGOING_REGGAE",
            "SONG_ONGOING_BLUES",
            "SONG_ONGOING_CLASSICAL",
            "SONG_ONGOING_HIPHOP",
            "SONG_ENDING",
        ],
        {
            "Music Lights": {"dimmer": 0},
            "Moving Head": {
                "dimmer": 255,
                "red": 255,
                "green": 255,
                "blue": 255,
                "white": 255,
            },
            "Stage Lights": {"red": 255, "green": 96},
            "Karaoke Lights": {"red": 26, "green": 10, "dimmer": 10},
            "Smoke Machine": {"smoke_gap": 15000, "duration": 5000},
        },
        {
            "beat": {
                "Stage Lights": {"red": 255, "green": 96, "duration": 100}
            },
            "chorus": {
                "Stage Lights": {"red": 255, "green": 96, "dimmer": 255},
                "Moving Head": {
                    "pan": 30000,
                    "tilt": 40000,
                    "dimmer": 255,
                    "red": 255,
                    "green": 255,
                    "blue": 255,
                    "white": 255,
                },
                "Karaoke Lights": {"red": 255, "green": 0, "blue": 0, "dimmer": 255},
            },
            "snare_hit": {
                "Stage Lights": {"white": 255, "dimmer": 255, "duration": 50}
            },
            "timer": {
                "after_seconds": 30,
                "Stage Lights": {
                    "from": {"red": 255, "green": 96},
                    "to": {"red": 128, "blue": 255},
                    "duration_ms": 45000,
                },
            },
        },
    )
    SONG_ENDING = (
        "Song Ending",
        0.02,
        (0, 0),
        ONGOING_STATES,
        ["INTERMISSION"],
        {
            "Music Lights": {"warm_white": 128, "dimmer": 128},
            "Moving Head": {
                "pan": 32768,
                "tilt": 16384,
                "dimmer": 255,
                "red": 255,
                "green": 255,
                "blue": 255,
                "white": 255,
            },
            "Stage Lights": {"dimmer": 0},
            "Karaoke Lights": {"red": 255, "green": 218, "blue": 185, "dimmer": 50},
            "Smoke Machine": {"smoke_gap": 30000, "duration": 5000},
        },
    )

def _fill_updates() -> None:
    """Ensure every scenario sets all available channels."""
    channel_map: dict[str, set[str]] = {}
    for cls, addr, names in DEVICES:
        device = cls(addr)
        if isinstance(names, (str, bytes)):
            names = [names]
        for name in names:
            channel_map.setdefault(name, set()).update(device.channels.keys())
    for scn in Scenario:
        for name, channels in channel_map.items():
            update = scn.updates.setdefault(name, {})
            for ch in channels:
                update.setdefault(ch, 0)
            if update.get("dimmer", 0) > 0:
                if "shutter" in channels:
                    update.setdefault("shutter", 63)
                color_names = [c for c in ("red", "green", "blue", "white") if c in channels]
                if color_names and not any(update.get(c, 0) > 0 for c in color_names):
                    for c in color_names:
                        update[c] = 255


_fill_updates()

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
