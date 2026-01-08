import os
import warnings

from eagle_eye.config.folder_manager import WEIGHTS_DIR

# Hide most TensorFlow messages: INFO, WARNING, ERROR
os.environ["TF_CPP_MIN_LOG_LEVEL"] = (
    "1"  # 0 = all, 1 = INFO, 2 = INFO+WARNING, 3 = INFO+WARNING+ERROR :contentReference[oaicite:0]{index=0}
)
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["DEEPFACE_HOME"] = str(WEIGHTS_DIR)


warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=Warning, module="tensorflow")
warnings.filterwarnings("ignore", category=DeprecationWarning)


def set_value():
    pass
