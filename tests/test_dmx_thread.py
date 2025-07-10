import sys
import pathlib
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from dmx import DMX, DmxDevice


class DummyDevice(DmxDevice):
    def __init__(self, addr: int) -> None:
        super().__init__({"val": addr})


def test_dmx_thread_repeats_and_updates(monkeypatch):
    calls = []

    class FakeSerial:
        def __init__(self, *_, **__):
            pass

        def send(self, frame):
            calls.append(dict(frame))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr('dmx.DmxSerial', FakeSerial)
    dmx = DMX([(DummyDevice, 1)], fps=100)
    dmx.update()
    dmx.start()
    time.sleep(0.05)
    # after some time multiple frames should have been sent
    first_len = len(calls)
    assert first_len >= 3
    assert all(c == {1: 0} for c in calls)

    dmx.devices[0].set_channel('val', 10)
    dmx.update()
    time.sleep(0.05)
    dmx.stop()
    assert calls[-1] == {1: 10}
