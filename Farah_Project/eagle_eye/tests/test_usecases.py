from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from eagle_eye.usecases.base import UResult, UseCase

# -------------------------
# Concrete implementation
# -------------------------


class ConcreteUseCase(UseCase):
    def _predict(self, input_data):
        return "prediction"

    def _draw(self, input_data, prediction):
        # For test purposes, just return the input
        return input_data


class ResultUseCase(ConcreteUseCase):
    """Returns a UResult via _transform_prediction."""

    def _transform_prediction(self, prediction):
        return UResult(object_count=1, detections=[prediction])


# -------------------------
# Fixtures
# -------------------------


@pytest.fixture
def dummy_frame():
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture
def use_case():
    return ConcreteUseCase(name="test-usecase")


@pytest.fixture
def result_use_case():
    return ResultUseCase(name="result-usecase")


@pytest.fixture
def alert_manager():
    manager = MagicMock()
    manager.process = MagicMock()
    return manager


# -------------------------
# Tests: UResult
# -------------------------


def test_uresult_addition():
    r1 = UResult(object_count=1, detections=["a"])
    r2 = UResult(object_count=2, detections=["b", "c"])

    r1 += r2

    assert r1.object_count == 3
    assert r1.detections == ["a", "b", "c"]


def test_uresult_addition_invalid_type():
    r = UResult()
    with pytest.raises(TypeError):
        r += "invalid"


# -------------------------
# Tests: _run pipeline
# -------------------------


def test_run_without_transformed_result(use_case, dummy_frame):
    frame, result = use_case._run(dummy_frame, stream_id="s1")

    assert np.array_equal(frame, dummy_frame)
    assert result is None


def test_run_with_transformed_result(result_use_case, dummy_frame):
    frame, result = result_use_case._run(dummy_frame, stream_id="s1")

    assert np.array_equal(frame, dummy_frame)
    assert isinstance(result, UResult)
    assert result.object_count == 1
    assert result.detections == ["prediction"]


# -------------------------
# Tests: invoke()
# -------------------------


def test_invoke_returns_frame_and_none(use_case, dummy_frame):
    frame, result = use_case.invoke(dummy_frame)

    assert np.array_equal(frame, dummy_frame)
    assert result is None


def test_call_is_alias_for_invoke(use_case, dummy_frame):
    frame1, result1 = use_case.invoke(dummy_frame)
    frame2, result2 = use_case(dummy_frame)

    assert np.array_equal(frame1, frame2)
    assert result1 == result2


# -------------------------
# Tests: alert dispatch logic
# -------------------------


def test_alert_not_triggered_when_notifications_disabled(
    result_use_case,
    dummy_frame,
    alert_manager,
):
    result_use_case.alert_manager = alert_manager

    with (
        patch("eagle_eye.usecases.base.settings.GMAIL_USER", ""),
        patch("eagle_eye.usecases.base.settings.GMAIL_PASSWORD", ""),
    ):
        frame, result = result_use_case.invoke(dummy_frame)

    assert result is not None
    alert_manager.process.assert_not_called()


def test_alert_triggered_when_enabled(
    result_use_case,
    dummy_frame,
    alert_manager,
):
    result_use_case.alert_manager = alert_manager

    # Force executor to run immediately
    def immediate_submit(fn, *args, **kwargs):
        fn(*args, **kwargs)

    with (
        patch("eagle_eye.usecases.base.settings.GMAIL_USER", "TEST_USER"),
        patch("eagle_eye.usecases.base.settings.GMAIL_PASSWORD", "TEST_PASSWORD"),
        patch.object(
            result_use_case._alert_executor,
            "submit",
            side_effect=immediate_submit,
        ),
    ):
        frame, result = result_use_case.invoke(dummy_frame, stream_id="stream-1")

    alert_manager.process.assert_called_once()

    args, kwargs = alert_manager.process.call_args
    stream_id, frame_bytes, metadata = args

    assert stream_id == "stream-1"
    assert isinstance(frame_bytes, bytes)
    assert metadata["object_count"] == 1


def test_alert_not_triggered_without_result(
    use_case,
    dummy_frame,
    alert_manager,
):
    use_case.alert_manager = alert_manager

    with (
        patch("eagle_eye.usecases.base.settings.GMAIL_USER", "TEST_USER"),
        patch("eagle_eye.usecases.base.settings.GMAIL_PASSWORD", "TEST_PASSWORD"),
    ):
        frame, result = use_case.invoke(dummy_frame)

    assert result is None
    alert_manager.process.assert_not_called()


# -------------------------
# Tests: robustness
# -------------------------


def test_dispatch_alert_handles_encoding_failure(
    result_use_case,
    dummy_frame,
    alert_manager,
):
    result_use_case.alert_manager = alert_manager

    with patch("cv2.imencode", return_value=(False, None)):
        result_use_case._dispatch_alert(
            stream_id="s1",
            frame=dummy_frame,
            result=UResult(object_count=1),
        )

    alert_manager.process.assert_not_called()


def test_dispatch_alert_exception_is_caught(
    result_use_case,
    dummy_frame,
    alert_manager,
):
    alert_manager.process.side_effect = RuntimeError("boom")
    result_use_case.alert_manager = alert_manager

    # Should not raise
    result_use_case._dispatch_alert(
        stream_id="s1",
        frame=dummy_frame,
        result=UResult(object_count=1),
    )
