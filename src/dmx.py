"""Simple DMX sender for an FTDI USB to DMX cable on COM4."""

from __future__ import annotations

import time
from typing import Mapping, Tuple
import argparse

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


def _parse_pair(text: str) -> Tuple[int, int]:
    """Return a ``(channel, value)`` tuple from ``CH:VAL`` input."""
    if ":" not in text:
        raise argparse.ArgumentTypeError("Expected CH:VAL")
    ch_str, val_str = text.split(":", 1)
    try:
        ch = int(ch_str)
        val = int(val_str)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Channel and value must be integers") from exc
    if not 1 <= ch <= 512:
        raise argparse.ArgumentTypeError("Channel must be 1-512")
    if not 0 <= val <= 255:
        raise argparse.ArgumentTypeError("Value must be 0-255")
    return ch, val


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a DMX frame once")
    parser.add_argument(
        "pairs",
        metavar="CH:VAL",
        nargs="*",
        type=_parse_pair,
        default=[],
        help="DMX channel and value pairs",
    )
    parser.add_argument("--port", default="COM4", help="Serial port")
    parser.add_argument("--channels", type=int, default=512,
                        help="Number of DMX channels")
    args = parser.parse_args()

    if not args.pairs:
        parser.print_usage()
        print("No channel/value pairs provided. Example: python dmx.py 1:255")
        return

    values = dict(args.pairs)
    with DmxSerial(port=args.port, channels=args.channels) as dmx:
        dmx.send(values)


if __name__ == "__main__":
    main()
