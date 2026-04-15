from __future__ import annotations

from typing import TYPE_CHECKING

from fonticon_fa6 import FA6S
from qtpy.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from superqt.fonticon import icon as qticon

if TYPE_CHECKING:
    from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


class SelectionWidget(QWidget):
    """Widget with buttons to control selection of nodes on TracksViewer."""

    def __init__(self, tracks_viewer: TracksViewer):
        super().__init__()
        self.tracks_viewer = tracks_viewer

        select_widget = QGroupBox("Selection")
        selection_layout = QHBoxLayout()

        # Invert button
        self.invert_btn = QPushButton("Invert selection")
        self.invert_btn.clicked.connect(self._invert_selection)
        self.invert_btn.setToolTip("Select all nodes not in current selection.")

        # Buttons to jump to next or previous node in the selection
        left_arrow = qticon(FA6S.arrow_left, color="white")
        self.jump_to_previous_btn = QPushButton(icon=left_arrow)
        self.jump_to_previous_btn.setToolTip("Navigate to previous selected node.")
        self.jump_to_previous_btn.setEnabled(False)
        self.jump_to_previous_btn.clicked.connect(
            lambda: self._jump_to_node(forward=False)
        )

        right_arrow = qticon(FA6S.arrow_right, color="white")
        self.jump_to_next_btn = QPushButton(icon=right_arrow)
        self.jump_to_next_btn.setToolTip("Navigate to next selected node.")
        self.jump_to_next_btn.setEnabled(False)
        self.jump_to_next_btn.clicked.connect(lambda: self._jump_to_node(forward=True))

        arrow_layout = QHBoxLayout()
        arrow_layout.addWidget(self.jump_to_previous_btn)
        arrow_layout.addWidget(self.jump_to_next_btn)

        # Buttons to select next and previous node set from history
        self.select_next_set_btn = QPushButton("Next Selection [N]")
        self.select_next_set_btn.setToolTip(
            "Select the next set of nodes from the selection history."
        )
        self.select_next_set_btn.setEnabled(False)
        self.select_next_set_btn.clicked.connect(
            lambda: self.tracks_viewer.select_node_set_from_history(previous=False)
        )
        self.select_previous_set_btn = QPushButton("Previous Selection [P]")
        self.select_previous_set_btn.setToolTip(
            "Select the previous set of nodes from the selection history."
        )
        self.select_previous_set_btn.setEnabled(False)
        self.select_previous_set_btn.clicked.connect(
            lambda: self.tracks_viewer.select_node_set_from_history(previous=True)
        )

        # Button to deselect all nodes
        self.deselect_btn = QPushButton("Deselect [ESC]")
        self.deselect_btn.setToolTip("Deselect all nodes.")
        self.deselect_btn.clicked.connect(self.tracks_viewer.deselect)
        self.deselect_btn.setEnabled(False)

        # Button to restore previous selection
        self.reselect_btn = QPushButton("Restore selection [E]")
        self.reselect_btn.setToolTip("Restore the last selection.")
        self.reselect_btn.clicked.connect(self.tracks_viewer.restore_selection)
        self.reselect_btn.setEnabled(False)

        # Organize buttons in two vertical columns
        col1_layout = QVBoxLayout()
        col2_layout = QVBoxLayout()

        col1_layout.addWidget(self.invert_btn)
        col1_layout.addLayout(arrow_layout)
        col1_layout.addWidget(self.select_next_set_btn)
        col2_layout.addWidget(self.deselect_btn)
        col2_layout.addWidget(self.reselect_btn)
        col2_layout.addWidget(self.select_previous_set_btn)

        selection_layout.addLayout(col1_layout)
        selection_layout.addLayout(col2_layout)
        select_widget.setLayout(selection_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(select_widget)
        self.setLayout(main_layout)
        self.setMaximumHeight(180)

        # Connect to selection updates to enable/disable buttons accordingly
        self.tracks_viewer.node_selection_updated.connect(self.update_selection_buttons)

        # Set initial button states
        self.update_selection_buttons()

    def update_selection_buttons(self):
        """Update the button states based on the current node selection (history)"""

        if len(self.tracks_viewer.selected_nodes) > 0:
            self.deselect_btn.setEnabled(True)
            self.jump_to_next_btn.setEnabled(True)
            self.jump_to_previous_btn.setEnabled(True)
        else:
            self.deselect_btn.setEnabled(False)
            self.jump_to_next_btn.setEnabled(False)
            self.jump_to_previous_btn.setEnabled(False)

        self.reselect_btn.setEnabled(
            self.tracks_viewer.selected_nodes.has_valid_last_shown_set
        )
        self.select_next_set_btn.setEnabled(
            self.tracks_viewer.selected_nodes.has_next_set
        )
        self.select_previous_set_btn.setEnabled(
            self.tracks_viewer.selected_nodes.has_previous_set
        )

    def _jump_to_node(self, forward: bool) -> None:
        """Jump to the next/previous selected node in the list"""

        node = self.tracks_viewer.selected_nodes.next_node(forward)
        if node:
            self.tracks_viewer.center_on_node(node)

    def _invert_selection(self) -> None:
        """Invert the current selection"""

        all_nodes = set(self.tracks_viewer.tracks.graph.nodes)
        inverted = list(all_nodes - set(self.tracks_viewer.selected_nodes))
        self.tracks_viewer.selected_nodes.add_list(inverted, append=False)
