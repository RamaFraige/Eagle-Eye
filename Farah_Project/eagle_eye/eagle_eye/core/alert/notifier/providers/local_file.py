import json
import logging
from datetime import datetime
from pathlib import Path

from eagle_eye.core.alert.event import AlertEvent
from eagle_eye.core.alert.snapshot import AlertSnapshot

from ..base import NotificationProvider

logger = logging.getLogger(__name__)


class LocalFileProvider(NotificationProvider):
    """
    Saves alerts to local filesystem.
    Creates a timestamped folder for each alert containing:
    - video.mp4: The video clip
    - alert.json: Alert metadata
    """

    def __init__(self, base_dir: str):
        """
        Args:
            base_dir: Base directory where alert folders will be created
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        # print the full path
        logger.debug(f"Base directory: `{self.base_dir.resolve()}`")

    def send(self, event: AlertEvent, snapshot: AlertSnapshot) -> None:
        # Create timestamped folder name: YYYY-MM-DD_HH-MM-SS_stream
        timestamp = datetime.fromtimestamp(event.timestamp)
        folder_name = timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        folder_name += f"_{event.stream_id}"

        alert_dir = self.base_dir / folder_name
        alert_dir.mkdir(parents=True, exist_ok=True)

        # Save video clip
        video_path = alert_dir / "video.mp4"
        video_path.write_bytes(snapshot.video_bytes)

        # Save thumbnail
        if snapshot.thumbnail_bytes is not None:
            thumbnail_path = alert_dir / "thumbnail.jpg"
            thumbnail_path.write_bytes(snapshot.thumbnail_bytes)

        # Save alert metadata as JSON
        alert_data = {
            "stream_id": event.stream_id,
            "severity": event.severity.value,
            "triggered_rules": event.triggered_rules,
            "metadata": event.metadata,
            "timestamp": event.timestamp,
            "timestamp_iso": timestamp.isoformat(),
        }

        json_path = alert_dir / "alert.json"
        json_path.write_text(json.dumps(alert_data, indent=2), encoding="utf-8")

        logger.debug(f"Alert saved to: '{alert_dir}'")
