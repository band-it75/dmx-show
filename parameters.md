# Current Implementation


# Future Implementation / Desired State

Good clarification! Here's a revised and consistent version of your scenario definitions (`parameters.py`), following your suggestions:

* Renamed `color_transition` → **`timer`** (clearer, indicates a trigger after a set time).
* Replaced `channel` with explicit color names (`red`, `green`, `blue`, `white`, etc.).
* Moved `beat` into the special events group for consistency.

## 🎛️ **Revised and Consistent Scenario Structure**

Here's your updated scenario format, clearly structured with the new `special_events` dict:

```python
SONG_ONGOING_POP = (
    "Song Ongoing - Pop",
    0.02,
    (110, 130),
    ["SONG_START", "SONG_ONGOING_SLOW", "SONG_ONGOING_JAZZ", "SONG_ONGOING_ROCK", "SONG_ONGOING_METAL"],
    ["SONG_ONGOING_SLOW", "SONG_ONGOING_JAZZ", "SONG_ONGOING_ROCK", "SONG_ONGOING_METAL", "SONG_ENDING"],
    {   # Initial Updates
        "House Lights": {"dimmer": 0},
        "Moving Head": {"dimmer": 255},
        "Overhead Effects": {"red": 255, "blue": 96, "dimmer": 255},
        "Karaoke Lights": {"red": 26, "blue": 10, "dimmer": 26},
        "Smoke Machine": {"smoke_gap": 10000, "duration": 5000},
    },
    {   # Special Events
        "beat": {
            "Overhead Effects": {
                "red": 255,
                "blue": 96,
                "dimmer": 255,
                "duration": 100,
            },
        },
        "chorus": {
            "Overhead Effects": {"green": 255, "blue": 128, "dimmer": 255},
            "Moving Head": {"pan": 30000, "tilt": 40000, "dimmer": 255},
        },
        "snare_hit": {
            "Overhead Effects": {"white": 255, "dimmer": 255, "duration": 50},
        },
        "timer": {
            "after_seconds": 30,
            "Overhead Effects": {
                "from": {"red": 255, "blue": 96},
                "to": {"red": 128, "blue": 255},
                "duration_ms": 45000,  # 45-second fade
            },
        },
    },
)
```

### 📌 **Structure Explanation:**

* `initial_updates`: The static initial state when entering the scenario.
* `special_events`: Optional dynamic events responding to audio features or timers:

  * `"beat"`: Triggered by detected beats.
  * `"chorus"`: Triggered during chorus sections.
  * `"snare_hit"`: Instantaneous flashes synced with snare hits.
  * `"timer"`: Initiates a smooth color fade after a specified number of seconds (`after_seconds`) into the scenario.

---

## 🎚️ **Implementing the Logic in `main.py`**

### ① **Beat Handler**

In your beat detection handler (`_handle_beat`):

```python
def apply_beat_effects(self):
    beat_config = self.scenario[-1].get("beat")
    if beat_config:
        now = time.time()
        for group, settings in beat_config.items():
            duration_ms = settings.pop("duration", 100)
            self._apply_update(group, settings)
            self.beat_ends[group] = now + duration_ms / 1000.0
```

```python
if detector.beat_detected:
    self.apply_beat_effects()
```

### ② **Chorus Handler**

```python
def apply_chorus_effects(self):
    chorus_config = self.scenario[-1].get("chorus")
    if chorus_config:
        self._print_state_change(chorus_config)
```

```python
if detector.is_chorus:
    self.apply_chorus_effects()
```

### ③ **Snare Hit Handler**

```python
def apply_snare_hit_effects(self):
    snare_config = self.scenario[-1].get("snare_hit")
    if snare_config:
        now = time.time()
        for group, settings in snare_config.items():
            duration_ms = settings.pop("duration", 50)
            self._apply_update(group, settings)
            self.beat_ends[group] = now + duration_ms / 1000.0
```

```python
if detector.snare_hit:
    self.apply_snare_hit_effects()
```

### ④ **Timer-Based Color Transition**

When entering the ONGOING scenario, trigger a timer thread if defined:

```python
def start_timer_effects(self):
    timer_config = self.scenario[-1].get("timer")
    if timer_config:
        after_seconds = timer_config["after_seconds"]
        threading.Thread(
            target=self._timer_worker,
            args=(timer_config, after_seconds),
            daemon=True
        ).start()

def _timer_worker(self, timer_config, after_seconds):
    time.sleep(after_seconds)  # wait until specified time has passed
    for group, colors in timer_config.items():
        if group == "after_seconds":
            continue
        self._color_fade_worker(group, colors)

def _color_fade_worker(self, group, colors):
    duration = colors["duration_ms"] / 1000.0
    start_time = time.time()
    end_time = start_time + duration

    from_colors = colors["from"]
    to_colors = colors["to"]

    while time.time() < end_time:
        elapsed = time.time() - start_time
        ratio = elapsed / duration
        current_colors = {
            color: int(from_colors[color] * (1 - ratio) + to_colors[color] * ratio)
            for color in from_colors
        }
        self._apply_update(group, current_colors)
        time.sleep(0.05)  # update smoothly at 20Hz
```

Trigger this when scenario changes:

```python
if new_state.startswith("SONG_ONGOING"):
    self.start_timer_effects()
```

---

## ⚙️ **Generalized Scenario Template**

Here's a generalized template to quickly create consistent scenario definitions:

```python
SCENARIO_TEMPLATE = (
    "Scenario Name",
    volume_threshold,
    (bpm_low, bpm_high),
    ["PREDECESSORS"],
    ["SUCCESSORS"],
    {   # initial_updates
        "Fixture Group": {"color": value, "dimmer": value},
    },
    {   # special_events (optional)
        "beat": {
            "Fixture Group": {"color": value, "dimmer": value, "duration": ms},
        },
        "chorus": {
            "Fixture Group": {"color": value, "dimmer": value},
        },
        "snare_hit": {
            "Fixture Group": {"color": value, "dimmer": value, "duration": ms},
        },
        "timer": {
            "after_seconds": seconds,
            "Fixture Group": {
                "from": {"color": start_value},
                "to": {"color": end_value},
                "duration_ms": ms,
            },
        },
    },
)
```

---

## 🎯 **Benefits of this Revised Structure**

* **Clearer Naming**: `timer` explicitly indicates the delayed event.
* **Consistent Use of Colors**: Replacing ambiguous terms (`channel`) with explicit color references (`red`, `blue`, etc.) is clear and self-documenting.
* **Minimal Structural Change**: Maintains the existing overall structure, keeping changes intuitive and easy to integrate.
* **Easily Extendable**: Flexible to add or omit events per scenario, making it practical and adaptable.

This revised definition gives you an intuitive, powerful, and straightforward way to configure dynamic and visually engaging DMX lighting scenarios without extensive code rewrites.
