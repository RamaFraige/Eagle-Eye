from dataclasses import dataclass


@dataclass
class AlertSnapshot:
    """Container for alert notification data."""

    video_bytes: bytes
    thumbnail_bytes: bytes | None = None
