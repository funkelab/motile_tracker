import napari
from qtpy.QtWidgets import (
    QButtonGroup,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


class EditingMenu(QWidget):
    def __init__(self, viewer: napari.Viewer):
        super().__init__()

        self.tracks_viewer = TracksViewer.get_instance(viewer)
        self.tracks_viewer.selected_nodes.list_updated.connect(self.update_buttons)
        self.tracks_viewer.tracks_updated.connect(self._update_continue_tracks_box)
        layout = QVBoxLayout()

        self.continue_tracks_box = QGroupBox("Point layer track mode")
        self.continue_tracks_box.setMaximumHeight(60)
        continue_tracks_layout = QHBoxLayout()
        button_group = QButtonGroup()
        self.continue_tracks_radio = QRadioButton("Continue tracks")
        self.continue_tracks_radio.clicked.connect(
            lambda: self.toggle_track_mode("continue")
        )
        self.new_track_radio = QRadioButton("Start new tracks")
        self.new_track_radio.setChecked(True)
        self.new_track_radio.clicked.connect(
            lambda: self.toggle_track_mode("new track")
        )
        button_group.addButton(self.continue_tracks_radio)
        button_group.addButton(self.new_track_radio)
        continue_tracks_layout.addWidget(self.continue_tracks_radio)
        continue_tracks_layout.addWidget(self.new_track_radio)

        self.continue_tracks_box.setLayout(continue_tracks_layout)
        if (
            self.tracks_viewer.tracking_layers.seg_layer is not None
            and self.tracks_viewer.tracking_layers.points_layer is not None
        ):
            self.continue_tracks_box.hide()

        node_box = QGroupBox("Edit Node(s)")
        node_box.setMaximumHeight(60)
        node_box_layout = QVBoxLayout()

        self.delete_node_btn = QPushButton("Delete [D]")
        self.delete_node_btn.clicked.connect(self.tracks_viewer.delete_node)
        self.delete_node_btn.setEnabled(False)
        # self.split_node_btn = QPushButton("Set split [S]")
        # self.split_node_btn.clicked.connect(self.tracks_viewer.set_split_node)
        # self.split_node_btn.setEnabled(False)
        # self.endpoint_node_btn = QPushButton("Set endpoint [E]")
        # self.endpoint_node_btn.clicked.connect(self.tracks_viewer.set_endpoint_node)
        # self.endpoint_node_btn.setEnabled(False)
        # self.linear_node_btn = QPushButton("Set linear [C]")
        # self.linear_node_btn.clicked.connect(self.tracks_viewer.set_linear_node)
        # self.linear_node_btn.setEnabled(False)

        node_box_layout.addWidget(self.delete_node_btn)
        # node_box_layout.addWidget(self.split_node_btn)
        # node_box_layout.addWidget(self.endpoint_node_btn)
        # node_box_layout.addWidget(self.linear_node_btn)

        node_box.setLayout(node_box_layout)

        edge_box = QGroupBox("Edit Edge(s)")
        edge_box.setMaximumHeight(100)
        edge_box_layout = QVBoxLayout()

        self.delete_edge_btn = QPushButton("Break [B]")
        self.delete_edge_btn.clicked.connect(self.tracks_viewer.delete_edge)
        self.delete_edge_btn.setEnabled(False)
        self.create_edge_btn = QPushButton("Add [A]")
        self.create_edge_btn.clicked.connect(self.tracks_viewer.create_edge)
        self.create_edge_btn.setEnabled(False)

        edge_box_layout.addWidget(self.delete_edge_btn)
        edge_box_layout.addWidget(self.create_edge_btn)

        edge_box.setLayout(edge_box_layout)

        self.undo_btn = QPushButton("Undo (Z)")
        self.undo_btn.clicked.connect(self.tracks_viewer.undo)

        self.redo_btn = QPushButton("Redo (R)")
        self.redo_btn.clicked.connect(self.tracks_viewer.redo)

        layout.addWidget(self.continue_tracks_box)
        layout.addWidget(node_box)
        layout.addWidget(edge_box)
        layout.addWidget(self.undo_btn)
        layout.addWidget(self.redo_btn)

        self.setLayout(layout)
        self.setMaximumHeight(360)

    def _update_continue_tracks_box(self):
        """Show or hide the continue tracks box depending on the presence of the TracksLabels layer. If a TracksLabels layer is present, adding nodes with points is disabled and therefore the continue_tracks_button should be hidden."""

        if (
            self.tracks_viewer.tracking_layers.seg_layer is not None
            and self.tracks_viewer.tracking_layers.points_layer is not None
        ):
            self.continue_tracks_box.hide()
        else:
            self.continue_tracks_box.show()

    def toggle_track_mode(self, mode: str):
        """Toggle the track mode (continue / new track on the tracks viewer)"""

        self.tracks_viewer.track_mode = mode

    def update_buttons(self):
        """Set the buttons to enabled/disabled depending on the currently selected nodes"""

        n_selected = len(self.tracks_viewer.selected_nodes)
        if n_selected == 0:
            self.delete_node_btn.setEnabled(False)
            # self.split_node_btn.setEnabled(False)
            # self.endpoint_node_btn.setEnabled(False)
            # self.linear_node_btn.setEnabled(False)
            self.delete_edge_btn.setEnabled(False)
            self.create_edge_btn.setEnabled(False)

        elif n_selected == 2:
            self.delete_node_btn.setEnabled(True)
            # self.split_node_btn.setEnabled(True)
            # self.endpoint_node_btn.setEnabled(True)
            # self.linear_node_btn.setEnabled(True)
            self.delete_edge_btn.setEnabled(True)
            self.create_edge_btn.setEnabled(True)

        else:
            self.delete_node_btn.setEnabled(True)
            # self.split_node_btn.setEnabled(True)
            # self.endpoint_node_btn.setEnabled(True)
            # self.linear_node_btn.setEnabled(True)
            self.delete_edge_btn.setEnabled(False)
            self.create_edge_btn.setEnabled(False)
