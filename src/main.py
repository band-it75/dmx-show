from __future__ import annotations

import time
from typing import Callable, Dict

from dmx import DMX
from Prolights_LumiPar7UTRI_8ch import Prolights_LumiPar7UTRI_8ch




def main() -> None:
    """Toggle red and green on a single fixture for testing."""
    with DMX([(Prolights_LumiPar7UTRI_8ch, 1)], port="COM4") as controller:
        fixture = controller.devices[0]
        fixture.set_dimmer(255)
        controller.update()
        red = True
        while True:
            if red:
                fixture.set_color(255, 0, 0)
            else:
                fixture.set_color(0, 255, 0)
            controller.update()
            red = not red
            time.sleep(1)


if __name__ == "__main__":
    main()
