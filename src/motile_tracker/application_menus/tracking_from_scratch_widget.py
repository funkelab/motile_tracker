import contextlib
import weakref

import napari
from funtracks.candidate_graph.utils import (
    nodes_from_points_list,
    nodes_from_segmentation,
)
from funtracks.data_model import SolutionTracks
from funtracks.utils import ensure_unique_labels
from funtracks.utils.tracksdata_utils import create_empty_graphview_graph
from napari.layers import Image, Labels, Points
from psygnal import Signal
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QComboBox,
    QGroupBox,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from motile_tracker.data_views.lazy_array_wrapper import LazyArrayWrapper
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


class LayerDropdown(QComboBox):
    """QComboBox widget with functions for updating the selected layer and to update the
    list of options when the list of layers is modified."""

    layer_changed = Signal(str)

    def __init__(self, viewer: napari.Viewer, layer_types: tuple, allow_none=False):
        super().__init__()

        self.viewer = viewer
        self.layer_types = layer_types
        self.allow_none = allow_none
        self.selected_layer = None
        self._deleted = False

        # track rename callbacks so we can disconnect them at cleanup
        self._rename_callbacks: dict[int, tuple[weakref.ref, callable]] = {}
        self.destroyed.connect(self._on_destroyed)  # for reference cleanup

        # viewer connections
        self.viewer.layers.events.inserted.connect(self._on_insert)
        self.viewer.layers.events.changed.connect(self._update_dropdown)
        self.viewer.layers.events.removed.connect(self._on_removed)
        self.viewer.layers.selection.events.changed.connect(self._on_selection_changed)

        self.currentTextChanged.connect(self._emit_layer_changed)
        self._update_dropdown()

    def _make_weak_rename_cb(self):
        """Create a weak callback to track name updates but do not let the layer keep the
        widget alive forever."""

        self_ref = weakref.ref(self)

        def _rename_cb(event=None):
            self_obj = self_ref()
            if self_obj is None or self_obj._deleted:
                return
            with contextlib.suppress(AttributeError, RuntimeError):
                self_obj._update_dropdown()

        return _rename_cb

    def _on_insert(self, event) -> None:
        """Update dropdown and make new layer responsive to name changes"""

        if self._deleted:
            return

        layer = event.value
        if isinstance(layer, self.layer_types):
            cb = self._make_weak_rename_cb()
            layer.events.name.connect(cb)
            self._rename_callbacks[id(layer)] = (weakref.ref(layer), cb)
            self._update_dropdown()

    def _on_removed(self, event) -> None:
        """Disconnect signals and update dropdown when a layer is removed."""

        if self._deleted:
            return

        layer = event.value
        pair = self._rename_callbacks.pop(id(layer), None)
        if pair is not None:
            layer_ref, cb = pair
            layer_obj = layer_ref() if layer_ref else None
            target = layer_obj if layer_obj else layer
            with contextlib.suppress(AttributeError, RuntimeError, TypeError):
                target.events.name.disconnect(cb)

        self._update_dropdown()

    def _on_selection_changed(self):
        """Update the active layer when the selection changes"""
        if self._deleted:
            return

        try:
            if len(self.viewer.layers.selection) == 1:
                selected = self.viewer.layers.selection.active
                if (
                    isinstance(selected, self.layer_types)
                    and selected != self.selected_layer
                ):
                    self.setCurrentText(selected.name)
                    self._emit_layer_changed()
        except (AttributeError, RuntimeError, TypeError):
            pass

    def _update_dropdown(self, event=None) -> None:
        """Update the layers in the dropdown"""

        if self._deleted:
            return

        try:
            previous = self.currentText()
            self.clear()

            layers = [
                layer
                for layer in self.viewer.layers
                if isinstance(layer, self.layer_types)
            ]

            names = []
            if self.allow_none:
                self.addItem("No selection")
                names.append("No selection")

            for layer in layers:
                self.addItem(layer.name)
                names.append(layer.name)

            # restore previous selection if still valid
            if previous in names:
                self.setCurrentText(previous)
        except (AttributeError, RuntimeError, TypeError):
            pass

    def _emit_layer_changed(self) -> None:
        """Emit a signal holding the currently selected layer"""

        if self._deleted:
            return

        try:
            name = self.currentText()
            if name != "No selection" and name in self.viewer.layers:
                self.selected_layer = self.viewer.layers[name]
            else:
                self.selected_layer = None
                name = ""
            self.layer_changed.emit(name)
        except (AttributeError, RuntimeError, TypeError):
            pass

    def _on_destroyed(self, *args):
        """Disconnect everything cleanly"""

        self._deleted = True

        with contextlib.suppress(AttributeError, RuntimeError, TypeError):
            self.viewer.layers.events.inserted.disconnect(self._on_insert)
            self.viewer.layers.events.changed.disconnect(self._update_dropdown)
            self.viewer.layers.events.removed.disconnect(self._on_removed)
            self.viewer.layers.selection.events.changed.disconnect(
                self._on_selection_changed
            )

        for layer_ref, cb in self._rename_callbacks.values():
            layer_obj = layer_ref() if layer_ref else None
            target = layer_obj
            if target:
                with contextlib.suppress(AttributeError, RuntimeError, TypeError):
                    target.events.name.disconnect(cb)

        self._rename_callbacks.clear()

        with contextlib.suppress(AttributeError, RuntimeError, TypeError):
            self.currentTextChanged.disconnect(self._emit_layer_changed)


class TrackingFromScratch(QWidget):
    """Widget to track from scratch or from detections without edges"""

    def __init__(self, viewer: napari.Viewer):
        super().__init__()

        self.viewer = viewer
        self.tracks_viewer = TracksViewer.get_instance(viewer)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        exp_manual = QLabel()
        exp_manual.setWordWrap(True)
        exp_manual.setTextFormat(Qt.MarkdownText)
        exp_manual.setText(
            "**Manual tracking from scratch**\n\n"
            "*This will create an empty graph, to which you can manually add nodes by "
            "placing points against the background of a given image layer.*"
        )

        image_box = QGroupBox("Manual tracking from scratch")
        image_box_layout = QVBoxLayout(image_box)

        image_label = QLabel("Select an Image layer")
        image_box_layout.addWidget(image_label)

        self.image_layer_dropdown = LayerDropdown(self.viewer, (Image))
        image_box_layout.addWidget(self.image_layer_dropdown)

        self.start_from_scratch_btn = QPushButton("Start")
        self.image_layer_dropdown.layer_changed.connect(self._update_buttons)
        self.start_from_scratch_btn.clicked.connect(self._start_empty_tracks)
        image_box_layout.addWidget(self.start_from_scratch_btn)

        exp_detection = QLabel()
        exp_detection.setWordWrap(True)
        exp_detection.setTextFormat(Qt.MarkdownText)
        exp_detection.setText(
            "**Manual tracking from detections**\n\n"
            "*This will create a graph with only detections and no connections. "
            "The type of input layer (Labels or Points) determines whether you will "
            "get nodes from point detections or label detections.*"
        )

        detections_box = QGroupBox("Manual tracking from detections")
        detections_box_layout = QVBoxLayout(detections_box)

        detections_label = QLabel("Select a Labels or Points layer")
        detections_box_layout.addWidget(detections_label)

        self.detections_layer_dropdown = LayerDropdown(self.viewer, (Labels, Points))
        detections_box_layout.addWidget(self.detections_layer_dropdown)

        self.start_from_detections_btn = QPushButton("Start")
        self.detections_layer_dropdown.layer_changed.connect(self._update_buttons)
        self.start_from_detections_btn.clicked.connect(self._start_from_detections)
        detections_box_layout.addWidget(self.start_from_detections_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(exp_manual)
        layout.addWidget(image_box)
        layout.addWidget(exp_detection)
        layout.addWidget(detections_box)
        layout.addStretch(0)

    def _update_buttons(self):
        """Enable/disable buttons according to whether a valid layer is selected"""

        self.start_from_scratch_btn.setEnabled(
            self.image_layer_dropdown.selected_layer is not None
        )
        self.start_from_detections_btn.setEnabled(
            self.detections_layer_dropdown.selected_layer is not None
        )

    def _start_empty_tracks(self):
        """Create an empty graph to be filled manually by placing points in an initially empty TrackPoints layer"""

        layer = self.image_layer_dropdown.selected_layer
        graph = create_empty_graphview_graph(
            node_attributes=["pos"], position_attrs=["pos"], ndim=layer.data.ndim
        )
        tracks = SolutionTracks(
            graph=graph,
            scale=layer.scale,
            ndim=layer.ndim,
            time_attr="t",
            pos_attr="pos",
        )
        self.tracks_viewer.tracks_list.add_tracks(tracks, f"{layer.name}_manual_tracks")
        self.tracks_viewer.set_new_track_id()

    def _start_from_detections(self):
        """Create a graph with only detections (no edges), derived from the selected layer (either Points or Labels)"""

        layer = self.detections_layer_dropdown.selected_layer
        if isinstance(layer, Labels):
            seg = layer.data
            if isinstance(seg, LazyArrayWrapper):
                seg = seg.__array__()
            try:
                graph, _ = nodes_from_segmentation(seg, scale=layer.scale)
                graph._update_metadata(segmentation_shape=seg.shape)

            except ValueError as e:
                if "Duplicate values found among nodes" in str(e):
                    seg = ensure_unique_labels(seg)
                    graph, _ = nodes_from_segmentation(seg, scale=layer.scale)
                    graph._update_metadata(segmentation_shape=seg.shape)
                else:
                    raise

        else:
            graph, _ = nodes_from_points_list(layer.data, layer.scale)

        tracks = SolutionTracks(
            graph=graph,
            scale=layer.scale,
            ndim=layer.ndim,
            time_attr="t",
            pos_attr="pos",
        )
        self.tracks_viewer.tracks_list.add_tracks(tracks, f"{layer.name}_manual_tracks")
