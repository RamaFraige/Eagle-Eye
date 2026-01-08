import tempfile
from pathlib import Path
from typing import List

import cv2
import numpy as np


class VideoEncoder:
    @staticmethod
    def encode(frames: List[bytes], fps: int = 10, codec: str = "mp4v") -> bytes:
        """
        Encode a list of frame bytes into a video file (MP4).

        Args:
            frames: List of frame data as bytes (JPEG/PNG encoded)
            fps: Frames per second for the output video
            codec: FourCC codec string (default: 'mp4v' for MP4)

        Returns:
            Video file as bytes
        """
        if not frames:
            return b""

        # Decode first frame to get dimensions
        first_frame = cv2.imdecode(
            np.frombuffer(frames[0], dtype=np.uint8), cv2.IMREAD_COLOR
        )
        if first_frame is None:
            return b"VIDEO_ENCODING_ERROR"

        height, width = first_frame.shape[:2]

        # Use system temp directory instead of current directory
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            temp_path = tmp_file.name

        try:
            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*codec)
            writer = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))

            # Write all frames
            for frame_bytes in frames:
                frame = cv2.imdecode(
                    np.frombuffer(frame_bytes, dtype=np.uint8), cv2.IMREAD_COLOR
                )
                if frame is not None:
                    writer.write(frame)

            writer.release()

            # Read the video file into memory
            with open(temp_path, "rb") as f:
                video_data = f.read()

            return video_data

        finally:
            # Cleanup temp file
            temp_path_obj = Path(temp_path)
            if temp_path_obj.exists():
                temp_path_obj.unlink()
