import logging
from functools import lru_cache
from typing import Any, List, Tuple

import numpy as np

from eagle_eye.core.alert.manager import AlertManagerGroup
from eagle_eye.usecases import USE_CASES
from eagle_eye.usecases.base import UResult, UseCase

logger = logging.getLogger(__name__)


class Pipeline(UseCase):
    """
    Pipeline UseCase that runs multiple UseCases.
    """

    def __init__(
        self,
        use_cases: List[UseCase],
        name: str = "pipeline",
    ) -> None:
        super().__init__(name=name)
        self.use_cases = use_cases
        self._setup_alert_manager()

    def _setup_alert_manager(self):
        self.alert_manager = AlertManagerGroup(
            managers=[uc.alert_manager for uc in self.use_cases if uc.alert_manager]
        )

    def _predict(self, input_data: np.ndarray) -> List[Tuple[UseCase, Any]]:
        """
        Run predictions for all use cases.

        Returns:
            List of (UseCase, raw_prediction)
        """

        return [uc._predict(input_data) for uc in self.use_cases]

    def _draw(
        self,
        input_data: np.ndarray,
        predictions: List[Tuple[UseCase, Any]],
    ) -> np.ndarray:
        """
        Draw predictions sequentially and aggregate UResult.

        Args:
            input_data: Original frame
            predictions: Output from _predict()

        Returns:
            Annotated frame
        """
        annotated_frame = input_data.copy()

        for use_case, prediction in zip(self.use_cases, predictions):
            annotated_frame = use_case._draw(annotated_frame, prediction)

        return annotated_frame

    def _transform_prediction(self, prediction: Any) -> Any:
        """
        Transform prediction from _predict() to UResult.

        Args:
            prediction: Output from _predict()

        Returns:
            UResult
        """

        result = UResult()

        for use_case, prediction in zip(self.use_cases, prediction):
            if prediction is not None:
                result += use_case._transform_prediction(prediction)

        return result


@lru_cache(maxsize=32)
def build_pipeline(
    use_case_names: Tuple[str, ...],
) -> Pipeline:
    """
    Build (and cache) a Pipeline instance.

    Args:
        use_case_names: Tuple of use case names (hashable).

    Returns:
        Cached Pipeline instance.
    """
    use_cases: List[UseCase] = []

    for name in use_case_names:
        if name not in USE_CASES:
            logger.warning("Use case '%s' not found.", name)
            continue
        # Create instance of each use case
        use_cases.append(USE_CASES[name]())

    return Pipeline(use_cases=use_cases)
