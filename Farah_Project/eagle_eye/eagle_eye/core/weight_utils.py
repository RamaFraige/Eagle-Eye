from pathlib import Path

from eagle_eye.config.folder_manager import HOME_DIR


def get_weight_path(
    backend_name: str,
    file_name: str,
) -> Path:
    """
    Get the path to the pre-trained weights.
    Args:
        backend_name (str): name of the backend
        file_name (str): target file name with extension
    Returns
        target_file (str): exact path for the target file
    """
    home = HOME_DIR
    target_file = home / "weights" / file_name

    if target_file.exists():
        return target_file

    # Create the directory if it doesn't exist
    target_file.parent.mkdir(parents=True, exist_ok=True)
    return target_file
