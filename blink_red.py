import argparse

from dmx import DmxSerial
from Prolights_LumiPar7UTRI_8ch import blink_red


def main() -> None:
    parser = argparse.ArgumentParser(description="Blink LumiPar 7UTRI red")
    parser.add_argument("--port", default="COM4",
                        help="Serial port, e.g. COM4 or /dev/ttyUSB0")
    parser.add_argument("--start-address", type=int, default=1,
                        help="Fixture start address")
    parser.add_argument("--blink-times", type=int, default=5,
                        help="Number of blinks")
    parser.add_argument("--interval", type=float, default=0.2,
                        help="Seconds between frames")
    args = parser.parse_args()

    with DmxSerial(port=args.port) as dmx:
        blink_red(dmx.send, start_address=args.start_address,
                  blink_times=args.blink_times, interval=args.interval)


if __name__ == "__main__":
    main()
