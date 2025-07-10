from __future__ import annotations

from dmx import DmxDevice


class Prolights_LumiPar7UTRI_3ch(DmxDevice):
    """Prolights LumiPar 7 UTRI fixture in 3-channel RGB mode."""

    CHANNEL_OFFSETS = {
        "red": 0,
        "green": 1,
        "blue": 2,
    }

    def __init__(self, start_address: int) -> None:
        self.start_address = int(start_address)
        channels = {
            name: self.start_address + off
            for name, off in self.CHANNEL_OFFSETS.items()
        }
        super().__init__(channels)
