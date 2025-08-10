import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from dmx.Fuzzix_PartyParUV_7ch import Fuzzix_PartyParUV_7ch


def test_fuzzix_partyparuv_7ch_controls():
    print("Running Fuzzix PartyPar UV 7ch test")
    lamp = Fuzzix_PartyParUV_7ch(1)
    print("Setting dimmer")
    lamp.set_dimmer(100)
    time.sleep(3)
    print("Setting uv1")
    lamp.set_channel("uv1", 10)
    time.sleep(3)
    print("Setting uv2")
    lamp.set_channel("uv2", 20)
    time.sleep(3)
    print("Setting uv3")
    lamp.set_channel("uv3", 30)
    time.sleep(3)
    print("Setting uv4")
    lamp.set_channel("uv4", 40)
    time.sleep(3)
    print("Setting strobe")
    lamp.set_strobe(200)
    time.sleep(3)
    print("Setting macro")
    lamp.set_channel("macro", 150)
    time.sleep(3)
    frame = lamp.frame()
    assert frame[lamp.channels["dimmer"]] == 100
    assert frame[lamp.channels["uv1"]] == 10
    assert frame[lamp.channels["uv2"]] == 20
    assert frame[lamp.channels["uv3"]] == 30
    assert frame[lamp.channels["uv4"]] == 40
    assert frame[lamp.channels["strobe"]] == 200
    assert frame[lamp.channels["macro"]] == 150
