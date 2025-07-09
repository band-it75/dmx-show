import argparse
import time

import numpy as np
import sounddevice as sd
import aubio
from ola.ClientWrapper import ClientWrapper


class DmxBeatBlinker:
    def __init__(self, universe: int = 1, channel: int = 1, samplerate: int = 44100):
        self.universe = universe
        self.channel = channel
        self.samplerate = samplerate
        self.wrapper = ClientWrapper()
        self.client = self.wrapper.Client()
        self.tempo = aubio.tempo("default", 1024, 512, samplerate)

    def _send_dmx_value(self, value: int):
        data = bytearray(512)
        data[self.channel - 1] = value
        self.client.SendDmx(self.universe, data, lambda state: self.wrapper.Stop())
        self.wrapper.Run()

    def _blink(self):
        self._send_dmx_value(255)
        time.sleep(0.05)
        self._send_dmx_value(0)

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print(status, flush=True)
        samples = np.frombuffer(indata, dtype=np.float32)
        if self.tempo(samples):
            print(f"Beat @ {self.tempo.get_last_s():.2f}s", flush=True)
            self._blink()

    def run(self):
        with sd.InputStream(channels=1, callback=self.audio_callback,
                            samplerate=self.samplerate, blocksize=512):
            print("Listening for beats. Press Ctrl+C to stop.")
            try:
                while True:
                    sd.sleep(1000)
            except KeyboardInterrupt:
                print("Stopping")


def main() -> None:
    parser = argparse.ArgumentParser(description="Blink DMX lights on detected beats from microphone")
    parser.add_argument("--universe", type=int, default=1, help="DMX universe to control")
    parser.add_argument("--channel", type=int, default=1, help="DMX channel to blink")
    args = parser.parse_args()

    blinker = DmxBeatBlinker(universe=args.universe, channel=args.channel)
    blinker.run()


if __name__ == "__main__":
    main()
