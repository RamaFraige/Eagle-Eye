from .ring_buffer import VideoRingBuffer


class VideoBufferRegistry:
    def __init__(self, seconds: int, fps: int):
        self.seconds = seconds
        self.fps = fps
        self._buffers: dict[str, VideoRingBuffer] = {}

    def get(self, stream_id: str) -> VideoRingBuffer:
        if stream_id not in self._buffers:
            self._buffers[stream_id] = VideoRingBuffer(
                seconds=self.seconds, fps=self.fps
            )
        return self._buffers[stream_id]
