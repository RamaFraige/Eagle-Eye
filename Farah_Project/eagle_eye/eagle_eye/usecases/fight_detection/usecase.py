from dataclasses import dataclass
from typing import Any

from fight_detection import fight_pipeline
from fight_detection.backends import BaseFightBackend
from fight_detection.backends.torch import TorchFightBackend

from eagle_eye.core.alert.buffer.registry import VideoBufferRegistry
from eagle_eye.core.alert.manager import AlertManager
from eagle_eye.core.alert.notifier.providers.email import EmailNotificationProvider
from eagle_eye.core.alert.rules import ConfidenceRule, DetectionMatchRule
from eagle_eye.core.alert.severity import AlertSeverity
from eagle_eye.core.weight_utils import get_weight_path
from eagle_eye.usecases.base import UResult, UseCase


@dataclass
class FightDetection(UseCase):
    """
    Fight detection use case using the fight_detection package.
    """

    def __init__(self):
        super().__init__(name="fight-detection")
        # Initialize the backend once
        self.backend: BaseFightBackend = TorchFightBackend(
            yolo_model_path=get_weight_path("yolo", "yolo11n-pose.pt"),
            action_model_path=get_weight_path("torch", "action.pth"),
            confidence_threshold=self.confidence_threshold,
        )
        self._setup_alert_manager()

    def _setup_alert_manager(self):
        r1 = ConfidenceRule(
            min_confidence=self.confidence_threshold,
        )

        r2 = DetectionMatchRule(
            trigger_classes=["fight"],
        )

        self.alert_manager = AlertManager(
            name=self.name,
            rules=[r1, r2],
            notifier=EmailNotificationProvider(),
            buffers=VideoBufferRegistry(seconds=20, fps=10),
            clip_seconds=15,
            cooldown_sec=15,
            severity=AlertSeverity.CRITICAL,
        )

    def _predict(self, input_data: Any) -> Any:
        try:
            # Assuming pipeline/backend.process accepts a list of images
            generator = fight_pipeline(input_data, backend=self.backend)
            _, result = next(generator)
            return result
        except StopIteration:
            return None
        except Exception as e:
            # Fallback for robustness
            print(f"Error in FightDetection predict: {e}")
            return None

    def _draw(self, input_data: Any, prediction: Any) -> Any:
        try:
            return prediction.plot()
        except Exception:
            return input_data

    def _transform_prediction(self, prediction: Any) -> Any:
        """
        Transforms the prediction output.

        Args:
            prediction (Any): The prediction output.

        Returns:
            Any: The transformed prediction output.
        """
        if prediction is None:
            return None
        data: list = []
        data_type: str = "interactions"

        if len(prediction.interactions) == 0 and hasattr(prediction, "actions"):
            data = prediction.actions
            data_type = "actions"
        else:
            data = prediction.interactions

        data = {
            "detections": [
                {
                    "class_name": detection.label,
                    "confidence": detection.conf,
                    "bbox": [int(val) for val in detection.box],
                }
                for detection in data
            ],
            "detection_count": len(data),
            "data_type": data_type,
        }
        return UResult(**data)
