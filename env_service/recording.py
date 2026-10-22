"""Stream Rig's composed JPEG frames to disk without buffering a whole episode."""
from pathlib import Path


class VideoRecorder:
    def __init__(self, path, fps=15):
        import imageio.v2 as imageio

        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.frame_count = 0
        self.closed = False
        # Fragmented MP4 preserves completed fragments if the worker is interrupted.
        self.writer = imageio.get_writer(str(self.path), fps=fps, macro_block_size=1, quality=8,
                                         output_params=["-movflags", "+frag_keyframe+empty_moov+default_base_moof"])

    def append(self, jpeg):
        import cv2

        if self.closed:
            raise RuntimeError("video recorder is closed")
        frame = cv2.imdecode(jpeg, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("invalid JPEG frame")
        self.writer.append_data(frame[..., ::-1])
        self.frame_count += 1

    def close(self):
        if not self.closed:
            self.writer.close()
            self.closed = True

