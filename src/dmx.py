"""Simple DMX sender for an FTDI USB to DMX cable on COM4."""

from __future__ import annotations

import time
from typing import Mapping

import serial


class DmxSerial:
    """Send DMX frames over a serial connection."""

    def __init__(self, port: str = "COM4", channels: int = 512) -> None:
        self.serial = serial.Serial(
            port=port,
            baudrate=250000,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO,
        )
        self.channels = channels
        # Allocate frame including the start code at index 0
        self.frame = bytearray(channels + 1)
        self.frame[0] = 0

    def send(self, values: Mapping[int, int]) -> None:
        """Update DMX channels and transmit the frame."""
        for channel, value in values.items():
            if not 1 <= channel <= self.channels:
                raise ValueError(f"Channel {channel} out of range")
            self.frame[channel] = max(0, min(255, value))

        # Transmit DMX break and frame
        self.serial.break_condition = True
        time.sleep(0.0001)
        self.serial.break_condition = False
        time.sleep(0.000012)
        self.serial.write(self.frame)
        self.serial.flush()

    def close(self) -> None:
        self.serial.close()

    def __enter__(self) -> "DmxSerial":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
