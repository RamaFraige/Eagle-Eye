import shutil
from pathlib import Path

from eagle_eye.config.folder_manager import WEIGHTS_DIR

# Project-local models directory
ROOT_DIR = Path("./checkpoints")

# Collect all model files (recursively)
MODELS_PATH: list[Path] = [p for p in ROOT_DIR.rglob("*") if p.is_file()]

for model_path in MODELS_PATH:
    shutil.copy(model_path, WEIGHTS_DIR)
