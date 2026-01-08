import hashlib
from functools import partial
from typing import Callable, Dict, Literal

from .base import UseCase
from .face_recognition import FaceRecognition
from .fight_detection import FightDetection
from .object_detection import ObjectDetection

USE_CASES: Dict[str, Callable[[], UseCase]] = {
    "face-detection": partial(FaceRecognition),
    "fight-detection": partial(FightDetection),
    "guns-detection": partial(ObjectDetection, model_name="guns11n.pt"),
}

# UseCase Literal
USE_CASES_LITERAL = Literal[*USE_CASES.keys()]


def get_use_case_color(name: str) -> str:
    """
    Get a deterministic hex color for a use case based on its name.
    """
    if name not in USE_CASES:
        raise ValueError(
            f"Unknown use case: {name}. Available: {list(USE_CASES.keys())}"
        )

    digest = hashlib.md5(name.encode("utf-8")).digest()
    r, g, b = digest[0], digest[1], digest[2]

    return f"#{r:02x}{g:02x}{b:02x}"
