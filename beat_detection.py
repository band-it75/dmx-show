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
                 end_duration: float = parameters.END_DURATION):
        self.samplerate = samplerate
        self.tempo = aubio.tempo("default", 1024, 512, samplerate)
        self.beat_times = []
        self.last_bpm_print = time.time()
        self.amplitude_threshold = amplitude_threshold
        self.start_duration = start_duration
        self.end_duration = end_duration
        self.state = "Intermission"
        self.state_change_time = time.time()
        self.last_loud_time = 0.0

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
        elif self.state == "Ongoing" and not is_loud and now - self.last_loud_time > self.end_duration:
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
        if self.tempo(samples):
            print(f"Beat @ {self.tempo.get_last_s():.2f}s", flush=True)
            self.beat_times.append(now)
        if now - self.last_bpm_print >= 10:
            bpm = self._compute_bpm()
            if bpm:
                print(f"Estimated BPM: {bpm:.2f}", flush=True)
                genre = self._detect_genre(bpm)
                print(f"Likely genre: {genre}", flush=True)
            else:
                print("Insufficient data for BPM", flush=True)
            self.last_bpm_print = now
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
    args = parser.parse_args()

    detector = BeatDetector(samplerate=args.samplerate,
                            amplitude_threshold=args.amplitude_threshold,
                            start_duration=args.start_duration,
                            end_duration=args.end_duration)
    detector.run()


if __name__ == "__main__":
    main()
