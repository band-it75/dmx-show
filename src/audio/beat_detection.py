import argparse
import time

import parameters
from parameters import Scenario

import numpy as np
import sounddevice as sd
import aubio


class BeatDetector:
    def __init__(self, samplerate: int = parameters.SAMPLERATE,
                 amplitude_threshold: float = parameters.AMPLITUDE_THRESHOLD,
                 start_duration: float = parameters.START_DURATION,
                 end_duration: float = parameters.END_DURATION,
                 print_interval: float = parameters.PRINT_INTERVAL):
        self.samplerate = samplerate
        self.tempo = aubio.tempo("default", 1024, 512, samplerate)
        self.beat_times = []
        self.amplitude_threshold = amplitude_threshold
        self.start_duration = start_duration
        self.end_duration = end_duration
        self.print_interval = print_interval
        self.scenario = parameters.SCENARIO_MAP[Scenario.INTERMISSION]
        self.last_smoke_time = 0.0
        self.smoke_on = False
        self.smoke_start_time = 0.0
        self.current_smoke_duration = 0.0
        self.state = "Intermission"
        self.state_change_time = time.time()
        self.last_loud_time = 0.0
        self.lighting_state = {
            "moving_light": "Artist",
            "stage_light": "Off",
            "overhead_effects": "Off",
            "karaoke_lights": "Off",
        }
        self.last_bpm = 0.0
        self.last_genre: Scenario | None = None

    def _set_scenario(self, name: Scenario) -> None:
        current = self.scenario
        if (
            name != current
            and (current not in name.predecessors or name not in current.successors)
        ):
            return
        self.scenario = parameters.SCENARIO_MAP[name]

    def _update_state_lighting(self) -> None:
        """Update lights based on the current song state."""
        if self.state == "Ending":
            self._print_state_change(
                moving_light="Audience",
                stage_light="Warm White (50%)",
            )
        elif self.state in ("Starting", "Ongoing"):
            self._print_state_change(moving_light="Artist", stage_light="Off")
        elif self.state == "Intermission":
            self._print_state_change(
                moving_light="Off",
                stage_light="Warm White (20%) Fading",
            )

    def _compute_bpm(self) -> float:
        """Return the estimated BPM using recent beat intervals."""
        if len(self.beat_times) < 2:
            return 0.0
        # only keep the last few beat times for a more robust estimate
        recent = self.beat_times[-8:]
        intervals = np.diff(recent)
        if len(intervals) == 0:
            return 0.0
        # median is less sensitive to occasional mis-detected beats
        return 60.0 / float(np.median(intervals))

    @staticmethod
    def _detect_genre(bpm: float) -> Scenario:
        """Return scenario for this BPM using ranges from ``parameters``."""
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

    def _print_state_change(self, **updates) -> None:
        changes = {}
        for name, val in updates.items():
            if self.lighting_state.get(name) != val:
                changes[name] = val
                self.lighting_state[name] = val
        if changes:
            print("Change:", flush=True)
            for name, val in changes.items():
                label = name.replace('_', ' ').title()
                print(f"- {label}: {val}", flush=True)
            print("Current:", flush=True)
            for name, val in self.lighting_state.items():
                label = name.replace('_', ' ').title()
                print(f"- {label}: {val}", flush=True)

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print(status, flush=True)
        samples = np.frombuffer(indata, dtype=np.float32)
        now = time.time()
        amplitude = float(np.sqrt(np.mean(np.square(samples))))
        is_loud = amplitude > self.amplitude_threshold
        if is_loud:
            self.last_loud_time = now

        # Song state machine based on amplitude
        if self.state == "Intermission" and is_loud:
            self.state = "Starting"
            self.state_change_time = now
            self._set_scenario(Scenario.SONG_START)
            print("Song starting", flush=True)
        elif self.state == "Starting":
            if now - self.state_change_time >= self.start_duration:
                if is_loud:
                    self.state = "Ongoing"
                    self._set_scenario(Scenario.SONG_START)
                    print("Song ongoing", flush=True)
                else:
                    self.state = "Intermission"
                    self._set_scenario(Scenario.INTERMISSION)
                    print("Intermission", flush=True)
            elif not is_loud and now - self.last_loud_time > self.end_duration:
                self.state = "Intermission"
                self._set_scenario(Scenario.INTERMISSION)
                print("Intermission", flush=True)
        elif (self.state == "Ongoing" and not is_loud and
              now - self.last_loud_time > self.end_duration):
            self.state = "Ending"
            self.state_change_time = now
            self._set_scenario(Scenario.SONG_ENDING)
            print("Song ending", flush=True)
        elif self.state == "Ending":
            if is_loud:
                self.state = "Starting"
                self.state_change_time = now
                self._set_scenario(Scenario.SONG_START)
                print("Song starting", flush=True)
            elif now - self.state_change_time >= self.end_duration:
                self.state = "Intermission"
                self._set_scenario(Scenario.INTERMISSION)
                print("Intermission", flush=True)

        # Update lights based on the detected state
        self._update_state_lighting()
        if self.tempo(samples):
            self.beat_times.append(now)
            bpm = self._compute_bpm()
            if bpm:
                genre = self._detect_genre(bpm)
                effect_color = self._genre_color(genre)
                if abs(bpm - self.last_bpm) >= 1 or genre != self.last_genre:
                    print(f"Estimated BPM: {bpm:.2f}", flush=True)
                    print(f"Likely genre: {genre.value}", flush=True)
                    self.last_bpm = bpm
                    self.last_genre = genre
                if self.state == "Ongoing" and genre != self.scenario:
                    self._set_scenario(genre)
                self._print_state_change(
                    overhead_effects=f"{effect_color.capitalize()} (80%) Pulsing",
                    karaoke_lights=f"{effect_color.capitalize()} (10%)",
                )
                gap, duration = parameters.smoke_settings(self.scenario)
                if (
                    not self.smoke_on
                    and (now - self.last_smoke_time) * 1000 >= gap
                ):
                    print("Smoke start", flush=True)
                    self.smoke_on = True
                    self.smoke_start_time = now
                    self.last_smoke_time = now
                    self.current_smoke_duration = duration / 1000.0
            else:
                if (self.lighting_state["moving_light"] != "Audience" or
                        self.lighting_state["stage_light"] != "Off"):
                    print("Insufficient data for BPM", flush=True)
                    self._print_state_change(moving_light="Audience", stage_light="Off")
        # handle smoke timing
        if self.smoke_on and now - self.smoke_start_time >= self.current_smoke_duration:
            print("Smoke end", flush=True)
            self.smoke_on = False
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
    parser = argparse.ArgumentParser(description="Detect beats from microphone input")
    parser.add_argument("--samplerate", type=int,
                        default=parameters.SAMPLERATE,
                        help="Audio samplerate")
    parser.add_argument("--amplitude-threshold", type=float,
                        default=parameters.AMPLITUDE_THRESHOLD,
                        help="RMS amplitude threshold for song detection")
    parser.add_argument("--start-duration", type=float,
                        default=parameters.START_DURATION,
                        help="Seconds audio must stay loud to mark song start")
    parser.add_argument("--end-duration", type=float,
                        default=parameters.END_DURATION,
                        help="Seconds audio must stay quiet to mark song end")
    parser.add_argument("--print-interval", type=float,
                        default=parameters.PRINT_INTERVAL,
                        help="Seconds between BPM summaries")
    args = parser.parse_args()

    detector = BeatDetector(samplerate=args.samplerate,
                            amplitude_threshold=args.amplitude_threshold,
                            start_duration=args.start_duration,
                            end_duration=args.end_duration,
                            print_interval=args.print_interval)
    detector.run()


if __name__ == "__main__":
    main()
