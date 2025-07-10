from __future__ import annotations

from typing import Dict

from dmx import DmxDevice


class Prolights_LumiPar7UTRI_8ch(DmxDevice):
    """Prolights LumiPar 7 UTRI fixture in 8-channel mode."""

    def frame_from_rgb(self, red: int, green: int, blue: int, dimmer: int = 255) -> Dict[int, int]:
        start = self.start_address
        return {
            start: red,
            start + 1: green,
            start + 2: blue,
            start + 6: dimmer,  # master dimmer
        }
