from typing import Any, Dict, Iterable, Literal, Mapping, Set

from .base import AlertRule


class DetectionMatchRule(AlertRule):
    """
    Fires an alert when specific class names are detected.

    Example:
        trigger_classes = ["fight"]
    """

    def __init__(
        self,
        trigger_classes: Iterable[str],
        name: str = "Match",
        method: Literal["includes", "exclude"] = "includes",
        match_mode: Literal["any", "all"] = "any",
    ) -> None:
        """
        Initialize the rule.

        Args:
            trigger_classes: List of class names that trigger the alert.
            name: Rule name (default: "Match").
            method:
                - "includes": fire if any class is detected
                - "exclude": fire if any class is NOT detected
            match_mode:
                - "any": fire if any class is detected
                - "all": fire only if all classes are detected
        """
        self.name = name
        self.method = method
        self.match_mode = match_mode

        # Normalize class names (case-insensitive)
        self.trigger_classes: Set[str] = {
            cls.strip().lower() for cls in trigger_classes
        }

    def evaluate(self, result: Dict[str, Any], stream_id: str) -> bool:
        """
        Evaluate whether the rule should fire.

        Args:
            result: Detection result dictionary.
            stream_id: Stream identifier (not used, stateless rule).

        Returns:
            True if rule conditions are satisfied.
        """
        detected_classes = self._extract_detected_classes(result)
        if not detected_classes and self.method == "includes":
            return False  # nothing detected to include

        # --- INCLUDE mode ---
        if self.method == "includes":
            if self.match_mode == "all":
                return self.trigger_classes.issubset(detected_classes)
            return bool(self.trigger_classes & detected_classes)  # any

        # --- EXCLUDE mode ---
        if self.method == "exclude":
            if self.match_mode == "all":
                # Fire if all trigger_classes are NOT in detected_classes
                return self.trigger_classes.isdisjoint(detected_classes)
            # any: fire if NONE of the trigger_classes are detected
            return not bool(self.trigger_classes & detected_classes)

        # fallback (should not happen)
        return False

    def _extract_detected_classes(self, result: Dict[str, Any]) -> Set[str]:
        """
        Extract detected class names from result payload.

        Supports:
        - detections[].class_name
        - detected_<CLASS_NAME> = true

        Args:
            result: Detection result dictionary.

        Returns:
            Set of detected class names (lowercase).
        """
        detected: Set[str] = set()

        # From detections list
        detections = result.get("detections", [])
        for item in detections:
            class_name = item.get("class_name")
            if class_name:
                detected.add(class_name.lower())

        # From detected_<class> boolean flags
        for key, value in result.items():
            if key.startswith("detected_") and value is True:
                detected.add(key.replace("detected_", "").lower())

        return detected

    def cleanup(self, stream_id: str) -> None:
        """
        Stateless rule — nothing to clean.
        """
        return


class DetectionMatchConfidenceRule(AlertRule):
    """
    Fires an alert when specified classes are detected
    with required confidence thresholds.

    Example:
        {
            "WALK": 0.6,
            "fight": 0.8
        }
    """

    def __init__(
        self,
        class_confidence_map: Mapping[str, float],
        name: str = "Match_Confidence",
        method: Literal["includes", "exclude"] = "includes",
        match_mode: Literal["any", "all"] = "any",
    ) -> None:
        """
        Initialize the DetectionMatchConfidenceRule.

        Args:
            class_confidence_map:
                Mapping of class_name -> minimum confidence.
            name: Rule name (default: "Match_Confidence").
            method:
                - "includes": fire if any class meets confidence
                - "exclude": fire if any class does NOT meet confidence
            match_mode:
                - "any": fire if any class meets confidence
                - "all": fire only if all classes meet confidence
        """
        self.name = name
        self.method = method
        self.match_mode = match_mode

        # Normalize class names
        self.class_confidence_map: Dict[str, float] = {
            cls.lower(): float(conf) for cls, conf in class_confidence_map.items()
        }

    def evaluate(self, result: Dict[str, Any], stream_id: str) -> bool:
        """
        Evaluate rule against detection result.

        Args:
            result: Detection result dictionary.
            stream_id: Stream identifier (unused).

        Returns:
            True if rule conditions are satisfied.
        """
        satisfied_classes = self._extract_satisfied_classes(result)

        # --- INCLUDE mode ---
        if self.method == "includes":
            if not satisfied_classes:
                return False
            if self.match_mode == "all":
                return set(self.class_confidence_map).issubset(satisfied_classes)
            return bool(set(self.class_confidence_map) & satisfied_classes)

        # --- EXCLUDE mode ---
        if self.method == "exclude":
            if self.match_mode == "all":
                # Fire if none of the trigger classes are detected
                return set(self.class_confidence_map).isdisjoint(satisfied_classes)
            # any: fire if NONE of the trigger classes are satisfied
            return not bool(set(self.class_confidence_map) & satisfied_classes)

        # fallback (should not happen)
        return False

    def _extract_satisfied_classes(
        self,
        result: Dict[str, Any],
    ) -> Set[str]:
        """
        Extract classes that satisfy confidence conditions.

        Args:
            result: Detection result dictionary.

        Returns:
            Set of class names that passed confidence threshold.
        """
        satisfied: Set[str] = set()

        # From detections list
        detections = result.get("detections", [])
        for item in detections:
            class_name = item.get("class_name")
            confidence = item.get("confidence")

            if not class_name or confidence is None:
                continue

            cls = class_name.lower()
            required_conf = self.class_confidence_map.get(cls)

            if required_conf is None:
                continue

            if float(confidence) >= required_conf:
                satisfied.add(cls)

        # Fallback: detected_<CLASS> boolean
        for cls, required_conf in self.class_confidence_map.items():
            flag = f"detected_{cls}"
            if result.get(flag) is True:
                satisfied.add(cls)

        return satisfied

    def cleanup(self, stream_id: str) -> None:
        """
        Stateless rule — nothing to clean.
        """
        return
