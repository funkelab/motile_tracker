from __future__ import annotations

from typing import TYPE_CHECKING

import napari
import numpy as np
from napari.utils import DirectLabelColormap

if TYPE_CHECKING:
    from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


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

        colormap = DirectLabelColormap(
            color_dict={
                **dict(
                    zip(
                        self.node_properties["track_id"],
                        self.node_properties["color"],
                        strict=False,
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
                    t_values = self.node_properties["t"]
                    track_ids = self.node_properties["track_id"]
                    index = np.where(
                        (t_values == event.position[0]) & (track_ids == label)
                    )[0]  # np.where returns a tuple with an array per dimension,
                    # here we apply it to a single dimension so take the first element
                    # (an array of indices fulfilling condition)
                    node_id = self.node_properties["node_id"][index[0]]
                    append = "Shift" in event.modifiers
                    self.tracks_viewer.selected_nodes.add(node_id, append)

        # Listen to paint events and changing the selected label
        self.events.paint.connect(self._on_paint)
        self.events.selected_label.connect(self._check_selected_label)

    def _get_node_properties(self):
        tracks = self.tracks_viewer.tracks
        nodes = list(tracks.graph.nodes())
        track_ids = tracks.get_seg_ids(nodes)
        times = tracks.get_times(nodes)
        colors = [self.tracks_viewer.colormap.map(tid) for tid in track_ids]
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
        tracks = self.tracks_viewer.tracks
        to_delete = []  # (node_ids, pixels)
        to_update_smaller = []  # (node_id, pixels)
        to_update_bigger = []  # (node_id, pixels)
        to_add = []  # (track_id, pixels)
        for pixels, old_value in updated_pixels:
            ndim = len(pixels)
            if old_value == 0:
                continue
            time = pixels[0][0]
            removed_node = tracks.get_node(old_value, time)
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
            for time in np.unique(all_pixels[0]):
                added_node = tracks.get_node(new_value, time)
                if added_node is not None:
                    to_update_bigger.append((added_node, all_pixels))
                else:
                    to_add.append((new_value, all_pixels))

        self.tracks_viewer.tracks_controller.update_segmentations(
            to_delete, to_update_smaller, to_update_bigger, to_add, current_timepoint
        )

    def _refresh(self):
        """Refresh the data in the labels layer"""

        self.data = self.tracks_viewer.tracks.segmentation[:, 0]
        self.node_properties = self._get_node_properties()

        self.colormap = DirectLabelColormap(
            color_dict={
                **dict(
                    zip(
                        self.node_properties["track_id"],
                        self.node_properties["color"],
                        strict=False,
                    )
                ),
                None: [0, 0, 0, 0],
            }
        )

        self.refresh()

    def update_label_colormap(self, visible: list[int] | str) -> None:
        """Updates the opacity of the label colormap to highlight the selected label
        and optionally hide cells not belonging to the current lineage"""

        highlighted = [
            self.tracks_viewer.tracks.get_track_id(node)
            for node in self.tracks_viewer.selected_nodes
            if self.tracks_viewer.tracks.get_time(node)
            == self.viewer.dims.current_step[0]
        ]

        if len(highlighted) > 0:
            self.selected_label = highlighted[
                0
            ]  # set the first track_id to be the selected label color

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
            for label in visible:
                # find the index in the cyclic label colormap
                self.colormap.color_dict[label][-1] = 0.6

        for label in highlighted:
            self.colormap.color_dict[label][-1] = 1  # full opacity

        self.colormap = DirectLabelColormap(
            color_dict=self.colormap.color_dict
        )  # create a new colormap from the updated colors (otherwise it does not refresh)

    def new_colormap(self):
        """Extended version of existing function, to emit refresh signal to also update colors in other layers/widgets"""

        super().new_colormap()
        self.tracks_viewer.colormap = self.colormap
        self.tracks_viewer._refresh()

    def _check_selected_label(self):
        """Check whether the selected label is larger than the current max_track_id and if so add it to the colormap (otherwise it draws in transparent color until the refresh event)"""

        if self.selected_label > self.tracks_viewer.tracks.max_track_id:
            self.events.selected_label.disconnect(
                self._check_selected_label
            )  # disconnect to prevent infinite loop, since setting the colormap emits a selected_label event
            self.colormap.color_dict[self.selected_label] = (
                self.tracks_viewer.colormap.map(self.selected_label)
            )
            self.colormap = DirectLabelColormap(color_dict=self.colormap.color_dict)
            self.events.selected_label.connect(
                self._check_selected_label
            )  # connect again
