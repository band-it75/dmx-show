from __future__ import annotations

import sys
import time
import os
import json
import logging
import log as log_config

logger = logging.getLogger("AI")
import traceback
from collections import deque
from pathlib import Path
from typing import Dict
import threading
import queue

import numpy as np
import math

try:
    import sounddevice as sd
except Exception:  # pragma: no cover - optional dependency for tests
    sd = None

from src.audio.beat_detection import SongState
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.audio.genre_classifier import GenreClassifier

_GENRE_SENTINEL = object()

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
        self.min_vu = float("inf")
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
    def __init__(
        self,
        samplerate: int = parameters.SAMPLERATE,
        dashboard: bool = parameters.SHOW_DASHBOARD,
        log_path: str = "vu_dimmer.log",
        *,
        ai_log_path: str = "ai.log",
        debug_log_path: str | None = None,
        genre_model: GenreClassifier | None | object = _GENRE_SENTINEL,
    ) -> None:
        self.samplerate = samplerate
        self.dashboard_enabled = dashboard
        self.dashboard = Dashboard() if dashboard else None
        self.detector = None
        self.persisted_state: Dict[str, object] = {}
        try:
            with open("ai_state.json") as fh:
                self.persisted_state = json.load(fh)
        except Exception:
            self.persisted_state = {}
        self.last_genre: Scenario | None = None
        self.persisted_state.pop("last_genre", None)
        self.current_state = SongState.INTERMISSION
        self.song_id = 0
        self.smoke_on = False
        self.smoke_start = 0.0
        self.last_smoke_time = 0.0
        self.scenario = parameters.SCENARIO_MAP[Scenario.INTERMISSION]
        self.last_bpm = 0.0
        self.smoke_gap_ms, self.smoke_duration_ms = parameters.smoke_settings(self.scenario)
        self.groups: Dict[str, list] = {}
        self.beat_ends: Dict[str, float] = {}
        self._beat_line: str | None = None
        self.last_vu_dimmer = -1
        self.smoothed_vu_dimmer = 0.0
        self.current_vu = 0.0
        self.log_file = None
        self.log_path = log_path
        self.ai_log_path = ai_log_path
        self.ai_log_handle = open(self.ai_log_path, "a")
        self.debug_log_path = debug_log_path or str(log_config.LOG_DIR / "debug.log")
        self.debug_log_handle = open(self.debug_log_path, "a")
        if genre_model is _GENRE_SENTINEL:
            from src.audio import GenreClassifier as GC

            self.genre_classifier = GC(verbose=True, log_file=self.ai_log_handle)
        else:
            self.genre_classifier = genre_model
        if self.genre_classifier is None:
            logger.info("Genre classifier disabled")
        else:
            logger.info("AI logging started")
        self.pre_song_buffer = deque(maxlen=int(5 * self.samplerate))
        self.buffering = False
        self.buffer_start_time = 0.0
        self.classify_after: float | None = None
        self.classifying = False
        self.last_genre_check = 0.0
        self.genre_label = ""
        self.audio_queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=20)
        self.running = False

    def __del__(self) -> None:  # pragma: no cover - cleanup
        if hasattr(self, "debug_log_handle") and self.debug_log_handle:
            try:
                self.debug_log_handle.close()
            except Exception:
                pass
        if hasattr(self, "ai_log_handle") and self.ai_log_handle:
            try:
                self.ai_log_handle.close()
            except Exception:
                pass

    @staticmethod
    def _genre_label(scn: Scenario | None) -> str:
        if scn and " - " in scn.value:
            return scn.value.split(" - ", 1)[1]
        return ""

    def _flush_beat_line(self) -> None:
        if self._beat_line is not None:
            print()
            self._beat_line = None

    def _ai_log(self, msg: str) -> None:
        logger.info(msg)
        if hasattr(self, "ai_log_handle") and self.ai_log_handle:
            self.ai_log_handle.write(msg + "\n")
            self.ai_log_handle.flush()

    def _debug_log(self, msg: str) -> None:
        if hasattr(self, "debug_log_handle") and self.debug_log_handle:
            self.debug_log_handle.write(msg + "\n")
            self.debug_log_handle.flush()

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
            self._debug_log(f"DMX update for {name}: {vals}")
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
            and scn != current
            and (current not in scn.predecessors or scn not in current.successors)
        ):
            return
        if scn != self.scenario:
            self._flush_beat_line()
            if not self.dashboard_enabled:
                print(f"Genre changed to {scn.value}", flush=True)
            logger.info("SCENARIO apply     %s", scn)
        self.scenario = scn
        self.smoke_gap_ms, self.smoke_duration_ms = parameters.smoke_settings(scn)
        self.beat_ends.clear()
        if self.controller:
            self.controller.reset()
        updates = dict(scn.updates)
        updates.pop("Smoke Machine", None)
        self._print_state_change(updates)

    def _start_genre_classification(self) -> None:
        self._launch_genre_classifier_immediately()

    def _run_genre_classifier(
        self, samples: np.ndarray, sr: int, song_id: int
    ) -> None:
        start_t = time.perf_counter()
        logger.info("THREAD start — calling model...")
        logger.info("THREAD start       song_id=%s", song_id)
        try:
            label = self.genre_classifier.classify(samples, sr)
            logger.info("THREAD got label: %s", label)
            scenario = self._scenario_from_label(label)
            self._ai_log(f"Genre classified as '{label}' -> Scenario: {scenario.name}")
            logger.info(
                "THREAD prediction  song_id=%s  label=%s  elapsed=%.2fs",
                song_id,
                label,
                time.perf_counter() - start_t,
            )
            if song_id == self.song_id:
                self.genre_label = label
                if label == "":
                    logger.info("THREAD empty label, scheduling retry")
                    self.classify_after = time.time() + 5.0
                    if self.dashboard_enabled:
                        self.dashboard.set_genre("(retry)")
                else:
                    self.last_genre = scenario
                    if self.current_state == SongState.STARTING:
                        self._handle_state_change(SongState.ONGOING)
                        self._set_scenario(scenario)
                    elif self.current_state == SongState.ONGOING:
                        self._set_scenario(scenario)
                    if self.dashboard_enabled:
                        self.dashboard.set_genre(label)
        except Exception as exc:  # pragma: no cover - model errors
            if self.dashboard_enabled:
                self.dashboard.set_genre("(error)")
            logger.exception("THREAD EXCEPTION:")
        finally:
            if song_id == self.song_id:
                self.classifying = False
                if self.last_genre is None:
                    self.classify_after = time.time() + 5.0
            logger.info(
                "THREAD finish      song_id=%s  elapsed=%.2fs",
                song_id,
                time.perf_counter() - start_t,
            )
            logger.info("THREAD finished.")

    def _launch_genre_classifier_immediately(self) -> None:
        logger.info("Attempting _launch_genre_classifier_immediately()")
        if not self.pre_song_buffer:
            logger.warning("SKIP: Buffer empty.")
        if self.classifying:
            logger.warning("SKIP: Already classifying.")
        if self.last_genre is not None:
            logger.warning("SKIP: Genre already set: %s", self.last_genre)
        if self.genre_classifier is None:
            logger.warning("SKIP   classification: classifier disabled")
            return
        if self.classifying:
            logger.warning("SKIP   classification: already running")
            return
        samples = np.array(self.pre_song_buffer, dtype=np.float32)
        if samples.size == 0:
            logger.warning("SKIP   classification: buffer empty")
            return
        self.classifying = True
        self.last_genre_check = time.time()
        sid = self.song_id
        logger.info(
            "LAUNCH classifier thread, %d samples in buffer",
            len(self.pre_song_buffer),
        )
        logger.info(
            "LAUNCH classifier  song_id=%s  frames=%d  secs=%.2f",
            sid,
            samples.shape[0],
            samples.shape[0] / self.samplerate,
        )
        th = threading.Thread(
            target=self._run_genre_classifier,
            args=(samples, self.samplerate, sid),
            daemon=True,
        )
        th.start()

    @staticmethod
    def _scenario_from_label(label: str) -> Scenario:
        """Map model label to a show scenario."""
        lbl = label.lower().strip()
        lbl = parameters.GENRE_ID_MAP.get(lbl, lbl)
        if "rock" in lbl:
            return Scenario.SONG_ONGOING_ROCK
        if "metal" in lbl:
            return Scenario.SONG_ONGOING_METAL
        if "jazz" in lbl:
            return Scenario.SONG_ONGOING_JAZZ
        if "pop" in lbl:
            return Scenario.SONG_ONGOING_POP
        if "disco" in lbl:
            return Scenario.SONG_ONGOING_DISCO
        if "reggae" in lbl:
            return Scenario.SONG_ONGOING_REGGAE
        if "blues" in lbl:
            return Scenario.SONG_ONGOING_BLUES
        if "classical" in lbl:
            return Scenario.SONG_ONGOING_CLASSICAL
        if "country" in lbl:
            return Scenario.SONG_ONGOING_COUNTRY
        if any(x in lbl for x in ["hip hop", "hip-hop", "hiphop"]):
            return Scenario.SONG_ONGOING_HIPHOP
        return Scenario.SONG_ONGOING_SLOW

    def _handle_state_change(self, state: SongState) -> None:
        prev_state = self.current_state
        if state == SongState.ONGOING and self.last_genre is None:
            logger.debug("Ignore Ongoing transition until genre classified")
            return

        self._flush_beat_line()
        if self.dashboard_enabled:
            self.dashboard.set_state(state.value)
            genre = "" if state == SongState.INTERMISSION else self._genre_label(self.last_genre)
            self.dashboard.set_genre(genre)
        else:
            logger.info("State changed to %s", state.value)
        self._debug_log(f"State changed to {state.value}")
        logger.info(
            "STATE change %s -> %s  | last_genre=%s  classifying=%s",
            prev_state,
            state,
            self.last_genre,
            self.classifying,
        )
        mapping = {
            SongState.INTERMISSION: Scenario.INTERMISSION,
            SongState.STARTING: Scenario.SONG_START,
            SongState.ONGOING: Scenario.SONG_START,
            SongState.ENDING: Scenario.SONG_ENDING,
        }
        self._set_scenario(mapping.get(state, Scenario.INTERMISSION))
        if state == SongState.STARTING:
            self.song_id += 1
            self.last_genre = None
            self.genre_label = ""
            self.classifying = False
            self.buffering = True
            self.buffer_start_time = time.time()
            self.classify_after = time.time() + 5.0
            self.pre_song_buffer.clear()
            self._ai_log("Scheduled genre classification in 5s.")
        elif state == SongState.ONGOING:
            if self.last_genre is None:
                # remain in STARTING until genre detected
                return
            self.buffering = True
            self.buffer_start_time = time.time()
        elif state == SongState.ENDING:
            self.buffering = False
            self.classify_after = None
        else:
            self.buffering = False
            self.classify_after = None
        self.current_state = state

    def _handle_beat(self, bpm: float, now: float) -> None:
        if bpm:
            self.last_bpm = bpm
            label = self._genre_label(self.last_genre)
            line = f"Beat at {bpm:.2f} BPM" + (f" - genre {label}" if label else "")
            if self.dashboard_enabled:
                self.dashboard.set_bpm(bpm)
            else:
                pad = (
                    ""
                    if self._beat_line is None
                    else " " * max(0, len(self._beat_line) - len(line))
                )
                if line != self._beat_line:
                    prefix = "\r" if self._beat_line is not None else ""
                    print(prefix + line + pad, end="", flush=True)
                    self._beat_line = line
            self._debug_log(line)

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
                self._debug_log("Smoke on")
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
            self._debug_log("Smoke off")
            self.smoke.set_channel("fog", 0)
            self.controller.update()
            self.smoke_on = False

    @staticmethod
    def _vu_to_level(vu: float) -> int:
        """Return a dimmer level that rises with VU above a baseline."""
        base = 25
        peak = 175
        if vu <= parameters.VU_PULSE_THRESHOLD:
            return base
        top = parameters.VU_FULL - parameters.VU_PULSE_THRESHOLD
        ratio = max(0.0, min(1.0, (vu - parameters.VU_PULSE_THRESHOLD) / top))
        level = base + ratio * (peak - base)
        return min(peak, int(level))

    def _update_overhead_from_vu(self, _ctrl: DMX) -> None:
        """Set Overhead Effects dimmer based on the latest VU reading."""
        now = time.time()
        end = self.beat_ends.get("Overhead Effects", 0.0)
        if now < end:
            return

        level = self._vu_to_level(self.current_vu)
        smooth = parameters.VU_SMOOTHING
        self.smoothed_vu_dimmer = self.smoothed_vu_dimmer * smooth + level * (1 - smooth)
        final_level = int(self.smoothed_vu_dimmer)
        if self.log_file:
            self.log_file.write(
                f"{now:.3f} VU:{self.current_vu:.3f} dimmer:{final_level}\n"
            )
            self.log_file.flush()
        if final_level != self.last_vu_dimmer:
            self._apply_update("Overhead Effects", {"dimmer": final_level})
            self._debug_log(f"VU dimmer: {final_level}")
            self.last_vu_dimmer = final_level


    def _process_samples(self, samples: np.ndarray) -> None:
        now = time.time()
        beat, bpm, state_changed, vu = self.detector.process(samples, now)
        self.pre_song_buffer.extend(samples)
        if self.buffering:
            total = len(self.pre_song_buffer)
            logger.debug(
                "AUDIO   buffer %d frames (%.2fs)",
                total,
                total / self.samplerate,
            )
            if now - self.buffer_start_time >= 5.0:
                self.buffering = False
            elif (
                len(self.pre_song_buffer) >= self.pre_song_buffer.maxlen
                and not self.classifying
            ):
                # Enough audio collected, start classification early
                self.classify_after = None
                self.buffering = False
                self._launch_genre_classifier_immediately()
        if (
            self.genre_classifier is not None
            and self.current_state == SongState.ONGOING
            and not self.classifying
            and len(self.pre_song_buffer) >= self.pre_song_buffer.maxlen
            and now - self.last_genre_check >= parameters.GENRE_CHECK_INTERVAL
        ):
            self._ai_log("Launching periodic genre classifier.")
            self._launch_genre_classifier_immediately()
        if (
            self.classify_after
            and time.time() >= self.classify_after
            and not self.classifying
        ):
            self._ai_log("Launching genre classifier after delay.")
            self._launch_genre_classifier_immediately()
        self._debug_log(
            f"proc amp:{vu:.3f} bpm:{bpm:.2f} beat:{beat} state:{self.detector.state.value}"
        )

        if self.detector.state == SongState.STARTING:
            pass

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
            self._debug_log(f"Snare flash: {update}")
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
                    self._debug_log(f"Restore {group}: {base}")
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

    def _process_audio_queue(self) -> None:
        while self.running or not self.audio_queue.empty():
            try:
                samples = self.audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            self._process_samples(samples)
            self.audio_queue.task_done()

    def audio_callback(self, indata, frames, time_info, status) -> None:
        if status:
            self._flush_beat_line()
            msg = str(status).strip()
            if self.dashboard_enabled:
                self.dashboard.set_status(msg)
            else:
                print(msg, flush=True)
        samples = np.frombuffer(indata, dtype=np.float32)
        try:
            self.audio_queue.put_nowait(samples)
        except queue.Full:
            pass

    def run(self) -> None:
        if sd is None:  # pragma: no cover - skip when sounddevice unavailable
            import sounddevice as sd_mod

            globals()["sd"] = sd_mod
        if self.detector is None:
            from src.audio import BeatDetector

            self.detector = BeatDetector(
                samplerate=self.samplerate,
                amplitude_threshold=parameters.AMPLITUDE_THRESHOLD,
                start_duration=parameters.START_DURATION,
                end_duration=parameters.END_DURATION,
                print_interval=parameters.PRINT_INTERVAL,
            )
            self.current_state = self.detector.state
        devices = parameters.DEVICES
        with open(self.log_path, "a") as log, DMX(
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
                genre = (
                    ""
                    if self.current_state == SongState.INTERMISSION
                    else self._genre_label(self.last_genre)
                )
                self.dashboard.set_genre(genre)
            else:
                init_genre = (
                    self._genre_label(self.last_genre)
                    if self.current_state != SongState.INTERMISSION
                    else ""
                )
                print(f"Initial genre {init_genre}", flush=True)
            self._print_state_change(self.scenario.updates)
            self._flush_beat_line()
            self.running = True
            worker = threading.Thread(target=self._process_audio_queue, daemon=True)
            worker.start()
            if not self.dashboard_enabled:
                print("Listening for beats. Press Ctrl+C to stop.")
            try:
                while True:
                    sd.sleep(1000)
            except KeyboardInterrupt:
                self._flush_beat_line()
                if not self.dashboard_enabled:
                    print("Stopping")
            finally:
                self.running = False
                worker.join()
        self.log_file = None


def main() -> None:
    show = BeatDMXShow()
    show.run()


if __name__ == "__main__":
    main()
