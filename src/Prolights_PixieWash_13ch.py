from __future__ import annotations

from dmx import DmxDevice


class Prolights_PixieWash_13ch(DmxDevice):
    """Prolights PixieWash moving head in 13-channel mode."""

    CHANNEL_OFFSETS = {
        "pan": 0,
        "pan_fine": 1,
        "tilt": 2,
        "tilt_fine": 3,
        "pan_tilt_speed": 4,
        "special": 5,
        "dimmer": 6,
        "shutter": 7,
        "red": 8,
        "green": 9,
        "blue": 10,
        "white": 11,
        "color_macros": 12,
    }

    def __init__(self, start_address: int) -> None:
        self.start_address = int(start_address)
        channels = {
            name: self.start_address + off
            for name, off in self.CHANNEL_OFFSETS.items()
        }
        super().__init__(channels)
