from __future__ import annotations

import random
from typing import TYPE_CHECKING

import napari
import numpy as np
from funtracks.exceptions import InvalidActionError
from napari.layers import Labels
from napari.utils import DirectLabelColormap
from napari.utils.action_manager import action_manager
from napari.utils.notifications import show_info

from motile_tracker.data_views.views.layers.click_utils import (
    detect_click,
    get_click_value,
)
from motile_tracker.data_views.views_coordinator.key_binds import (
    KEYMAP,
    bind_keymap,
)

if TYPE_CHECKING:
    from napari.utils.events import Event

    from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


def new_label(layer: TrackLabels):
    """A function to override the default napari labels new_label function.
    Must be registered (see end of this file)"""

    layer.events.selected_label.disconnect(layer._ensure_valid_label)
    _new_label(layer, new_track_id=True)
    layer.events.selected_label.connect(layer._ensure_valid_label)


def _new_label(layer: TrackLabels, new_track_id=True):
    """A function to get a new label for a given TrackLabels layer. Should properly
    go on the class, but needs to be registered to override the default napari function
    in the action manager. This helper is abstracted out because we want to do the same
    thing without making a new track id in the layer, and with the new track id in the
    overriden action.

    Args:
        layer (TrackLabels): A TrackLabels layer from which get a new label for drawing a
            new segmentation. Updates the selected_label attribute.
        new_track_id (bool, optional): If you should also generate a new track id and set
            it to the selected_track attribute. Defaults to True.
    """

    if isinstance(layer.data, np.ndarray):
        new_selected_label = np.max(layer.data) + 1
        if new_track_id or layer.tracks_viewer.selected_track is None:
            layer.tracks_viewer.set_new_track_id()
        layer.selected_label = new_selected_label
        layer.colormap.color_dict[new_selected_label] = (
            layer.tracks_viewer.track_id_color
        )
        # to refresh, otherwise you paint with a transparent label until you
        # release the mouse
        layer.colormap = DirectLabelColormap(color_dict=layer.colormap.color_dict)
    else:
        show_info("Calculating empty label on non-numpy array is not supported")


class TrackLabels(napari.layers.Labels):
    """Extended labels layer that holds the track information and emits
    and responds to dynamics visualization signals"""

    @property
    def _type_string(self) -> str:
        return "labels"  # to make sure that the layer is treated as labels layer for saving

    def __init__(
        self,
        viewer: napari.Viewer,
        data: np.array,
        name: str,
        opacity: float,
        scale: tuple,
        tracks_viewer: TracksViewer,
    ):
        self.tracks_viewer = tracks_viewer
        colormap = self._get_colormap()

        super().__init__(
            data=data,
            name=name,
            opacity=opacity,
            colormap=colormap,
            scale=scale,
        )

        self.viewer = viewer

        # Key bindings (should be specified both on the viewer (in tracks_viewer)
        bind_keymap(self, KEYMAP, self.tracks_viewer)

        # Listen to paint events and changing the selected label
        self.mouse_drag_callbacks.append(self.click)
        self.events.paint.connect(self._on_paint)
        self.tracks_viewer.selected_nodes.list_updated.connect(
            self.update_selected_label
        )
        self.events.mode.connect(self._check_mode)
        self.events.selected_label.connect(self._ensure_valid_label)

    # Connect click events to node selection
    def click(self, _, event):
        if (
            event.type == "mouse_press"
            and self.mode == "pan_zoom"
            and not (
                self.tracks_viewer.mode == "lineage" and self.viewer.dims.ndisplay == 3
            )
        ):  # disable selecting in lineage mode in 3D
            # differentiate between click and drag
            was_click = yield from detect_click(event)
            if was_click:
                value = get_click_value(self, event)
                self.process_click(event, value)

    def assign_new_label(self, event):
        """Function for orthoviews to connect to so the 'm' event can be processed here"""

        new_label(self)

    def process_click(self, event: Event, label: int):
        """Process the click event to update the selected nodes"""

        if (
            label is not None and label != 0 and self.colormap.map(label)[-1] != 0
        ):  # check opacity (=visibility) in the colormap
            append = "Shift" in event.modifiers
            self.tracks_viewer.selected_nodes.add(label, append)

    def _get_colormap(self) -> DirectLabelColormap:
        """Get a DirectLabelColormap that maps node ids to their track ids, and then
        uses the tracks_viewer.colormap to map from track_id to color.

        Returns:
            DirectLabelColormap: A map from node ids to colors based on track id
        """
        tracks = self.tracks_viewer.tracks
        if tracks is not None:
            nodes = list(tracks.graph.nodes())
            track_ids = [tracks.get_track_id(node) for node in nodes]
            colors = [self.tracks_viewer.colormap.map(tid) for tid in track_ids]
        else:
            nodes = []
            colors = []
        return DirectLabelColormap(
            color_dict={
                **dict(zip(nodes, colors, strict=True)),
                None: [0, 0, 0, 0],
            }
        )

    def _check_mode(self):
        """Check if the mode is valid and call the ensure_valid_label function"""
        # here disconnecting the event listener is still necessary because
        # self.mode = paint triggers the event internally and it is not blocked with
        # event.blocker()
        self.events.mode.disconnect(self._check_mode)
        if self.mode == "polygon":
            show_info("Please use the paint tool to update the label")
            self.mode = "paint"

        self.events.mode.connect(self._check_mode)

    def redo(self):
        """Overwrite the redo functionality of the labels layer and invoke redo action on
        the tracks_viewer.tracks_controller first
        """

        self.tracks_viewer.redo()

    def undo(self):
        """Overwrite undo function and invoke undo action on the
        tracks_viewer.tracks_controller
        """

        self.tracks_viewer.undo()

    def _parse_paint_event(self, event_val):
        """_summary_

        Args:
            event_val (list[tuple]): A list of paint "atoms" generated by the labels
                layer. Each atom is a 3-tuple of arrays containing:
                - a numpy multi-index, pointing to the array elements that were
                changed (a tuple with len ndims)
                - the values corresponding to those elements before the change
                - the value after the change
        Returns:
            tuple(int, list[tuple]): The new value, and a list of node update actions
                defined by the time point and node update item
                Each "action" is a 2-tuple containing:
                - a numpy multi-index, pointing to the array elements that were
                changed (a tuple with len ndims)
                - the value before the change
        """

        new_value = event_val[-1][-1]
        ndim = len(event_val[-1][0])
        concatenated_indices = tuple(
            np.concatenate([ev[0][dim] for ev in event_val]) for dim in range(ndim)
        )
        concatenated_values = np.concatenate([ev[1] for ev in event_val])
        old_values = np.unique(concatenated_values)
        actions = []
        for old_value in old_values:
            mask = concatenated_values == old_value
            indices = tuple(concatenated_indices[dim][mask] for dim in range(ndim))
            time_points = np.unique(indices[0])
            for time_point in time_points:
                time_mask = indices[0] == time_point
                actions.append(
                    (tuple(indices[dim][time_mask] for dim in range(ndim)), old_value)
                )
        return new_value, actions

    def _revert_paint(self, _, source_layer: Labels | None = None):
        """Revert a paint event after it fails validation (no motile tracker Actions have
        been created). This keeps the view synced with the backend data.
        been created). If a source_layer is provided, the paint event will be reverted on
        this layer (this is necessary for orthoviews). This keeps the view synced with
        the backend data.
        """
        if source_layer is not None:
            source_layer.undo()  # revert on the orthoview
        else:
            super().undo()

    def _on_paint(self, event):
        """Listen to the paint event and check which track_ids have changed"""

        # make sure that 0 (in the case or erasing) or a valid label (in the case of
        # painting) is selected.
        if (
            self.mode == "erase"
            or (self.mode == "fill" and self.selected_label == 0)
            or (self.mode == "paint" and self.selected_label == 0)
        ):
            target_value = 0
        else:
            self._ensure_valid_label()
            target_value = self.selected_label

        with self.events.selected_label.blocker():
            try:
                current_timepoint = self.viewer.dims.current_step[
                    0
                ]  # also pass on the current time point to know which node to select later
                _, updated_pixels = self._parse_paint_event(event.value)
                self.tracks_viewer.tracks_controller.update_segmentations(
                    target_value,
                    updated_pixels,
                    current_timepoint,
                    self.tracks_viewer.selected_track,
                )  # paint with the updated self.selected_label, not with the value from the
                # event, to ensure it is a valid label.
            except InvalidActionError as e:
                show_info(str(e))
                super().undo()
                new_label(
                    self
                )  # help the user to paint with a new label that should be
                # valid

    def _refresh(self):
        """Refresh the data in the labels layer"""
        self.data = self.tracks_viewer.tracks.segmentation
        self.colormap = self._get_colormap()
        self.refresh()

    def update_label_colormap(self, visible: list[int] | str) -> None:
        """Updates the opacity of the label colormap to highlight the selected label
        and optionally hide cells not belonging to the current lineage

        Visible is a list of visible node id
        """
        with self.events.selected_label.blocker():
            highlighted = self.tracks_viewer.selected_nodes

            # update the opacity of the cyclic label colormap values according to
            # whether nodes are visible/invisible/highlighted
            if visible == "all":
                self.colormap.color_dict = {
                    key: np.array(
                        [
                            *value[:-1],
                            0.6 if key is not None and key != 0 else value[-1],
                        ],
                        dtype=np.float32,
                    )
                    for key, value in self.colormap.color_dict.items()
                }

            else:
                self.colormap.color_dict = {
                    key: np.array([*value[:-1], 0], dtype=np.float32)
                    for key, value in self.colormap.color_dict.items()
                }
                for node in visible:
                    # find the index in the colormap
                    self.colormap.color_dict[node][-1] = 0.6

            for node in highlighted:
                self.colormap.color_dict[node][-1] = 1  # full opacity
            # create a new colormap from the updated colors (to ensure refresh)
            self.colormap = DirectLabelColormap(color_dict=self.colormap.color_dict)

    def new_colormap(self):
        """Override existing function to generate new colormap on tracks_viewer and
        emit refresh signal to update colors in all layers/widgets"""

        self.tracks_viewer.colormap = napari.utils.colormaps.label_colormap(
            49,
            seed=random.uniform(0, 1),
            background_value=0,
        )
        self.tracks_viewer._refresh()

    def update_selected_label(self):
        """Update the selected label in the labels layer"""

        if len(self.tracks_viewer.selected_nodes) > 0:
            node = int(self.tracks_viewer.selected_nodes[0])
            self.selected_label = node
            self.tracks_viewer.selected_track = int(
                self.tracks_viewer.tracks.get_track_id(node)
            )

    def _ensure_valid_label(self, event: Event | None = None):
        """Make sure a valid label is selected, because it is not allowed to paint with a
        label that already exists at a different timepoint.
        Scenarios:
        1. If a node with the selected label value (node id) exists at a different time
            point, check if there is any node with the same track_id at the current time
            point
            1.a if there is a node with the same track id, select that one, so that it
                can be used to update an existing node
            1.b if there is no node with the same track id, create a new node id and
                paint with the track_id of the selected label.
              This can be used to add a new node with the same track id at a time point
              where it does not (yet) exist (anymore).
        2. if there is no existing node with this value in the graph, it is assume that
            you want to add a node with the current track id
        Retrieve the track_id from self.current_track_id and use it to find if there are
        any nodes of this track id at current time point
        3. If no node with this label exists yet, it is valid and can be used to start a
            new track id. Therefore, create a new node id and map a new color.
            Add it to the dictionary.
        4. If a node with the label exists at the current time point, it is valid and
            can be used to update the existing node in a paint event. No action is needed
        """

        update_colormap = False
        if self.tracks_viewer.tracks is not None:
            current_timepoint = self.viewer.dims.current_step[0]
            # if a node with the given label is already in the graph
            if self.tracks_viewer.tracks.graph.has_node(self.selected_label):
                # Update the track id
                self.tracks_viewer.selected_track = (
                    self.tracks_viewer.tracks.get_track_id(self.selected_label)
                )
                existing_time = self.tracks_viewer.tracks.get_time(self.selected_label)
                if existing_time == current_timepoint:
                    # we are changing the existing node. This is fine
                    pass
                else:
                    # if there is already a node in that track in this frame, edit that
                    # instead
                    edit = False
                    if (
                        self.tracks_viewer.selected_track
                        in self.tracks_viewer.tracks.track_id_to_node
                    ):
                        for node in self.tracks_viewer.tracks.track_id_to_node[
                            self.tracks_viewer.selected_track
                        ]:
                            if (
                                self.tracks_viewer.tracks.get_time(node)
                                == current_timepoint
                            ):
                                self.selected_label = int(node)
                                edit = True
                                break

                    if not edit:
                        # use a new label, but the same track id
                        _new_label(self, new_track_id=False)
                        self.colormap = DirectLabelColormap(
                            color_dict=self.colormap.color_dict
                        )

            # the current node does not exist in the graph.
            # Use the current selected_track as the track id (will be a new track if a
            # new label was found with "m")
            # Check that the track id is not already in this frame.
            else:
                # if there is already a node in that track in this frame, edit that
                # instead
                if (
                    self.tracks_viewer.selected_track
                    in self.tracks_viewer.tracks.track_id_to_node
                ):
                    for node in self.tracks_viewer.tracks.track_id_to_node[
                        self.tracks_viewer.selected_track
                    ]:
                        if (
                            self.tracks_viewer.tracks.get_time(node)
                            == current_timepoint
                        ):
                            self.selected_label = int(node)
                            break

                elif self.tracks_viewer.selected_track is None:
                    self.tracks_viewer.selected_track = (
                        self.tracks_viewer.tracks.get_next_track_id()
                    )
                    update_colormap = True

        # update color and emit signal
        self.tracks_viewer.set_track_id_color(self.tracks_viewer.selected_track)
        if update_colormap:
            self.colormap.color_dict[self.selected_label] = (
                self.tracks_viewer.track_id_color
            )
            with self.events.selected_label.blocker():
                self.colormap = DirectLabelColormap(
                    color_dict=self.colormap.color_dict
                )  # refresh
        self.tracks_viewer.update_track_id.emit()

    @napari.layers.Labels.n_edit_dimensions.setter
    def n_edit_dimensions(self, n_edit_dimensions):
        # Overriding the setter to disable editing in time dimension
        if n_edit_dimensions > self.tracks_viewer.tracks.ndim - 1:
            n_edit_dimensions = self.tracks_viewer.tracks.ndim - 1
        self._n_edit_dimensions = n_edit_dimensions
        self.events.n_edit_dimensions()


# This is to override the default napari function to get a new label for the labels layer
action_manager.register_action(
    name="napari:new_label",
    command=new_label,
    keymapprovider=TrackLabels,
    description="",
)
TrackLabels.bind_key("m", overwrite=True)(new_label)
