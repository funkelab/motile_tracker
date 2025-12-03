"""Tests for log widget."""

from __future__ import annotations

from pathlib import Path

import pytest

from motile_tracker.widgets.log_widget import LogWidget, ansi_to_html


@pytest.fixture
def log_file(tmp_path: Path) -> Path:
    """Create a temporary log file with some content."""
    log_path = tmp_path / "test.log"
    log_path.write_text("Line 1\nLine 2\nLine 3\n")
    return log_path


class TestLogWidget:
    """Tests for LogWidget class."""

    def test_init_sets_readonly(self, log_file: Path, qtbot) -> None:
        """Test that the widget is read-only."""
        widget = LogWidget(log_file)
        qtbot.addWidget(widget)
        assert widget.isReadOnly()

    def test_displays_log_content(self, log_file: Path, qtbot) -> None:
        """Test that the widget displays log file content."""
        widget = LogWidget(log_file)
        qtbot.addWidget(widget)
        content = widget.toPlainText()
        assert "Line 1" in content
        assert "Line 2" in content
        assert "Line 3" in content

    def test_handles_missing_file(self, tmp_path: Path, qtbot) -> None:
        """Test that the widget handles missing log file gracefully."""
        missing_path = tmp_path / "nonexistent.log"
        widget = LogWidget(missing_path)
        qtbot.addWidget(widget)
        # Should not raise, content should be empty
        assert widget.toPlainText() == ""

    def test_respects_max_lines(self, tmp_path: Path, qtbot) -> None:
        """Test that the widget respects max_lines limit."""
        log_path = tmp_path / "test.log"
        # Write 10 lines
        lines = [f"Line {i}\n" for i in range(10)]
        log_path.write_text("".join(lines))

        # Create widget with max 3 lines
        widget = LogWidget(log_path, max_lines=3)
        qtbot.addWidget(widget)

        content = widget.toPlainText()
        # Should only have the last 3 lines
        assert "Line 7" in content
        assert "Line 8" in content
        assert "Line 9" in content
        assert "Line 0" not in content

    def test_timer_is_started(self, log_file: Path, qtbot) -> None:
        """Test that the update timer is started."""
        widget = LogWidget(log_file, refresh_ms=500)
        qtbot.addWidget(widget)
        assert widget.timer.isActive()
        assert widget.timer.interval() == 500

    def test_updates_on_file_change(self, log_file: Path, qtbot) -> None:
        """Test that the widget updates when the file changes."""
        widget = LogWidget(log_file, refresh_ms=100)
        qtbot.addWidget(widget)

        # Initial content check
        assert "Line 1" in widget.toPlainText()

        # Append to log file
        with open(log_file, "a") as f:
            f.write("New line\n")

        # Manually trigger update (instead of waiting for timer)
        widget._update_log()

        content = widget.toPlainText()
        assert "New line" in content


class TestAnsiToHtml:
    """Tests for ansi_to_html function."""

    def test_plain_text_unchanged(self) -> None:
        """Test that plain text without ANSI codes is unchanged (except escaping)."""
        result = ansi_to_html("Hello World")
        assert "Hello World" in result

    def test_escapes_html_characters(self) -> None:
        """Test that HTML special characters are escaped."""
        result = ansi_to_html("<script>alert('xss')</script>")
        assert "&lt;script&gt;" in result
        assert "<script>" not in result

    def test_converts_color_codes(self) -> None:
        """Test that ANSI color codes are converted to HTML spans."""
        # Red text
        result = ansi_to_html("\x1b[31mRed text\x1b[0m")
        assert "color:#cc0000" in result
        assert "Red text" in result

    def test_converts_bold(self) -> None:
        """Test that ANSI bold code is converted to HTML."""
        result = ansi_to_html("\x1b[1mBold text\x1b[0m")
        assert "font-weight:bold" in result
        assert "Bold text" in result

    def test_newlines_to_br(self) -> None:
        """Test that newlines are converted to <br> tags."""
        result = ansi_to_html("Line 1\nLine 2")
        assert "<br>" in result

    def test_strips_ansi_from_plain_text(self, tmp_path: Path, qtbot) -> None:
        """Test that ANSI codes don't appear as garbage in widget."""
        log_path = tmp_path / "test.log"
        log_path.write_text("\x1b[31mRed error\x1b[0m\n")

        widget = LogWidget(log_path)
        qtbot.addWidget(widget)

        content = widget.toPlainText()
        # Should see the text but not the escape codes
        assert "Red error" in content
        assert "\x1b" not in content
