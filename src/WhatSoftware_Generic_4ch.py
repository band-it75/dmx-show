from __future__ import annotations

from dmx import DmxDevice


class WhatSoftware_Generic_4ch(DmxDevice):
    """Generic 4-channel fog machine driver."""

    CHANNEL_OFFSETS = {
        "fog": 0,
        "reserved_2": 1,
        "reserved_3": 2,
        "reserved_4": 3,
    }

    def __init__(self, start_address: int) -> None:
        self.start_address = int(start_address)
        channels = {
            name: self.start_address + off
            for name, off in self.CHANNEL_OFFSETS.items()
        }
        super().__init__(channels)
