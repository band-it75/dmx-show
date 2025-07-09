# DMX Show

This project contains utilities to drive DMX lights and detect beats from microphone input.

## Beat-controlled blinking

The `beat_dmx.py` script listens to microphone input, detects beats using `aubio`,
and blinks a chosen DMX channel every time a beat is found. It also periodically
prints the estimated BPM and a rough music genre classification.

### Usage

```bash
pip install -r requirements.txt
python beat_dmx.py --universe 1 --channel 1
```

Ensure you have PortAudio installed for microphone access and that an OLA
daemon is running to handle the DMX output.

## Standalone beat detection

If you just want to detect beats without sending DMX commands, use `beat_detection.py`:

```bash
pip install -r requirements.txt
python beat_detection.py
```

On Windows, you can run `install_requirements.ps1` to install the Python dependencies.
