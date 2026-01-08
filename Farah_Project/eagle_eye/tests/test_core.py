import numpy as np
import pytest

from eagle_eye.usecases.base import UResult, UseCase
from eagle_eye.usecases.pipe import Pipeline


# Mock UseCase that overrides transformation
class MockUseCaseWithTransform(UseCase):
    def _predict(self, input_data):
        return "prediction"

    def _draw(self, input_data, prediction):
        return input_data

    def _transform_prediction(self, prediction):
        # Returning a UResult to test accumulation
        return UResult(object_count=1, detections=["det_with_transform"])


# Mock UseCase that DOES NOT override transformation
class MockUseCaseNoTransform(UseCase):
    def _predict(self, input_data):
        return "prediction"

    def _draw(self, input_data, prediction):
        return input_data


@pytest.fixture
def mock_use_case_with_transform():
    return MockUseCaseWithTransform(name="with_transform")


@pytest.fixture
def mock_use_case_no_transform():
    return MockUseCaseNoTransform(name="no_transform")


def test_pipeline_process_sequential_with_transform(mock_use_case_with_transform):
    pipeline = Pipeline([mock_use_case_with_transform])
    frame = np.zeros((10, 10, 3), dtype=np.uint8)

    result_frame, uresult = pipeline(frame)

    assert isinstance(uresult, UResult)
    # Since transformation IS overridden, we expect results
    assert uresult.object_count == 1
    assert uresult.detections == ["det_with_transform"]


def test_get_weight_path(tmp_path):
    from unittest.mock import patch

    from eagle_eye.core.weight_utils import get_weight_path

    # Mock HOME_DIR to be our temporary path
    with patch("eagle_eye.core.weight_utils.HOME_DIR", tmp_path):
        # Case 1: Directory creation
        target = get_weight_path("backend", "model.h5")

        expected_path = tmp_path / "weights" / "model.h5"
        assert target == expected_path
        assert expected_path.parent.exists()

        # Case 2: Existing file (logic check)
        # Create the file
        expected_path.touch()
        target_existing = get_weight_path("backend", "model.h5")
        assert target_existing == expected_path
