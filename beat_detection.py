import argparse
import time

import parameters

import numpy as np
import sounddevice as sd
import aubio


class BeatDetector:
    def __init__(self, samplerate: int = parameters.SAMPLERATE,
                 amplitude_threshold: float = parameters.AMPLITUDE_THRESHOLD,
                 start_duration: float = parameters.START_DURATION,
                 end_duration: float = parameters.END_DURATION,
                 print_interval: float = parameters.PRINT_INTERVAL,
                 smoke_gap: float = parameters.SMOKE_GAP,
                 smoke_duration: float = parameters.SMOKE_DURATION):
        self.samplerate = samplerate
        self.tempo = aubio.tempo("default", 1024, 512, samplerate)
        self.beat_times = []
        self.amplitude_threshold = amplitude_threshold
        self.start_duration = start_duration
        self.end_duration = end_duration
        self.print_interval = print_interval
        self.smoke_gap = smoke_gap
        self.smoke_duration = smoke_duration
        self.slow_gap = 15.0
        self.slow_duration = 2.0
        self.intermission_gap = 60.0
        self.intermission_duration = 5.0
        self.last_smoke_time = 0.0
        self.smoke_on = False
        self.smoke_start_time = 0.0
        self.current_smoke_duration = smoke_duration
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
        self.last_genre = ""

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
            self._print_state_change(moving_light="Audience", stage_light="Off")

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
            print("Song starting", flush=True)
        elif self.state == "Starting":
            if now - self.state_change_time >= self.start_duration:
                if is_loud:
                    self.state = "Ongoing"
                    print("Song ongoing", flush=True)
                else:
                    self.state = "Intermission"
                    print("Intermission", flush=True)
            elif not is_loud and now - self.last_loud_time > self.end_duration:
                self.state = "Intermission"
                print("Intermission", flush=True)
        elif (self.state == "Ongoing" and not is_loud and
              now - self.last_loud_time > self.end_duration):
            self.state = "Ending"
            self.state_change_time = now
            print("Song ending", flush=True)
        elif self.state == "Ending":
            if is_loud:
                self.state = "Starting"
                self.state_change_time = now
                print("Song starting", flush=True)
            elif now - self.state_change_time >= self.end_duration:
                self.state = "Intermission"
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
                    print(f"Likely genre: {genre}", flush=True)
                    self.last_bpm = bpm
                    self.last_genre = genre
                self._print_state_change(
                    moving_light="Artist",
                    overhead_effects=f"{effect_color.capitalize()} (80%) Pulsing",
                    karaoke_lights=f"{effect_color.capitalize()} (10%)",
                )
                gap = self.smoke_gap
                duration = self.smoke_duration
                if self.state == "Intermission":
                    gap = self.intermission_gap
                    duration = self.intermission_duration
                elif self.state == "Ongoing" and genre == "Slow":
                    gap = self.slow_gap
                    duration = self.slow_duration
                if not self.smoke_on and now - self.last_smoke_time >= gap:
                    print("Smoke start", flush=True)
                    self.smoke_on = True
                    self.smoke_start_time = now
                    self.last_smoke_time = now
                    self.current_smoke_duration = duration
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
    parser.add_argument("--smoke-gap", type=float,
                        default=parameters.SMOKE_GAP,
                        help="Seconds between automatic smoke bursts")
    parser.add_argument("--smoke-duration", type=float,
                        default=parameters.SMOKE_DURATION,
                        help="Length of each smoke burst in seconds")
    args = parser.parse_args()

    detector = BeatDetector(samplerate=args.samplerate,
                            amplitude_threshold=args.amplitude_threshold,
                            start_duration=args.start_duration,
                            end_duration=args.end_duration,
                            print_interval=args.print_interval,
                            smoke_gap=args.smoke_gap,
                            smoke_duration=args.smoke_duration)
    detector.run()


if __name__ == "__main__":
    main()
