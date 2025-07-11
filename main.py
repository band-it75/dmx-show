from __future__ import annotations

"""Beat-driven DMX show controller.

LumiPar 12UAW5 units double as house lights. Overhead effects pulse with BPM.
Smoke bursts last 3 seconds with a 30-second gap. Genre-specific colors guide
intensity and timing. The moving head stays on the artist during songs and
points at the audience to end each song. Stage lights fade to black during
songs and return when the moving head faces the audience.
"""

import sys
import time
from pathlib import Path
from typing import Dict

import numpy as np
import sounddevice as sd

from src.audio.beat_detection import BeatDetector, SongState

import parameters
from parameters import Scenario

# Ensure src is on the Python path so we can import the DMX modules
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dmx.dmx import DMX


class BeatDMXShow:
    def __init__(self, samplerate: int = parameters.SAMPLERATE) -> None:
        self.samplerate = samplerate
        self.detector = BeatDetector(
            samplerate=samplerate,
            amplitude_threshold=parameters.AMPLITUDE_THRESHOLD,
            start_duration=parameters.START_DURATION,
            end_duration=parameters.END_DURATION,
            print_interval=parameters.PRINT_INTERVAL,
        )
        self.last_genre: Scenario | None = None
        self.current_state: SongState = self.detector.state
        self.smoke_on = False
        self.smoke_start = 0.0
        self.last_smoke_time = 0.0
        self.scenario = parameters.SCENARIO_MAP[Scenario.INTERMISSION]
        self.smoke_gap_ms, self.smoke_duration_ms = parameters.smoke_settings(
            self.scenario
        )
        self.groups: Dict[str, list] = {}
        self.beat_ends: Dict[str, float] = {}
        self._beat_line: str | None = None

    def _flush_beat_line(self) -> None:
        if self._beat_line is not None:
            print()
            self._beat_line = None

    def _apply_update(self, group: str, values: Dict[str, int]) -> None:
        fixtures = self.groups.get(group, [])
        for fx in fixtures:
            pan = values.get("pan")
            tilt = values.get("tilt")
            if pan is not None or tilt is not None:
                try:
                    fx.set_pan_tilt(pan or 0, tilt or 0)
                except KeyError:
                    pass
            for ch, val in values.items():
                if ch in {"pan", "tilt"}:
                    continue
                try:
                    fx.set_channel(ch, val)
                except KeyError:
                    pass
        self.controller.update()

    def _print_state_change(self, updates: Dict[str, Dict[str, int]]) -> None:
        for name, vals in updates.items():
            self._flush_beat_line()
            print(f"DMX update for {name}: {vals}", flush=True)
            self._apply_update(name, vals)


    def _set_scenario(self, name: parameters.Scenario) -> None:
        scn = parameters.SCENARIO_MAP.get(name)
        if scn is None:
            return
        current = self.scenario
        if (
            name != current
            and (current not in name.predecessors or name not in current.successors)
        ):
            return
        if scn != self.scenario:
            self._flush_beat_line()
            print(f"Scenario changed to {scn.value}", flush=True)
        self.scenario = scn
        self.smoke_gap_ms, self.smoke_duration_ms = parameters.smoke_settings(
            scn
        )
        self.beat_ends.clear()
        updates = dict(scn.updates)
        updates.pop("Smoke Machine", None)
        self._print_state_change(updates)

    @staticmethod
    def _detect_genre(bpm: float) -> parameters.Scenario:
        """Return scenario for this BPM using ``parameters`` ranges."""
        return parameters.scenario_for_bpm(bpm)

    def _handle_state_change(self, state: SongState) -> None:
        self._flush_beat_line()
        print(f"Song state changed to {state.value}", flush=True)
        mapping = {
            SongState.INTERMISSION: Scenario.INTERMISSION,
            SongState.STARTING: Scenario.SONG_START,
            SongState.ONGOING: self.last_genre or Scenario.SONG_START,
            SongState.ENDING: Scenario.SONG_ENDING,
        }
        self._set_scenario(mapping.get(state, Scenario.INTERMISSION))
        self.current_state = state

    def _handle_beat(self, bpm: float, now: float) -> None:
        if bpm:
            genre = self._detect_genre(bpm)
            line = f"Beat at {bpm:.2f} BPM - genre {genre.value}"
            pad = "" if self._beat_line is None else " " * max(0, len(self._beat_line) - len(line))
            if line != self._beat_line:
                prefix = "\r" if self._beat_line is not None else ""
                print(prefix + line + pad, end="", flush=True)
                self._beat_line = line
            if genre != self.last_genre or self.scenario != genre:
                self.last_genre = genre
                if self.current_state == SongState.ONGOING:
                    self._set_scenario(genre)

            if (
                not self.smoke_on
                and (now - self.last_smoke_time) * 1000 >= self.smoke_gap_ms
            ):
                self._flush_beat_line()
                print("Smoke on", flush=True)
                self.smoke.set_channel("fog", 255)
                self.controller.update()
                self.smoke_on = True
                self.smoke_start = now
                self.last_smoke_time = now

            if self.scenario.beat:
                for group, vals in self.scenario.beat.items():
                    dur = vals.get("duration", 0) / 1000.0
                    update = {k: v for k, v in vals.items() if k != "duration"}
                    self._flush_beat_line()
                    print(f"Beat update {group}: {update}", flush=True)
                    self._apply_update(group, update)
                    self.beat_ends[group] = now + dur

    def _tick(self, now: float) -> None:
        if self.smoke_on and (now - self.smoke_start) * 1000 >= self.smoke_duration_ms:
            self._flush_beat_line()
            print("Smoke off", flush=True)
            self.smoke.set_channel("fog", 0)
            self.controller.update()
            self.smoke_on = False

    def audio_callback(self, indata, frames, time_info, status) -> None:
        if status:
            self._flush_beat_line()
            print(status, flush=True)
        samples = np.frombuffer(indata, dtype=np.float32)
        now = time.time()

        beat, bpm, state_changed = self.detector.process(samples, now)

        for group, end in list(self.beat_ends.items()):
            if now >= end:
                base = self.scenario.updates.get(group, {})
                if base:
                    self._flush_beat_line()
                    print(f"Restore {group}: {base}", flush=True)
                    self._apply_update(group, base)
                del self.beat_ends[group]

        if state_changed:
            self._handle_state_change(self.detector.state)

        if beat:
            self._handle_beat(bpm, now)

        self._tick(now)

    def run(self) -> None:
        devices = parameters.DEVICES
        with DMX(devices, port=parameters.COM_PORT) as ctrl, sd.InputStream(
            channels=1,
            callback=self.audio_callback,
            samplerate=self.samplerate,
            blocksize=512,
        ):
            self.controller = ctrl
            self.groups = ctrl.groups
            smoke_group = ctrl.groups.get("Smoke Machine")
            self.smoke = smoke_group[0] if smoke_group else ctrl.devices[8]
            self._flush_beat_line()
            print(f"Initial scenario {self.scenario.value}", flush=True)
            self._print_state_change(self.scenario.updates)
            self._flush_beat_line()
            print("Listening for beats. Press Ctrl+C to stop.")
            try:
                while True:
                    sd.sleep(1000)
            except KeyboardInterrupt:
                self._flush_beat_line()
                print("Stopping")


def main() -> None:
    show = BeatDMXShow()
    show.run()


if __name__ == "__main__":
    main()
