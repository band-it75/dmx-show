import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from dmx.Prolights_LumiPar7UTRI_8ch import Prolights_LumiPar7UTRI_8ch


def test_lumipar7utri_8ch_controls():
    print("Running Prolights LumiPar 7 UTRI 8ch test")
    lamp = Prolights_LumiPar7UTRI_8ch(1)
    print("Setting green")
    lamp.set_channel("green", 2)
    time.sleep(3)
    print("Setting red")
    lamp.set_channel("red", 1)
    time.sleep(3)
    print("Setting blue")
    lamp.set_channel("blue", 3)
    time.sleep(3)
    print("Setting strobe")
    lamp.set_strobe(4)
    time.sleep(3)
    print("Setting dimmer")
    lamp.set_dimmer(5)
    time.sleep(3)
    print("Setting color macros")
    lamp.set_channel("color_macros", 6)
    time.sleep(3)
    print("Setting programs")
    lamp.set_channel("programs", 7)
    time.sleep(3)
    print("Setting dimmer speed")
    lamp.set_channel("dimmer_speed", 8)
    time.sleep(3)
    frame = lamp.frame()
    assert frame[lamp.channels["red"]] == 1
    assert frame[lamp.channels["green"]] == 2
    assert frame[lamp.channels["blue"]] == 3
    assert frame[lamp.channels["strobe"]] == 4
    assert frame[lamp.channels["dimmer"]] == 5
    assert frame[lamp.channels["color_macros"]] == 6
    assert frame[lamp.channels["programs"]] == 7
    assert frame[lamp.channels["dimmer_speed"]] == 8
