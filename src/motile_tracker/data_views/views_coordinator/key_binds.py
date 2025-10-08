DEFAULT_KEYMAP = {
    "q": "toggle_display_mode",
    "a": "create_edge",
    "d": "delete_node",
    "Delete": "delete_node",
    "b": "delete_edge",
    "z": "undo",
    "r": "redo",
}

LABELS_KEYMAP = {
    **DEFAULT_KEYMAP,
    "m": "assign_new_label",
}


def bind_keymap(target, keymap, tracks_viewer):
    """Bind all keys in `keymap` to the corresponding methods on `tracks_viewer`."""
    for key, method_name in keymap.items():
        handler = getattr(tracks_viewer, method_name, None)
        if handler is not None:
            target.bind_key(key)(handler)
