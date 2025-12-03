"""Logging utilities for motile-tracker."""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TextIO

from appdirs import AppDirs


class TeeStream:
    """Stream that writes to both the original stream and a file."""

    def __init__(self, original: TextIO | None, file: TextIO):
        self.original = original
        self.file = file

    def write(self, text: str) -> int:
        """Write text to both original stream and file."""
        if self.original:
            self.original.write(text)
        self.file.write(text)
        self.file.flush()
        return len(text)

    def flush(self) -> None:
        """Flush both streams."""
        if self.original:
            self.original.flush()
        self.file.flush()

    def isatty(self) -> bool:
        """Return whether the original stream is a tty."""
        if self.original:
            return self.original.isatty()
        return False

    def fileno(self) -> int:
        """Return the file descriptor of the original stream."""
        if self.original:
            return self.original.fileno()
        raise OSError("No file descriptor available")


def get_log_path() -> Path:
    """Get the path to the log file."""
    appdir = AppDirs("motile-tracker")
    log_dir = Path(appdir.user_log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "motile_tracker.log"


def setup_logging() -> Path:
    """Set up logging to file with tee to original stdout/stderr.

    Adds a rotating file handler to the root logger (doesn't call basicConfig
    so napari's -v flag can control log level). Also redirects stdout/stderr
    to write to the log file.

    Returns:
        Path to the log file.
    """
    log_path = get_log_path()
    log_file = open(log_path, "a", encoding="utf-8")  # noqa: SIM115

    # Set root logger to INFO level
    logging.root.setLevel(logging.INFO)

    # Add rotating file handler to root logger
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logging.root.addHandler(file_handler)

    # Log startup banner for visual separation between runs
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info(
        "Motile Tracker started at %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    logger.info("Log file: %s", log_path)
    logger.info("=" * 80)

    # Also tee stdout/stderr to capture print statements and tqdm
    sys.stdout = TeeStream(sys.stdout, log_file)  # type: ignore[assignment]
    sys.stderr = TeeStream(sys.stderr, log_file)  # type: ignore[assignment]

    return log_path
