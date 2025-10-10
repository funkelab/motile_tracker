from __future__ import annotations

import math
from typing import TYPE_CHECKING

import napari
import numpy as np
from funtracks.data_model import NodeType, Tracks
from napari.layers.points._points_mouse_bindings import select
from napari.utils.notifications import show_info
from psygnal import Signal

from motile_tracker.data_views.graph_attributes import NodeAttr
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


def custom_select(layer: napari.layers.Points, event: Event):
    """Block the current_size signal when selecting points to avoid changing the point
    size by accident."""

    with layer.events.current_size.blocker():
        yield from select(layer, event)


class TrackPoints(napari.layers.Points):
    """Extended points layer that holds the track information and emits and
    responds to dynamics visualization signals
    """

    # overwrite the select function to block the current_size event signal
    _drag_modes = napari.layers.Points._drag_modes.copy()
    _drag_modes[napari.layers.Points._modeclass.SELECT] = custom_select
    data_updated = Signal()

    @property
    def _type_string(self) -> str:
        return "points"  # to make sure that the layer is treated as points layer for saving

    def __init__(
        self,
        name: str,
        tracks_viewer: TracksViewer,
    ):
        self.tracks_viewer = tracks_viewer
        self.nodes = list(tracks_viewer.tracks.graph.nodes)
        self.node_index_dict = {node: idx for idx, node in enumerate(self.nodes)}

        points = self.tracks_viewer.tracks.get_positions(self.nodes, incl_time=True)
        track_ids = [
            self.tracks_viewer.tracks.graph.nodes[node][NodeAttr.TRACK_ID.value]
            for node in self.nodes
        ]
        colors = [self.tracks_viewer.colormap.map(track_id) for track_id in track_ids]
        symbols = self.get_symbols(
            self.tracks_viewer.tracks, self.tracks_viewer.symbolmap
        )

        self.default_size = 5

        super().__init__(
            data=points,
            name=name,
            symbol=symbols,
            face_color=colors,
            size=self.default_size,
            properties={
                "node_id": self.nodes,
                "track_id": track_ids,
            },  # TODO: use features
            border_color=[1, 1, 1, 1],
            blending="translucent_no_depth",
        )

        # Key bindings (should be specified both on the viewer (in tracks_viewer)
        bind_keymap(self, KEYMAP, self.tracks_viewer)

        # Connect to click events to select nodes
        @self.mouse_drag_callbacks.append
        def click(layer, event):
            if event.type == "mouse_press":
                was_click = yield from detect_click(event)
                if was_click:
                    # find the point matching the click location, if any. Warning: the
                    # search area depends on the point size. If points are large and
                    # overlapping, this may result in the wrong value being returned.
                    value = get_click_value(self, event)
                    self.process_click(event, value)

        # listen to updates of the data
        self.events.data.connect(self._update_data)

        # connect to changing the point size in the UI (see note)
        self.events.current_size.connect(
            lambda: self.set_point_size(size=self.current_size)
        )

        # listen to updates in the selected data (from the point selection tool)
        # to update the nodes in self.tracks_viewer.selected_nodes
        self.selected_data.events.items_changed.connect(self._update_selection)

    def add(self, coords: list[float]):
        """Block the current_size event before calling the 'add' function to avoid calling
        set_point_size (triggered by the current_size event) with a new point size."""

        with self.events.current_size.blocker():
            super().add(coords)

    def process_click(self, event: Event, point_index: int | None):
        """Select the clicked point(s)"""

        if point_index is None:
            self.tracks_viewer.selected_nodes.reset()
        else:
            node_id = self.nodes[point_index]
            append = "Shift" in event.modifiers
            self.tracks_viewer.selected_nodes.add(node_id, append)

    def set_point_size(self, size: int) -> None:
        """Sets a new default point size.
        NOTE: This function call is triggered by the current_size event, which is emitted
        when the user moves the 'point size' slider in the layer controls. However, this
        event is also emitted in the 'add' and 'select' functions, so we have to block the
         signals there to avoid increasing the point size by accident, since new or
        selected points are displayed at a 30% bigger size."""

        self.default_size = size
        self._refresh()

    def _refresh(self):
        """Refresh the data in the points layer"""

        self.events.data.disconnect(
            self._update_data
        )  # do not listen to new events until updates are complete
        self.nodes = list(self.tracks_viewer.tracks.graph.nodes)

        self.node_index_dict = {node: idx for idx, node in enumerate(self.nodes)}

        track_ids = [
            self.tracks_viewer.tracks.graph.nodes[node][NodeAttr.TRACK_ID.value]
            for node in self.nodes
        ]
        self.data = self.tracks_viewer.tracks.get_positions(self.nodes, incl_time=True)
        self.data_updated.emit()  # emit update signal for the orthogonal views to connect to

        self.symbol = self.get_symbols(
            self.tracks_viewer.tracks, self.tracks_viewer.symbolmap
        )
        self.face_color = [
            self.tracks_viewer.colormap.map(track_id) for track_id in track_ids
        ]
        self.properties = {"node_id": self.nodes, "track_id": track_ids}
        self.size = self.default_size
        self.border_color = [1, 1, 1, 1]

        self.events.data.connect(
            self._update_data
        )  # reconnect listening to update events

    def _create_node_attrs(self, new_point: np.array) -> tuple[np.array, dict]:
        """Create attributes for a new node at given time point"""

        t = int(new_point[0])
        # Check if we already have a node for the current track id at this time point,
        # since it is not allowed to have two nodes for the same track at the same time
        # point.
        if self.tracks_viewer.selected_track is None:
            self.tracks_viewer.set_new_track_id()
        if (
            self.tracks_viewer.selected_track
            in self.tracks_viewer.tracks.track_id_to_node
        ):
            for node in self.tracks_viewer.tracks.track_id_to_node[
                self.tracks_viewer.selected_track
            ]:
                if self.tracks_viewer.tracks.get_time(node) == t:
                    # We need a new node because one already exists for this track id at
                    # this time point
                    self.tracks_viewer.set_new_track_id()
                    break

        # track id does not exist yet in tracks.track_id_to_node, so it is safe to use
        track_id = self.tracks_viewer.selected_track
        area = 0

        attributes = {
            NodeAttr.POS.value: np.array([new_point[1:]]),
            NodeAttr.TIME.value: np.array([t]),
            NodeAttr.TRACK_ID.value: np.array([track_id]),
            NodeAttr.AREA.value: np.array([area]),
        }
        return attributes

    def _update_data(self, event: Event):
        """Calls the tracks controller with to update the data in the Tracks object and
        dispatch the update
        """

        if event.action == "added":
            # we only want to allow this update if there is no seg layer
            if self.tracks_viewer.tracking_layers.seg_layer is None:
                new_point = event.value[-1]
                attributes = self._create_node_attrs(new_point)
                self.tracks_viewer.tracks_controller.add_nodes(attributes)
            else:
                show_info(
                    "Mixed point and segmentation nodes not allowed: add points by "
                    "drawing on segmentation layer"
                )
                self._refresh()

        elif event.action == "removed":
            self.tracks_viewer.tracks_controller.delete_nodes(
                self.tracks_viewer.selected_nodes._list
            )

        elif event.action == "changed":
            # we only want to allow this update if there is no seg layer
            if self.tracks_viewer.tracking_layers.seg_layer is None:
                positions = []
                node_ids = []
                for ind in self.selected_data:
                    point = self.data[ind]
                    pos = point[1:]
                    positions.append(pos)
                    node_id = self.properties["node_id"][ind]
                    node_ids.append(node_id)

                attributes = {NodeAttr.POS.value: positions}
                self.tracks_viewer.tracks_controller.update_node_attrs(
                    node_ids, attributes
                )
            else:
                self._refresh()  # refresh to move points back where they belong

    def _update_selection(self):
        """Replaces the list of selected_nodes with the selection provided by the user"""

        if self.mode == "select":
            selected_points = self.selected_data
            self.tracks_viewer.selected_nodes.reset()
            for point in selected_points:
                node_id = self.nodes[point]
                self.tracks_viewer.selected_nodes.add(node_id, True)

    def get_symbols(self, tracks: Tracks, symbolmap: dict[NodeType, str]) -> list[str]:
        statemap = {
            0: NodeType.END,
            1: NodeType.CONTINUE,
            2: NodeType.SPLIT,
        }
        symbols = [symbolmap[statemap[degree]] for _, degree in tracks.graph.out_degree]
        return symbols

    def update_point_outline(self, visible: list[int] | str) -> None:
        """Update the outline color of the selected points and visibility according to
        display mode

        Args:
            visible (list[int] | str): A list of track ids, or "all"
        """
        # filter out the non-selected tracks if in lineage mode
        if visible == "all":
            self.shown[:] = True
        else:
            indices = np.where(np.isin(self.properties["track_id"], visible))[
                0
            ].tolist()
            self.shown[:] = False
            self.shown[indices] = True

        # set border color for selected item
        self.border_color = [1, 1, 1, 1]
        self.size = self.default_size
        for node in self.tracks_viewer.selected_nodes:
            index = self.node_index_dict[node]
            self.border_color[index] = (
                0,
                1,
                1,
                1,
            )
            self.size[index] = math.ceil(self.default_size + 0.3 * self.default_size)

        # emit the event to trigger update in orthogonal views
        self.border_color = self.border_color
        self.size = self.size
        self.refresh()
