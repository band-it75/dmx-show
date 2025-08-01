from __future__ import annotations

from dmx import DmxDevice


class Prolights_LumiPar12UQPro_4ch(DmxDevice):
    """Prolights LumiPar 12 UQ Pro fixture in 4-channel mode."""

    CHANNEL_OFFSETS = {
        "red": 0,
        "green": 1,
        "blue": 2,
        "white": 3,
    }

    def __init__(self, start_address: int) -> None:
        self.start_address = int(start_address)
        channels = {
            name: self.start_address + off
            for name, off in self.CHANNEL_OFFSETS.items()
        }
        super().__init__(channels)
