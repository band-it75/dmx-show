"""Audio analysis utilities to detect beats and basic song state."""

from __future__ import annotations

import time
from enum import Enum
from typing import Tuple

import numpy as np
import sounddevice as sd
import aubio
import librosa
from .debounce import DebouncedFlag
from parameters import Scenario


class SongState(Enum):
    """Simple states derived from audio volume."""

    INTERMISSION = "Intermission"
    STARTING = "Starting"
    ONGOING = "Ongoing"
    ENDING = "Ending"



_SCENARIO_TO_STATE = {
    Scenario.INTERMISSION: SongState.INTERMISSION,
    Scenario.SONG_START: SongState.STARTING,
    Scenario.SONG_ENDING: SongState.ENDING,
    Scenario.SONG_ONGOING_SLOW: SongState.ONGOING,
    Scenario.SONG_ONGOING_JAZZ: SongState.ONGOING,
    Scenario.SONG_ONGOING_POP: SongState.ONGOING,
    Scenario.SONG_ONGOING_ROCK: SongState.ONGOING,
    Scenario.SONG_ONGOING_METAL: SongState.ONGOING,
}


def _compute_allowed_transitions() -> dict[SongState, set[SongState]]:
    mapping = {s: set() for s in SongState}
    for scn in Scenario:
        state_from = _SCENARIO_TO_STATE.get(scn)
        for succ in scn.successors:
            state_to = _SCENARIO_TO_STATE.get(succ)
            if state_from is not None and state_to is not None:
                mapping[state_from].add(state_to)
    return mapping


ALLOWED_STATE_TRANSITIONS = _compute_allowed_transitions()


class BeatDetector:
    """Detect beats and estimate song state purely from audio."""

    def __init__(
        self,
        samplerate: int = 44100,
        amplitude_threshold: float = 0.02,
        start_duration: float = 2.0,
        end_duration: float = 3.0,
        print_interval: float = 10.0,
        chorus_debounce: float = 0.5,
        crescendo_debounce: float = 0.5,
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
        self.chorus_flag = DebouncedFlag(chorus_debounce)
        self.crescendo_flag = DebouncedFlag(crescendo_debounce)


    def _set_state(self, new_state: SongState, now: float) -> bool:
        """Set ``self.state`` if transition is allowed."""
        if new_state == self.state:
            return False
        allowed = ALLOWED_STATE_TRANSITIONS.get(self.state, set())
        if new_state not in allowed:
            print(
                f"Blocked illegal state transition: {self.state} -> {new_state}",
                flush=True,
            )
            return False
        self.state = new_state
        self.state_change_time = now
        return True

    # ------------------------------------------------------------------
    def _compute_bpm(self) -> float:
        if len(self.beat_times) < 4:
            return 0.0
        recent = self.beat_times[-8:]
        intervals = np.diff(recent)
        if len(intervals) == 0:
            return 0.0
        median = float(np.median(intervals))
        if median <= 0:
            return 0.0
        bpm = 60.0 / median
        if bpm > 120:
            if np.std(intervals) > median * 0.2 or self.last_amplitude < 0.1:
                bpm /= 2.0
        return bpm

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
        n_fft = min(1024, len(samples))
        rms = float(
            librosa.feature.rms(
                y=samples, frame_length=n_fft, hop_length=n_fft // 2
            ).mean()
        )
        flatness = float(
            librosa.feature.spectral_flatness(y=samples, n_fft=n_fft).mean()
        )
        chorus_raw = rms > 0.1 and flatness < 0.2
        crescendo_raw = rms > self.previous_rms * 1.1
        self.is_chorus = self.chorus_flag.update(chorus_raw, now)
        self.is_crescendo = self.crescendo_flag.update(crescendo_raw, now)
        self.previous_rms = rms

        S = librosa.stft(samples, n_fft=n_fft, hop_length=n_fft // 2)
        y_harm, y_perc = librosa.decompose.hpss(S)
        perc_energy = float(np.sum(np.abs(y_perc) ** 2))
        harm_energy = float(np.sum(np.abs(y_harm) ** 2))
        self.is_drum_solo = perc_energy > 3 * harm_energy

        # Transient detection for snare/kick hits
        self.snare_hit = False
        self.kick_hit = False
        if self.onset(samples):
            centroid = float(
                librosa.feature.spectral_centroid(
                    y=samples, sr=self.samplerate, n_fft=n_fft
                ).mean()
            )
            if centroid > 4000:
                self.snare_hit = True
            elif centroid < 500:
                self.kick_hit = True

        # song state machine
        if self.state == SongState.INTERMISSION and loud:
            state_changed |= self._set_state(SongState.STARTING, now)
        elif self.state == SongState.STARTING:
            if loud:
                if now - self.state_change_time >= self.start_duration:
                    state_changed |= self._set_state(SongState.ONGOING, now)
            elif now - self.last_loud_time > self.end_duration:
                # remain in STARTING; do not revert to Intermission
                self.state_change_time = now
        elif (
            self.state == SongState.ONGOING
            and not loud
            and now - self.last_loud_time > self.end_duration
        ):
            state_changed |= self._set_state(SongState.ENDING, now)
        elif self.state == SongState.ENDING:
            if loud:
                state_changed |= self._set_state(SongState.STARTING, now)
            elif now - self.state_change_time >= self.end_duration:
                state_changed |= self._set_state(SongState.INTERMISSION, now)

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
