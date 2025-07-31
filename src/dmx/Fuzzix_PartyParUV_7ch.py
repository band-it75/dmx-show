from __future__ import annotations

from dmx import DmxDevice


class Fuzzix_PartyParUV_7ch(DmxDevice):
    """Fuzzix PartyPar UV fixture in 7-channel mode."""

    CHANNEL_OFFSETS = {
        "dimmer": 0,
        "uv1": 1,
        "uv2": 2,
        "uv3": 3,
        "uv4": 4,
        "strobe": 5,
        "macro": 6,
    }

    def __init__(self, start_address: int) -> None:
        self.start_address = int(start_address)
        channels = {
            name: self.start_address + off
            for name, off in self.CHANNEL_OFFSETS.items()
        }
        super().__init__(channels)
