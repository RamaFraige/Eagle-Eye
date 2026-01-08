import logging
import threading
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Iterable, List

import cv2
import numpy as np

from .buffer.registry import VideoBufferRegistry
from .event import AlertEvent
from .notifier.base import NotificationProvider
from .rules.base import AlertRule
from .severity import AlertSeverity
from .snapshot import AlertSnapshot
from .video.encoder import VideoEncoder

logger = logging.getLogger(__name__)


class BaseAlertManager(ABC):
    """Base contract for all alert managers."""

    @abstractmethod
    def process(self, stream_id: str, frame_bytes: bytes, result: dict) -> None:
        """Process a frame and inference result."""
        raise NotImplementedError


class AlertManager(BaseAlertManager):
    """
    Manages the lifecycle of alerts, including rule evaluation, cooldown management,
    and notification dispatching with video clips.
    """

    def __init__(
        self,
        rules: List[AlertRule],
        notifier: NotificationProvider,
        buffers: VideoBufferRegistry,
        name: str = "alert-manager",
        clip_seconds: int = 15,
        cooldown_sec: int = 30,
        severity: AlertSeverity = AlertSeverity.MEDIUM,
    ):
        """
        Initializes the AlertManager.

        Args:
            rules: A list of alert rules to evaluate against incoming data.
            notifier: The provider used to send notifications.
            buffers: Registry for managing video buffers for clip generation.
            name: Name of the alert manager.
            clip_seconds: Duration of the video clip to include with alerts.
            cooldown_sec: Minimum time between alerts for the same stream.
            severity: Default severity level for alerts.
        """
        self.rules = rules
        self.notifier = notifier
        self.buffers = buffers
        self.name = name
        self.clip_seconds = clip_seconds
        self.cooldown_sec = cooldown_sec
        self._cooldowns = defaultdict(float)
        self._lock = threading.RLock()
        self.severity = severity

    def process(self, stream_id: str, frame_bytes: bytes, result: dict):
        with self._lock:
            buffer = self.buffers.get(stream_id)
            buffer.push(frame_bytes)

            now = time.time()
            # Check cooldown
            if now < self._cooldowns[stream_id]:
                return

            # Evaluate ALL rules
            satisfied_rules = []
            for rule in self.rules:
                if rule.evaluate(result, stream_id):
                    satisfied_rules.append(rule)

            # Requirement: "rules inside the AlertManager must all is True to send a one event"
            if len(satisfied_rules) == len(self.rules) and len(self.rules) > 0:
                # All rules passed. Trigger one event.
                event = AlertEvent(
                    name=self.name,
                    stream_id=stream_id,
                    severity=self.severity,
                    triggered_rules=[r.name for r in satisfied_rules],
                    metadata=result,
                    timestamp=now,
                )

                data = self._build_clip(stream_id)

                self.notifier.send(event, data)

                self._cooldowns[stream_id] = now + self.cooldown_sec

                # Cleanup all rules
                for rule in self.rules:
                    rule.cleanup(stream_id)

    def _build_clip(self, stream_id: str) -> AlertSnapshot:
        frames = self.buffers.get(stream_id).get_last_seconds(self.clip_seconds)
        fps = self.buffers.get(stream_id).fps

        # Extract thumbnail from first available frame
        thumbnail_bytes = None
        if frames:
            try:
                # Decode first frame
                nparr = np.frombuffer(frames[0], np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is not None:
                    # Encode as JPEG with high quality
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
                    _, buffer = cv2.imencode(".jpg", img, encode_param)
                    thumbnail_bytes = buffer.tobytes()
            except Exception as e:
                logger.error(f"Failed to extract thumbnail: {e}")

        video_bytes = self._encode_video(frames, fps)
        return AlertSnapshot(video_bytes=video_bytes, thumbnail_bytes=thumbnail_bytes)

    def _encode_video(self, frames: List[bytes], fps: int) -> bytes:
        return VideoEncoder.encode(frames, fps=fps)


class AlertManagerGroup(BaseAlertManager):
    """
    Composite alert manager.
    Dispatches processing to multiple alert managers.
    """

    def __init__(self, managers: Iterable[BaseAlertManager]):
        self.managers: List[BaseAlertManager] = list(managers)

    def process(self, stream_id: str, frame_bytes: bytes, result: dict) -> None:
        for manager in self.managers:
            try:
                manager.process(stream_id, frame_bytes, result)
            except Exception:
                logger.exception(
                    "AlertManager %s failed for stream_id=%s",
                    manager.__class__.__name__,
                    stream_id,
                )
