from typing import Any, Dict, List, Literal

from .base import AlertRule


class ConfidenceRule(AlertRule):
    """
    Fires an alert based only on confidence values of detections.

    Does NOT care about class names.
    """

    def __init__(
        self,
        min_confidence: float,
        name: str = "Confidence",
        match_mode: Literal["any", "all"] = "any",
    ) -> None:
        """
        Initialize ConfidenceOnlyRule.

        Args:
            min_confidence: Minimum confidence threshold.
            name: Rule name (default: "Confidence").
            match_mode:
                - any: fire if any detection meets confidence
                - all: fire only if all detections meet confidence
        """
        self.name = name
        self.min_confidence = float(min_confidence)
        self.match_mode = match_mode

    def evaluate(self, result: Dict[str, Any], stream_id: str) -> bool:
        """
        Evaluate confidence-only rule.

        Args:
            result: Detection result dictionary.
            stream_id: Stream identifier (unused).

        Returns:
            True if confidence conditions are satisfied.
        """
        confidences = self._extract_confidences(result)

        if not confidences:
            return False

        if self.match_mode == "all":
            return all(conf >= self.min_confidence for conf in confidences)

        # any
        return any(conf >= self.min_confidence for conf in confidences)

    def _extract_confidences(self, result: Dict[str, Any]) -> List[float]:
        """
        Extract confidence values from result payload.

        Args:
            result: Detection result dictionary.

        Returns:
            List of confidence values.
        """
        confidences: List[float] = []

        for item in result.get("detections", []):
            conf = item.get("confidence")
            if conf is not None:
                confidences.append(float(conf))

        return confidences

    def cleanup(self, stream_id: str) -> None:
        """
        Stateless rule — nothing to clean.
        """
        return
