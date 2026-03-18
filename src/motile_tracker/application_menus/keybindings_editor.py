"""Popup dialog for viewing and editing keybindings."""

from __future__ import annotations

from qtpy.QtCore import Qt
from qtpy.QtGui import QKeyEvent, QMouseEvent
from qtpy.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from motile_tracker.data_views.key_bindable import (
    qt_key_to_string,
    qt_mouse_to_string,
)
from motile_tracker.data_views.keybindings_manager import KeybindingsManager

ACTION_DISPLAY_NAMES: dict[str, str] = {
    "delete_node": "Delete Node",
    "create_edge": "Add Edge",
    "delete_edge": "Break Edge",
    "swap_nodes": "Swap Nodes",
    "undo": "Undo",
    "redo": "Redo",
    "deselect": "Deselect",
    "restore_selection": "Restore Selection",
    "hide_panels": "Hide Panels",
    "toggle_display_mode": "Toggle Display Mode",
    "toggle_feature_mode": "Toggle Feature Mode",
    "flip_axes": "Flip Axes",
    "navigate_left": "Navigate Left",
    "navigate_right": "Navigate Right",
    "navigate_up": "Navigate Up",
    "navigate_down": "Navigate Down",
    "zoom_constrain_x": "Zoom Constrain X",
    "zoom_constrain_y": "Zoom Constrain Y",
}


def _context_label(targets: list[str]) -> str:
    if "tree_widget" in targets and "tracks_viewer" not in targets:
        return "Tree only"
    return "All"


class KeyCaptureWidget(QLineEdit):
    """Line edit that captures the next key/mouse press as a keybinding string.

    Signals are emitted via *captured* (str) and *cancelled* (no args).
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("Press a key...")
        self.setAlignment(Qt.AlignCenter)
        self.captured_key: str | None = None

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()

        # Escape cancels
        if key == Qt.Key_Escape:
            self.captured_key = None
            self.clearFocus()
            return

        # Backspace / Delete clears the binding
        if key in (Qt.Key_Backspace, Qt.Key_Delete):
            self.captured_key = ""
            self.setText("")
            self.clearFocus()
            return

        key_str = qt_key_to_string(event)
        if key_str is not None:
            self.captured_key = key_str
            self.setText(key_str)
            self.clearFocus()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        key_str = qt_mouse_to_string(event)
        if key_str is not None:
            self.captured_key = key_str
            self.setText(key_str)
            self.clearFocus()
            return
        super().mousePressEvent(event)


# Column indices
COL_ACTION = 0
COL_KEY1 = 1
COL_KEY2 = 2
COL_CONTEXT = 3
COL_RESET = 4


class KeybindingsDialog(QDialog):
    """Modal dialog for editing keybindings."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Keybindings")
        self.setMinimumSize(600, 500)
        self._mgr = KeybindingsManager.get_instance()

        # Ordered list of actions (consistent display order)
        self._actions = list(self._mgr.keybindings.keys())

        # --- layout ---
        layout = QVBoxLayout(self)

        info = QLabel(
            "Double-click a key cell to capture a new shortcut. "
            "Press Backspace to clear. Press Escape to cancel."
        )
        info.setWordWrap(True)
        font = info.font()
        font.setItalic(True)
        info.setFont(font)
        layout.addWidget(info)

        self._table = QTableWidget(len(self._actions), 5)
        self._table.setHorizontalHeaderLabels(
            ["Action", "Key 1", "Key 2", "Context", ""]
        )
        self._table.verticalHeader().hide()
        self._table.setSelectionMode(QTableWidget.NoSelection)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(COL_ACTION, QHeaderView.Stretch)
        header.setSectionResizeMode(COL_KEY1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_KEY2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_CONTEXT, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_RESET, QHeaderView.ResizeToContents)

        self._populate_table()
        self._table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        layout.addWidget(self._table)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        reset_all_btn = QPushButton("Reset All to Defaults")
        reset_all_btn.clicked.connect(self._on_reset_all)
        btn_layout.addStretch()
        btn_layout.addWidget(reset_all_btn)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self._mgr.keybindings_changed.connect(self._refresh_table)

    # ------------------------------------------------------------------

    def _populate_table(self) -> None:
        for row, action in enumerate(self._actions):
            keys = self._mgr.get_keys(action)
            targets = self._mgr.get_targets(action)

            # Action name
            name_item = QTableWidgetItem(ACTION_DISPLAY_NAMES.get(action, action))
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self._table.setItem(row, COL_ACTION, name_item)

            # Key 1
            key1_item = QTableWidgetItem(keys[0] if len(keys) > 0 else "")
            key1_item.setFlags(key1_item.flags() & ~Qt.ItemIsEditable)
            key1_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, COL_KEY1, key1_item)

            # Key 2
            key2_item = QTableWidgetItem(keys[1] if len(keys) > 1 else "")
            key2_item.setFlags(key2_item.flags() & ~Qt.ItemIsEditable)
            key2_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, COL_KEY2, key2_item)

            # Context
            ctx_item = QTableWidgetItem(_context_label(targets))
            ctx_item.setFlags(ctx_item.flags() & ~Qt.ItemIsEditable)
            ctx_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, COL_CONTEXT, ctx_item)

            # Reset button
            reset_btn = QPushButton("Reset")
            reset_btn.setMaximumWidth(60)
            reset_btn.clicked.connect(
                lambda checked, a=action: self._on_reset_action(a)
            )
            self._table.setCellWidget(row, COL_RESET, reset_btn)

    def _refresh_table(self) -> None:
        for row, action in enumerate(self._actions):
            keys = self._mgr.get_keys(action)
            self._table.item(row, COL_KEY1).setText(keys[0] if len(keys) > 0 else "")
            self._table.item(row, COL_KEY2).setText(keys[1] if len(keys) > 1 else "")

    # ------------------------------------------------------------------
    # Editing
    # ------------------------------------------------------------------

    def _on_cell_double_clicked(self, row: int, col: int) -> None:
        if col not in (COL_KEY1, COL_KEY2):
            return

        action = self._actions[row]
        slot_index = col - COL_KEY1  # 0 or 1

        capture = KeyCaptureWidget()
        self._table.setCellWidget(row, col, capture)
        capture.setFocus()

        def _finish():
            self._table.removeCellWidget(row, col)
            if capture.captured_key is None:
                return  # cancelled

            new_key = capture.captured_key
            current_keys = list(self._mgr.get_keys(action))

            # Pad to at least 2 slots
            while len(current_keys) < 2:
                current_keys.append("")

            old_value = current_keys[slot_index]
            if new_key == old_value:
                return  # no change

            # Conflict check (skip if clearing)
            if new_key:
                conflicts = self._mgr.find_conflicts(action, new_key)
                if conflicts:
                    names = ", ".join(ACTION_DISPLAY_NAMES.get(c, c) for c in conflicts)
                    reply = QMessageBox.warning(
                        self,
                        "Key Conflict",
                        f'Key "{new_key}" is already used by: {names}.\n\n'
                        "Assign anyway?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No,
                    )
                    if reply != QMessageBox.Yes:
                        return

            current_keys[slot_index] = new_key
            # Remove trailing empty slots
            while current_keys and current_keys[-1] == "":
                current_keys.pop()
            self._mgr.set_keys(action, current_keys)

        capture.editingFinished.connect(_finish)

    def _on_reset_action(self, action: str) -> None:
        self._mgr.reset_action(action)

    def _on_reset_all(self) -> None:
        reply = QMessageBox.question(
            self,
            "Reset Keybindings",
            "Reset all keybindings to their default values?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._mgr.reset_to_defaults()
