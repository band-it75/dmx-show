import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from dmx.Prolights_LumiPar12UAW5_7ch import Prolights_LumiPar12UAW5_7ch


def test_lumipar12uaw5_7ch_controls():
    print("Running Prolights LumiPar 12 UAW5 7ch test")
    lamp = Prolights_LumiPar12UAW5_7ch(1)
    print("Setting amber")
    lamp.set_channel("amber", 50)
    time.sleep(3)
    print("Setting cold white")
    lamp.set_channel("cold_white", 60)
    time.sleep(3)
    print("Setting warm white")
    lamp.set_channel("warm_white", 70)
    time.sleep(3)
    print("Setting strobe")
    lamp.set_strobe(80)
    time.sleep(3)
    print("Setting dimmer")
    lamp.set_dimmer(90)
    time.sleep(3)
    print("Setting programs")
    lamp.set_channel("programs", 100)
    time.sleep(3)
    print("Setting dimmer curve")
    lamp.set_channel("dimmer_curve", 110)
    time.sleep(3)
    frame = lamp.frame()
    assert frame[lamp.channels["amber"]] == 50
    assert frame[lamp.channels["cold_white"]] == 60
    assert frame[lamp.channels["warm_white"]] == 70
    assert frame[lamp.channels["strobe"]] == 80
    assert frame[lamp.channels["dimmer"]] == 90
    assert frame[lamp.channels["programs"]] == 100
    assert frame[lamp.channels["dimmer_curve"]] == 110
