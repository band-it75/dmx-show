from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple, Type

try:
    import serial  # type: ignore
except Exception:  # pragma: no cover - serial only required when running on real hardware
    serial = None


@dataclass
class DmxDevice:
    """Base class for DMX fixtures."""

    start_address: int

    def frame(self) -> Dict[int, int]:
        """Return a mapping of channel numbers to values."""
        raise NotImplementedError


class DmxSerial:
    """Simple DMX sender using a serial interface."""

    def __init__(self, port: str = "COM4", baudrate: int = 250000) -> None:
        self.port = port
        self.baudrate = baudrate
        self._serial = None

    def __enter__(self) -> "DmxSerial":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # -- serial helpers -------------------------------------------------
    def open(self) -> None:
        if serial is None:
            raise RuntimeError("pyserial not available")
        if self._serial is None:
            self._serial = serial.Serial(self.port, self.baudrate)

    def close(self) -> None:
        if self._serial is not None:
            self._serial.close()
            self._serial = None

    def send(self, values: Dict[int, int]) -> None:
        """Send DMX values as a full 512 byte frame."""
        data = bytearray(512)
        for channel, value in values.items():
            if 1 <= channel <= 512:
                data[channel - 1] = max(0, min(255, value))
        if self._serial is None:
            raise RuntimeError("Serial port not open")
        # Start code (0) + data
        self._serial.write(bytes([0]) + data)


class DMX:
    """Manage multiple devices and send combined frames."""

    def __init__(self, devices: Iterable[Tuple[Type[DmxDevice], int]], port: str = "COM4") -> None:
        self.devices = [cls(addr) for cls, addr in devices]
        self.serial = DmxSerial(port)

    def send_frame(self) -> None:
        frame: Dict[int, int] = {}
        for device in self.devices:
            frame.update(device.frame())
        self.serial.send(frame)

    def __enter__(self) -> "DMX":
        self.serial.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.serial.__exit__(exc_type, exc, tb)
