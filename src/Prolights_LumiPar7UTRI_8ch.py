"""Helpers for the Prolights LumiPar 7 UTRI fixture in 8-channel mode."""

from __future__ import annotations

import time
from typing import Callable, Dict

# Channel offsets (0-indexed) according to the fixture manual
RED_OFFSET = 0
GREEN_OFFSET = 1
BLUE_OFFSET = 2
DIMMER_OFFSET = 6


def blink_red(send_func: Callable[[Dict[int, int]], None], *, start_address: int = 1,
              blink_times: int = 3, interval: float = 0.1) -> None:
    """Blink the fixture red using ``send_func`` to transmit DMX values.

    ``send_func`` should accept a mapping of DMX channel numbers to values.
    Only the channels relevant for this fixture are included in the map.
    """
    on_frame = {
        start_address + RED_OFFSET: 255,
        start_address + GREEN_OFFSET: 0,
        start_address + BLUE_OFFSET: 0,
        start_address + DIMMER_OFFSET: 255,
    }
    off_frame = {
        start_address + DIMMER_OFFSET: 0,
    }
    for _ in range(blink_times):
        send_func(on_frame)
        time.sleep(interval)
        send_func(off_frame)
        time.sleep(interval)
