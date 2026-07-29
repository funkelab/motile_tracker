import contextlib
import weakref

import napari
import numpy as np
from funtracks.data_model import SolutionTracks
from funtracks.exceptions import InvalidActionError
from funtracks.user_actions import UserAddNode
from funtracks.utils.tracksdata_utils import create_empty_graphview_graph
from napari.layers import Image, Labels, Points
from napari.utils.notifications import show_info
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

from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer
from motile_tracker.data_views.views_coordinator.user_dialogs import (
    confirm_force_operation,
)


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

        # the detections layer that is currently connected as a copy source, and the
        # right-click callback attached to it (so we can disconnect it later)
        self._source_layer = None
        self._source_callback = None

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
            "*This creates empty track layers that stay linked to the selected "
            "detections layer. Right-click a label or point on the source layer to "
            "copy that detection into the tracks with the current tracklet id. "
            "Use the 'new track' action to start a new tracklet.*"
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
        """Create an empty graph (with empty TrackLabels/TrackPoints layers) that stays
        linked to the selected detections layer. Detections are copied into the tracks by
        right-clicking on the source layer (see _copy_detection)."""

        layer = self.detections_layer_dropdown.selected_layer

        # disconnect any previously connected source layer
        self._teardown_source_connection()

        if isinstance(layer, Labels):
            # an empty segmentation-backed graph: registering the 'mask' attribute and
            # the segmentation shape makes SolutionTracks expose an (empty) segmentation,
            # so a TrackLabels layer is created and grows as labels are copied in.
            graph = create_empty_graphview_graph(
                node_attributes=["pos", "area", "mask", "bbox"],
                position_attrs=["pos"],
                ndim=layer.data.ndim,
            )
            graph._update_metadata(segmentation_shape=layer.data.shape)
        else:
            graph = create_empty_graphview_graph(
                node_attributes=["pos"],
                position_attrs=["pos"],
                ndim=layer.data.shape[1],
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

        self._setup_source_connection(layer)

    def _setup_source_connection(self, source_layer: Labels | Points) -> None:
        """Keep the detections layer visible and attach a right-click callback that copies
        the clicked detection into the tracks."""

        self._source_layer = source_layer
        # update_tracks hides all input Labels/Points layers, so re-show the source
        source_layer.visible = True
        if isinstance(source_layer, Labels):
            source_layer.contour = 1
        self._source_callback = self._make_source_callback()
        source_layer.mouse_drag_callbacks.append(self._source_callback)
        # make the source layer active so its click callbacks receive events
        self.viewer.layers.selection.active = source_layer

    def _teardown_source_connection(self) -> None:
        """Disconnect the right-click callback from the previously connected source layer."""

        if self._source_layer is not None and self._source_callback is not None:
            with contextlib.suppress(ValueError):
                self._source_layer.mouse_drag_callbacks.remove(self._source_callback)
        self._source_layer = None
        self._source_callback = None

    def _make_source_callback(self) -> callable:
        """Create the mouse callback that copies a detection on right-click."""

        def callback(layer, event):
            if event.type == "mouse_press" and event.button == 2:
                self._copy_detection(layer, event)

        return callback

    def _copy_detection(self, layer: Labels | Points, event) -> None:
        """Copy the label or point that was right-clicked on the source layer into the
        tracks as a new node with the current tracklet id."""

        if self.tracks_viewer.tracks is None:
            return

        if isinstance(layer, Labels):
            self._copy_label(layer, event)
        else:
            self._copy_point(layer, event)

    def _copy_label(self, layer: Labels, event) -> None:
        """Copy the clicked label (in the clicked time point) into the tracks as a
        segmentation node via an UserAddNode action."""

        value = layer.get_value(
            event.position,
            view_direction=event.view_direction,
            dims_displayed=event.dims_displayed,
            world=True,
        )
        # ignore clicks on the background or outside the data
        if not value:
            return

        coords = layer.world_to_data(event.position)
        t = int(round(coords[0]))
        frame = np.asarray(layer.data[t])
        spatial_coords = np.where(frame == value)
        if spatial_coords[0].size == 0:
            return

        t_array = np.full(spatial_coords[0].size, t, dtype=int)
        pixels = (t_array, *spatial_coords)
        self._add_node(t, pixels=pixels)

    def _copy_point(self, layer: Points, event) -> None:
        """Copy the clicked point into the tracks as a point node via an UserAddNode
        action."""

        index = layer.get_value(
            event.position,
            view_direction=event.view_direction,
            dims_displayed=event.dims_displayed,
            world=True,
        )
        if index is None:
            return

        point = np.asarray(layer.data[index])
        t = int(round(point[0]))
        # tracks store positions in world coordinates (see nodes_from_points_list)
        position = point[1:] * np.asarray(layer.scale[1:])
        self._add_node(t, position=position)

    def _add_node(
        self,
        t: int,
        position: np.ndarray | None = None,
        pixels: tuple[np.ndarray, ...] | None = None,
    ) -> None:
        """Add a node to the tracks with the current tracklet id, from either a position
        (points) or pixels (segmentation)."""

        tracks = self.tracks_viewer.tracks

        if self.tracks_viewer.selected_track is None:
            self.tracks_viewer.set_new_track_id()
        track_id = self.tracks_viewer.selected_track

        features = tracks.features
        attributes = {
            features.time_key: t,
            features.tracklet_key: track_id,
        }
        if position is not None:
            attributes[features.position_key] = position

        try:
            node_id = tracks._get_new_node_ids(1)[0]
            UserAddNode(
                tracks,
                node=node_id,
                attributes=attributes,
                pixels=pixels,
                force=self.tracks_viewer.force,
            )
        except InvalidActionError as e:
            if e.forceable:
                force, always_force = confirm_force_operation(message=str(e))
                self.tracks_viewer.force = always_force
                if force:
                    node_id = tracks._get_new_node_ids(1)[0]
                    UserAddNode(
                        tracks,
                        node=node_id,
                        attributes=attributes,
                        pixels=pixels,
                        force=True,
                    )
            else:
                show_info(str(e))
