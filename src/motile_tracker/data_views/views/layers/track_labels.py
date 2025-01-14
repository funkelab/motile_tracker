from __future__ import annotations

import random
from typing import TYPE_CHECKING

import napari
import numpy as np
from napari.utils import DirectLabelColormap
from napari.utils.action_manager import action_manager
from napari.utils.notifications import show_info
from napari.utils.translations import trans

if TYPE_CHECKING:
    from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer
from motile_toolbox.candidate_graph.graph_attributes import NodeAttr


def new_label(layer: TrackLabels):
    """Set the currently selected label to the largest used label plus one."""
    _new_label(layer, new_track_id=True)


def _new_label(layer: TrackLabels, new_track_id=True):
    if isinstance(layer.data, np.ndarray):
        new_selected_label = np.max(layer.data) + 1
        if layer.selected_label == new_selected_label:
            show_info(
                trans._(
                    "Current selected label is not being used. You will need to use it first "
                    "to be able to set the current select label to the next one available",
                )
            )
        else:
            layer.selected_label = new_selected_label
            if new_track_id:
                new_selected_track = layer.tracks_viewer.tracks.get_next_track_id()
                layer.selected_track = new_selected_track
            layer.colormap.color_dict[new_selected_label] = (
                layer.tracks_viewer.colormap.map(layer.selected_track)
            )
            layer.colormap = DirectLabelColormap(
                color_dict=layer.colormap.color_dict
            )  # to refresh, otherwise you paint with a transparent label until you release the mouse
    else:
        show_info(
            trans._("Calculating empty label on non-numpy array is not supported")
        )


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
        self.node_properties = self._get_node_properties()
        self.selected_track = None

        colormap = DirectLabelColormap(
            color_dict={
                **dict(
                    zip(
                        self.node_properties["node_id"],
                        self.node_properties["color"],
                        strict=True,
                    )
                ),
                None: [0, 0, 0, 0],
            }
        )

        super().__init__(
            data=data,
            name=name,
            opacity=opacity,
            colormap=colormap,
            scale=scale,
        )

        self.viewer = viewer

        # Key bindings (should be specified both on the viewer (in tracks_viewer)
        # and on the layer to overwrite napari defaults)
        self.bind_key("q")(self.tracks_viewer.toggle_display_mode)
        self.bind_key("a")(self.tracks_viewer.create_edge)
        self.bind_key("d")(self.tracks_viewer.delete_node)
        self.bind_key("Delete")(self.tracks_viewer.delete_node)
        self.bind_key("b")(self.tracks_viewer.delete_edge)
        # self.bind_key("s")(self.tracks_viewer.set_split_node)
        # self.bind_key("e")(self.tracks_viewer.set_endpoint_node)
        # self.bind_key("c")(self.tracks_viewer.set_linear_node)
        self.bind_key("z")(self.tracks_viewer.undo)
        self.bind_key("r")(self.tracks_viewer.redo)

        # Connect click events to node selection
        @self.mouse_drag_callbacks.append
        def click(_, event):
            if (
                event.type == "mouse_press"
                and self.mode == "pan_zoom"
                and not (
                    self.tracks_viewer.mode == "lineage"
                    and self.viewer.dims.ndisplay == 3
                )
            ):  # disable selecting in lineage mode in 3D
                label = self.get_value(
                    event.position,
                    view_direction=event.view_direction,
                    dims_displayed=event.dims_displayed,
                    world=True,
                )

                if (
                    label is not None
                    and label != 0
                    and self.colormap.map(label)[-1] != 0
                ):  # check opacity (=visibility) in the colormap
                    append = "Shift" in event.modifiers
                    self.tracks_viewer.selected_nodes.add(label, append)

        # Listen to paint events and changing the selected label
        self.events.paint.connect(self._on_paint)
        self.tracks_viewer.selected_nodes.list_updated.connect(
            self.update_selected_label
        )
        self.events.selected_label.connect(self._ensure_valid_label)
        self.viewer.dims.events.current_step.connect(self._ensure_valid_label)

    def _get_node_properties(self):
        tracks = self.tracks_viewer.tracks
        if tracks is not None:
            nodes = list(tracks.graph.nodes())
            track_ids = [tracks.get_track_id(node) for node in nodes]
            times = tracks.get_times(nodes)
            colors = [self.tracks_viewer.colormap.map(tid) for tid in track_ids]
        else:
            nodes = []
            track_ids = []
            times = []
            colors = []
        return {"node_id": nodes, "track_id": track_ids, "t": times, "color": colors}

    def redo(self):
        """Overwrite the redo functionality of the labels layer and invoke redo action on the tracks_viewer.tracks_controller first"""

        self.tracks_viewer.redo()

    def undo(self):
        """Overwrite undo function and invoke undo action on the tracks_viewer.tracks_controller"""

        self.tracks_viewer.undo()

    def _parse_paint_event(self, event_val):
        """_summary_

        Args:
            event_val (list[tuple]): A list of paint "atoms" generated by the labels layer.
                Each atom is a 3-tuple of arrays containing:
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
            for time in time_points:
                time_mask = indices[0] == time
                actions.append(
                    (tuple(indices[dim][time_mask] for dim in range(ndim)), old_value)
                )
        return new_value, actions

    def _on_paint(self, event):
        """Listen to the paint event and check which track_ids have changed"""

        current_timepoint = self.viewer.dims.current_step[
            0
        ]  # also pass on the current time point to know which node to select later
        new_value, updated_pixels = self._parse_paint_event(event.value)
        # updated_pixels is a list of tuples. Each tuple is (indices, old_value)
        to_delete = []  # (node_ids, pixels)
        to_update_smaller = []  # (node_id, pixels)
        to_update_bigger = []  # (node_id, pixels)
        to_add = []  # (track_id, pixels)
        for pixels, old_value in updated_pixels:
            ndim = len(pixels)
            if old_value == 0:
                continue
            time = pixels[0][0]
            removed_node = old_value
            assert (
                removed_node is not None
            ), f"Node with label {old_value} in time {time} was not found"
            # check if all pixels of old_value are removed
            if np.sum(self.data[time] == old_value) == 0:
                to_delete.append((removed_node, pixels))
            else:
                to_update_smaller.append((removed_node, pixels))
        if new_value != 0:
            all_pixels = tuple(
                np.concatenate([pixels[dim] for pixels, _ in updated_pixels])
                for dim in range(ndim)
            )
            for _ in np.unique(all_pixels[0]):
                existing_node = self.tracks_viewer.tracks.graph.has_node(new_value)
                if existing_node:
                    to_update_bigger.append((new_value, all_pixels))
                else:
                    to_add.append((new_value, self.selected_track, all_pixels))

        self.tracks_viewer.tracks_controller.update_segmentations(
            to_delete, to_update_smaller, to_update_bigger, to_add, current_timepoint
        )

    def _refresh(self):
        """Refresh the data in the labels layer"""

        self.data = self.tracks_viewer.tracks.segmentation
        self.node_properties = self._get_node_properties()

        self.colormap = DirectLabelColormap(
            color_dict={
                **dict(
                    zip(
                        self.node_properties["node_id"],
                        self.node_properties["color"],
                        strict=True,
                    )
                ),
                None: [0, 0, 0, 0],
            }
        )

        self.refresh()

    def update_label_colormap(self, visible: list[int] | str) -> None:
        """Updates the opacity of the label colormap to highlight the selected label
        and optionally hide cells not belonging to the current lineage

        Visible is a list of visible node ids"""

        highlighted = self.tracks_viewer.selected_nodes

        # update the opacity of the cyclic label colormap values according to whether nodes are visible/invisible/highlighted
        if visible == "all":
            self.colormap.color_dict = {
                key: np.array(
                    [*value[:-1], 0.6 if key is not None and key != 0 else value[-1]],
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

        # This is the minimal set of things necessary to get the updates to display ## For me this does not work, the highlighting is out of sync or not displayed at all
        # self.colormap._clear_cache()
        # self.events.colormap()

        self.colormap = DirectLabelColormap(
            color_dict=self.colormap.color_dict
        )  # create a new colormap from the updated colors (otherwise it does not refresh)

    def new_colormap(self):
        """Replace existing function, to generate new colormap and emit refresh signal to also update colors in other layers/widgets"""

        self.tracks_viewer.colormap = napari.utils.colormaps.label_colormap(
            49,
            seed=random.uniform(0, 1),
            background_value=0,
        )

        track_ids = [
            self.tracks_viewer.tracks.get_track_id(node)
            for node in self.tracks_viewer.tracks.graph.nodes
        ]
        self.node_properties["colors"] = [
            self.tracks_viewer.colormap.map(tid) for tid in track_ids
        ]
        self.tracks_viewer._refresh()

    def update_selected_label(self):
        """Update the selected label in the labels layer"""

        if len(self.tracks_viewer.selected_nodes) > 0:
            self.selected_label = self.tracks_viewer.selected_nodes[0]

    def _ensure_valid_label(self, event):
        """Make sure a valid label is selected, because it is not allowed to paint with a
        label that already exists at a different timepoint.
        Scenarios:
        1. If a node with the selected label value (node id) exists at a different time point,
        check if there is any node with the same track_id at the current time point
            1.a if there is a node with the same track id, select that one, so that it can be used to update an existing node
            1.b if there is no node with the same track id, create a new node id and paint with the track_id of the selected label.
              This can be used to add a new node with the same track id at a time point where it does not (yet) exist (anymore).
        2. if there is no existing node with this value in the graph, it is assume that you want to add a node with the current track id
        Retrieve the track_id from self.current_track_id and use it to find if there are any nodes of this track id
        at current time point
        3. If no node with this label exists yet, it is valid and can be used to start a new track id.
        Therefore, create a new node id and map a new color. Add it to the dictionary.
        4. If a node with the label exists at the current time point, it is valid and can be used to update the existing node in a paint event. No action is needed"""

        self.events.selected_label.disconnect(self._ensure_valid_label)
        if self.tracks_viewer.tracks is not None:
            current_timepoint = self.viewer.dims.current_step[0]
            # if a node with the given label is already in the graph
            if self.tracks_viewer.tracks.graph.has_node(self.selected_label):
                # Update the track id
                self.selected_track = self.tracks_viewer.tracks._get_node_attr(
                    self.selected_label, NodeAttr.TRACK_ID.value
                )
                existing_time = self.tracks_viewer.tracks._get_node_attr(
                    self.selected_label, NodeAttr.TIME.value
                )
                if existing_time == current_timepoint:
                    # we are changing the existing node. This is fine
                    pass
                else:
                    # if there is already a node in that track in this frame, edit that instead
                    edit = False
                    if (
                        self.selected_track
                        in self.tracks_viewer.tracks.track_id_to_node
                    ):
                        for node in self.tracks_viewer.tracks.track_id_to_node[
                            self.selected_track
                        ]:
                            if (
                                self.tracks_viewer.tracks._get_node_attr(
                                    node, NodeAttr.TIME.value
                                )
                                == current_timepoint
                            ):
                                # raise ValueError("Can't add new node with track id {self.selected_track} in time {current_timepoint}")

                                self.selected_label = node
                                edit = True
                                break

                    if not edit:
                        # use a new label, but the same track id
                        _new_label(self, new_track_id=False)
                        self.colormap = DirectLabelColormap(
                            color_dict=self.colormap.color_dict
                        )

            # the current node does not exist in the graph.
            # Use the current selected_track as the track id (will be a new track if a new label was found with "m")
            #  Check that the track id is not already in this frame.
            else:
                # if there is already a node in that track in this frame, edit that instead
                edit = False
                if self.selected_track in self.tracks_viewer.tracks.track_id_to_node:
                    for node in self.tracks_viewer.tracks.track_id_to_node[
                        self.selected_track
                    ]:
                        if (
                            self.tracks_viewer.tracks._get_node_attr(
                                node, NodeAttr.TIME.value
                            )
                            == current_timepoint
                        ):
                            self.selected_label = node
                            edit = True
                            break
        self.events.selected_label.connect(self._ensure_valid_label)


action_manager.register_action(
    name="napari:new_label",
    command=new_label,
    keymapprovider=TrackLabels,
    description="",
)
