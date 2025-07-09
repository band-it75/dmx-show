# DMX Show

This project contains utilities to drive DMX lights.

## Beat-controlled blinking

The `beat_dmx.py` script listens to microphone input, detects beats using `aubio`,
and blinks a chosen DMX channel every time a beat is found.

### Usage

```bash
pip install -r requirements.txt
python beat_dmx.py --universe 1 --channel 1
```

Ensure you have PortAudio installed for microphone access and that an OLA
daemon is running to handle the DMX output.

