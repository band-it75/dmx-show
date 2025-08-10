import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from dmx.Prolights_LumiPar12UQPro_9ch import Prolights_LumiPar12UQPro_9ch


def test_lumipar12uqpro_9ch_controls():
    print("Running Prolights LumiPar 12 UQ Pro 9ch test")
    lamp = Prolights_LumiPar12UQPro_9ch(1)
    print("Setting green")
    lamp.set_channel("green", 2)
    time.sleep(3)
    print("Setting red")
    lamp.set_channel("red", 1)
    time.sleep(3)
    print("Setting blue")
    lamp.set_channel("blue", 3)
    time.sleep(3)
    print("Setting white")
    lamp.set_channel("white", 4)
    time.sleep(3)
    print("Setting strobe")
    lamp.set_strobe(5)
    time.sleep(3)
    print("Setting dimmer")
    lamp.set_dimmer(6)
    time.sleep(3)
    print("Setting color macros")
    lamp.set_channel("color_macros", 7)
    time.sleep(3)
    print("Setting programs")
    lamp.set_channel("programs", 8)
    time.sleep(3)
    print("Setting dimmer curve")
    lamp.set_channel("dimmer_curve", 9)
    time.sleep(3)
    frame = lamp.frame()
    assert frame[lamp.channels["red"]] == 1
    assert frame[lamp.channels["green"]] == 2
    assert frame[lamp.channels["blue"]] == 3
    assert frame[lamp.channels["white"]] == 4
    assert frame[lamp.channels["strobe"]] == 5
    assert frame[lamp.channels["dimmer"]] == 6
    assert frame[lamp.channels["color_macros"]] == 7
    assert frame[lamp.channels["programs"]] == 8
    assert frame[lamp.channels["dimmer_curve"]] == 9
