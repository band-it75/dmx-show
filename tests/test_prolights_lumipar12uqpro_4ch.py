import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from dmx.Prolights_LumiPar12UQPro_4ch import Prolights_LumiPar12UQPro_4ch


def test_lumipar12uqpro_4ch_color():
    print("Running Prolights LumiPar 12 UQ Pro 4ch test")
    lamp = Prolights_LumiPar12UQPro_4ch(1)
    print("Setting green")
    lamp.set_channel("green", 20)
    time.sleep(3)
    print("Setting red")
    lamp.set_channel("red", 10)
    time.sleep(3)
    print("Setting blue")
    lamp.set_channel("blue", 30)
    time.sleep(3)
    print("Setting white")
    lamp.set_channel("white", 40)
    time.sleep(3)
    frame = lamp.frame()
    assert frame[lamp.channels["red"]] == 10
    assert frame[lamp.channels["green"]] == 20
    assert frame[lamp.channels["blue"]] == 30
    assert frame[lamp.channels["white"]] == 40
