import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from main import blink_red

def test_blink_red_sends_correct_frames(monkeypatch):
    calls = []
    def fake_send(data):
        # store a copy to avoid mutation
        calls.append(dict(data))

    monkeypatch.setattr('time.sleep', lambda *_: None)
    blink_red(fake_send, start_address=10, blink_times=2, interval=0.01)
    on_frame = {10: 255, 11: 0, 12: 0, 16: 255}
    off_frame = {16: 0}
    assert calls == [on_frame, off_frame, on_frame, off_frame]
