"""Mixin that adds napari-style bind_key() to any QWidget.

Provides:
- qt_key_to_string / qt_mouse_to_string  -- translate Qt events to napari key strings
- KeyBindable mixin with bind_key, bind_key_release, and event dispatch
"""

from __future__ import annotations

from qtpy.QtCore import Qt
from qtpy.QtGui import QKeyEvent, QMouseEvent

# Mapping from Qt key constants to napari-style key strings.
# Only keys that differ from chr(key).lower() need to be listed.
_QT_KEY_TO_STRING: dict[int, str] = {
    Qt.Key_Delete: "Delete",
    Qt.Key_Backspace: "Backspace",
    Qt.Key_Escape: "Escape",
    Qt.Key_Return: "Return",
    Qt.Key_Enter: "Enter",
    Qt.Key_Tab: "Tab",
    Qt.Key_Space: "Space",
    Qt.Key_Left: "Left",
    Qt.Key_Right: "Right",
    Qt.Key_Up: "Up",
    Qt.Key_Down: "Down",
    Qt.Key_Home: "Home",
    Qt.Key_End: "End",
    Qt.Key_PageUp: "PageUp",
    Qt.Key_PageDown: "PageDown",
    Qt.Key_Slash: "/",
    Qt.Key_Minus: "-",
    Qt.Key_Plus: "+",
    Qt.Key_Equal: "=",
    Qt.Key_Period: ".",
    Qt.Key_Comma: ",",
    Qt.Key_BracketLeft: "[",
    Qt.Key_BracketRight: "]",
    Qt.Key_F1: "F1",
    Qt.Key_F2: "F2",
    Qt.Key_F3: "F3",
    Qt.Key_F4: "F4",
    Qt.Key_F5: "F5",
    Qt.Key_F6: "F6",
    Qt.Key_F7: "F7",
    Qt.Key_F8: "F8",
    Qt.Key_F9: "F9",
    Qt.Key_F10: "F10",
    Qt.Key_F11: "F11",
    Qt.Key_F12: "F12",
}

# Mouse buttons that can be bound (extra buttons only -- left/right stay normal)
_QT_MOUSE_TO_STRING: dict[int, str] = {
    Qt.BackButton: "MouseBack",
    Qt.ForwardButton: "MouseForward",
    Qt.MiddleButton: "MouseMiddle",
}


def qt_key_to_string(event: QKeyEvent) -> str | None:
    """Convert a QKeyEvent to a napari-style key string.

    Returns None for pure modifier-key presses (Shift, Control, etc.).
    Modifier prefixes are added for Control, Alt, Shift (in that order).
    Examples: "d", "Delete", "Control-z", "Shift-Left"
    """
    key = event.key()

    # Ignore standalone modifier key presses
    if key in (
        Qt.Key_Shift,
        Qt.Key_Control,
        Qt.Key_Alt,
        Qt.Key_Meta,
        Qt.Key_AltGr,
    ):
        return None

    # Determine the base key string
    if key in _QT_KEY_TO_STRING:
        base = _QT_KEY_TO_STRING[key]
    elif Qt.Key_A <= key <= Qt.Key_Z:
        base = chr(key).lower()
    elif Qt.Key_0 <= key <= Qt.Key_9:
        base = chr(key)
    else:
        return None

    # Build modifier prefix
    mods = event.modifiers()
    parts: list[str] = []
    if mods & Qt.ControlModifier:
        parts.append("Control")
    if mods & Qt.AltModifier:
        parts.append("Alt")
    if mods & Qt.ShiftModifier:
        parts.append("Shift")
    parts.append(base)

    return "-".join(parts)


def qt_mouse_to_string(event: QMouseEvent) -> str | None:
    """Convert extra mouse buttons to napari-style strings.

    Returns None for left/right buttons (those keep normal Qt mouse handling).
    """
    return _QT_MOUSE_TO_STRING.get(event.button())


class KeyBindable:
    """Mixin that gives any QWidget a napari-compatible ``bind_key`` API.

    Usage::

        class MyWidget(KeyBindable, QWidget):
            def __init__(self):
                super().__init__()
                self.__init_keymap__()
    """

    def __init_keymap__(self):
        self._keymap: dict[str, callable] = {}
        self._release_keymap: dict[str, callable] = {}

    def clear_keymap(self):
        """Remove all key-press and key-release bindings."""
        self._keymap.clear()
        self._release_keymap.clear()

    def bind_key(self, key_string: str, overwrite: bool = False):
        """Decorator that registers a handler for the given key string.

        Parameters
        ----------
        key_string : str
            Napari-style key, e.g. ``"d"``, ``"Delete"``, ``"MouseBack"``.
        overwrite : bool
            If True, silently replace an existing binding.
        """

        def decorator(func):
            if not overwrite and key_string in self._keymap:
                raise ValueError(
                    f"Key '{key_string}' is already bound. Use overwrite=True to replace."
                )
            self._keymap[key_string] = func
            return func

        return decorator

    def bind_key_release(self, key_string: str):
        """Decorator that registers a handler for a key *release* event."""

        def decorator(func):
            self._release_keymap[key_string] = func
            return func

        return decorator

    # -- Qt event overrides ---------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key_str = qt_key_to_string(event)
        if key_str is not None and key_str in self._keymap:
            self._keymap[key_str]()
            event.accept()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        key_str = qt_key_to_string(event)
        if key_str is not None and key_str in self._release_keymap:
            self._release_keymap[key_str]()
            event.accept()
            return
        super().keyReleaseEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        key_str = qt_mouse_to_string(event)
        if key_str is not None and key_str in self._keymap:
            self._keymap[key_str]()
            event.accept()
            return
        super().mousePressEvent(event)
