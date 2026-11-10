"""Centralized logging for Pixora application."""
from __future__ import annotations

import logging
import os
from pathlib import Path


def setup_logger(name: str = "pixora") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # A restricted environment must not prevent Pixora from starting.  File
    # logging is a convenience; console logging remains available if the
    # per-user application directory cannot be created or written.
    try:
        app_data = Path(os.environ.get("PIXORA_DATA_DIR", Path.home() / ".pixora"))
        app_data.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(app_data / "pixora.log"), encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as error:
        logger.warning("File logging unavailable; continuing with console logging: %s", error)

    return logger


logger = setup_logger()

