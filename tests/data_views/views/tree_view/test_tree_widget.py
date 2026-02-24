"""Tests for TreeWidget - the lineage tree visualization widget.

Tests cover TreePlot data display, node selection, keyboard shortcuts,
mode switching, and integration with TracksViewer.
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from funtracks.data_model import SolutionTracks
from PyQt6.QtCore import QRectF
from qtpy.QtCore import Qt

from motile_tracker.data_views.views.tree_view.navigation_widget import (
    NavigationWidget,
)
from motile_tracker.data_views.views.tree_view.tree_widget import TreeWidget
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


def test_tree_plot_initialization_and_update(make_napari_viewer, graph_2d):
    """Test TreePlot initialization, signals, and update method."""
    # Need napari viewer context for Qt initialization
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    tree_widget = TreeWidget(viewer)
    tree_plot = tree_widget.tree_widget

    # Test 1: Initialization
    assert tree_plot is not None
    # After loading data, adj contains edge data as numpy array
    assert len(tree_plot.adj) > 0  # Should have edges from graph_2d
    assert tree_plot.view_direction == "vertical"

    # Test 2: Signals
    assert hasattr(tree_plot, "node_clicked")
    assert hasattr(tree_plot, "jump_to_node")
    assert hasattr(tree_plot, "nodes_selected")

    # Test 3: Update with all parameters
    track_df = tree_widget.track_df
    tree_widget.tree_widget.update(
        track_df=track_df,
        view_direction="horizontal",
        plot_type="tree",
        feature=None,
        selected_nodes=[1, 2],
        reset_view=True,
        allow_flip=False,
    )
    assert tree_widget.tree_widget.view_direction == "horizontal"


def test_tree_plot_data_display(make_napari_viewer, graph_2d):
    """Test TreePlot data display with empty data, track data, and view directions."""
    viewer = make_napari_viewer()
    tree_widget = TreeWidget(viewer)
    tree_plot = tree_widget.tree_widget

    # Test 1: Empty DataFrame
    empty_df = pd.DataFrame()
    tree_plot.set_data(empty_df, "tree", None)
    assert tree_plot._pos == []
    assert tree_plot.adj == []
    assert tree_plot.node_ids == []

    # Test 2: Actual track data
    tracks = SolutionTracks(graph=graph_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    # Create new tree_widget after loading data
    tree_widget = TreeWidget(viewer)
    tree_plot = tree_widget.tree_widget

    # Verify data was loaded
    assert len(tree_plot._pos) > 0
    assert len(tree_plot.node_ids) > 0

    # Test 3: Vertical view direction
    tree_plot.set_view("vertical", "tree")
    assert tree_plot.view_direction == "vertical"

    # Test 4: Horizontal view direction
    tree_plot.set_view("horizontal", "tree")
    assert tree_plot.view_direction == "horizontal"


def test_tree_plot_selection(make_napari_viewer, qtbot):
    """Test selection with empty list and rectangle selection signal."""
    viewer = make_napari_viewer()
    tree_widget = TreeWidget(viewer)
    tree_plot = tree_widget.tree_widget

    # Test 1: Setting selection with empty list
    empty_df = pd.DataFrame()
    tree_plot.track_df = empty_df

    # Should not raise an error
    tree_plot.set_selection([], "tree")

    # Test 2: Rectangle selection emits signal
    with qtbot.waitSignal(tree_plot.nodes_selected, timeout=1000) as blocker:
        # Create a dummy rectangle and emit selection
        rect = QRectF(0, 0, 100, 100)
        tree_plot.select_points_in_rect(rect)

    # Signal should have been emitted (even if with empty list)
    assert blocker.signal_triggered


def test_centering(make_napari_viewer, graph_2d):
    """Test centering on nodes with various scenarios."""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    tree_widget = TreeWidget(viewer)
    tree_plot = tree_widget.tree_widget

    # Test 1: Try to center on a node that doesn't exist - should not raise an error
    tree_widget.tree_widget.center_on_node(999)

    # Test 2: Center on existing node and verify it's in view
    node_id = 1
    node_df = tree_plot.track_df.loc[tree_plot.track_df["node_id"] == node_id]
    assert not node_df.empty, "Node should exist in track_df"

    node_x = tree_plot.track_df.loc[
        tree_plot.track_df["node_id"] == node_id, "x_axis_pos"
    ].values[0]
    node_t = tree_plot.track_df.loc[
        tree_plot.track_df["node_id"] == node_id, "t"
    ].values[0]

    # Set view range to exclude the node (far away from node position)
    view_box = tree_plot.plotItem.getViewBox()
    view_box.setRange(
        xRange=(node_x + 100, node_x + 200),
        yRange=(node_t + 100, node_t + 200),
        padding=0,
    )

    # Verify node is not in current view
    current_range = view_box.viewRange()
    assert not (
        current_range[0][0] <= node_x <= current_range[0][1]
        and current_range[1][0] <= node_t <= current_range[1][1]
    ), "Node should not be in initial view range"

    # Center on the node
    tree_plot.center_on_node(node_id)

    # Verify the view range now includes the node
    new_range = view_box.viewRange()
    assert (
        new_range[0][0] <= node_x <= new_range[0][1]
        and new_range[1][0] <= node_t <= new_range[1][1]
    ), "Node should be centered in view after center_on_node call"

    # Test 3: _center_view early return when point is already in view
    # First, center on a node to set up the view
    tree_plot.center_on_node(1)

    # Get current view range
    view_box = tree_plot.plotItem.getViewBox()
    current_range = view_box.viewRange()

    # Try to center on same location - should not change view
    center_x = (current_range[0][0] + current_range[0][1]) / 2
    center_y = (current_range[1][0] + current_range[1][1]) / 2

    # Verify setRange is not called when point is already in view
    with patch.object(view_box, "setRange", wraps=view_box.setRange) as spy_set_range:
        tree_plot._center_view(center_x, center_y)
        spy_set_range.assert_not_called()

    # Test 4: _center_range early return when range is already in view
    # Get current view range
    current_range = view_box.viewRange()

    # Center on a range that's already visible
    min_x = current_range[0][0] + 1
    max_x = current_range[0][1] - 1
    min_t = current_range[1][0] + 1
    max_t = current_range[1][1] - 1

    # Verify setRange is not called when range is already in view
    with patch.object(view_box, "setRange", wraps=view_box.setRange) as spy_set_range:
        tree_plot._center_range(min_x, max_x, min_t, max_t)
        spy_set_range.assert_not_called()

    # Test 5: set_selection centers on range for multiple nodes
    # Select multiple nodes
    tree_plot.set_selection([1, 2, 3], "tree")

    # Should have updated sizes and outlines without error


def test_tree_widget_initialization(make_napari_viewer, graph_2d):
    """Test TreeWidget initialization without and with tracks."""
    viewer = make_napari_viewer()

    # Test 1: Basic initialization
    tree_widget = TreeWidget(viewer)

    assert tree_widget is not None
    assert tree_widget.mode == "all"
    assert tree_widget.plot_type == "tree"
    assert tree_widget.view_direction == "vertical"
    assert hasattr(tree_widget, "tree_widget")
    assert hasattr(tree_widget, "mode_widget")
    assert hasattr(tree_widget, "plot_type_widget")
    assert hasattr(tree_widget, "navigation_widget")
    assert hasattr(tree_widget, "flip_widget")

    # Test 2: Initialization with tracks loaded
    tracks = SolutionTracks(graph=graph_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    tree_widget_with_tracks = TreeWidget(viewer)

    assert not tree_widget_with_tracks.track_df.empty
    assert tree_widget_with_tracks.graph is not None


@patch.object(NavigationWidget, "move")
def test_keyboard_shortcuts_all(mock_move, make_napari_viewer, graph_2d, qtbot):
    """Test all keyboard shortcuts including standard keys, releases, arrows, and toggles."""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    # Mock all methods
    delete_mock = MagicMock()
    tracks_viewer.delete_node = delete_mock
    create_edge_mock = MagicMock()
    tracks_viewer.create_edge = create_edge_mock
    delete_edge_mock = MagicMock()
    tracks_viewer.delete_edge = delete_edge_mock
    swap_mock = MagicMock()
    tracks_viewer.swap_nodes = swap_mock
    undo_mock = MagicMock()
    tracks_viewer.undo = undo_mock
    redo_mock = MagicMock()
    tracks_viewer.redo = redo_mock

    tree_widget = TreeWidget(viewer)

    # Test 1: D key calls delete_node
    qtbot.keyPress(tree_widget, Qt.Key_D)
    delete_mock.assert_called_once()

    # Test 2: A key calls create_edge
    qtbot.keyPress(tree_widget, Qt.Key_A)
    create_edge_mock.assert_called_once()

    # Test 3: B key calls delete_edge
    qtbot.keyPress(tree_widget, Qt.Key_B)
    delete_edge_mock.assert_called_once()

    # Test 4: S key calls swap_nodes
    qtbot.keyPress(tree_widget, Qt.Key_S)
    swap_mock.assert_called_once()

    # Test 5: Z key calls undo
    qtbot.keyPress(tree_widget, Qt.Key_Z)
    undo_mock.assert_called_once()

    # Test 6: R key calls redo
    qtbot.keyPress(tree_widget, Qt.Key_R)
    redo_mock.assert_called_once()

    # Test 7: F key flips axes
    initial_direction = tree_widget.view_direction
    qtbot.keyPress(tree_widget, Qt.Key_F)
    assert tree_widget.view_direction != initial_direction

    # Test 8: X key release re-enables mouse in both directions
    qtbot.keyPress(tree_widget, Qt.Key_X)
    qtbot.keyRelease(tree_widget, Qt.Key_X)

    # Test 9: Y key release re-enables mouse in both directions
    qtbot.keyPress(tree_widget, Qt.Key_Y)
    qtbot.keyRelease(tree_widget, Qt.Key_Y)

    # Test 10: All arrow keys call navigation widget move method
    qtbot.keyPress(tree_widget, Qt.Key_Left)
    mock_move.assert_called_with("left")

    qtbot.keyPress(tree_widget, Qt.Key_Right)
    mock_move.assert_called_with("right")

    qtbot.keyPress(tree_widget, Qt.Key_Up)
    mock_move.assert_called_with("up")

    qtbot.keyPress(tree_widget, Qt.Key_Down)
    mock_move.assert_called_with("down")

    # Test 11: Q key toggles display mode
    with patch.object(tree_widget.mode_widget, "_toggle_display_mode") as mock_toggle:
        qtbot.keyPress(tree_widget, Qt.Key_Q)
        mock_toggle.assert_called_once()

    # Test 12: W key toggles feature mode
    with patch.object(tree_widget.plot_type_widget, "_toggle_plot_type") as mock_toggle:
        qtbot.keyPress(tree_widget, Qt.Key_W)
        mock_toggle.assert_called_once()


def test_mode_and_plot_type_switching(make_napari_viewer, graph_2d):
    """Test mode switching, plot type switching, and their interaction."""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    tree_widget = TreeWidget(viewer)

    # Test 1: Setting mode to 'all'
    tree_widget._set_mode("all")
    assert tree_widget.mode == "all"

    # Test 2: Setting mode to 'lineage'
    # Select a node first
    tracks_viewer.selected_nodes = [1]
    tree_widget._set_mode("lineage")
    assert tree_widget.mode == "lineage"
    assert tree_widget.view_direction == "horizontal"

    # Test 3: Invalid mode raises ValueError
    with pytest.raises(ValueError, match="must be 'all' or 'lineage'"):
        tree_widget._set_mode("invalid")

    # Test 4: Setting plot type to 'tree'
    tree_widget._set_mode("all")  # Reset to all mode
    tree_widget._set_plot_type("tree")
    assert tree_widget.plot_type == "tree"

    # Test 5: Setting plot type to 'feature'
    tree_widget._set_plot_type("feature")
    assert tree_widget.plot_type == "feature"
    assert tree_widget.view_direction == "horizontal"

    # Test 6: Invalid plot type raises ValueError
    with pytest.raises(ValueError, match="must be 'tree' or 'feature'"):
        tree_widget._set_plot_type("invalid")

    # Test 7: Setting mode to 'all' with plot_type='tree' sets vertical view
    tree_widget.plot_type = "tree"
    tree_widget._set_mode("all")
    assert tree_widget.view_direction == "vertical"

    # Test 8: Setting mode to 'all' with plot_type='feature' sets horizontal view
    tree_widget.plot_type = "feature"
    tree_widget._set_mode("all")
    assert tree_widget.view_direction == "horizontal"


def test_lineage_mode_edge_cases(make_napari_viewer, graph_2d):
    """Test lineage mode edge cases with selection changes."""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    tree_widget = TreeWidget(viewer)

    # Test 1: _update_selected in lineage mode doesn't crash
    # Switch to lineage mode with a selection
    tracks_viewer.selected_nodes.add_list([1], append=False)
    tree_widget._set_mode("lineage")

    # Change selection to a node not in current lineage
    tracks_viewer.selected_nodes.add_list([2], append=False)

    # _update_selected should handle this without crashing
    tree_widget._update_selected()

    # Test 2: _update_lineage_df doesn't crash with empty selection
    # Select node and switch to lineage mode
    tracks_viewer.selected_nodes = [1]
    tree_widget._set_mode("lineage")

    # Clear selection but lineage_df still has data
    tracks_viewer.selected_nodes.clear()

    # This should not crash
    tree_widget._update_lineage_df()
    # Test passes if we reach here without exception


def test_tree_widget_integration(make_napari_viewer, graph_2d):
    """Test TreeWidget signal response, axis flipping, and mouse controls."""
    viewer = make_napari_viewer()
    tracks_viewer = TracksViewer.get_instance(viewer)

    # Test 1: TreeWidget responds to tracks_updated signal
    tree_widget = TreeWidget(viewer)
    assert tree_widget.track_df.empty

    # Update tracks
    tracks = SolutionTracks(graph=graph_2d, ndim=3)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    # Verify track_df was updated
    assert not tree_widget.track_df.empty

    # Test 2: flip_axes toggles between horizontal and vertical
    # Start with vertical
    assert tree_widget.view_direction == "vertical"

    # Flip to horizontal
    tree_widget.flip_axes()
    assert tree_widget.view_direction == "horizontal"

    # Flip back to vertical
    tree_widget.flip_axes()
    assert tree_widget.view_direction == "vertical"

    # Test 3: set_mouse_enabled changes mouse behavior (should not raise error)
    tree_widget.set_mouse_enabled(x=True, y=False)
    tree_widget.set_mouse_enabled(x=False, y=True)
    tree_widget.set_mouse_enabled(x=True, y=True)


def test_update_track_data_without_reset(make_napari_viewer, graph_2d):
    """Test _update_track_data preserves axis_order when reset_view=False."""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    tree_widget = TreeWidget(viewer)

    # Update without reset
    tree_widget._update_track_data(reset_view=False)

    # axis_order should have been passed through
    assert hasattr(tree_widget, "axis_order")


def test_update_track_data_with_none_tracks(make_napari_viewer):
    """Test _update_track_data handles None tracks."""
    viewer = make_napari_viewer()
    tree_widget = TreeWidget(viewer)

    # Update with no tracks
    tree_widget._update_track_data(reset_view=True)

    assert tree_widget.track_df.empty
    assert tree_widget.graph is None
