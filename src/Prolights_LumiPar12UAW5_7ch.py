from __future__ import annotations

from dmx import DmxDevice


class Prolights_LumiPar12UAW5_7ch(DmxDevice):
    """Prolights LumiPar 12 UAW5 fixture in 7-channel mode."""

    CHANNEL_OFFSETS = {
        "amber": 0,
        "cold_white": 1,
        "warm_white": 2,
        "strobe": 3,
        "programs": 4,
        "dimmer": 5,
        "dimmer_curve": 6,
    }

    def __init__(self, start_address: int) -> None:
        self.start_address = int(start_address)
        channels = {
            name: self.start_address + off
            for name, off in self.CHANNEL_OFFSETS.items()
        }
        super().__init__(channels)
