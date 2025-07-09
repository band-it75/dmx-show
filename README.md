# DMX Show

This project contains utilities to drive DMX lights and detect beats from microphone input.

## Beat-controlled blinking

The `beat_dmx.py` script listens to microphone input, detects beats using `aubio`,
and blinks a chosen DMX channel every time a beat is found. It also periodically
prints the estimated BPM and a rough music genre classification based on
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

## Standalone beat detection

If you just want to detect beats without sending DMX commands, use `beat_detection.py`:

```bash
pip install -r requirements.txt
python beat_detection.py
```

The detector will also analyze the incoming volume (VU level) to determine when a
song is starting, ongoing, ending or if there is an intermission. Thresholds and
timings for this detection can be adjusted by editing `parameters.py` or with
command line flags:

```bash
python beat_detection.py --amplitude-threshold 0.02 \
    --start-duration 2.0 --end-duration 3.0
```

On Windows, you can run `install_requirements.ps1` to install the Python dependencies.
