import argparse
import time

import numpy as np
import sounddevice as sd
import aubio
from ola.ClientWrapper import ClientWrapper

import parameters


class DmxBeatBlinker:
    """Blink one DMX channel whenever a beat is detected."""

    def __init__(
        self,
        universe: int = parameters.UNIVERSE,
        channel: int = parameters.CHANNEL,
        samplerate: int = parameters.SAMPLERATE,
        print_interval: float = parameters.PRINT_INTERVAL,
    ) -> None:
        self.universe = universe
        self.channel = channel
        self.samplerate = samplerate
        self.wrapper = ClientWrapper()
        self.client = self.wrapper.Client()
        self.tempo = aubio.tempo("default", 1024, 512, samplerate)
        self.beat_times: list[float] = []
        self.print_interval = print_interval
        self.last_print = 0.0
        self.on_beat = None

    def _send_dmx_value(self, channel: int, value: int) -> None:
        data = bytearray(512)
        data[channel - 1] = value
        self.client.SendDmx(self.universe, data, lambda state: self.wrapper.Stop())
        self.wrapper.Run()

    def _blink(self):
        self._send_dmx_value(self.channel, 255)
        time.sleep(0.05)
        self._send_dmx_value(self.channel, 0)

    def _compute_bpm(self) -> float:
        """Return the average BPM from recorded beat times."""
        if len(self.beat_times) < 2:
            return 0.0
        intervals = np.diff(self.beat_times)
        if len(intervals) == 0:
            return 0.0
        return 60.0 / np.mean(intervals)

    def get_bpm(self) -> float:
        """Return the most recent BPM estimate."""
        return self._compute_bpm()

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print(status, flush=True)
        samples = np.frombuffer(indata, dtype=np.float32)
        now = time.time()
        if self.tempo(samples):
            self._blink()
            self.beat_times.append(now)
            bpm = self._compute_bpm()
            if bpm and now - self.last_print >= self.print_interval:
                print(f"Estimated BPM: {bpm:.2f}", flush=True)
                self.last_print = now
            if self.on_beat:
                try:
                    self.on_beat(bpm)
                except Exception as exc:  # pragma: no cover - user callback
                    print(f"Callback error: {exc}", flush=True)
        self.beat_times = [t for t in self.beat_times if now - t <= 60]

    def run(self):
        with sd.InputStream(channels=1, callback=self.audio_callback,
                            samplerate=self.samplerate, blocksize=512):
            print("Listening for beats. Press Ctrl+C to stop.")
            try:
                while True:
                    sd.sleep(1000)
            except KeyboardInterrupt:
                print("Stopping")


def main() -> None:
    parser = argparse.ArgumentParser(description="Blink DMX lights on detected beats from microphone")
    parser.add_argument("--universe", type=int,
                        default=parameters.UNIVERSE,
                        help="DMX universe to control")
    parser.add_argument("--channel", type=int,
                        default=parameters.CHANNEL,
                        help="DMX channel to blink")
    parser.add_argument("--print-interval", type=float,
                        default=parameters.PRINT_INTERVAL,
                        help="Seconds between BPM summaries")
    args = parser.parse_args()

    blinker = DmxBeatBlinker(universe=args.universe,
                             channel=args.channel,
                             print_interval=args.print_interval)
    blinker.run()


if __name__ == "__main__":
    main()
