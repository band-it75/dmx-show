from __future__ import annotations

from dmx import DmxDevice

class Prolights_LumiPar7UTRI_8ch(DmxDevice):
    """Prolights LumiPar 7 UTRI fixture in 8-channel mode."""

    CHANNEL_OFFSETS = {
        "red": 0,
        "green": 1,
        "blue": 2,
        "color_macros": 3,
        "strobe": 4,
        "programs": 5,
        "dimmer": 6,
        "dimmer_speed": 7,
    }

    def __init__(self, start_address: int) -> None:
        self.start_address = int(start_address)
        channels = {name: self.start_address + off for name, off in self.CHANNEL_OFFSETS.items()}
        super().__init__(channels)

