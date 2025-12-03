"""Log widget for displaying application logs."""

from __future__ import annotations

import html
import re
from pathlib import Path

from qtpy.QtCore import QTimer
from qtpy.QtGui import QFont
from qtpy.QtWidgets import QTextEdit

# ANSI color code to HTML color mapping
ANSI_COLORS = {
    "30": "#000000",  # Black
    "31": "#cc0000",  # Red
    "32": "#00cc00",  # Green
    "33": "#cccc00",  # Yellow
    "34": "#0000cc",  # Blue
    "35": "#cc00cc",  # Magenta
    "36": "#00cccc",  # Cyan
    "37": "#cccccc",  # White
    "90": "#666666",  # Bright Black (Gray)
    "91": "#ff0000",  # Bright Red
    "92": "#00ff00",  # Bright Green
    "93": "#ffff00",  # Bright Yellow
    "94": "#0000ff",  # Bright Blue
    "95": "#ff00ff",  # Bright Magenta
    "96": "#00ffff",  # Bright Cyan
    "97": "#ffffff",  # Bright White
}

# Regex to match ANSI escape codes
ANSI_PATTERN = re.compile(r"\x1b\[([0-9;]*)m")


def ansi_to_html(text: str) -> str:
    """Convert ANSI escape codes to HTML spans."""
    # Escape HTML special characters first
    text = html.escape(text)

    result = []
    last_end = 0
    open_spans = 0

    for match in ANSI_PATTERN.finditer(text):
        # Add text before this match
        result.append(text[last_end : match.start()])

        codes = match.group(1).split(";")
        for code in codes:
            if code == "0" or code == "":
                # Reset - close all open spans
                result.append("</span>" * open_spans)
                open_spans = 0
            elif code == "1":
                # Bold
                result.append("<span style='font-weight:bold'>")
                open_spans += 1
            elif code in ANSI_COLORS:
                result.append(f"<span style='color:{ANSI_COLORS[code]}'>")
                open_spans += 1

        last_end = match.end()

    # Add remaining text
    result.append(text[last_end:])
    # Close any remaining open spans
    result.append("</span>" * open_spans)

    # Convert newlines to <br> for HTML
    return "".join(result).replace("\n", "<br>")


class LogWidget(QTextEdit):
    """Widget that displays the last N lines of a log file with ANSI color support."""

    def __init__(
        self, log_path: Path, max_lines: int = 500, refresh_ms: int = 1000
    ) -> None:
        super().__init__()
        self.log_path = log_path
        self.max_lines = max_lines
        self.setReadOnly(True)

        # Use monospace font
        font = QFont("Menlo, Monaco, Courier New, monospace")
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        self.timer = QTimer(self)  # Parent to widget to ensure it stays alive
        self.timer.timeout.connect(self._update_log)
        self.timer.start(refresh_ms)

        self._update_log()  # Initial load

    def _update_log(self) -> None:
        """Read and display the last N lines of the log file."""
        if not self.log_path.exists():
            return

        try:
            with open(self.log_path, encoding="utf-8") as f:
                lines = f.readlines()
                tail = (
                    lines[-self.max_lines :] if len(lines) > self.max_lines else lines
                )
                text = "".join(tail)
                self.setHtml(f"<pre style='margin:0'>{ansi_to_html(text)}</pre>")
                self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        except OSError:
            pass  # Ignore read errors (file in use, permissions, etc.)


def show_log_window() -> LogWidget:
    """Return a LogWidget for use as a napari dock widget."""
    from motile_tracker.utils.logging import get_log_path

    return LogWidget(get_log_path())
