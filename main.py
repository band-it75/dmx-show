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
import aubio

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
        self.tempo = aubio.tempo("default", 1024, 512, samplerate)
        self.beat_times = []
        self.last_bpm = 0.0
        self.last_genre: parameters.Scenario | None = None
        self.state = "Intermission"
        self.state_change = time.time()
        self.last_loud = 0.0
        self.smoke_on = False
        self.smoke_start = 0.0
        self.last_smoke_time = 0.0
        self.scenario = parameters.SCENARIO_MAP[parameters.Scenario.INTERMISSION]
        self.smoke_gap_ms, self.smoke_duration_ms = parameters.smoke_settings(
            self.scenario
        )
        self.groups: Dict[str, list] = {}
        self.beat_ends: Dict[str, float] = {}

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
            self._apply_update(name, vals)

    def _compute_bpm(self) -> float:
        if len(self.beat_times) < 2:
            return 0.0
        recent = self.beat_times[-8:]
        intervals = np.diff(recent)
        if len(intervals) == 0:
            return 0.0
        return 60.0 / float(np.median(intervals))

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

    def audio_callback(self, indata, frames, time_info, status) -> None:
        if status:
            print(status, flush=True)
        samples = np.frombuffer(indata, dtype=np.float32)
        now = time.time()
        for group, end in list(self.beat_ends.items()):
            if now >= end:
                base = self.scenario.updates.get(group, {})
                if base:
                    self._apply_update(group, base)
                del self.beat_ends[group]
        amp = float(np.sqrt(np.mean(np.square(samples))))
        loud = amp > parameters.AMPLITUDE_THRESHOLD
        if loud:
            self.last_loud = now

        if self.state == "Intermission" and loud:
            self.state = "Starting"
            self.state_change = now
            self._set_scenario(parameters.Scenario.SONG_START)
        elif self.state == "Starting":
            if now - self.state_change >= parameters.START_DURATION:
                self.state = "Ongoing" if loud else "Intermission"
                if self.state == "Intermission":
                    self._set_scenario(parameters.Scenario.INTERMISSION)
            elif not loud and now - self.last_loud > parameters.END_DURATION:
                self.state = "Intermission"
                self._set_scenario(parameters.Scenario.INTERMISSION)
        elif (
            self.state == "Ongoing"
            and not loud
            and now - self.last_loud > parameters.END_DURATION
        ):
            self.state = "Ending"
            self.state_change = now
            self._set_scenario(parameters.Scenario.SONG_ENDING)
        elif self.state == "Ending":
            if loud:
                self.state = "Starting"
                self.state_change = now
                self._set_scenario(parameters.Scenario.SONG_START)
            elif now - self.state_change >= parameters.END_DURATION:
                self.state = "Intermission"
                self._set_scenario(parameters.Scenario.INTERMISSION)


        if self.tempo(samples):
            self.beat_times.append(now)
            bpm = self._compute_bpm()
            if bpm:
                genre = self._detect_genre(bpm)
                if genre != self.last_genre or self.scenario != genre:
                    self.last_genre = genre
                    self._set_scenario(genre)
                if (
                    not self.smoke_on
                    and (now - self.last_smoke_time) * 1000 >= self.smoke_gap_ms
                ):
                    self.smoke.set_channel("fog", 255)
                    self.controller.update()
                    self.smoke_on = True
                    self.smoke_start = now
                    self.last_smoke_time = now
                if self.scenario.beat:
                    for group, vals in self.scenario.beat.items():
                        dur = vals.get("duration", 0) / 1000.0
                        update = {k: v for k, v in vals.items() if k != "duration"}
                        self._apply_update(group, update)
                        self.beat_ends[group] = now + dur

        if self.smoke_on and (now - self.smoke_start) * 1000 >= self.smoke_duration_ms:
            self.smoke.set_channel("fog", 0)
            self.controller.update()
            self.smoke_on = False

        self.beat_times = [t for t in self.beat_times if now - t <= 60]

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
            self.smoke = ctrl.groups.get("Smoke Machine", ctrl.devices[8])
            self._print_state_change(self.scenario.updates)
            print("Listening for beats. Press Ctrl+C to stop.")
            try:
                while True:
                    sd.sleep(1000)
            except KeyboardInterrupt:
                print("Stopping")


def main() -> None:
    show = BeatDMXShow()
    show.run()


if __name__ == "__main__":
    main()
