import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from dmx.WhatSoftware_Generic_4ch import WhatSoftware_Generic_4ch


def test_whatsoftware_generic_4ch_fog():
    print("Running WhatSoftware Generic 4ch test")
    lamp = WhatSoftware_Generic_4ch(1)
    print("Setting fog")
    lamp.set_channel("fog", 200)
    time.sleep(3)
    frame = lamp.frame()
    assert frame[lamp.channels["fog"]] == 200
