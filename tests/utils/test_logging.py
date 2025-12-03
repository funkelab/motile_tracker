"""Tests for logging utilities."""

from __future__ import annotations

import logging
import sys
from io import StringIO
from pathlib import Path

from motile_tracker.utils.logging import TeeStream, get_log_path, setup_logging


class TestTeeStream:
    """Tests for TeeStream class."""

    def test_write_to_both_streams(self, tmp_path: Path) -> None:
        """Test that TeeStream writes to both original and file streams."""
        original = StringIO()
        log_file = tmp_path / "test.log"

        with open(log_file, "w") as f:
            tee = TeeStream(original, f)
            tee.write("Hello, World!")
            tee.flush()

        assert original.getvalue() == "Hello, World!"
        assert log_file.read_text() == "Hello, World!"

    def test_write_with_none_original(self, tmp_path: Path) -> None:
        """Test that TeeStream works when original is None."""
        log_file = tmp_path / "test.log"

        with open(log_file, "w") as f:
            tee = TeeStream(None, f)
            tee.write("Hello, World!")
            tee.flush()

        assert log_file.read_text() == "Hello, World!"

    def test_write_returns_length(self, tmp_path: Path) -> None:
        """Test that write returns the length of the text."""
        log_file = tmp_path / "test.log"

        with open(log_file, "w") as f:
            tee = TeeStream(StringIO(), f)
            result = tee.write("Hello")

        assert result == 5

    def test_flush_both_streams(self, tmp_path: Path) -> None:
        """Test that flush is called on both streams."""
        original = StringIO()
        log_file = tmp_path / "test.log"

        with open(log_file, "w") as f:
            tee = TeeStream(original, f)
            tee.write("test")
            tee.flush()
            # If we get here without error, flush worked

    def test_flush_with_none_original(self, tmp_path: Path) -> None:
        """Test that flush works when original is None."""
        log_file = tmp_path / "test.log"

        with open(log_file, "w") as f:
            tee = TeeStream(None, f)
            tee.flush()
            # If we get here without error, flush worked


class TestGetLogPath:
    """Tests for get_log_path function."""

    def test_returns_path(self) -> None:
        """Test that get_log_path returns a Path object."""
        result = get_log_path()
        assert isinstance(result, Path)

    def test_path_has_log_filename(self) -> None:
        """Test that the log path has the expected filename."""
        result = get_log_path()
        assert result.name == "motile_tracker.log"

    def test_creates_parent_directory(self) -> None:
        """Test that get_log_path creates the parent directory."""
        result = get_log_path()
        assert result.parent.exists()


class TestSetupLogging:
    """Tests for setup_logging function."""

    def _cleanup_logging(
        self, original_stdout, original_stderr, original_handlers
    ) -> None:
        """Restore original streams and logging handlers."""
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        # Remove any handlers that were added
        for handler in logging.root.handlers[:]:
            if handler not in original_handlers:
                logging.root.removeHandler(handler)
                handler.close()

    def test_returns_log_path(self) -> None:
        """Test that setup_logging returns the log path."""
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        original_handlers = logging.root.handlers[:]

        try:
            result = setup_logging()
            assert isinstance(result, Path)
            assert result.name == "motile_tracker.log"
        finally:
            self._cleanup_logging(original_stdout, original_stderr, original_handlers)

    def test_replaces_stdout_and_stderr(self) -> None:
        """Test that setup_logging replaces stdout and stderr with TeeStreams."""
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        original_handlers = logging.root.handlers[:]

        try:
            setup_logging()
            assert isinstance(sys.stdout, TeeStream)
            assert isinstance(sys.stderr, TeeStream)
        finally:
            self._cleanup_logging(original_stdout, original_stderr, original_handlers)

    def test_writes_to_log_file(self) -> None:
        """Test that output is written to the log file."""
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        original_handlers = logging.root.handlers[:]

        try:
            log_path = setup_logging()

            # Write something to stdout
            test_message = "Test message for logging"
            print(test_message)

            # Flush to ensure it's written
            sys.stdout.flush()

            # Check the log file
            log_content = log_path.read_text()
            assert test_message in log_content
        finally:
            self._cleanup_logging(original_stdout, original_stderr, original_handlers)

    def test_logs_startup_banner(self) -> None:
        """Test that setup_logging logs a startup banner."""
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        original_handlers = logging.root.handlers[:]

        try:
            log_path = setup_logging()

            # Check the log file contains startup banner
            log_content = log_path.read_text()
            assert "=" * 80 in log_content
            assert "Motile Tracker started at" in log_content
        finally:
            self._cleanup_logging(original_stdout, original_stderr, original_handlers)

    def test_adds_file_handler_to_root_logger(self) -> None:
        """Test that setup_logging adds a file handler to the root logger."""
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        original_handlers = logging.root.handlers[:]

        try:
            setup_logging()

            # Check that a new handler was added
            assert len(logging.root.handlers) > len(original_handlers)
        finally:
            self._cleanup_logging(original_stdout, original_stderr, original_handlers)
