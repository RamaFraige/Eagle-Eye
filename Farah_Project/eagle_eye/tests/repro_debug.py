import numpy as np

from eagle_eye.usecases.base import UResult, UseCase
from eagle_eye.usecases.pipe import Pipeline


# Mock UseCase that overrides transformation
class MockUseCaseWithTransform(UseCase):
    def _predict(self, input_data):
        return "prediction"

    def _draw(self, input_data, prediction):
        return input_data

    def _transform_prediction(self, prediction):
        return UResult(object_count=1, detections=["det_with_transform"])


def test():
    try:
        mock = MockUseCaseWithTransform(name="with_transform")
        pipeline = Pipeline([mock], parallel=False)
        frame = np.zeros((10, 10, 3), dtype=np.uint8)

        print("Running pipeline...")
        result_frame, uresult = pipeline(frame)
        print("Pipeline result:", uresult)

        assert isinstance(uresult, UResult)
        assert uresult.object_count == 1
        assert uresult.detections == ["det_with_transform"]
        print("Success!")
    except Exception:
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test()
