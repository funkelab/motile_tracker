import napari
import networkx as nx
from qtpy.QtWidgets import QLabel, QVBoxLayout, QWidget

from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


class TrackSummaryWidget(QWidget):
    def __init__(self, viewer: napari.Viewer):
        super().__init__()
        self.tracks_viewer = TracksViewer.get_instance(viewer)
        self._update_statistics()
        self.tracks_viewer.tracks_updated.connect(self._update)
        self.title_label = QLabel(self.label_text)
        self.tracklet_label = QLabel(f"{self.num_tracklets} tracklets")
        self.lineage_label = QLabel(f"{self.num_lineages} lineages")
        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(self.tracklet_label)
        layout.addWidget(self.lineage_label)
        self.setLayout(layout)

    def _update(self) -> None:
        self._update_statistics()
        self._update_labels()

    def _update_statistics(self) -> None:
        """Get the statistics of the currently selected tracks"""
        tracks = self.tracks_viewer.tracks
        if tracks is None:
            self.label_text = "No tracks currently selected"
            self.num_lineages = 0
            self.num_tracklets = 0
        else:
            self.label_text = f"Viewing tracks {self.tracks_viewer.tracks_name}"
            self.num_lineages = nx.number_weakly_connected_components(tracks.graph)
            unique_track_ids = set(tracks.node_id_to_track_id.values())
            self.num_tracklets = len(unique_track_ids)

    def _update_labels(self) -> None:
        self.title_label.setText(self.label_text)
        self.tracklet_label.setText(f"{self.num_tracklets} tracklets")
        self.lineage_label.setText(f"{self.num_lineages} lineages")
