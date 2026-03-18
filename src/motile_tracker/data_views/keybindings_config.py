"""Unified keybindings configuration for napari layers and Qt widgets.

Each entry in KEYBINDINGS maps an action name to:
- ``keys``: list of napari-style key strings (e.g. ``"d"``, ``"Delete"``)
- ``targets``: list of ``"tracks_viewer"`` and/or ``"tree_widget"``

Derived keymaps (action -> list of key strings):
- ``NAPARI_KEYMAP``       -- actions targeting ``"tracks_viewer"`` (bound on napari layers + viewer)
- ``TREE_WIDGET_KEYMAP``  -- actions targeting ``"tree_widget"`` *or* ``"tracks_viewer"``
- ``TABLE_WIDGET_KEYMAP`` -- actions targeting ``"tracks_viewer"``
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from napari.layers import Labels, Points

    from motile_tracker.data_views.key_bindable import KeyBindable
    from motile_tracker.data_views.views.layers.track_labels import TrackLabels
    from motile_tracker.data_views.views.layers.track_points import TrackPoints
    from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


def bind_keymap(
    target: TrackPoints | Points | TrackLabels | Labels | KeyBindable,
    keymap: dict[str, list[str]],
    *providers: TracksViewer | KeyBindable,
):
    """Bind all keys in *keymap* to methods found on *providers*.

    Works for napari layers (which already have ``bind_key``) and for Qt widgets
    that inherit from :class:`KeyBindable`.

    For each action in *keymap*, the *providers* are searched in order and the
    first one that has the named method wins. Handlers are late-bound: the
    actual method is looked up via ``getattr`` at call time, so replacing an
    attribute on a provider after binding still takes effect.
    """
    for method_name, keys in keymap.items():
        # Find which provider owns this action
        owner = None
        for provider in providers:
            if getattr(provider, method_name, None) is not None:
                owner = provider
                break
        if owner is None:
            continue

        def _make_handler(obj, name):
            def handler(*args, **kwargs):
                getattr(obj, name)(*args, **kwargs)

            return handler

        handler = _make_handler(owner, method_name)
        for key in keys:
            target.bind_key(key)(handler)


KEYBINDINGS = {
    # --- Actions targeting tracks_viewer (napari layers, table, and tree) ---
    "delete_node": {
        "keys": ["d", "Delete"],
        "targets": ["tracks_viewer"],
    },
    "create_edge": {
        "keys": ["a"],
        "targets": ["tracks_viewer"],
    },
    "delete_edge": {
        "keys": ["b"],
        "targets": ["tracks_viewer"],
    },
    "swap_nodes": {
        "keys": ["s"],
        "targets": ["tracks_viewer"],
    },
    "undo": {
        "keys": ["z"],
        "targets": ["tracks_viewer"],
    },
    "redo": {
        "keys": ["r"],
        "targets": ["tracks_viewer"],
    },
    "deselect": {
        "keys": ["Escape"],
        "targets": ["tracks_viewer"],
    },
    "restore_selection": {
        "keys": ["e"],
        "targets": ["tracks_viewer"],
    },
    "hide_panels": {
        "keys": ["/"],
        "targets": ["tracks_viewer"],
    },
    # --- Actions available in both napari and tree_widget ---
    "toggle_display_mode": {
        "keys": ["q"],
        "targets": ["tracks_viewer", "tree_widget"],
    },
    # --- Tree-widget-specific actions ---
    "toggle_feature_mode": {
        "keys": ["w"],
        "targets": ["tree_widget"],
    },
    "flip_axes": {
        "keys": ["f"],
        "targets": ["tree_widget"],
    },
    # --- Navigation (tree widget only) ---
    "navigate_left": {
        "keys": ["Left"],
        "targets": ["tree_widget"],
    },
    "navigate_right": {
        "keys": ["Right"],
        "targets": ["tree_widget"],
    },
    "navigate_up": {
        "keys": ["Up"],
        "targets": ["tree_widget"],
    },
    "navigate_down": {
        "keys": ["Down"],
        "targets": ["tree_widget"],
    },
    # --- Zoom axis constraints (tree widget only) ---
    "zoom_constrain_x": {
        "keys": ["x"],
        "targets": ["tree_widget"],
    },
    "zoom_constrain_y": {
        "keys": ["y"],
        "targets": ["tree_widget"],
    },
}

# ---------------------------------------------------------------------------
# Derived keymaps: action_name -> list[key_string]
# ---------------------------------------------------------------------------

NAPARI_KEYMAP: dict[str, list[str]] = {
    action: config["keys"]
    for action, config in KEYBINDINGS.items()
    if "tracks_viewer" in config["targets"]
}

TREE_WIDGET_KEYMAP: dict[str, list[str]] = {
    action: config["keys"]
    for action, config in KEYBINDINGS.items()
    if "tree_widget" in config["targets"] or "tracks_viewer" in config["targets"]
}

TABLE_WIDGET_KEYMAP: dict[str, list[str]] = {
    action: config["keys"]
    for action, config in KEYBINDINGS.items()
    if "tracks_viewer" in config["targets"]
}
