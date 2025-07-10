import argparse
import time

import numpy as np
import sounddevice as sd
import aubio
from ola.ClientWrapper import ClientWrapper

import parameters
from parameters import Scenario


class DmxBeatBlinker:
    def __init__(self, universe: int = parameters.UNIVERSE,
                 channel: int = parameters.CHANNEL,
                 samplerate: int = parameters.SAMPLERATE,
                 print_interval: float = parameters.PRINT_INTERVAL):
        self.universe = universe
        self.channel = channel
        self.samplerate = samplerate
        self.wrapper = ClientWrapper()
        self.client = self.wrapper.Client()
        self.tempo = aubio.tempo("default", 1024, 512, samplerate)
        self.beat_times = []
        self.print_interval = print_interval
        # fixed smoke parameters controlled by the show
        self.smoke_channel = 115
        self.smoke_gap = 30000  # milliseconds
        self.smoke_duration = 3000  # milliseconds
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
        self.last_genre: Scenario | None = None

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
    def _detect_genre(bpm: float) -> Scenario:
        """Return scenario for this BPM using ``parameters`` ranges."""
        return parameters.scenario_for_bpm(bpm)

    @staticmethod
    def _genre_color(genre: Scenario) -> str:
        mapping = {
            Scenario.SONG_ONGOING_SLOW: "red",
            Scenario.SONG_ONGOING_JAZZ: "amber",
            Scenario.SONG_ONGOING_POP: "pink",
            Scenario.SONG_ONGOING_ROCK: "red",
            Scenario.SONG_ONGOING_METAL: "white",
        }
        return mapping.get(genre, "white")

    @staticmethod
    def _stage_light_color(genre: Scenario) -> str:
        if genre in (Scenario.SONG_ONGOING_SLOW, Scenario.SONG_ONGOING_JAZZ):
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
        if self.smoke_on and (now - self.smoke_start_time) * 1000 >= self.smoke_duration:
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
                    print(f"Likely genre: {genre.value}", flush=True)
                    self.last_bpm = bpm
                    self.last_genre = genre
                self._print_state_change(
                    moving_light="Artist",
                    stage_light=stage_color,
                    overhead=f"{effect_color.capitalize()} (80%) Pulsing",
                    karaoke=f"{effect_color.capitalize()} (10%)",
                )
                if (
                    not self.smoke_on
                    and (now - self.last_smoke_time) * 1000 >= self.smoke_gap
                ):
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
    args = parser.parse_args()

    blinker = DmxBeatBlinker(universe=args.universe,
                             channel=args.channel,
                             print_interval=args.print_interval)
    blinker.run()


if __name__ == "__main__":
    main()
