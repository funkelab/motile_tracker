import napari
from qtpy.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


class EditingMenu(QWidget):
    def __init__(self, viewer: napari.Viewer):
        super().__init__()

        self.tracks_viewer = TracksViewer.get_instance(viewer)
        self.tracks_viewer.selected_nodes.list_updated.connect(self.update_buttons)
        layout = QVBoxLayout()

        self.label = QLabel(f"Current Track ID: {self.tracks_viewer.selected_track}")
        self.tracks_viewer.update_track_id.connect(self.update_track_id_color)

        new_track_btn = QPushButton("Start new")
        new_track_btn.clicked.connect(self.tracks_viewer.request_new_track)
        track_layout = QHBoxLayout()
        track_layout.addWidget(self.label)
        track_layout.addWidget(new_track_btn)
        layout.addLayout(track_layout)

        # Checkbox for activating/deactivating contours for lineage/group display
        self.contour_checkbox = QCheckBox("Show contours (Lineage/Group mode)")
        self.contour_checkbox.setToolTip(
            "<html><body><p style='white-space:pre-wrap; width: 400px;'>"
            "When checked, displays contours for node labels that are not in the current lineage(s) or group. When not checked, these nodes are hidden entirely."
        )
        self.contour_checkbox.clicked.connect(self._update_contours)
        self.tracks_viewer.tracks_updated.connect(
            lambda: self.contour_checkbox.setVisible(True)
            if self.tracks_viewer.tracking_layers.seg_layer is not None
            else self.contour_checkbox.setVisible(False)
        )
        layout.addWidget(self.contour_checkbox)

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

        layout.addWidget(node_box)
        layout.addWidget(edge_box)
        layout.addWidget(self.undo_btn)
        layout.addWidget(self.redo_btn)

        self.setLayout(layout)
        self.setMaximumHeight(400)

    def update_track_id_color(self):
        """Display track ID value and color"""

        color = self.tracks_viewer.track_id_color
        r, g, b, a = [int(c * 255) if i < 3 else c for i, c in enumerate(color)]
        css_color = f"rgba({r}, {g}, {b}, {a})"
        self.label.setText(f"Current Track ID: {self.tracks_viewer.selected_track}")
        self.label.setStyleSheet(
            f"""
            color: white;
            border: 2px solid {css_color};
            padding: 5px;
            """
        )

    def update_buttons(self):
        """Set the buttons to enabled/disabled depending on the selected nodes"""

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

    def _update_contours(self, state: bool) -> None:
        """Update whether or not to display contours for lineage/group nodes in TrackLabels."""

        self.tracks_viewer.use_contours = state
        self.tracks_viewer.filter_visible_nodes()
        self.tracks_viewer.tracking_layers.update_visible(self.tracks_viewer.visible)
