import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler

from eagle_eye.config.settings import settings


def setup_logger():
    """Configure logging with Rich output, only for fastrtc, fastrtsp, and eagle_eye."""

    log_level = settings.LOG_LEVEL.upper()

    # Ensure logs directory exists
    logs_dir = Path("./logs")
    logs_dir.mkdir(exist_ok=True, parents=True)
    log_file_path = logs_dir / "app.log"

    # Console handler with Rich
    console_handler = RichHandler(rich_tracebacks=True, markup=True)
    console_formatter = logging.Formatter("%(message)s", datefmt="[%X]")
    console_handler.setFormatter(console_formatter)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file_path, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)

    # Only configure loggers for the libraries you want
    allowed_loggers = ["fastrtc", "fastrtsp", "eagle_eye"]

    for name in allowed_loggers:
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.propagate = False  # prevent logs from going to root logger

    # Suppress all other libraries
    logging.getLogger().setLevel("CRITICAL")  # root logger suppressed
