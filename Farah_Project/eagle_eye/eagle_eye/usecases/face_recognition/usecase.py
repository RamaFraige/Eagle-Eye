import logging
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np
from deepface import DeepFace

from eagle_eye.core.alert.buffer.registry import VideoBufferRegistry
from eagle_eye.core.alert.manager import AlertManager
from eagle_eye.core.alert.notifier.providers.email import EmailNotificationProvider
from eagle_eye.core.alert.rules import ConfidenceRule, DetectionMatchRule
from eagle_eye.core.alert.severity import AlertSeverity
from eagle_eye.database.vector import face_db
from eagle_eye.usecases.base import UResult, UseCase

logger = logging.getLogger(__name__)


@dataclass
class FaceRecognition(UseCase):
    """Face recognition use case using DeepFace and FAISS."""

    def __init__(self):
        super().__init__(name="face-recognition")
        self._setup_alert_manager()

    def _setup_alert_manager(self):
        r1 = ConfidenceRule(
            min_confidence=self.confidence_threshold,
        )

        r2 = DetectionMatchRule(
            trigger_classes=["unknown"],
            method="exclude",
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
            # Detect faces
            # extract_faces returns a list of dicts with 'face', 'facial_area', 'confidence'
            faces = DeepFace.extract_faces(
                img_path=input_data,
                detector_backend="opencv",
                enforce_detection=False,
                align=False,
            )

            # Flitter the faces with confidence >= threshold
            faces = [
                face
                for face in faces
                if face["confidence"] >= self.confidence_threshold
            ]

            results = []
            for face_obj in faces:
                name = "Unknown"
                similarity = face_obj["confidence"]

                try:
                    # Prepare face image for representation
                    face_img = face_obj["face"]
                    # extract_faces returns RGB float [0,1]. Convert to BGR uint8 [0,255]
                    face_uint8 = (face_img * 255).astype(np.uint8)
                    face_bgr = cv2.cvtColor(face_uint8, cv2.COLOR_RGB2BGR)

                    # Get embedding for the cropped face
                    emb_objs = DeepFace.represent(
                        img_path=face_bgr,
                        model_name=face_db.model_name,
                        enforce_detection=False,
                    )

                    if emb_objs:
                        embedding = emb_objs[0]["embedding"]
                        vector = np.array([embedding], dtype="float32")

                        # Search in DB
                        result = face_db.search(
                            vector, threshold=self.confidence_threshold
                        )
                        if result:
                            name, similarity = result

                except Exception as e:
                    logger.warning(f"Recognition failed for a face: {e}")

                face_obj["name"] = name
                face_obj["similarity"] = similarity

                results.append(face_obj)

            return results
        except Exception as e:
            logger.error(f"Face recognition error: {e}")
            return []

    def _draw(self, input_data: Any, prediction: Any) -> Any:
        frame = input_data.copy()
        for face_obj in prediction:
            facial_area = face_obj.get("facial_area")
            name = face_obj.get("name", "Unknown")
            text = f"{name}: {face_obj['similarity']:.2f}"

            if facial_area:
                x = facial_area["x"]
                y = facial_area["y"]
                w = facial_area["w"]
                h = facial_area["h"]

                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)

                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(
                    frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2
                )
        return frame

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
                    "class_name": face_obj["name"],
                    "confidence": float(face_obj["similarity"]),
                    "bbox": [
                        face_obj["facial_area"]["x"],
                        face_obj["facial_area"]["y"],
                        face_obj["facial_area"]["w"],
                        face_obj["facial_area"]["h"],
                    ],
                }
                for face_obj in prediction
            ],
            "detection_count": len(prediction),
        }
        return UResult(**data)
