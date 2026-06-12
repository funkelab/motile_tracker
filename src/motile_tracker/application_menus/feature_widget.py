from __future__ import annotations

import napari
from funtracks.annotators._regionprops_annotator import (
    DEFAULT_POS_KEY,
    RegionpropsAnnotator,
)
from funtracks.features._feature import Feature
from qtpy.QtWidgets import (
    QCheckBox,
    QVBoxLayout,
    QWidget,
)

from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


class FeatureWidget(QWidget):
    """Widget to enable/disable RegionProps features."""

    def __init__(self, viewer: napari.Viewer):
        super().__init__()

        self.viewer = viewer
        self.tracks_viewer = TracksViewer.get_instance(viewer)
        self.tracks_viewer.tracks_updated.connect(self._update_checkboxes)
        self._checkboxes: dict[str, QCheckBox] = {}

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

    def _update_checkboxes(self):
        """Update the list of available checkboxes."""

        self._clear_layout()
        self._checkboxes.clear()

        tracks = self.tracks_viewer.tracks
        if tracks is None:
            return

        for feature_key, feature in self._discover_features().items():
            checkbox = QCheckBox(feature["display_name"])

            checkbox.setChecked(feature_key in tracks.features)

            checkbox.toggled.connect(
                lambda checked, key=feature_key: self._on_toggled(key, checked)
            )

            self._checkboxes[feature_key] = checkbox
            self.layout.addWidget(checkbox)

        self.layout.addStretch()

    def _clear_layout(self) -> None:
        """Remove all checkboxes from the layout"""

        while self.layout.count():
            item = self.layout.takeAt(0)

            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _discover_features(self) -> dict[str, Feature]:
        """Find all features available for the current tracks (excluding position)"""

        tracks = self.tracks_viewer.tracks

        features = RegionpropsAnnotator.get_available_features(ndim=tracks.ndim)

        features.pop(DEFAULT_POS_KEY, None)

        return features

    def _on_toggled(self, feature_key: str, checked: bool) -> None:
        """Enable/disable features on tracks

        Args:
            feature_key (str): the feature the enable/disable
            checked (bool): whether to enable (True) or disable (False)
        """

        tracks = self.tracks_viewer.tracks

        if checked:
            tracks.enable_features([feature_key])
        else:
            tracks.disable_features([feature_key])

        self.tracks_viewer.update_track_df(initialization=False, refresh_view=False)
