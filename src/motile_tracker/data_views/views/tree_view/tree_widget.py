# do not put the from __future__ import annotations as it breaks the injection

from typing import Any

import napari
import numpy as np
import pandas as pd
import pyqtgraph as pg
from psygnal import Signal
from pyqtgraph.Qt import QtCore
from qtpy.QtCore import Qt
from qtpy.QtGui import QColor, QKeyEvent, QMouseEvent
from qtpy.QtWidgets import (
    QHBoxLayout,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from superqt import QCollapsible

from motile_tracker.data_views.views.tree_view.custom_table_widget import (
    ColoredTableWidget,
)
from motile_tracker.data_views.views.tree_view.flip_axes_widget import FlipTreeWidget
from motile_tracker.data_views.views.tree_view.navigation_widget import NavigationWidget
from motile_tracker.data_views.views.tree_view.tree_view_feature_widget import (
    TreeViewFeatureWidget,
)
from motile_tracker.data_views.views.tree_view.tree_view_mode_widget import (
    TreeViewModeWidget,
)
from motile_tracker.data_views.views.tree_view.tree_widget_utils import (
    extract_lineage_tree,
    extract_sorted_tracks,
    get_features_from_tracks,
)
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


class CustomViewBox(pg.ViewBox):
    selected_rect = Signal(Any)

    def __init__(self, *args, **kwds):
        kwds["enableMenu"] = False
        pg.ViewBox.__init__(self, *args, **kwds)
        # self.setMouseMode(self.RectMode)

    ## reimplement right-click to zoom out
    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.MouseButton.RightButton:
            self.autoRange()

    def showAxRect(self, ax, **kwargs):
        """Set the visible range to the given rectangle
        Emits sigRangeChangedManually without changing the range.
        """
        # Emit the signal without setting the range
        self.sigRangeChangedManually.emit(self.state["mouseEnabled"])

    def mouseDragEvent(self, ev, axis=None):
        """Modified mouseDragEvent function to check which mouse mode to use
        and to submit rectangle coordinates for selecting multiple nodes if necessary"""

        # check if SHIFT is pressed
        shift_down = ev.modifiers() == QtCore.Qt.ShiftModifier

        if shift_down:
            # if starting a shift-drag, record the scene position
            if ev.isStart():
                self.mouse_start_pos = self.mapSceneToView(ev.scenePos())

            # Put the ViewBox in RectMode so it draws its usual yellow rectangle
            self.setMouseMode(self.RectMode)
            super().mouseDragEvent(ev, axis)

            # Once the drag finishes, emit the rectangle
            if ev.isFinish():
                rect_end_pos = self.mapSceneToView(ev.scenePos())
                rect = QtCore.QRectF(self.mouse_start_pos, rect_end_pos).normalized()
                self.selected_rect.emit(rect)  # emit the rectangle
                ev.accept()

                if hasattr(self, "rbScaleBox") and self.rbScaleBox:
                    self.rbScaleBox.hide()

        else:
            # SHIFT not pressed - use PanMode normally
            self.setMouseMode(self.PanMode)
            super().mouseDragEvent(ev, axis)

            # hide the leftover box if any
            if hasattr(self, "rbScaleBox") and self.rbScaleBox:
                self.rbScaleBox.hide()


class TreePlot(pg.PlotWidget):
    node_clicked = Signal(Any, bool)  # node_id, append
    jump_to_node = Signal(int)  # node to jump to
    nodes_selected = Signal(list, bool)

    def __init__(self) -> pg.PlotWidget:
        """Construct the pyqtgraph treewidget. This is the actual canvas
        on which the tree view is drawn.
        """
        super().__init__(viewBox=CustomViewBox())

        self.setFocusPolicy(Qt.StrongFocus)
        self.setTitle("Lineage Tree")

        self._pos = []
        self.adj = []
        self.symbolBrush = []
        self.symbols = []
        self.pen = []
        self.outline_pen = []
        self.node_ids = []
        self.sizes = []

        self.view_direction = None
        self.feature = None
        self.g = pg.GraphItem()
        self.g.scatter.sigClicked.connect(self._on_click)
        self.addItem(self.g)
        self.set_view("vertical", plot_type="tree")
        self.getViewBox().selected_rect.connect(self.select_points_in_rect)

    def select_points_in_rect(self, rect: QtCore.QRectF):
        """Select all nodes in given rectangle"""

        scatter_data = self.g.scatter.data
        x = scatter_data["x"]
        y = scatter_data["y"]
        data = scatter_data["data"]

        # Filter points that are within the rectangle
        points_within_rect = [
            (x[i], y[i], data[i]) for i in range(len(x)) if rect.contains(x[i], y[i])
        ]
        selected_nodes = [point[2] for point in points_within_rect]
        self.nodes_selected.emit(selected_nodes, True)

    def update(
        self,
        track_df: pd.DataFrame,
        view_direction: str,
        plot_type: str,
        feature: str,
        selected_nodes: list[Any],
        reset_view: bool | None = False,
        allow_flip: bool | None = True,
    ):
        """Update the entire view, including the data, view direction, and
        selected nodes

        Args:
            track_df (pd.DataFrame): The dataframe containing the graph data
            view_direction (str): The view direction
            plot_type (str): The plot_type ('tree' or 'feature')f
            feature (str): The feature to be plotted if plot_type == 'feature'
            selected_nodes (list[Any]): The currently selected nodes to be highlighted
        """
        if plot_type == "feature" and (
            feature is None or feature == ""
        ):  # feature is not available
            plot_type = "tree"
        self.set_data(track_df, plot_type, feature)
        self._update_viewed_data(view_direction)  # this can be expensive
        self.set_view(view_direction, plot_type, reset_view, allow_flip)
        self.set_selection(selected_nodes, plot_type)

    def set_view(
        self,
        view_direction: str,
        plot_type: str,
        reset_view: bool | None = False,
        allow_flip: bool | None = True,
    ):
        """Set the view direction, saving the new value as an attribute and
        changing the axes labels. Shortcuts if the view direction is already
        correct. Does not actually update the rendered graph (need to call
        _update_viewed_data).

        Args:
            view_direction (str): "horizontal" or "vertical"
            plot_type (str): the plot type being displayed, it can be 'tree' or 'feature'
        """

        # if view_direction == self.view_direction and plot_type == self.plot_type:
        #     if reset_view:
        #         self.autoRange()
        #     return

        axis_titles = {
            "time": "Time Point",
            "feature": f"Object {self.feature} in calibrated units",
            "tree": "",
        }
        if allow_flip:
            if view_direction == "vertical":
                time_axis = "left"  # time is on y axis
                feature_axis = "bottom"
                self.invertY(True)  # to show tracks from top to bottom
            else:
                time_axis = "bottom"  # time is on y axis
                feature_axis = "left"
                self.invertY(False)
            self.setLabel(time_axis, text=axis_titles["time"])
            self.getAxis(time_axis).setStyle(showValues=True)

            self.setLabel(feature_axis, text=axis_titles[plot_type])
            if plot_type == "tree":
                self.getAxis(feature_axis).setStyle(showValues=False)
            else:
                self.getAxis(feature_axis).setStyle(showValues=True)
                self.autoRange()  # not sure if this is necessary or not

        if (
            self.view_direction != view_direction
            or self.plot_type != plot_type
            or reset_view
        ):
            self.autoRange()
        self.view_direction = view_direction
        self.plot_type = plot_type

    def _on_click(self, _, points: np.ndarray, ev: QMouseEvent) -> None:
        """Adds the selected point to the selected_nodes list. Called when
        the user clicks on the TreeWidget to select nodes.

        Args:
            points (np.ndarray): _description_
            ev (QMouseEvent): _description_
        """

        modifiers = ev.modifiers()
        node_id = points[0].data()
        append = Qt.ShiftModifier == modifiers
        jump = Qt.ControlModifier == modifiers
        if jump:
            self.jump_to_node.emit(node_id)
        else:
            self.node_clicked.emit(node_id, append)
            self.setFocus()

    def set_data(self, track_df: pd.DataFrame, plot_type: str, feature: str) -> None:
        """Updates the stored pyqtgraph content based on the given dataframe.
        Does not render the new information (need to call _update_viewed_data).

        Args:
            track_df (pd.DataFrame): The tracks df to compute the pyqtgraph
                content for. Can be all lineages or any subset of them.
            plot_type (str): The plot_type to be plotted. Can either be 'tree', or 'feature'.
            feature (str): the header name of the feature to be plotted, if plot_type == "feature"
        """
        self.track_df = track_df
        self._create_pyqtgraph_content(track_df, plot_type, feature)

    def _update_viewed_data(self, view_direction: str):
        """Set the data according to the view direction
        Args:
            view_direction (str): direction to plot the data, either 'horizontal' or
                'vertical'
        """
        # first reset the pen to avoid problems with length mismatch between the
        # different properties
        self.g.scatter.setPen(pg.mkPen(QColor(150, 150, 150)))
        self.g.scatter.setSize(10)
        if len(self._pos) == 0 or view_direction == "vertical":
            pos_data = self._pos
        else:
            pos_data = np.flip(self._pos, axis=1)

        self.g.setData(
            pos=pos_data,
            adj=self.adj,
            symbol=self.symbols,
            symbolBrush=self.symbolBrush,
            pen=self.pen,
            data=self.node_ids,
        )
        self.g.scatter.setPen(self.outline_pen)
        self.g.scatter.setSize(self.sizes)

    def _create_pyqtgraph_content(
        self, track_df: pd.DataFrame, plot_type: str, feature: str | None = None
    ) -> None:
        """Parse the given track_df into the format that pyqtgraph expects
        and save the information as attributes.

        Args:
            track_df (pd.DataFrame): The dataframe containing the graph to be
                rendered in the tree view. Can be all lineages or a subset.
            plot_type (str): The plot type to be plotted. Can either be 'tree' or 'feature'.
            feature (str): The header name of the feature to be plotted, if plot_type == feature.
        """
        self._pos = []
        self.adj = []
        self.symbols = []
        self.symbolBrush = []
        self.pen = []
        self.sizes = []
        self.node_ids = []
        self.feature = feature

        if track_df is not None and not track_df.empty:
            self.symbols = track_df["symbol"].to_list()
            self.symbolBrush = track_df["color"].to_numpy()
            if plot_type == "tree":
                self._pos = track_df[["x_axis_pos", "t"]].to_numpy()
            elif plot_type == "feature":
                self._pos = track_df[[feature, "t"]].to_numpy()
            self.node_ids = track_df["node_id"].to_list()
            self.sizes = np.array(
                [
                    8,
                ]
                * len(self.symbols)
            )

            valid_edges_df = track_df[track_df["parent_id"] != 0]
            node_ids_to_index = {
                node_id: index for index, node_id in enumerate(self.node_ids)
            }
            edges_df = valid_edges_df[["node_id", "parent_id"]]
            self.pen = valid_edges_df["color"].to_numpy()
            edges_df_mapped = edges_df.map(lambda _id: node_ids_to_index[_id])
            self.adj = edges_df_mapped.to_numpy()

        self.outline_pen = np.array(
            [pg.mkPen(QColor(150, 150, 150)) for i in range(len(self._pos))]
        )

    def set_selection(self, selected_nodes: list[Any], plot_type: str) -> None:
        """Set the provided list of nodes to be selected. Increases the size
        and highlights the outline with blue.

        Note: Single-node centering is handled separately via the center_node signal
        from TracksViewer. Multi-node range centering is handled here.

        Args:
            selected_nodes (list[Any]): A list of node ids to be selected.
            plot_type (str): the plot type being displayed, either 'tree' or 'feature'
        """

        # reset to default size and color to avoid problems with the array lengths
        self.g.scatter.setPen(pg.mkPen(QColor(150, 150, 150)))
        self.g.scatter.setSize(10)

        size = (
            self.sizes.copy()
        )  # just copy the size here to keep the original self.sizes intact

        outlines = self.outline_pen.copy()
        axis_label = self.feature if plot_type == "feature" else "x_axis_pos"

        if len(selected_nodes) > 0:
            x_values = []
            t_values = []
            for node_id in selected_nodes:
                node_df = self.track_df.loc[self.track_df["node_id"] == node_id]
                if not node_df.empty:
                    x_axis_value = node_df[axis_label].values[0]
                    t = node_df["t"].values[0]

                    x_values.append(x_axis_value)
                    t_values.append(t)

                    # Update size and outline
                    index = self.node_ids.index(node_id)
                    size[index] += 5
                    outlines[index] = pg.mkPen(color="c", width=2)

            # Center range if multiple nodes are selected (single-node centering
            # is handled by the center_node signal)
            if len(x_values) > 1:
                min_x = np.min(x_values)
                max_x = np.max(x_values)
                min_t = np.min(t_values)
                max_t = np.max(t_values)
                self._center_range(min_x, max_x, min_t, max_t)

        self.g.scatter.setPen(outlines)
        self.g.scatter.setSize(size)

    def _center_range(self, min_x: int, max_x: int, min_t: int, max_t: int):
        """Check whether viewbox contains current range and adjust if not"""

        if self.view_direction == "horizontal":
            min_x, max_x, min_t, max_t = min_t, max_t, min_x, max_x

        view_box = self.plotItem.getViewBox()
        current_range = view_box.viewRange()

        x_range = current_range[0]
        y_range = current_range[1]

        # Check if the new range is within the current range
        if (
            x_range[0] <= min_x
            and x_range[1] >= max_x
            and y_range[0] <= min_t
            and y_range[1] >= max_t
        ):
            return
        else:
            self.autoRange()

    def center_on_node(self, node_id: int) -> None:
        """Center the view on a specific node by ID.

        Args:
            node_id: The node ID to center on.
        """
        if not hasattr(self, "track_df") or self.track_df is None:
            return
        node_df = self.track_df.loc[self.track_df["node_id"] == node_id]
        if node_df.empty:
            return
        axis_label = self.feature if self.plot_type == "feature" else "x_axis_pos"
        x_axis_value = node_df[axis_label].values[0]
        t = node_df["t"].values[0]
        self._center_view(x_axis_value, t)

    def _center_view(self, center_x: int, center_y: int):
        """Center the Viewbox on given coordinates, preserving the current zoom level.

        Only pans if the point is outside the current view.
        """

        if self.view_direction == "horizontal":
            center_x, center_y = (
                center_y,
                center_x,
            )  # flip because the axes have changed in horizontal mode

        view_box = self.plotItem.getViewBox()
        current_range = view_box.viewRange()

        x_range = current_range[0]
        y_range = current_range[1]

        # Check if the new center is within the current range
        if (
            x_range[0] <= center_x <= x_range[1]
            and y_range[0] <= center_y <= y_range[1]
        ):
            return

        # Pan to center the point while preserving current zoom level
        x_width = x_range[1] - x_range[0]
        y_width = y_range[1] - y_range[0]
        new_x_range = (center_x - x_width / 2, center_x + x_width / 2)
        new_y_range = (center_y - y_width / 2, center_y + y_width / 2)
        view_box.setRange(xRange=new_x_range, yRange=new_y_range, padding=0)


class TreeWidget(QWidget):
    """pyqtgraph-based widget for lineage tree visualization and navigation"""

    def __init__(self, viewer: napari.Viewer):
        super().__init__()
        self.track_df = pd.DataFrame()  # all tracks
        self.lineage_df = pd.DataFrame()  # the currently viewed subset of lineages
        self.graph = None
        self.mode = "all"  # options: "all", "lineage"
        self.plot_type = "tree"  # options: "tree", "feature"
        self.view_direction = "vertical"  # options: "horizontal", "vertical"

        self.tracks_viewer = TracksViewer.get_instance(viewer)
        self.selected_nodes = self.tracks_viewer.selected_nodes
        self.selected_nodes.list_updated.connect(self._update_selected)
        self.tracks_viewer.tracks_updated.connect(self._update_track_data)

        # Construct the tree view pyqtgraph widget
        layout = QVBoxLayout()

        self.tree_widget: TreePlot = TreePlot()
        self.tree_widget.node_clicked.connect(self.selected_nodes.add)
        self.tree_widget.jump_to_node.connect(self.tracks_viewer.center_on_node)
        self.tree_widget.nodes_selected.connect(self.selected_nodes.add_list)
        self.tracks_viewer.center_node.connect(self.tree_widget.center_on_node)

        # Add radiobuttons for switching between different display modes
        self.mode_widget = TreeViewModeWidget()
        self.mode_widget.change_mode.connect(self._set_mode)

        # Add buttons to change which feature to display
        features_to_plot = get_features_from_tracks(
            self.tracks_viewer.tracks, features_to_ignore=["Time", "Tracklet ID"]
        )
        self.plot_type_widget = TreeViewFeatureWidget(
            features_to_plot,
            get_features=lambda: get_features_from_tracks(
                self.tracks_viewer.tracks, features_to_ignore=["Time", "Tracklet ID"]
            ),
        )
        self.plot_type_widget.change_plot_type.connect(self._set_plot_type)

        # Add navigation widget
        self.navigation_widget = NavigationWidget(
            self.track_df,
            self.lineage_df,
            self.view_direction,
            self.selected_nodes,
            self.plot_type,
        )
        # Add widget to flip the axes
        self.flip_widget = FlipTreeWidget()
        self.flip_widget.flip_tree.connect(self._flip_axes)

        # Construct a toolbar and set main layout
        panel_layout = QHBoxLayout()
        panel_layout.addWidget(self.mode_widget)
        panel_layout.addWidget(self.plot_type_widget)
        panel_layout.addWidget(self.navigation_widget)
        panel_layout.addWidget(self.flip_widget)
        panel_layout.setSpacing(0)
        panel_layout.setContentsMargins(0, 0, 0, 0)

        panel = QWidget()
        panel.setLayout(panel_layout)
        panel.setMaximumWidth(930)
        panel.setMaximumHeight(82)

        # Make a collapsible for TreeView widgets
        collapsable_widget = QCollapsible("Show/Hide Tree View Controls")
        collapsable_widget.layout().setContentsMargins(0, 0, 0, 0)
        collapsable_widget.layout().setSpacing(0)
        collapsable_widget.addWidget(panel)
        collapsable_widget.collapse(animate=False)

        tree_widget = QWidget()
        layout.addWidget(collapsable_widget)
        layout.addWidget(self.tree_widget)
        layout.setSpacing(0)
        tree_widget.setLayout(layout)

        splitter = QSplitter(Qt.Horizontal)

        self.table_widget = ColoredTableWidget(self.tracks_viewer, self.track_df)
        splitter.addWidget(tree_widget)
        splitter.addWidget(self.table_widget)

        main_layout = QHBoxLayout()
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        self._update_track_data(reset_view=True)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events."""
        key_map = {
            Qt.Key_Delete: self.delete_node,
            Qt.Key_D: self.delete_node,
            Qt.Key_A: self.create_edge,
            Qt.Key_B: self.delete_edge,
            Qt.Key_S: self.swap_nodes,
            Qt.Key_Z: self.undo,
            Qt.Key_R: self.redo,
            Qt.Key_Q: self.toggle_display_mode,
            Qt.Key_W: self.toggle_feature_mode,
            Qt.Key_F: self._flip_axes,
            Qt.Key_X: lambda: self.set_mouse_enabled(x=True, y=False),
            Qt.Key_Y: lambda: self.set_mouse_enabled(x=False, y=True),
        }

        # Check if the key has a handler in the map
        handler = key_map.get(event.key())

        if handler:
            handler()  # Call the function bound to the key
        else:
            # Handle navigation (Arrow keys)
            direction_map = {
                Qt.Key_Left: "left",
                Qt.Key_Right: "right",
                Qt.Key_Up: "up",
                Qt.Key_Down: "down",
            }
            direction = direction_map.get(event.key())
            if direction:
                self.navigation_widget.move(direction)
                self.tree_widget.setFocus()

    def delete_node(self):
        """Delete a node."""
        self.tracks_viewer.delete_node()

    def create_edge(self):
        """Create an edge."""
        self.tracks_viewer.create_edge()

    def delete_edge(self):
        """Delete an edge."""
        self.tracks_viewer.delete_edge()

    def swap_nodes(self):
        """Swap the nodes by swapping upstream edges"""
        self.tracks_viewer.swap_nodes()

    def undo(self):
        """Undo action."""
        self.tracks_viewer.undo()

    def redo(self):
        """Redo action."""
        self.tracks_viewer.redo()

    def toggle_display_mode(self):
        """Toggle display mode."""
        self.mode_widget._toggle_display_mode()

    def toggle_feature_mode(self):
        """Toggle feature mode."""
        self.plot_type_widget._toggle_plot_type()

    def _flip_axes(self):
        """Flip the axes of the plot"""

        if self.view_direction == "horizontal":
            self.view_direction = "vertical"
        else:
            self.view_direction = "horizontal"

        self.navigation_widget.view_direction = self.view_direction
        self.tree_widget._update_viewed_data(self.view_direction)
        self.tree_widget.set_view(
            view_direction=self.view_direction,
            plot_type=self.tree_widget.plot_type,
            reset_view=False,
        )

    def set_mouse_enabled(self, x: bool, y: bool):
        """Enable or disable mouse zoom scrolling in X or Y direction."""
        self.tree_widget.setMouseEnabled(x=x, y=y)

    def keyReleaseEvent(self, ev):
        """Reset the mouse scrolling when releasing the X/Y key"""

        if ev.key() == Qt.Key_X or ev.key() == Qt.Key_Y:
            self.tree_widget.setMouseEnabled(x=True, y=True)

    def _update_selected(self):
        """Called whenever the selection list is updated. Only re-computes
        the full graph information when the new selection is not in the
        lineage df (and in lineage mode)
        """

        if self.mode == "lineage" and any(
            node not in np.unique(self.lineage_df["node_id"].values)
            for node in self.selected_nodes
        ):
            self._update_lineage_df()
            self.tree_widget.update(
                self.lineage_df,
                self.view_direction,
                self.plot_type,
                self.plot_type_widget.get_current_feature(),
                self.selected_nodes,
            )
        else:
            self.tree_widget.set_selection(self.selected_nodes, self.plot_type)

    def _update_track_data(self, reset_view: bool | None = None) -> None:
        """Called when the TracksViewer emits the tracks_updated signal, indicating
        that a new set of tracks should be viewed.
        """

        if self.tracks_viewer.tracks is None:
            self.track_df = pd.DataFrame()
            self.graph = None
        else:
            if reset_view:
                self.track_df, self.axis_order = extract_sorted_tracks(
                    self.tracks_viewer.tracks, self.tracks_viewer.colormap
                )
            else:
                self.track_df, self.axis_order = extract_sorted_tracks(
                    self.tracks_viewer.tracks,
                    self.tracks_viewer.colormap,
                    self.axis_order,
                )
            self.graph = self.tracks_viewer.tracks.graph

        # check whether we have regionprop measurements and therefore should activate the
        # feature button
        features_to_plot = get_features_from_tracks(
            self.tracks_viewer.tracks, features_to_ignore=["Time", "Tracklet ID"]
        )
        self.plot_type_widget.update_feature_dropdown(features_to_plot)

        # if reset_view, we got new data and want to reset display and feature before
        # calling the plot update
        if reset_view:
            self.lineage_df = pd.DataFrame()
            self.mode = "all"
            self.mode_widget.show_all_radio.setChecked(True)
            self.view_direction = "vertical"
            self.plot_type = "tree"
            self.plot_type_widget.show_tree_radio.setChecked(True)
            allow_flip = True
        else:
            allow_flip = False

        # also update the navigation widget
        self.navigation_widget.track_df = self.track_df
        self.navigation_widget.lineage_df = self.lineage_df

        # check which view to set
        if self.mode == "lineage":
            self._update_lineage_df()
            self.tree_widget.update(
                self.lineage_df,
                self.view_direction,
                self.plot_type,
                self.plot_type_widget.get_current_feature(),
                self.selected_nodes,
                reset_view=reset_view,
                allow_flip=allow_flip,
            )

        else:
            self.tree_widget.update(
                self.track_df,
                self.view_direction,
                self.plot_type,
                self.plot_type_widget.get_current_feature(),
                self.selected_nodes,
                reset_view=reset_view,
                allow_flip=allow_flip,
            )

        columns_to_display = ["node_id"] + get_features_from_tracks(
            self.tracks_viewer.tracks
        )
        self.table_widget.set_data(self.track_df, columns_to_display)

    def _set_mode(self, mode: str) -> None:
        """Set the display mode to all or lineage view. Currently, linage
        view is always horizontal and all view is always vertical.

        Args:
            mode (str): The mode to set the view to. Options are "all" or "lineage"
        """
        if mode not in ["all", "lineage"]:
            raise ValueError(f"Mode must be 'all' or 'lineage', got {mode}")

        self.mode = mode
        if mode == "all":
            if self.plot_type == "tree":
                self.view_direction = "vertical"
            else:
                self.view_direction = "horizontal"
            df = self.track_df
        elif mode == "lineage":
            self.view_direction = "horizontal"
            self._update_lineage_df()
            df = self.lineage_df
        self.navigation_widget.view_direction = self.view_direction
        self.tree_widget.update(
            df,
            self.view_direction,
            self.plot_type,
            self.plot_type_widget.get_current_feature(),
            self.selected_nodes,
            reset_view=True,
        )

    def _set_plot_type(self, plot_type: str) -> None:
        """Set the plot_type mode to 'tree' or 'feature', and adjust view direction. Also
        update the feature on the navigation_widget.

        Args:
            plot_type (str): The plot type to display. Options are "tree" or "feature"
        """
        if plot_type not in ["tree", "feature"]:
            raise ValueError(f"Plot type must be 'tree' or 'feature', got {plot_type}")

        self.plot_type = plot_type
        if plot_type == "tree" and self.mode == "all":
            self.view_direction = "vertical"
        else:
            self.view_direction = "horizontal"

        current_feature = self.plot_type_widget.get_current_feature()

        # Check if we need to rebuild dataframes for a newly computed feature
        if (
            plot_type == "feature"
            and current_feature is not None
            and current_feature not in self.track_df.columns
        ):
            self._update_track_data(reset_view=False)

        self.navigation_widget.feature = current_feature
        self.navigation_widget.view_direction = self.view_direction

        if self.mode == "all":
            df = self.track_df
        if self.mode == "lineage":
            df = self.lineage_df

        self.navigation_widget.plot_type = self.plot_type
        self.tree_widget.update(
            df,
            self.view_direction,
            self.plot_type,
            current_feature,
            self.selected_nodes,
            reset_view=True,
        )

    def _update_lineage_df(self) -> None:
        """Subset dataframe to include only nodes belonging to the current lineage"""

        if len(self.selected_nodes) == 0 and not self.lineage_df.empty:
            # try to restore lineage df based on previous selection, even if those nodes
            # are now deleted. this is to prevent that deleting nodes will remove those
            # lineages from the lineage view, which is confusing.
            prev_visible_set = set(self.lineage_df["node_id"])
            prev_visible = [
                node for node in prev_visible_set if self.graph.has_node(node)
            ]
            visible = []
            for node_id in prev_visible:
                visible += extract_lineage_tree(self.graph, node_id)
                if set(prev_visible).issubset(visible):
                    break
        else:
            visible = []
            for node_id in self.selected_nodes:
                visible += extract_lineage_tree(self.graph, node_id)
        self.lineage_df = self.track_df[
            self.track_df["node_id"].isin(visible)
        ].reset_index()
        self.lineage_df["x_axis_pos"] = (
            self.lineage_df["x_axis_pos"].rank(method="dense").astype(int) - 1
        )
        self.navigation_widget.lineage_df = self.lineage_df
