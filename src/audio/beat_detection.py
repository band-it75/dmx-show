"""Audio analysis utilities to detect beats and basic song state."""

from __future__ import annotations

import time
from enum import Enum
from typing import Tuple

import numpy as np
import sounddevice as sd
import aubio
import librosa


class SongState(Enum):
    """Simple states derived from audio volume."""

    INTERMISSION = "Intermission"
    STARTING = "Starting"
    ONGOING = "Ongoing"
    ENDING = "Ending"


class BeatDetector:
    """Detect beats and estimate song state purely from audio."""

    def __init__(
        self,
        samplerate: int = 44100,
        amplitude_threshold: float = 0.02,
        start_duration: float = 2.0,
        end_duration: float = 3.0,
        print_interval: float = 10.0,
    ) -> None:
        self.samplerate = samplerate
        self.tempo = aubio.tempo("default", 1024, 512, samplerate)
        self.onset = aubio.onset("default", 1024, 512, samplerate)
        self.beat_times: list[float] = []
        self.amplitude_threshold = amplitude_threshold
        self.start_duration = start_duration
        self.end_duration = end_duration
        self.print_interval = print_interval
        self.state: SongState = SongState.INTERMISSION
        self.state_change_time = time.time()
        self.last_loud_time = 0.0
        self.last_print = 0.0
        self.last_amplitude = 0.0
        self.previous_rms = 0.0
        self.is_drum_solo = False
        self.is_chorus = False
        self.is_crescendo = False
        self.snare_hit = False
        self.kick_hit = False

    # ------------------------------------------------------------------
    def _compute_bpm(self) -> float:
        if len(self.beat_times) < 2:
            return 0.0
        recent = self.beat_times[-8:]
        intervals = np.diff(recent)
        if len(intervals) == 0:
            return 0.0
        return 60.0 / float(np.median(intervals))

    def process(
        self, samples: np.ndarray, now: float | None = None
    ) -> Tuple[bool, float, bool, float]:
        """Process raw audio samples and return analysis results.

        Returns ``(beat_detected, bpm, state_changed, vu)`` where ``vu`` is the
        RMS level of ``samples``.
        """
        if now is None:
            now = time.time()
        amplitude = float(np.sqrt(np.mean(np.square(samples))))
        self.last_amplitude = amplitude
        loud = amplitude > self.amplitude_threshold
        state_changed = False
        if loud:
            self.last_loud_time = now

        # Feature extraction for section detection
        rms = float(librosa.feature.rms(y=samples).mean())
        flatness = float(librosa.feature.spectral_flatness(y=samples).mean())
        self.is_chorus = rms > 0.1 and flatness < 0.2
        self.is_crescendo = rms > self.previous_rms * 1.1
        self.previous_rms = rms

        y_harm, y_perc = librosa.effects.hpss(samples)
        perc_energy = float(np.sum(y_perc ** 2))
        harm_energy = float(np.sum(y_harm ** 2))
        self.is_drum_solo = perc_energy > 3 * harm_energy

        # Transient detection for snare/kick hits
        self.snare_hit = False
        self.kick_hit = False
        if self.onset(samples):
            centroid = float(
                librosa.feature.spectral_centroid(y=samples, sr=self.samplerate).mean()
            )
            if centroid > 4000:
                self.snare_hit = True
            elif centroid < 500:
                self.kick_hit = True

        # song state machine
        if self.state == SongState.INTERMISSION and loud:
            self.state = SongState.STARTING
            self.state_change_time = now
            state_changed = True
        elif self.state == SongState.STARTING:
            if now - self.state_change_time >= self.start_duration:
                self.state = SongState.ONGOING if loud else SongState.INTERMISSION
                self.state_change_time = now
                state_changed = True
            elif not loud and now - self.last_loud_time > self.end_duration:
                self.state = SongState.INTERMISSION
                self.state_change_time = now
                state_changed = True
        elif (
            self.state == SongState.ONGOING
            and not loud
            and now - self.last_loud_time > self.end_duration
        ):
            self.state = SongState.ENDING
            self.state_change_time = now
            state_changed = True
        elif self.state == SongState.ENDING:
            if loud:
                self.state = SongState.STARTING
                self.state_change_time = now
                state_changed = True
            elif now - self.state_change_time >= self.end_duration:
                self.state = SongState.INTERMISSION
                self.state_change_time = now
                state_changed = True

        beat = False
        bpm = 0.0
        if self.tempo(samples):
            beat = True
            self.beat_times.append(now)
            bpm = self._compute_bpm()
            if bpm and now - self.last_print >= self.print_interval:
                print(f"Estimated BPM: {bpm:.2f}", flush=True)
                self.last_print = now

        self.beat_times = [t for t in self.beat_times if now - t <= 60]
        return beat, bpm, state_changed, amplitude

    # ------------------------------------------------------------------
    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print(status, flush=True)
        samples = np.frombuffer(indata, dtype=np.float32)
        self.process(samples, time.time())

    def run(self) -> None:
        """Run beat detection using the default input device."""
        with sd.InputStream(
            channels=1,
            callback=self.audio_callback,
            samplerate=self.samplerate,
            blocksize=512,
        ):
            print("Listening for beats. Press Ctrl+C to stop.")
            try:
                while True:
                    sd.sleep(1000)
            except KeyboardInterrupt:
                print("Stopping")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Detect beats from microphone input"
    )
    parser.add_argument("--samplerate", type=int, default=44100, help="Audio samplerate")
    parser.add_argument(
        "--amplitude-threshold",
        type=float,
        default=0.02,
        help="RMS amplitude threshold for song detection",
    )
    parser.add_argument(
        "--start-duration",
        type=float,
        default=2.0,
        help="Seconds audio must stay loud to mark song start",
    )
    parser.add_argument(
        "--end-duration",
        type=float,
        default=3.0,
        help="Seconds audio must stay quiet to mark song end",
    )
    parser.add_argument(
        "--print-interval",
        type=float,
        default=10.0,
        help="Seconds between BPM summaries",
    )
    args = parser.parse_args()

    detector = BeatDetector(
        samplerate=args.samplerate,
        amplitude_threshold=args.amplitude_threshold,
        start_duration=args.start_duration,
        end_duration=args.end_duration,
        print_interval=args.print_interval,
    )
    detector.run()


if __name__ == "__main__":
    main()
