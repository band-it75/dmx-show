import argparse
import time

import numpy as np
import sounddevice as sd
import aubio
from ola.ClientWrapper import ClientWrapper

import parameters


class DmxBeatBlinker:
    def __init__(self, universe: int = parameters.UNIVERSE,
                 channel: int = parameters.CHANNEL,
                 samplerate: int = parameters.SAMPLERATE,
                 print_interval: float = parameters.PRINT_INTERVAL,
                 smoke_channel: int = parameters.SMOKE_CHANNEL,
                 smoke_gap: float = parameters.SMOKE_GAP,
                 smoke_duration: float = parameters.SMOKE_DURATION):
        self.universe = universe
        self.channel = channel
        self.samplerate = samplerate
        self.wrapper = ClientWrapper()
        self.client = self.wrapper.Client()
        self.tempo = aubio.tempo("default", 1024, 512, samplerate)
        self.beat_times = []
        self.print_interval = print_interval
        self.smoke_channel = smoke_channel
        self.smoke_gap = smoke_gap
        self.smoke_duration = smoke_duration
        self.last_smoke_time = 0.0
        self.smoke_on = False
        self.smoke_start_time = 0.0
        self.state = {
            "moving_light": "Artist",
            "stage_light": "Off",
            "overhead": "Off",
            "karaoke": "Off",
        }
        self.last_bpm = 0.0
        self.last_genre = ""

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

    @staticmethod
    def _detect_genre(bpm: float) -> str:
        """Rough genre estimation based on BPM."""
        if bpm >= 160:
            return "Metal"
        if bpm >= 130:
            return "Rock"
        if bpm >= 100:
            return "Pop"
        if bpm >= 80:
            return "Jazz"
        return "Slow"

    @staticmethod
    def _genre_color(genre: str) -> str:
        mapping = {
            "Slow": "red",
            "Jazz": "amber",
            "Pop": "pink",
            "Rock": "red",
            "Metal": "white",
        }
        return mapping.get(genre, "white")

    @staticmethod
    def _stage_light_color(genre: str) -> str:
        if genre in ("Slow", "Jazz"):
            return "amber"
        return "white"

    def _print_state_change(self, **updates) -> None:
        changes = {}
        for name, val in updates.items():
            if self.state.get(name) != val:
                changes[name] = val
                self.state[name] = val
        if changes:
            print("Change:", flush=True)
            for name, val in changes.items():
                label = name.replace('_', ' ').title()
                print(f"- {label}: {val}", flush=True)
            print("Current:", flush=True)
            for name, val in self.state.items():
                label = name.replace('_', ' ').title()
                print(f"- {label}: {val}", flush=True)

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print(status, flush=True)
        samples = np.frombuffer(indata, dtype=np.float32)
        now = time.time()
        # handle smoke timing
        if self.smoke_on and now - self.smoke_start_time >= self.smoke_duration:
            print("Smoke end", flush=True)
            self._send_dmx_value(self.smoke_channel, 0)
            self.smoke_on = False
        if self.tempo(samples):
            self._blink()
            self.beat_times.append(now)
            bpm = self._compute_bpm()
            if bpm:
                genre = self._detect_genre(bpm)
                stage_color = self._stage_light_color(genre)
                effect_color = self._genre_color(genre)
                if abs(bpm - self.last_bpm) >= 1 or genre != self.last_genre:
                    print(f"Estimated BPM: {bpm:.2f}", flush=True)
                    print(f"Likely genre: {genre}", flush=True)
                    self.last_bpm = bpm
                    self.last_genre = genre
                self._print_state_change(
                    moving_light="Artist",
                    stage_light=stage_color,
                    overhead=f"{effect_color.capitalize()} (80%) Pulsing",
                    karaoke=f"{effect_color.capitalize()} (10%)",
                )
                if not self.smoke_on and now - self.last_smoke_time >= self.smoke_gap:
                    print("Smoke start", flush=True)
                    self._send_dmx_value(self.smoke_channel, 255)
                    self.smoke_on = True
                    self.smoke_start_time = now
                    self.last_smoke_time = now
            else:
                if (self.state["moving_light"] != "Audience" or
                        self.state["stage_light"] != "Off"):
                    print("Insufficient data for BPM", flush=True)
                    self._print_state_change(moving_light="Audience", stage_light="Off")
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
    parser.add_argument("--smoke-channel", type=int,
                        default=parameters.SMOKE_CHANNEL,
                        help="DMX channel controlling the smoke machine")
    parser.add_argument("--smoke-gap", type=float,
                        default=parameters.SMOKE_GAP,
                        help="Seconds between automatic smoke bursts")
    parser.add_argument("--smoke-duration", type=float,
                        default=parameters.SMOKE_DURATION,
                        help="Length of each smoke burst in seconds")
    args = parser.parse_args()

    blinker = DmxBeatBlinker(universe=args.universe, channel=args.channel,
                             print_interval=args.print_interval,
                             smoke_channel=args.smoke_channel,
                             smoke_gap=args.smoke_gap,
                             smoke_duration=args.smoke_duration)
    blinker.run()


if __name__ == "__main__":
    main()
