import logging
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from pydantic import BaseModel, Field

from eagle_eye.config.settings import settings

if TYPE_CHECKING:
    from eagle_eye.core.alert.manager import AlertManager

logger = logging.getLogger(__name__)


class UResult(BaseModel):
    """
    Unified result object returned by a UseCase.

    Attributes:
        object_count: Number of detected objects.
        detections: Raw or processed detection results.
    """

    object_count: int = 0
    detections: List[Any] = Field(default_factory=list)

    class Config:
        extra = "allow"

    def __iadd__(self, other: "UResult") -> "UResult":
        """
        Merge another UResult into this instance.

        Args:
            other: Another UResult instance.

        Returns:
            Self after merging.
        """
        # Check the type of other
        if not isinstance(other, UResult):
            raise TypeError(f"Cannot add {type(other)} to UResult")

        self.object_count += other.object_count
        self.detections.extend(other.detections)
        return self


@dataclass
class UseCase(ABC):
    """
    Base class for all AI use cases (e.g., weapon detection, fight detection).

    Each use case:
    - Runs inference
    - Draws results
    - Optionally triggers alerts without blocking the pipeline
    """

    name: Optional[str] = None
    confidence_threshold: float = 0.6
    alert_manager: Optional["AlertManager"] = None

    #: Shared executor for alert processing (fire-and-forget)
    _alert_executor: ThreadPoolExecutor = field(
        default=ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="alert-worker",
        ),
        init=False,
        repr=False,
    )

    @abstractmethod
    def _predict(self, input_data: Any) -> Any:
        """
        Run inference on input data.

        Args:
            input_data: Input frame or data.

        Returns:
            Raw prediction output.
        """
        raise NotImplementedError

    @abstractmethod
    def _draw(self, input_data: Any, prediction: Any) -> np.ndarray:
        """
        Draw prediction results on the input frame.

        Args:
            input_data: Original frame.
            prediction: Raw model prediction.

        Returns:
            Annotated frame.
        """
        raise NotImplementedError

    def _transform_prediction(self, prediction: Any) -> Any:
        """
        Optional hook to normalize or transform model output.

        Override this method to return UResult or another structured object.

        Args:
            prediction: Raw prediction output.

        Returns:
            Transformed prediction.
        """
        return prediction

    def _run(
        self, input_data: Any, stream_id: str
    ) -> Tuple[np.ndarray, Optional[UResult]]:
        """
        Run inference and drawing pipeline.

        Args:
            input_data: Input frame.

        Returns:
            Tuple of:
                - Annotated frame
                - Transformed result (UResult or None)
        """
        prediction: Any = self._predict(input_data)
        annotated_frame: np.ndarray = self._draw(input_data, prediction)

        transformed = self._transform_prediction(prediction)

        if isinstance(transformed, UResult):
            return annotated_frame, transformed

        return annotated_frame, None

    def _dispatch_alert(
        self,
        stream_id: str,
        frame: np.ndarray,
        result: UResult,
    ) -> None:
        """
        Dispatch alert processing in a background thread.

        Args:
            stream_id: Unique video stream identifier.
            frame: Original frame.
            result: Use case result.
        """
        try:
            success, buffer = cv2.imencode(".jpg", frame)
            if not success:
                logger.warning("Failed to encode frame for alert")
                return

            frame_bytes: bytes = buffer.tobytes()
            metadata: Dict[str, Any] = result.model_dump()

            self.alert_manager.process(stream_id, frame_bytes, metadata)

        except Exception:
            logger.exception(
                f"Alert dispatch failed for use case '{self.name}' stream ID '{stream_id}'"
            )

    def invoke(
        self,
        input_data: Any,
        stream_id: str = "default",
    ) -> Tuple[np.ndarray, Optional[UResult]]:
        """
        Invoke the use case on a single frame.

        This method is synchronous and **never blocks** on alert processing.

        Args:
            input_data: Input frame.
            stream_id: Unique identifier for the video stream.

        Returns:
            Annotated frame and result.
        """
        annotated_frame, result = self._run(input_data, stream_id=stream_id)

        if settings.notification_enabled:
            if self.alert_manager and result:
                # Fire-and-forget alert processing
                self._alert_executor.submit(
                    self._dispatch_alert,
                    stream_id,
                    input_data,
                    result,
                )

        return annotated_frame, result

    def __call__(
        self,
        input_data: Any,
        stream_id: str = "default",
    ) -> Tuple[np.ndarray, Optional[UResult]]:
        """
        Callable shortcut for invoke().

        Args:
            input_data: Input frame.
            stream_id: Stream identifier.

        Returns:
            Annotated frame and result.
        """
        return self.invoke(input_data, stream_id=stream_id)
