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

    app_data = Path(os.environ.get("PIXORA_DATA_DIR", Path.home() / ".pixora"))
    app_data.mkdir(parents=True, exist_ok=True)
    log_file = app_data / "pixora.log"

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler
    file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()

