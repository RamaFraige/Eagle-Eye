from collections import deque
from typing import List


class VideoRingBuffer:
    def __init__(self, seconds: int, fps: int):
        self.seconds = seconds
        self.fps = fps
        self.capacity = seconds * fps
        self._buffer: deque[bytes] = deque(maxlen=self.capacity)

    def push(self, frame_bytes: bytes) -> None:
        self._buffer.append(frame_bytes)

    def get_last_seconds(self, seconds: int) -> List[bytes]:
        """
        Retrieve the last N seconds of video frames.
        If the buffer doesn't have enough frames, returns all available frames.
        """
        frame_count = seconds * self.fps
        # slice the deque from the end
        if frame_count >= len(self._buffer):
            return list(self._buffer)

        # Inefficient to list(deque) but robust for now.
        # For high perf, use itertools.islice or similar, but list conversion is needed anyway.
        # list(deque)[-n:] copies efficiently enough for reasonable buffer sizes.
        return list(self._buffer)[-frame_count:]

    def clear(self) -> None:
        self._buffer.clear()
