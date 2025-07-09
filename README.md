# DMX Show

This project contains utilities to drive DMX lights and detect beats from microphone input.

## Beat-controlled blinking

The `beat_dmx.py` script listens to microphone input, detects beats using `aubio`,
and blinks a chosen DMX channel every time a beat is found. It periodically
prints a summary of the estimated BPM and a rough music genre classification
every 10 seconds based on
adjustable BPM ranges. BPM is derived from the median of the most recent beat
intervals, which helps smooth out any occasional mis-detected beats.

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

## Stage lighting and smoke demo

`beat_dmx.py` can also trigger smoke bursts and print the current stage light
color based on the estimated genre. LumiPar 12UAW5 units double as house lights
and overhead effects pulse with BPM. Smoke bursts last 3 seconds with a
30-second gap. The moving head stays on the artist during songs and points at
the audience to end each song. Stage lights fade to black during songs and
return at 50% warm white when the moving head faces the crowd.

The beat detector now automatically turns the moving head toward the audience
when a song is ending, providing a clear signal for applause.

```bash
python beat_dmx.py --smoke-channel 115 --smoke-gap 30 --smoke-duration 3
```

Stage light color names such as "amber" are printed whenever BPM summaries are
shown. "Smoke start" and "Smoke end" indicate each burst.

Typical console output for a cue looks like:

```
Change:
- Moving Light: Audience
Current:
- Moving Light: Audience
- Stage Light: Off
- Overhead Effects: Red (80%) Pulsing
- Karaoke Lights: Red (10%)
```

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

## Show

Lighting cues are BPM-driven. LumiPar 12UAW5 units double as house lights.
Overheads pulse with BPM and smoke bursts last 3 seconds with a 30-second gap.
The moving head stays on the artist during songs and aims at the audience to end each song.

### Intermission
House at 20% with slow wall fades.
- 5-s smoke burst every 60 s.

### Song start
Stage lights fade to black as overheads rise to 30% warm white. Moving head centers on the artist.

### Slow (BPM <80)
- Overhead deep red pulse every 2 beats.
- Moving head gentle pan on the artist.
- 2-s smoke burst every 15 s.

### Jazz (80-110 BPM)
- Overhead amber pulse each beat.
- Moving head narrow sweeps.
- 3-s smoke burst every 30 s.

### Pop (110-130 BPM)
- Overhead pink chase each beat.
- Moving head wide sweeps.
- 3-s smoke burst every 30 s.

### Rock (130-160 BPM)
- Overhead red pulse each beat with 1-s white strobe every 8 beats.
- Moving head fast pan and tilt.
- 3-s smoke burst every 30 s.

### Metal (>160 BPM)
- Overhead white strobe each beat.
- Moving head erratic sweeps.
- 3-s smoke burst every 30 s.

### Song end
Moving head points at the audience while stage lights fade to 50% warm white
for applause. Smoke bursts last 3 seconds with at least 30 seconds between
triggers.
