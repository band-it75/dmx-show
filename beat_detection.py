import argparse
import time

import numpy as np
import sounddevice as sd
import aubio


class BeatDetector:
    def __init__(self, samplerate: int = 44100):
        self.samplerate = samplerate
        self.tempo = aubio.tempo("default", 1024, 512, samplerate)
        self.beat_times = []
        self.last_bpm_print = time.time()

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
        if bpm > 140:
            return "Metal"
        if bpm > 110:
            return "Rock"
        if bpm > 90:
            return "Pop"
        return "Slow"

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print(status, flush=True)
        samples = np.frombuffer(indata, dtype=np.float32)
        now = time.time()
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
    parser.add_argument("--samplerate", type=int, default=44100,
                        help="Audio samplerate")
    args = parser.parse_args()

    detector = BeatDetector(samplerate=args.samplerate)
    detector.run()


if __name__ == "__main__":
    main()
