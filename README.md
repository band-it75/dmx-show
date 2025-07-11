# DMX Show

This project contains utilities to drive DMX lights and detect beats from microphone input.

## Beat-controlled blinking

The `beat_dmx.py` script listens to microphone input, detects beats using `aubio`,
and blinks a chosen DMX channel every time a beat is found. It periodically
prints a summary of the estimated BPM and a rough music genre classification
every 10 seconds based on adjustable BPM ranges. BPM is derived from the median
of the most recent beat intervals, which helps smooth out occasional
mis-detected beats. The detector also provides lightweight heuristics for chorus,
crescendo
and drum solo detection using spectral features with a 0.5-second debounce.

### Usage

```bash
pip install -r requirements.txt
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
lights and overhead effects pulse with BPM. Smoke bursts last 3 seconds with a
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

## Standalone beat detection

If you just want to detect beats without sending DMX commands, use `beat_detection.py`:

```bash
pip install -r requirements.txt
python beat_detection.py
```

Output is limited to a short summary printed every 10 seconds to avoid
performance issues when detecting rapid beats. Each summary also prints the
current stage lighting state and whether smoke bursts are firing. LumiPar 12UAW5
units double as house lights, overhead effects pulse with BPM and smoke bursts
last 3 seconds with a 30-second gap.

The detector will also analyze the incoming volume (VU level) to determine when a
song is starting, ongoing, ending or if there is an intermission. Thresholds and
timings for this detection can be adjusted by editing `parameters.py` or with
command line flags:

```bash
python beat_detection.py --amplitude-threshold 0.02 \
    --start-duration 2.0 --end-duration 3.0 --print-interval 5
```

On Windows, you can run `install_requirements.ps1` to install the Python dependencies.
Librosa is installed automatically for spectral analysis.

### Additional detection features

`beat_detection.py` also exposes simple detection of drum solos, crescendo events
and chorus sections. These rely on RMS loudness trends, harmonic/percussive
ratios and spectral flatness. Results are heuristic and may produce occasional
false triggers but can be useful for debugging lighting ideas. Their status is
visible in dashboard mode. Chorus and crescendo detection now include a
0.5-second debounce interval to reduce erratic short bursts.
You can tweak this debounce time by editing the ``BeatDetector``
``chorus_debounce`` and ``crescendo_debounce`` parameters.

## Genre classification

When a song begins, audio from the first few seconds feeds a pre-trained
`music_genres_classification` model via the Transformers pipeline. The predicted
label selects the closest lighting scenario:

- rock -> Song Ongoing - Rock
- metal -> Song Ongoing - Metal
- jazz -> Song Ongoing - Jazz
- pop/disco -> Song Ongoing - Pop
- blues, country, reggae or classical -> Song Ongoing - Slow

This model runs in a background thread so beat detection remains responsive.

## Devices

The following table lists the DMX fixtures currently configured for the
show. Address ranges are inclusive and correspond to the channels used
by each fixture.

| Addr Range | Fixture                | Mode (ch)                | Notes                |
| ---------- | ---------------------- | ------------------------ | -------------------- |
| 001-005    | LumiPar 12UAW5 #1      | 5-ch                     | Stage left house (amber/white) |
| 010-014    | LumiPar 12UAW5 #2      | 5-ch                     | Stage center (amber/white) |
| 019-023    | LumiPar 12UAW5 #3      | 5-ch                     | Stage right (amber/white) |
| 030-036    | LumiPar 7UTRI #1       | 7-ch                     | Karaoke wall left    |
| 041-047    | LumiPar 7UTRI #2       | 7-ch                     | Karaoke wall right   |
| 055-064    | LumiPar 12UQPro #1     | 10-ch                    | Overhead effects     |
| 069-078    | LumiPar 12UQPro #2     | 10-ch                    | Overhead effects     |
| 085-107    | PixieWash              | 13-ch                    | Moving head front    |
| 115-118    | Smoke machine          | 1-ch used, 3-ch reserved | Timed fog bursts |

Note: the Overhead Effects group expects LumiPar 12UQPro fixtures with a white
channel. When testing with a LumiPar 7UTRI the controller now maps ``white`` to
equal RGB values so scenarios need no manual changes.

## Show

Lighting cues are BPM-driven. LumiPar 12UAW5 units double as house lights.
Overheads pulse with BPM and smoke bursts last 3 seconds with a 30-second gap.
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

* Overhead **deep indigo** pulse every 2 beats (RGB: 54, 0, 88).
* Accent color: **soft lavender** highlights during crescendos detected by gradual RMS loudness increases (RGB: 200, 160, 255).
* Moving head gentle pan focusing on the artist.
* **2-second smoke burst** every **15 seconds**.

### Song Ongoing - Jazz (80-110 BPM)

* Overhead **amber** pulse each beat (RGB: 255, 147, 41).
* Accent color: **teal** accents triggered by detection of instrumental solos (stable mid/high-frequency harmonic content) (RGB: 0, 128, 128).
* Moving head performs narrow, rhythmic sweeps.
* **3-second smoke burst** every **30 seconds**.

### Song Ongoing - Pop (110-130 BPM)

* Overhead **candy pink** chase each beat (RGB: 255, 64, 200).
* Accent color: **bright cyan** flashes synchronized with detected snare hits (high-frequency spectral peaks) (RGB: 0, 200, 255).
* Snare hits push Overhead Effects to full intensity for 100 ms.
* Moving head executes wide, energetic sweeps.
* **3-second smoke burst** every **30 seconds**.

### Song Ongoing - Rock (130-160 BPM)

* Overhead **fire red** pulse each beat utilizing kick drum beat detection (strong low-frequency energy peaks) (RGB: 255, 0, 0).
* Accent color: **electric blue** during verses (RGB: 0, 64, 255) and **golden amber** on chorus downbeats detected via increased harmonic richness and loudness (RGB: 255, 180, 0).
* Moving head rapid pan and tilt movements.
* **3-second smoke burst** every **30 seconds**.

### Song Ongoing - Metal (>160 BPM)

* Overhead **icy white** pulse each beat (RGB: 255, 255, 255).
* Accent color: **UV purple** washes during riffs (repetitive melodic mid-frequency patterns) (RGB: 128, 0, 255) and **blood red** bursts on detected kick drum hits (low-frequency energy peaks) (RGB: 180, 0, 0).
* Moving head performs rapid, erratic sweeps.
* **3-second smoke burst** every **30 seconds**.



### Song Ending
Moving head points at the audience while stage lights fade to 50% warm white
for applause. Smoke bursts last 3 seconds with at least 30 seconds between
triggers.
