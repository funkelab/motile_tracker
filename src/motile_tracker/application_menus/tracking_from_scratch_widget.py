import contextlib
import weakref

import napari
import numpy as np
from fonticon_fa6 import FA6S
from funtracks.data_model import SolutionTracks
from funtracks.exceptions import InvalidActionError
from funtracks.user_actions import UserAddNode, UserUpdateSegmentation
from funtracks.utils.tracksdata_utils import create_empty_graphview_graph
from napari.layers import Image, Labels, Points
from napari.utils.notifications import show_info
from psygnal import Signal
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from superqt.fonticon import icon as qticon

from motile_tracker.application_menus.editing_selection_menu import NewTrackWidget
from motile_tracker.data_views.views.layers.track_labels import TrackLabels
from motile_tracker.data_views.views.layers.track_points import TrackPoints
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer
from motile_tracker.data_views.views_coordinator.user_dialogs import (
    confirm_force_operation,
)


class LayerDropdown(QComboBox):
    """QComboBox widget with functions for updating the selected layer and to update the
    list of options when the list of layers is modified."""

    layer_changed = Signal(str)

    def __init__(
        self,
        viewer: napari.Viewer,
        layer_types: tuple,
        allow_none=False,
        exclude_types: tuple = (),
    ):
        super().__init__()

        self.viewer = viewer
        self.layer_types = layer_types
        self.exclude_types = exclude_types
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
        if isinstance(layer, self.layer_types) and not isinstance(
            layer, self.exclude_types
        ):
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
                    and not isinstance(selected, self.exclude_types)
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
                and not isinstance(layer, self.exclude_types)
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

    def set_layer_types(self, layer_types: tuple, exclude_types: tuple = ()) -> None:
        """Change which layer types are listed (and which to exclude) and refresh."""

        self.layer_types = layer_types
        self.exclude_types = exclude_types
        self._update_dropdown()

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

        # the source layer that is currently connected as a copy source, its target
        # track layer, the right-click callback attached to the source, and the current
        # tracking mode ("points" or "labels", set by the start buttons)
        self._source_layer = None
        self._target_layer = None
        self._source_callback = None
        self._mode = None

        exp = QLabel()
        exp.setWordWrap(True)
        exp.setTextFormat(Qt.MarkdownText)
        exp.setText(
            "**Manual tracking**\n\n"
            "*Create an empty tree with either point or label tracks. Then connect a "
            "source layer to copy detections from: right-click (or use the button) to "
            "copy the clicked detection into the tracks with the current tracklet id.*"
        )

        # --- Box 1: create an empty tree --------------------------------------------
        create_box = QGroupBox("Create empty tracks")
        create_layout = QVBoxLayout(create_box)
        create_layout.addWidget(
            QLabel("Select an Image or Labels layer (defines the array size)")
        )
        self.size_layer_dropdown = LayerDropdown(self.viewer, (Image, Labels))
        self._detach_dropdown_autoselect(self.size_layer_dropdown)
        self.size_layer_dropdown.layer_changed.connect(self._update_buttons)
        create_layout.addWidget(self.size_layer_dropdown)

        start_row = QHBoxLayout()
        self.start_points_btn = QPushButton("Tracking with Points")
        self.start_points_btn.clicked.connect(lambda: self._start_tracking("points"))
        self.start_labels_btn = QPushButton("Tracking with Labels")
        self.start_labels_btn.clicked.connect(lambda: self._start_tracking("labels"))
        start_row.addWidget(self.start_points_btn)
        start_row.addWidget(self.start_labels_btn)
        create_layout.addLayout(start_row)

        # --- Box 2: connect a source layer ------------------------------------------
        source_box = QGroupBox("Copy from source layer")
        source_layout = QVBoxLayout(source_box)
        source_layout.addWidget(QLabel("Select a source layer to copy detections from"))
        self.source_layer_dropdown = LayerDropdown(
            self.viewer,
            (Labels, Points),
            exclude_types=(TrackLabels, TrackPoints),
        )
        self._detach_dropdown_autoselect(self.source_layer_dropdown)
        self.source_layer_dropdown.layer_changed.connect(
            self._on_source_dropdown_changed
        )
        source_layout.addWidget(self.source_layer_dropdown)

        self.chain_btn = QPushButton()
        self.chain_btn.setCheckable(True)
        self.chain_btn.setEnabled(False)
        self.chain_btn.toggled.connect(self._on_chain_toggled)
        self._set_chain_icon(connected=False)
        source_layout.addWidget(self.chain_btn)

        # Controls to copy detections into the tracks, only shown while a source
        # is connected and its layer (or its track layer) is the active layer.
        self.copy_controls_box = QGroupBox("Copy detections into tracks")
        copy_controls_layout = QVBoxLayout(self.copy_controls_box)
        # current track id + "start new track" (same widget as in the Editing menu)
        self.new_track_widget = NewTrackWidget(self.tracks_viewer)
        copy_controls_layout.addWidget(self.new_track_widget)
        self.add_label_btn = QPushButton("Add selected label to track")
        self.add_label_btn.clicked.connect(self._add_selected_label)
        copy_controls_layout.addWidget(self.add_label_btn)
        self.switch_layer_btn = QPushButton("Switch source / target layer [\\]")
        self.switch_layer_btn.clicked.connect(self._switch_layer)
        copy_controls_layout.addWidget(self.switch_layer_btn)
        self.copy_controls_box.setVisible(False)

        # show/hide the copy controls depending on the active layer
        self.viewer.layers.selection.events.active.connect(
            self._update_copy_controls_visibility
        )

        layout = QVBoxLayout(self)
        layout.addWidget(exp)
        layout.addWidget(create_box)
        layout.addWidget(source_box)
        layout.addWidget(self.copy_controls_box)
        layout.addStretch(0)

        self._update_buttons()

    def _detach_dropdown_autoselect(self, dropdown: LayerDropdown) -> None:
        """Stop a LayerDropdown from following the active layer, so it only changes when
        the user explicitly picks a layer from it."""

        with contextlib.suppress(TypeError, RuntimeError):
            dropdown.viewer.layers.selection.events.changed.disconnect(
                dropdown._on_selection_changed
            )

    def _update_buttons(self, *args) -> None:
        """Enable the start buttons only when a size layer is selected."""

        has_size = self.size_layer_dropdown.selected_layer is not None
        self.start_points_btn.setEnabled(has_size)
        self.start_labels_btn.setEnabled(has_size)

    def _start_tracking(self, mode: str) -> None:
        """Create a new empty tree with empty TrackPoints/TrackGraph layers (and a
        TrackLabels layer for ``mode == 'labels'``). The array size is taken from the
        selected Image/Labels layer. Detections are copied in later by connecting a
        source layer (see the chain button).

        Args:
            mode (str): "points" to track with points, "labels" to track with a
                segmentation.
        """

        layer = self.size_layer_dropdown.selected_layer
        if layer is None:
            return

        # a new tree replaces any previously connected source
        self._reset_chain()
        self._teardown_source_connection()

        if mode == "labels":
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
                ndim=layer.data.ndim,
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

        self._mode = mode
        # only allow source layers of the matching type (excluding the track layers)
        if mode == "labels":
            self.source_layer_dropdown.set_layer_types(
                (Labels,), exclude_types=(TrackLabels,)
            )
        else:
            self.source_layer_dropdown.set_layer_types(
                (Points,), exclude_types=(TrackPoints,)
            )
        self._update_source_controls()

    def _set_chain_icon(self, connected: bool) -> None:
        """Show a closed chain icon when connected, an open (broken) chain when not."""

        if connected:
            self.chain_btn.setIcon(qticon(FA6S.link, color="white"))
            self.chain_btn.setText("Source connected")
        else:
            self.chain_btn.setIcon(qticon(FA6S.link_slash, color="white"))
            self.chain_btn.setText("Connect source")

    def _reset_chain(self) -> None:
        """Set the chain button back to the disconnected (unchecked) state without
        triggering a toggle."""

        self.chain_btn.blockSignals(True)
        self.chain_btn.setChecked(False)
        self.chain_btn.blockSignals(False)
        self._set_chain_icon(connected=False)

    def _update_source_controls(self) -> None:
        """Enable the chain button only when a mode is active and a valid source layer is
        selected."""

        self.chain_btn.setEnabled(
            self._mode is not None
            and self.source_layer_dropdown.selected_layer is not None
        )

    def _on_source_dropdown_changed(self, name=None) -> None:
        """React to the user picking a different source layer. If a source is already
        connected, switch the connection to the newly selected layer."""

        self._update_source_controls()
        if not self.chain_btn.isChecked():
            return

        source = self.source_layer_dropdown.selected_layer
        if source is self._source_layer:
            return
        self._teardown_source_connection()
        if source is not None:
            self._setup_source_connection(source)
        else:
            self._reset_chain()

    def _on_chain_toggled(self, checked: bool) -> None:
        """Connect (closed chain) or disconnect (open chain) the selected source layer."""

        if checked:
            source = self.source_layer_dropdown.selected_layer
            if source is None or self._mode is None:
                self._reset_chain()
                return
            self._teardown_source_connection()
            self._setup_source_connection(source)
            self._set_chain_icon(connected=True)
        else:
            self._teardown_source_connection()
            self._set_chain_icon(connected=False)

    def _setup_source_connection(self, source_layer: Labels | Points) -> None:
        """Keep the detections layer visible and attach a right-click callback that copies
        the clicked detection into the tracks."""

        self._source_layer = source_layer
        self._target_layer = self._get_target_layer()
        # update_tracks hides all input Labels/Points layers, so re-show the source
        source_layer.visible = True
        if isinstance(source_layer, Labels):
            source_layer.contour = 1
        self._source_callback = self._make_source_callback()
        source_layer.mouse_drag_callbacks.append(self._source_callback)
        # expose the copy function so orthogonal-view copies of the source layer can
        # forward their right-clicks to it (see source_layer_hook in ortho_views.py)
        source_layer._manual_copy_detection = self._copy_detection

        # Bind the '\' key to switch between source and target layer. We bind it on both
        # layers (rather than the viewer) so it works whenever either is the active layer,
        # including in the orthogonal views (source_layer_hook binds the ortho copies).
        for layer in (source_layer, self._target_layer):
            if layer is not None:
                layer._manual_switch_layer = self._switch_layer
                layer.bind_key("\\", self._switch_layer_key, overwrite=True)

        # color the 'add selected label' button border with the selected label color
        if isinstance(source_layer, Labels):
            source_layer.events.selected_label.connect(self._update_add_label_border)
            self._update_add_label_border()

        # make the source layer active so its click callbacks receive events
        self.viewer.layers.selection.active = source_layer
        self._update_copy_controls_visibility()

    def _teardown_source_connection(self) -> None:
        """Disconnect the right-click callback and shortcuts from the previously connected
        source and target layers."""

        if isinstance(self._source_layer, Labels):
            with contextlib.suppress(TypeError, RuntimeError):
                self._source_layer.events.selected_label.disconnect(
                    self._update_add_label_border
                )

        for layer in (self._source_layer, self._target_layer):
            if layer is None:
                continue
            with contextlib.suppress(AttributeError):
                del layer._manual_switch_layer
            with contextlib.suppress(Exception):
                layer.bind_key("\\", None, overwrite=True)

        if self._source_layer is not None:
            if self._source_callback is not None:
                with contextlib.suppress(ValueError):
                    self._source_layer.mouse_drag_callbacks.remove(
                        self._source_callback
                    )
            with contextlib.suppress(AttributeError):
                del self._source_layer._manual_copy_detection

        self._source_layer = None
        self._target_layer = None
        self._source_callback = None
        self._update_copy_controls_visibility()

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
        """Copy the clicked label (in the clicked time point) into the target
        segmentation via an UserUpdateSegmentation action."""

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

        self._add_segmentation_node(t, spatial_coords)

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

    def _add_node(self, t: int, position: np.ndarray) -> None:
        """Add a point node to the tracks with the current tracklet id, at the given
        position (used for Points sources)."""

        tracks = self.tracks_viewer.tracks

        if self.tracks_viewer.selected_track is None:
            self.tracks_viewer.set_new_track_id()
        track_id = self.tracks_viewer.selected_track

        features = tracks.features
        attributes = {
            features.time_key: t,
            features.tracklet_key: track_id,
            features.position_key: position,
        }

        try:
            node_id = tracks._get_new_node_ids(1)[0]
            UserAddNode(
                tracks,
                node=node_id,
                attributes=attributes,
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
                        force=True,
                    )
            else:
                show_info(str(e))

    def _add_segmentation_node(
        self, t: int, spatial_coords: tuple[np.ndarray, ...]
    ) -> None:
        """Copy a label into the target segmentation at time ``t``, fully replacing those
        pixels. The new node takes the current tracklet id; any existing node at those
        pixels is shrunk, or deleted entirely if all of its pixels were overwritten.

        Args:
            t (int): The time point of the copied label.
            spatial_coords (tuple[np.ndarray, ...]): The spatial (non-time) coordinates of
                the label pixels, as returned by ``np.where`` on a single time frame.
        """

        tracks = self.tracks_viewer.tracks
        if tracks.segmentation is None:
            return

        if self.tracks_viewer.selected_track is None:
            self.tracks_viewer.set_new_track_id()
        track_id = self.tracks_viewer.selected_track

        t_array = np.full(spatial_coords[0].size, t, dtype=int)
        pixels = (t_array, *spatial_coords)

        # Read the node ids currently occupying those pixels in the target segmentation,
        # grouped so UserUpdateSegmentation can shrink/delete the overwritten nodes.
        target_frame = np.asarray(tracks.segmentation[t])
        old_values = target_frame[spatial_coords]
        updated_pixels = [
            (tuple(dim[old_values == old_value] for dim in pixels), int(old_value))
            for old_value in np.unique(old_values)
        ]

        def apply(force: bool) -> None:
            UserUpdateSegmentation(
                tracks,
                new_value=tracks._get_new_node_ids(1)[0],
                updated_pixels=updated_pixels,
                current_track_id=track_id,
                force=force,
            )

        try:
            apply(self.tracks_viewer.force)
        except InvalidActionError as e:
            if e.forceable:
                force, always_force = confirm_force_operation(message=str(e))
                self.tracks_viewer.force = always_force
                if force:
                    apply(True)
            else:
                show_info(str(e))

    def _get_target_layer(self) -> Labels | Points | None:
        """Return the track layer that copies go into, based on the active mode: the
        TrackLabels layer for 'labels', the TrackPoints layer for 'points'."""

        if self._mode == "labels":
            return self.tracks_viewer.tracking_layers.seg_layer
        if self._mode == "points":
            return self.tracks_viewer.tracking_layers.points_layer
        return None

    def _update_copy_controls_visibility(self, event=None) -> None:
        """Show the copy controls only while a source layer is connected and either the
        source or its target track layer is the active layer."""

        if self._source_layer is None:
            self.copy_controls_box.setVisible(False)
            return

        active = self.viewer.layers.selection.active
        on_source = active is self._source_layer
        self.copy_controls_box.setVisible(
            on_source or active is self._get_target_layer()
        )
        # 'add selected label' only makes sense on the source layer
        self.add_label_btn.setEnabled(on_source)

    def _switch_layer(self, *args) -> None:
        """Toggle the active layer between the source detections layer and its target
        track layer."""

        if self._source_layer is None:
            return

        target = self._get_target_layer()
        active = self.viewer.layers.selection.active
        if active is self._source_layer and target is not None:
            new_active = target
        else:
            new_active = self._source_layer
        new_active.visible = True
        self.viewer.layers.selection.active = new_active

    def _switch_layer_key(self, layer=None) -> None:
        """Keybinding handler ('\\' key) to switch between source and target layer."""

        self._switch_layer()

    def _update_add_label_border(self, event=None) -> None:
        """Color the 'add selected label' button border with the color of the currently
        selected label in the source layer."""

        layer = self._source_layer
        if not isinstance(layer, Labels):
            return
        color = np.asarray(layer.colormap.map(layer.selected_label)).flatten()
        r, g, b = (int(c * 255) for c in color[:3])
        a = float(color[3])
        self.add_label_btn.setStyleSheet(
            f"QPushButton {{ border: 2px solid rgba({r}, {g}, {b}, {a}); padding: 5px; }}"
        )

    def _add_selected_label(self, *args) -> None:
        """Copy the currently selected label (or selected point) from the source layer into
        the tracks, at the current time point. Same effect as right-clicking the detection."""

        if self._source_layer is None or self.tracks_viewer.tracks is None:
            return

        layer = self._source_layer
        t = int(self.viewer.dims.current_step[0])

        if isinstance(layer, Labels):
            value = layer.selected_label
            if not value:
                show_info("No label selected on the source layer.")
                return
            frame = np.asarray(layer.data[t])
            spatial_coords = np.where(frame == value)
            if spatial_coords[0].size == 0:
                show_info(f"Label {value} not found at t={t}.")
                return
            self._add_segmentation_node(t, spatial_coords)
        else:
            selected = list(layer.selected_data)
            if not selected:
                show_info("No point selected on the source layer.")
                return
            for idx in selected:
                point = np.asarray(layer.data[idx])
                pt_t = int(round(point[0]))
                position = point[1:] * np.asarray(layer.scale[1:])
                self._add_node(pt_t, position=position)
