from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple, Type, Optional
import threading
import time

try:
    import serial  # type: ignore
except Exception:  # pragma: no cover - serial only required when running on real hardware
    serial = None

@dataclass
class DmxDevice:
    """
    Base class for any DMX fixture.  
    - Define `channels` as a dict of feature → channel-offset (0-based).  
    - Use the provided setters (or override compute_values) to update internal state.  
    - Call frame() to get {offset: value} ready for your DMX output pipeline.
    """

    def __init__(self, channels: Dict[str, int]) -> None:
        """
        :param channels: mapping of logical feature names to relative DMX offsets.
                         e.g. {"red":0, "green":1, "blue":2, "fog":3, "pan":4, ...}
        """
        # Validate & store channel offsets
        self.channels: Dict[str, int] = {}
        for name, off in channels.items():
            off = int(off)
            if off < 0:
                raise ValueError(f"Offset for '{name}' must be ≥ 0")
            self.channels[name] = off

        # Initialize all channel values to 0
        self._values: Dict[str, int] = {name: 0 for name in self.channels}

    def reset(self) -> None:
        """Reset all channels to zero."""
        for name in self._values:
            self._values[name] = 0

    def _approximate_channel(self, name: str, value: int) -> bool:
        """Fallback for abstract color channels.

        Returns ``True`` if the value was mapped to existing channels.
        """
        if name in {"white", "warm_white", "cold_white"}:
            if "white" in self.channels:
                self._values["white"] = max(0, min(255, int(value)))
                return True
            if {"red", "green", "blue"}.issubset(self.channels):
                val = max(0, min(255, int(value)))
                # Avoid recursion by setting RGB directly
                self._values["red"] = val
                self._values["green"] = val
                self._values["blue"] = val
                return True
        if name == "amber":
            if "amber" in self.channels:
                self._values["amber"] = max(0, min(255, int(value)))
                return True
            if {"red", "green"}.issubset(self.channels):
                val = max(0, min(255, int(value)))
                # simple approximation using mostly red
                # Set RGB directly to prevent recursive calls
                self._values["red"] = val
                self._values["green"] = int(val * 0.5)
                return True
        return False

    def set_channel(self, name: str, value: int) -> None:
        """Set one channel by logical name (0–255)."""
        if name in self.channels:
            self._values[name] = max(0, min(255, int(value)))
        elif not self._approximate_channel(name, value):
            raise KeyError(f"No such channel: '{name}'")

    def get_channel(self, name: str) -> int:
        """Get current value for a logical channel (defaults to 0)."""
        return self._values.get(name, 0)

    # Convenience color methods:

    def set_color(self, red: int, green: int, blue: int, white: int = 0, amber: int = 0, uv: int = 0) -> None:
        """Set multiple color channels at once with fallbacks."""
        for name, val in (
            ("red", red),
            ("green", green),
            ("blue", blue),
            ("white", white),
            ("amber", amber),
            ("uv", uv),
        ):
            try:
                self.set_channel(name, val)
            except KeyError:
                # Ignore unknown channels if they cannot be approximated
                pass

    def set_dimmer(self, value: int) -> None:
        if "dimmer" not in self.channels:
            raise KeyError("No 'dimmer' channel defined")
        self._values["dimmer"] = max(0, min(255, int(value)))

    def set_strobe(self, value: int) -> None:
        for key in ("strobe", "shutter"):
            if key in self.channels:
                self._values[key] = max(0, min(255, int(value)))
                return
        raise KeyError("No strobe/shutter channel defined")

    # Movement:

    def set_pan_tilt(self, pan: int, tilt: int) -> None:
        # Pan
        if "pan" not in self.channels:
            raise KeyError("No 'pan' channel defined")
        pan = max(0, int(pan))
        if "pan_fine" in self.channels:
            self._values["pan"] = pan >> 8
            self._values["pan_fine"] = pan & 0xFF
        else:
            self._values["pan"] = min(255, pan)

        # Tilt
        if "tilt" not in self.channels:
            raise KeyError("No 'tilt' channel defined")
        tilt = max(0, int(tilt))
        if "tilt_fine" in self.channels:
            self._values["tilt"] = tilt >> 8
            self._values["tilt_fine"] = tilt & 0xFF
        else:
            self._values["tilt"] = min(255, tilt)

    # Hook for subclasses to inject computed values before framing:
    def compute_values(self) -> None:
        """
        Override this in subclasses if you need to calculate channel values
        dynamically (e.g. moving-head effects, chases, etc.).
        By default, does nothing—relies on manual setters.
        """
        pass

    def frame(self) -> Dict[int, int]:
        """
        Returns a dict mapping *relative* channel-offset → 0–255 value.
        Call compute_values() first, so any dynamic logic runs.
        """
        self.compute_values()
        # Only include channels that exist in self.channels
        return {
            offset: max(0, min(255, self._values[name]))
            for name, offset in self.channels.items()
        }


class DmxSerial:
    """Simple DMX sender using a serial interface."""

    def __init__(self, port: str = "COM4", baudrate: int = 250000) -> None:
        self.port = port
        self.baudrate = baudrate
        self._serial = None
        self.error: Optional[str] = None
        self._last_frame = bytearray(512)

    def __enter__(self) -> "DmxSerial":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # -- serial helpers -------------------------------------------------
    def open(self) -> None:
        if serial is None:
            self.error = "pyserial not available"
            return
        if self._serial is None:
            try:
                # DMX512 uses 8 data bits, no parity and two stop bits
                self._serial = serial.Serial(
                    self.port,
                    self.baudrate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_TWO,
                )
                self.error = None
            except Exception:
                self.error = f"{self.port} not available"

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
        if data == self._last_frame:
            return
        self._last_frame[:] = data
        if self._serial is None:
            return
        # Break (>=88us) and mark after break (>=8us)
        self._serial.break_condition = True
        time.sleep(0.0001)
        self._serial.break_condition = False
        time.sleep(0.000012)
        # Start code (0) + data
        self._serial.write(bytes([0]) + data)


class DMX:
    """Manage multiple devices and continuously send combined frames."""

    def __init__(
        self,
        devices: Iterable[
            Tuple[Type[DmxDevice], int] | Tuple[Type[DmxDevice], int, str]
        ],
        port: str = "COM4",
        fps: int = 44,
        pre_send: Callable[["DMX"], None] | None = None,
    ) -> None:
        """Create a DMX controller.

        ``pre_send`` is an optional callback executed in the sending thread
        right before each frame is transmitted. It can update device values
        without risking a backlog of pending frames.
        """

        self.devices: list[DmxDevice] = []
        self.groups: Dict[str, list[DmxDevice]] = {}
        for item in devices:
            if len(item) == 2:
                cls, addr = item  # type: ignore[misc]
                name = None
            else:
                cls, addr, name = item  # type: ignore[misc]
            device = cls(addr)
            self.devices.append(device)
            if name:
                self.groups.setdefault(name, []).append(device)

        self.serial = DmxSerial(port)
        self.interval = 1.0 / float(fps)
        self._frame: Dict[int, int] = {}
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.pre_send = pre_send

    def reset(self) -> None:
        """Reset all device channels to zero and store the frame."""
        for device in self.devices:
            device.reset()
        self.update()

    def _compute_frame(self) -> Dict[int, int]:
        frame: Dict[int, int] = {}
        for device in self.devices:
            frame.update(device.frame())
        return frame

    def update(self) -> None:
        """Compute the current frame from devices and store it."""
        frame = self._compute_frame()
        with self._lock:
            self._frame = frame

    def send_frame(self) -> None:
        self.update()
        with self._lock:
            frame = dict(self._frame)
        self.serial.send(frame)

    def _loop(self) -> None:
        while self._running:
            if self.pre_send:
                try:
                    self.pre_send(self)
                except Exception:
                    pass
            with self._lock:
                frame = dict(self._frame)
            self.serial.send(frame)
            time.sleep(self.interval)

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join()
            self._thread = None

    def __enter__(self) -> "DMX":
        self.serial.__enter__()
        self.update()
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()
        self.serial.__exit__(exc_type, exc, tb)
