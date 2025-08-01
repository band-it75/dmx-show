# DMX Show

This project contains utilities to drive DMX lights and detect beats from microphone input.

## Beat-controlled blinking

The `beat_dmx.py` script listens to microphone input, detects beats using
`aubio`, and blinks a chosen DMX channel on each beat. It prints the estimated
BPM every few seconds and runs a genre classifier based on the
`music_genres_classification` transformer model stored under
`models/music_genres_classification`. The detector also provides lightweight
heuristics for chorus, crescendo and drum solo detection using a
0.375-second debounce.

### Usage

```bash
pip install -r requirements.txt
pip install torch  # required for genre classification
python beat_dmx.py --universe 1 --channel 1
```

Ensure you have PortAudio installed for microphone access and that an OLA
daemon is running to handle the DMX output.

Default values for the DMX universe, channel, audio samplerate and song
detection thresholds are defined in `parameters.py`. You can edit that file or
override them with command-line options.
`DMX_FPS` in that file sets how many frames are sent each second.

## Quick LumiPar 7UTRI blink

Run `blink_red.py` to flash a LumiPar 7UTRI fixture without beat detection:

```bash
python blink_red.py --port /dev/ttyUSB0 --start-address 1 --blink-times 3
```


## Stage lighting demo

`beat_dmx.py` simply blinks one channel whenever a beat is detected. It prints
the estimated BPM every few seconds. LumiPar 12UAW5 units double as house
lights and overhead effects respond to the current genre. Smoke bursts last 3 seconds with a
30-second gap. The moving head stays on the artist during songs and points at
the audience to end each song. Stage lights fade to black during songs and
return at 50% warm white when the moving head faces the crowd.

```bash
python beat_dmx.py
```

The script prints "Estimated BPM" every few seconds. You can attach a callback
to ``BeatTrigger.on_beat`` to trigger other effects.

### Dashboard mode

Set ``SHOW_DASHBOARD`` in ``parameters.py`` to ``True`` to display a static
console dashboard instead of log lines. Only changed DMX values, BPM and smoke
state refresh on screen so the current lighting status is always visible. The
dashboard also shows the current VU level along with minimum and maximum
readings. Chorus, drum solo and crescendo flags appear alongside the song
state and detected genre at the top.
Running the show writes VU and dimmer levels to ``vu_dimmer.log`` for debugging.
The dimmer idles around 25 until the VU crosses a threshold, then rises toward
175 with 0.8 smoothing. Snare hits briefly push it to full brightness.
Genre classifier details are also logged to ``ai.log``. The file begins with a
status line noting whether the genre classifier loaded successfully. Messages
appear only once even if both the show and classifier write to the same file.
Runtime details are logged to ``logs/debug.log`` by default; set
``debug_log_path`` to override the location.

## Standalone beat detection

If you just want to detect beats without sending DMX commands, use `beat_detection.py`:

```bash
pip install -r requirements.txt
pip install torch
python beat_detection.py
```

Output is limited to a short summary printed every 10 seconds to avoid
performance issues when detecting rapid beats. Each summary also prints the
current stage lighting state and whether smoke bursts are firing. LumiPar 12UAW5
units double as house lights, overhead effects track the detected genre and smoke bursts
last 3 seconds with a 30-second gap.

The detector will also analyze the incoming volume (VU level) to determine when a
song is starting, ongoing, ending or if there is an intermission. Thresholds and
timings for this detection can be adjusted by editing `parameters.py` or with
command line flags:

```bash
python beat_detection.py --amplitude-threshold 0.02 \
    --start-duration 2.0 --end-duration 3.0 --print-interval 5
```

On Windows, run `install_requirements.ps1` from a PowerShell prompt to install
dependencies and preload the genre classification model under
`models/music_genres_classification`. Librosa is installed automatically for
spectral analysis.

### Additional detection features

`beat_detection.py` also exposes simple detection of drum solos, crescendo events
and chorus sections. These rely on RMS loudness trends, harmonic/percussive
ratios and spectral flatness. Results are heuristic and may produce occasional
false triggers but can be useful for debugging lighting ideas. Their status is
visible in dashboard mode. Chorus and crescendo detection now include a
0.375-second debounce interval to reduce erratic short bursts.
You can tweak this debounce time by editing the ``BeatDetector``
``chorus_debounce`` and ``crescendo_debounce`` parameters.
Detection sensitivity for chorus, drum solo, crescendo, snare and kick adapts
over time. ``beat_detection.py`` tracks how often each event fires along with
the current BPM and VU level. It adjusts the thresholds every 30 seconds and
saves them to ``tuning.json`` so the next run starts with the tuned values.

## Genre classification

When a song begins, audio from the first few seconds feeds a pre-trained
`music_genres_classification` model via the Transformers pipeline. The
classifier loads the model from `models/music_genres_classification`. The
predicted
label selects the closest lighting scenario:

- disco -> Song Ongoing - Disco
- metal -> Song Ongoing - Metal
- reggae -> Song Ongoing - Reggae
- blues -> Song Ongoing - Blues
- rock -> Song Ongoing - Rock
- classical -> Song Ongoing - Classical
- jazz -> Song Ongoing - Jazz
- hiphop -> Song Ongoing - HipHop
- country -> Song Ongoing - Country
- pop -> Song Ongoing - Pop

This model runs in a background thread so beat detection remains responsive.
If the genre remains blank, create ``GenreClassifier(verbose=True)`` to see
model loading details and the raw label returned.
The show retries classification every five seconds while it stays in the
``Song Start`` scenario so a label is eventually detected.

### Troubleshooting

If no genre predictions appear at runtime, verify the classifier can load
independently. Run ``python check_classifier.py`` from the project root. The
script reports the installed versions of ``torch`` and ``transformers`` and
prints a test prediction. If the model fails to load, reinstall the Python
dependencies or re-run ``install_requirements.ps1`` to download the model
under ``models/music_genres_classification``.

## Devices

The following table lists the DMX fixtures currently configured for the
show. Address ranges are inclusive and correspond to the channels used
by each fixture.

| Addr Range | Fixture                 | Mode | Notes |
|------------|-------------------------|------|-------------------------|
| 001–007 | LumiPar 12UAW5 #1 | 7-ch | House left (amber/white) |
| 008–014 | LumiPar 12UAW5 #2 | 7-ch | House right (amber/white) |
| 015–022 | LumiPar 7UTRI #1 | 8-ch | Karaoke wall left |
| 023–030 | LumiPar 7UTRI #2 | 8-ch | Karaoke wall right |
| 031–039 | LumiPar 12UQPro #1 | 9-ch | Overhead #1 |
| 040–048 | LumiPar 12UQPro #2 | 9-ch | Overhead #2 |
| 049–057 | LumiPar 12UQPro #3 | 9-ch | Overhead #3 |
| 058–070 | PixieWash | 13-ch | Moving head |
| 071–074 | Smoke machine | 4-ch | Fog bursts |
| 075–082 | Fuzzix PartyPar UV #1 | 7-ch | UV wash left |
| 083–090 | Fuzzix PartyPar UV #2 | 7-ch | UV wash right |

Note: the Overhead Effects group expects LumiPar 12UQPro fixtures with a white
channel. When testing with a LumiPar 7UTRI the controller now maps ``white`` to
equal RGB values so scenarios need no manual changes.

The moving head's shutter automatically opens when the dimmer is above zero.
If no color is provided, all four color channels (red, green, blue and white)
default to full so the beam always appears during songs.

## Show

Lighting cues follow the AI-detected genre. LumiPar 12UAW5 units double as house lights.
Overhead effects respond to the current genre and smoke bursts last 3 seconds with a 30-second gap.
Beat updates briefly change overhead colors for 100 ms on each beat.
Genre-specific colors guide intensity and timing. The moving head stays on the
artist during songs and aims at the audience to end each song. Stage lights fade
to black during songs and return when the moving head faces the audience.
Avoid cues that rely on solos or other musical details the software cannot
sense.
Each ``Scenario`` constant stores DMX updates, an optional beat mapping, BPM range
and VU level along with predecessor and successor lists. ``Song Start`` follows
``Intermission``. All ``Song Ongoing`` states can switch among themselves.
``Song Ending`` only follows ``Song Ongoing`` and ``Intermission`` returns after
``Song Ending``.

### Intermission
House at 20% with slow wall fades.
- 5-s smoke burst every 60 s.
- Moving head off until songs start.

### Song Start
Stage lights fade to black as overheads rise to 30% warm white. Moving head centers on the artist.

### Song Ongoing - Slow (BPM <80)

* Overhead **deep indigo** flashes every 2 beats (RGB: 54, 0, 88).
* Accent color: **soft lavender** highlights crescendos (RGB: 200, 160, 255).
* Moving head gentle pan focusing on the artist.
* **2-second smoke burst** every **15 seconds**.

### Song Ongoing - Jazz (80-110 BPM)

* Overhead **amber** accent on each beat (RGB: 255, 147, 41).
* Accent color: **teal** accents highlight dynamic sections (RGB: 0, 128, 128).
* Moving head performs narrow, rhythmic sweeps.
* **3-second smoke burst** every **30 seconds**.

### Song Ongoing - Pop (110-130 BPM)

* Overhead **candy pink** chase each beat (RGB: 255, 64, 200).
* Accent color: **bright cyan** flashes on strong beats (RGB: 0, 200, 255).
* Beat accents change color for 100 ms beyond the VU level.
* Moving head executes wide, energetic sweeps.
* **3-second smoke burst** every **30 seconds**.

### Song Ongoing - Rock (130-160 BPM)

* Overhead **fire red** accent each beat using strong low-frequency peaks (RGB: 255, 0, 0).
* Accent color: **electric blue** in sustained sections (RGB: 0, 64, 255).
* Chorus downbeats switch to **golden amber** (RGB: 255, 180, 0).
* Moving head rapid pan and tilt movements.
* **3-second smoke burst** every **30 seconds**.

### Song Ongoing - Metal (>160 BPM)

* Overhead **icy white** accent each beat (RGB: 255, 255, 255).
* Accent color: **UV purple** washes during intense passages (RGB: 128, 0, 255).
* **Blood red** bursts on strong low-frequency hits (RGB: 180, 0, 0).
* Moving head performs rapid, erratic sweeps.
* **3-second smoke burst** every **30 seconds**.



### Song Ending
Moving head points at the audience while stage lights fade to 50% warm white
for applause. Smoke bursts last 3 seconds with at least 30 seconds between
triggers.
