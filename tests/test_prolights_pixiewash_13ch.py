import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from dmx.Prolights_PixieWash_13ch import Prolights_PixieWash_13ch


def test_pixiewash_13ch_controls():
    print("Running Prolights PixieWash 13ch test")
    lamp = Prolights_PixieWash_13ch(1)
    print("Setting pan/tilt")
    lamp.set_pan_tilt(0x1234, 0x5678)
    time.sleep(3)
    print("Setting dimmer")
    lamp.set_dimmer(70)
    time.sleep(3)
    print("Setting strobe")
    lamp.set_strobe(80)
    time.sleep(3)
    print("Setting red")
    lamp.set_channel("red", 10)
    time.sleep(3)
    print("Setting green")
    lamp.set_channel("green", 20)
    time.sleep(3)
    print("Setting blue")
    lamp.set_channel("blue", 30)
    time.sleep(3)
    print("Setting white")
    lamp.set_channel("white", 40)
    time.sleep(3)
    print("Setting special")
    lamp.set_channel("special", 50)
    time.sleep(3)
    print("Setting pan/tilt speed")
    lamp.set_channel("pan_tilt_speed", 60)
    time.sleep(3)
    print("Setting color macros")
    lamp.set_channel("color_macros", 90)
    time.sleep(3)
    frame = lamp.frame()
    assert frame[lamp.channels["pan"]] == 0x12
    assert frame[lamp.channels["pan_fine"]] == 0x34
    assert frame[lamp.channels["tilt"]] == 0x56
    assert frame[lamp.channels["tilt_fine"]] == 0x78
    assert frame[lamp.channels["dimmer"]] == 70
    assert frame[lamp.channels["shutter"]] == 80
    assert frame[lamp.channels["red"]] == 10
    assert frame[lamp.channels["green"]] == 20
    assert frame[lamp.channels["blue"]] == 30
    assert frame[lamp.channels["white"]] == 40
    assert frame[lamp.channels["special"]] == 50
    assert frame[lamp.channels["pan_tilt_speed"]] == 60
    assert frame[lamp.channels["color_macros"]] == 90
