from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Dict

import numpy as np
import sounddevice as sd

from src.audio import BeatDetector, SongState, GenreClassifier

import parameters
from parameters import Scenario

# Ensure src is on the Python path so we can import the DMX modules
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dmx.dmx import DMX


class Dashboard:
    """Simple console dashboard that refreshes on state changes."""

    def __init__(self) -> None:
        self.genre = ""
        self.song_state = ""
        self.bpm = 0.0
        self.vu = 0.0
        self.min_vu = float('inf')
        self.max_vu = 0.0
        self.smoke = False
        self.status = ""
        self.chorus = False
        self.drum_solo = False
        self.crescendo = False
        self.snare = False
        self.kick = False
        self.groups: Dict[str, Dict[str, int]] = {}
        self._last_out = ""

    def set_genre(self, name: str) -> None:
        self.genre = name
        self._render()

    def set_state(self, state: str) -> None:
        self.song_state = state
        self._render()

    def set_bpm(self, bpm: float) -> None:
        self.bpm = bpm
        self._render()

    def set_vu(self, vu: float) -> None:
        self.vu = vu
        if vu < self.min_vu:
            self.min_vu = vu
        if vu > self.max_vu:
            self.max_vu = vu
        self._render()

    def set_smoke(self, on: bool) -> None:
        self.smoke = on
        self._render()

    def set_group(self, group: str, values: Dict[str, int]) -> None:
        self.groups[group] = values
        self._render()

    def set_status(self, status: str) -> None:
        self.status = status
        self._render()

    def set_chorus(self, value: bool) -> None:
        self.chorus = value
        self._render()

    def set_drum_solo(self, value: bool) -> None:
        self.drum_solo = value
        self._render()

    def set_crescendo(self, value: bool) -> None:
        self.crescendo = value
        self._render()

    def set_snare(self, value: bool) -> None:
        self.snare = value
        self._render()

    def set_kick(self, value: bool) -> None:
        self.kick = value
        self._render()

    def _render(self) -> None:
        lines = [
            f"Genre: {self.genre}",
            f"State: {self.song_state}",
            f"BPM: {self.bpm:.2f}",
            f"VU: {self.vu:.3f} (Min: {self.min_vu:.3f} Max: {self.max_vu:.3f})",
            f"Smoke: {'On' if self.smoke else 'Off'}",
            f"Chorus: {'Yes' if self.chorus else 'No'}",
            f"Drum Solo: {'Yes' if self.drum_solo else 'No'}",
            f"Crescendo: {'Yes' if self.crescendo else 'No'}",
            f"Snare: {'Hit' if self.snare else 'No'}",
            f"Kick: {'Hit' if self.kick else 'No'}",
            f"Status: {self.status}",
            "",
            "Groups:",
        ]
        for name, vals in self.groups.items():
            lines.append(f"  {name}: {vals}")
        out = "\n".join(lines)
        if out != self._last_out:
            print("\033[H\033[J" + out, end="", flush=True)
            self._last_out = out


class BeatDMXShow:
    def __init__(self, samplerate: int = parameters.SAMPLERATE,
                 dashboard: bool = parameters.SHOW_DASHBOARD,
                 log_path: str = "vu_dimmer.log",
                 genre_model: GenreClassifier | None = None) -> None:
        self.samplerate = samplerate
        self.dashboard_enabled = dashboard
        self.dashboard = Dashboard() if dashboard else None
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
        self.last_vu_dimmer = -1
        self.current_vu = 0.0
        self.log_file = None
        self.log_path = log_path
        self.genre_classifier = genre_model or GenreClassifier()
        self.audio_buffer: list[np.ndarray] = []
        self.classifying = False
        self.genre_label = ""

    @staticmethod
    def _genre_label(scn: Scenario | None) -> str:
        if scn and " - " in scn.value:
            return scn.value.split(" - ", 1)[1]
        return ""

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
            if self.dashboard_enabled:
                self.dashboard.set_group(name, vals)
            else:
                print(f"DMX update for {name}: {vals}", flush=True)
            self._apply_update(name, vals)


    def _set_scenario(self, name: parameters.Scenario, force: bool = False) -> None:
        scn = parameters.SCENARIO_MAP.get(name)
        if scn is None:
            return
        current = self.scenario
        if (
            not force
            and name != current
            and (current not in name.predecessors or name not in current.successors)
        ):
            return
        if scn != self.scenario:
            self._flush_beat_line()
            if not self.dashboard_enabled:
                print(f"Genre changed to {scn.value}", flush=True)
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

    def _start_genre_classification(self) -> None:
        if self.classifying or not self.audio_buffer:
            return
        samples = np.concatenate(self.audio_buffer)
        self.audio_buffer.clear()
        self.classifying = True

        def work() -> None:
            try:
                label = self.genre_classifier.classify(samples, self.samplerate)
                scenario = self._scenario_from_label(label)
                self.genre_label = label
                self.last_genre = scenario
                if self.current_state == SongState.ONGOING:
                    self._set_scenario(scenario)
                if self.dashboard_enabled:
                    self.dashboard.set_genre(label)
            except Exception as exc:  # pragma: no cover - model errors
                if not self.dashboard_enabled:
                    print(f"Genre classification error: {exc}", flush=True)
            finally:
                self.classifying = False

        import threading

        threading.Thread(target=work, daemon=True).start()

    @staticmethod
    def _scenario_from_label(label: str) -> Scenario:
        """Map model label to a show scenario."""
        lbl = label.lower()
        if "rock" in lbl:
            return Scenario.SONG_ONGOING_ROCK
        if "metal" in lbl:
            return Scenario.SONG_ONGOING_METAL
        if "jazz" in lbl:
            return Scenario.SONG_ONGOING_JAZZ
        if "pop" in lbl or "disco" in lbl:
            return Scenario.SONG_ONGOING_POP
        if lbl in {"blues", "country", "reggae", "classical", "hip hop", "hip-hop"}:
            return Scenario.SONG_ONGOING_SLOW
        return Scenario.SONG_ONGOING_SLOW

    def _handle_state_change(self, state: SongState) -> None:
        self._flush_beat_line()
        if self.dashboard_enabled:
            self.dashboard.set_state(state.value)
            genre = "" if state == SongState.INTERMISSION else self._genre_label(self.last_genre)
            self.dashboard.set_genre(genre)
        else:
            print(f"State changed to {state.value}", flush=True)
        mapping = {
            SongState.INTERMISSION: Scenario.INTERMISSION,
            SongState.STARTING: Scenario.SONG_START,
            SongState.ONGOING: Scenario.SONG_START,
            SongState.ENDING: Scenario.SONG_ENDING,
        }
        self._set_scenario(mapping.get(state, Scenario.INTERMISSION))
        if state == SongState.STARTING:
            self.audio_buffer.clear()
        elif state == SongState.ONGOING:
            self._start_genre_classification()
        self.current_state = state

    def _handle_beat(self, bpm: float, now: float) -> None:
        if bpm:
            genre = self.last_genre or self._detect_genre(bpm)
            line = f"Beat at {bpm:.2f} BPM - genre {genre.value}"
            if self.dashboard_enabled:
                self.dashboard.set_bpm(bpm)
            else:
                pad = "" if self._beat_line is None else " " * max(0, len(self._beat_line) - len(line))
                if line != self._beat_line:
                    prefix = "\r" if self._beat_line is not None else ""
                    print(prefix + line + pad, end="", flush=True)
                    self._beat_line = line
            if self.last_genre is None and self.scenario != genre:
                if self.current_state == SongState.ONGOING:
                    self._set_scenario(genre)
                if self.dashboard_enabled and self.current_state != SongState.INTERMISSION:
                    self.dashboard.set_genre(self._genre_label(genre))

            if (
                not self.smoke_on
                and self.smoke is not None
                and (now - self.last_smoke_time) * 1000 >= self.smoke_gap_ms
            ):
                self._flush_beat_line()
                if self.dashboard_enabled:
                    self.dashboard.set_smoke(True)
                else:
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
                    if self.dashboard_enabled:
                        self.dashboard.set_group(group, update)
                    else:
                        print(f"Beat update {group}: {update}", flush=True)
                    self._apply_update(group, update)
                    self.beat_ends[group] = now + dur

    def _tick(self, now: float) -> None:
        if (
            self.smoke_on
            and self.smoke is not None
            and (now - self.smoke_start) * 1000 >= self.smoke_duration_ms
        ):
            self._flush_beat_line()
            if self.dashboard_enabled:
                self.dashboard.set_smoke(False)
            else:
                print("Smoke off", flush=True)
            self.smoke.set_channel("fog", 0)
            self.controller.update()
            self.smoke_on = False

    def _update_overhead_from_vu(self, _ctrl: DMX) -> None:
        """Set Overhead Effects dimmer based on the latest VU reading."""
        level = int(min(1.0, self.current_vu / parameters.VU_FULL) * 255)
        if self.log_file:
            self.log_file.write(
                f"{time.time():.3f} VU:{self.current_vu:.3f} dimmer:{level}\n"
            )
            self.log_file.flush()
        if level != self.last_vu_dimmer:
            self._apply_update("Overhead Effects", {"dimmer": level})
            self.last_vu_dimmer = level

    def audio_callback(self, indata, frames, time_info, status) -> None:
        if status:
            self._flush_beat_line()
            print(status, flush=True)
        samples = np.frombuffer(indata, dtype=np.float32)
        now = time.time()

        beat, bpm, state_changed, vu = self.detector.process(samples, now)

        if self.detector.state == SongState.STARTING:
            self.audio_buffer.append(samples.copy())
        elif self.detector.state == SongState.ONGOING and not self.classifying and self.last_genre is None:
            self.audio_buffer.append(samples.copy())
            total = sum(len(buf) for buf in self.audio_buffer)
            if total >= self.samplerate * 5:
                self._start_genre_classification()

        if self.dashboard_enabled:
            self.dashboard.set_chorus(self.detector.is_chorus)
            self.dashboard.set_drum_solo(self.detector.is_drum_solo)
            self.dashboard.set_crescendo(self.detector.is_crescendo)
            self.dashboard.set_snare(self.detector.snare_hit)
            self.dashboard.set_kick(self.detector.kick_hit)

        if self.detector.snare_hit:
            update = {"dimmer": 255}
            self._flush_beat_line()
            if self.dashboard_enabled:
                self.dashboard.set_group("Overhead Effects", update)
            else:
                print(f"Snare flash: {update}", flush=True)
            self._apply_update("Overhead Effects", update)
            self.beat_ends["Overhead Effects"] = max(
                self.beat_ends.get("Overhead Effects", 0.0), now + 0.1
            )

        for group, end in list(self.beat_ends.items()):
            if now >= end:
                base = self.scenario.updates.get(group, {})
                if base:
                    self._flush_beat_line()
                    if self.dashboard_enabled:
                        self.dashboard.set_group(group, base)
                    else:
                        print(f"Restore {group}: {base}", flush=True)
                    self._apply_update(group, base)
                del self.beat_ends[group]

        if state_changed:
            self._handle_state_change(self.detector.state)

        if beat:
            self._handle_beat(bpm, now)

        self._tick(now)

        self.current_vu = vu
        if self.dashboard_enabled:
            self.dashboard.set_vu(vu)

    def run(self) -> None:
        devices = parameters.DEVICES
        with open(self.log_path, "a") as log, \
            DMX(
                devices,
                port=parameters.COM_PORT,
                fps=parameters.DMX_FPS,
                pre_send=self._update_overhead_from_vu,
            ) as ctrl, sd.InputStream(
                channels=1,
                callback=self.audio_callback,
                samplerate=self.samplerate,
                blocksize=512,
            ):
            self.log_file = log
            self.controller = ctrl
            self.groups = ctrl.groups
            smoke_group = ctrl.groups.get("Smoke Machine")
            self.smoke = smoke_group[0] if smoke_group else None
            if self.dashboard_enabled:
                if ctrl.serial.error:
                    self.dashboard.set_status(f"DMX Error, {ctrl.serial.error}")
                else:
                    self.dashboard.set_status("DMX OK")
            elif ctrl.serial.error:
                print(f"Status: DMX Error, {ctrl.serial.error}", flush=True)
            self._flush_beat_line()
            if self.dashboard_enabled:
                self.dashboard.set_state(self.current_state.value)
                genre = "" if self.current_state == SongState.INTERMISSION else self._genre_label(self.last_genre)
                self.dashboard.set_genre(genre)
            else:
                init_genre = self._genre_label(self.last_genre) if self.current_state != SongState.INTERMISSION else ""
                print(f"Initial genre {init_genre}", flush=True)
            self._print_state_change(self.scenario.updates)
            self._flush_beat_line()
            if not self.dashboard_enabled:
                print("Listening for beats. Press Ctrl+C to stop.")
            try:
                while True:
                    sd.sleep(1000)
            except KeyboardInterrupt:
                self._flush_beat_line()
                if not self.dashboard_enabled:
                    print("Stopping")
        self.log_file = None


def main() -> None:
    show = BeatDMXShow()
    show.run()


if __name__ == "__main__":
    main()
