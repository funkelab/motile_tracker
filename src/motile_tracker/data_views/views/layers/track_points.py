from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

import napari
import numpy as np
from motile_toolbox.candidate_graph import NodeAttr
from napari.utils.notifications import show_info

from motile_tracker.data_model import NodeType, Tracks

if TYPE_CHECKING:
    from napari.utils.events import Event

    from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


class TrackPoints(napari.layers.Points):
    """Extended points layer that holds the track information and emits and
    responds to dynamics visualization signals
    """

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

        self.visible_nodes = "all"
        self.plane_nodes = "all"

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
        self.selected_track = None

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

        # Connect to click events to select nodes
        @self.mouse_drag_callbacks.append
        def click(layer, event):
            if event.type == "mouse_press":
                # differentiate between click and drag
                mouse_press_time = time.time()
                dragged = False
                yield
                # on move
                while event.type == "mouse_move":
                    dragged = True
                    yield
                if dragged and time.time() - mouse_press_time < 0.5:
                    dragged = (
                        False  # suppress micro drag events and treat them as click
                    )
                if not dragged:
                    # is the value passed from the click event?
                    point_index = layer.get_value(
                        event.position,
                        view_direction=event.view_direction,
                        dims_displayed=event.dims_displayed,
                        world=True,
                    )
                    self.process_point_click(point_index, event)

        # listen to updates of the data
        self.events.data.connect(self._update_data)

        # listen to updates in the selected data (from the point selection tool)
        # to update the nodes in self.tracks_viewer.selected_nodes
        self.selected_data.events.items_changed.connect(self._update_selection)

    def process_point_click(self, point_index: int | None, event: Event):
        """Select the clicked point(s)"""

        if point_index is None:
            self.tracks_viewer.selected_nodes.reset()
        else:
            node_id = self.nodes[point_index]
            append = "Shift" in event.modifiers
            self.tracks_viewer.selected_nodes.add(node_id, append)

    def set_point_size(self, size: int) -> None:
        """Sets a new default point size"""

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

        if self.tracks_viewer.track_mode == "new track":
            track_id = self.tracks_viewer.tracks.get_next_track_id()
        else:
            # make sure there is no node with this track id at this time point yet
            track_id_nodes = self.tracks_viewer.tracks.track_id_to_node[
                self.selected_track
            ]
            for node in track_id_nodes:
                if (
                    self.tracks_viewer.tracks._get_node_attr(node, NodeAttr.TIME.value)
                    == t
                ):  # there is a node with this track id already, so create a new track id in this case
                    track_id = self.tracks_viewer.tracks.get_next_track_id()
                    break
            else:
                track_id = self.selected_track

        area = 0

        attributes = {
            NodeAttr.POS.value: np.array([new_point[1:]]),
            NodeAttr.TIME.value: np.array([t]),
            NodeAttr.TRACK_ID.value: np.array([track_id]),
            NodeAttr.AREA.value: np.array([area]),
        }
        return attributes

    def _update_data(self, event):
        """Calls the tracks controller with to update the data in the Tracks object and dispatch the update"""

        if event.action == "added":
            # we only want to allow this update if there is no seg layer
            if self.tracks_viewer.tracking_layers.seg_layer is None:
                new_point = event.value[-1]
                attributes = self._create_node_attrs(new_point)
                self.tracks_viewer.tracks_controller.add_nodes(attributes)
            else:
                show_info(
                    "Mixed point and segmentation nodes not allowed: add points by drawing on segmentation layer"
                )
                self._refresh()

        if event.action == "removed":
            self.tracks_viewer.tracks_controller.delete_nodes(
                self.tracks_viewer.selected_nodes._list
            )

        if event.action == "changed":
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

        selected_points = self.selected_data
        self.tracks_viewer.selected_nodes.reset()
        for point in selected_points:
            node_id = self.nodes[point]
            self.tracks_viewer.selected_nodes.add(node_id, True)
            self.selected_track = self.tracks_viewer.tracks._get_node_attr(
                node_id, NodeAttr.TRACK_ID.value
            )

    def get_symbols(self, tracks: Tracks, symbolmap: dict[NodeType, str]) -> list[str]:
        statemap = {
            0: NodeType.END,
            1: NodeType.CONTINUE,
            2: NodeType.SPLIT,
        }
        symbols = [symbolmap[statemap[degree]] for _, degree in tracks.graph.out_degree]
        return symbols

    def update_point_outline(
        self, visible: list[int] | str, plane_nodes: list[int] | str | None = None
    ) -> None:
        """Update the outline color of the selected points and visibility according to display mode

        Args:
            visible (list[int] | str): A list of node ids, or "all"
            plane_nodes (list[int] | str): A list of node ids, or "all"
        """

        if visible is not None:
            self.visible_nodes = visible

        if plane_nodes is not None:
            self.plane_nodes = plane_nodes

        if isinstance(self.visible_nodes, str) and isinstance(self.plane_nodes, str):
            visible = "all"
        elif not isinstance(self.visible_nodes, str) and isinstance(
            self.plane_nodes, str
        ):
            visible = self.visible_nodes
        elif isinstance(self.visible_nodes, str) and not isinstance(
            self.plane_nodes, str
        ):
            visible = self.plane_nodes
        else:
            visible = list(set(self.visible_nodes).intersection(set(self.plane_nodes)))

        if isinstance(visible, str):
            self.shown[:] = True
        else:
            indices = np.where(np.isin(self.properties["node_id"], visible))[0].tolist()
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
        self.refresh()
