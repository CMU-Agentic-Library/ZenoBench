"""Actual encoding/decoding without Isaac Sim."""
import cv2
import numpy as np
import pytest

from env_service.recording import VideoRecorder


def test_streamed_video_is_readable_and_finalized(tmp_path):
    path = tmp_path / "episode" / "run.mp4"
    recorder = VideoRecorder(path, fps=15)
    for i in range(12):
        frame = np.full((64, 96, 3), i * 15, dtype=np.uint8)
        ok, jpeg = cv2.imencode(".jpg", frame)
        assert ok
        recorder.append(jpeg)
    recorder.close()
    recorder.close()
    assert path.stat().st_size > 0 and recorder.frame_count == 12
    reader = cv2.VideoCapture(str(path))
    try:
        assert reader.isOpened()
        assert reader.get(cv2.CAP_PROP_FPS) == pytest.approx(15)
        frames = 0
        while True:
            ok, frame = reader.read()
            if not ok:
                break
            assert frame.shape == (64, 96, 3)
            frames += 1
        assert frames == 12
    finally:
        reader.release()
    with pytest.raises(RuntimeError, match="closed"):
        recorder.append(jpeg)
