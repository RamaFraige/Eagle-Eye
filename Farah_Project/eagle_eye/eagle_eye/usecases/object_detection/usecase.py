import logging
from dataclasses import dataclass
from typing import Any, Optional

from ultralytics import YOLO

from eagle_eye.core.alert.buffer.registry import VideoBufferRegistry
from eagle_eye.core.alert.manager import AlertManager
from eagle_eye.core.alert.notifier.providers.email import EmailNotificationProvider
from eagle_eye.core.alert.rules import ConfidenceRule
from eagle_eye.core.alert.severity import AlertSeverity
from eagle_eye.core.weight_utils import get_weight_path
from eagle_eye.usecases.base import UResult, UseCase

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class ObjectDetection(UseCase):
    """Object detection use case using YOLO and Ultralytics colors."""

    model: Optional[YOLO] = None

    def __init__(
        self, model_name: str, severity: Optional[AlertSeverity] = AlertSeverity.MEDIUM
    ):
        super().__init__(name="object-detection")
        self.model_name = model_name
        self.severity = severity
        self._setup_alert_manager()

    def __load_model(self):
        model_path = get_weight_path("yolo", self.model_name)
        self.model = YOLO(model_path)

    def _setup_alert_manager(self):
        r1 = ConfidenceRule(
            min_confidence=self.confidence_threshold,
        )

        self.alert_manager = AlertManager(
            name=f"{self.name}_{self.model_name.replace('.pt', '')}",
            rules=[r1],
            notifier=EmailNotificationProvider(),
            buffers=VideoBufferRegistry(seconds=20, fps=10),
            clip_seconds=15,
            cooldown_sec=15,
        )

    def _predict(self, input_data: Any) -> Any:
        if self.model is None:
            self.__load_model()
        # YOLO prediction
        results = self.model.predict(
            input_data, verbose=False, conf=self.confidence_threshold
        )
        return results[0]

    def _draw(self, input_data: Any, prediction: Any) -> Any:
        # Plot results on the frame
        return prediction.plot(img=input_data)

    def _transform_prediction(self, prediction: Any) -> Any:
        """
        Transforms the prediction output.

        Args:
            prediction (Any): The prediction output.

        Returns:
            Any: The transformed prediction output.
        """
        data = {
            "detections": [
                {
                    "class_name": prediction.names[int(box.cls)],
                    "confidence": float(box.conf),
                    "bbox": [int(val) for val in box.xyxy[0].tolist()],
                }
                for box in prediction.boxes
            ],
            "detection_count": len(prediction.boxes),
        }
        return UResult(**data)
