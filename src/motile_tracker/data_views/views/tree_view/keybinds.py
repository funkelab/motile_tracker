from qtpy.QtCore import Qt

# Define keyboard shortcuts for tree view and table widgets.

# General keybinds: work in both TreeWidget and table, call TracksViewer methods.
GENERAL_KEY_ACTIONS = {
    Qt.Key_Delete: "delete_node",
    Qt.Key_D: "delete_node",
    Qt.Key_A: "create_edge",
    Qt.Key_B: "delete_edge",
    Qt.Key_S: "swap_nodes",
    Qt.Key_Z: "undo",
    Qt.Key_R: "redo",
    Qt.Key_Escape: "deselect",
    Qt.Key_E: "restore_selection",
}

# Tree-widget-specific keybinds, call TreeWidget methods.
TREE_WIDGET_SPECIFIC_ACTIONS = {
    Qt.Key_Q: "toggle_display_mode",
    Qt.Key_W: "toggle_feature_mode",
    Qt.Key_F: "_flip_axes",
}

# Modifier-based keybinds for mouse scrolling (TreeWidget only)
# Maps key to (x_enabled, y_enabled) tuple for set_mouse_enabled()
TREE_WIDGET_MODIFIER_ACTIONS = {
    Qt.Key_X: (True, False),  # Enable X-axis zoom only
    Qt.Key_Y: (False, True),  # Enable Y-axis zoom only
}

# Navigation keybinds for TreeWidget (arrow keys)
# Maps key to direction string passed to navigation_widget.move()
TREE_WIDGET_NAVIGATION_KEYS = {
    Qt.Key_Left: "left",
    Qt.Key_Right: "right",
    Qt.Key_Up: "up",
    Qt.Key_Down: "down",
}
