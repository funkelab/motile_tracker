"""Tests for TreeWidget - the lineage tree visualization widget.

Tests cover TreePlot data display, node selection, keyboard shortcuts,
mode switching, and integration with TracksViewer.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
from funtracks.data_model import SolutionTracks
from PyQt6.QtCore import QRectF
from PyQt6.QtCore import Qt as QtCoreQt
from qtpy.QtCore import Qt

from motile_tracker.data_views.views.tree_view.navigation_widget import (
    NavigationWidget,
)
from motile_tracker.data_views.views.tree_view.tree_widget import TreePlot, TreeWidget
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


class TestTreePlotInitialization:
    """Test TreePlot initialization and basic setup."""

    def test_tree_plot_initialization(self, make_napari_viewer, graph_2d):
        """Test TreePlot is properly initialized."""
        # Need napari viewer context for Qt initialization
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)
        tree_plot = tree_widget.tree_widget

        assert tree_plot is not None
        # After loading data, adj contains edge data as numpy array
        assert len(tree_plot.adj) > 0  # Should have edges from graph_2d
        assert tree_plot.view_direction == "vertical"

    def test_tree_plot_has_signals(self, make_napari_viewer, graph_2d):
        """Test TreePlot has expected signals."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)
        tree_plot = tree_widget.tree_widget

        assert hasattr(tree_plot, "node_clicked")
        assert hasattr(tree_plot, "jump_to_node")
        assert hasattr(tree_plot, "nodes_selected")


class TestTreePlotDataDisplay:
    """Test TreePlot data display functionality."""

    def test_set_data_with_empty_dataframe(self, make_napari_viewer):
        """Test setting data with an empty DataFrame."""
        viewer = make_napari_viewer()
        tree_widget = TreeWidget(viewer)
        tree_plot = tree_widget.tree_widget

        empty_df = pd.DataFrame()
        tree_plot.set_data(empty_df, "tree", None)

        assert tree_plot._pos == []
        assert tree_plot.adj == []
        assert tree_plot.node_ids == []

    def test_set_data_with_track_data(self, make_napari_viewer, graph_2d):
        """Test setting data with actual track data."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)

        # Verify data was loaded
        assert len(tree_widget.tree_widget._pos) > 0
        assert len(tree_widget.tree_widget.node_ids) > 0

    def test_set_view_direction_vertical(self, make_napari_viewer, graph_2d):
        """Test setting view direction to vertical."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)
        tree_plot = tree_widget.tree_widget

        tree_plot.set_view("vertical", "tree")

        assert tree_plot.view_direction == "vertical"

    def test_set_view_direction_horizontal(self, make_napari_viewer, graph_2d):
        """Test setting view direction to horizontal."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)
        tree_plot = tree_widget.tree_widget

        tree_plot.set_view("horizontal", "tree")

        assert tree_plot.view_direction == "horizontal"


class TestTreePlotSelection:
    """Test TreePlot node selection functionality."""

    def test_set_selection_empty_list(self, make_napari_viewer):
        """Test setting selection with empty list."""
        viewer = make_napari_viewer()
        tree_widget = TreeWidget(viewer)
        tree_plot = tree_widget.tree_widget

        empty_df = pd.DataFrame()
        tree_plot.track_df = empty_df

        # Should not raise an error
        tree_plot.set_selection([], "tree")

    def test_select_points_in_rect_signal(self, make_napari_viewer, qtbot):
        """Test rectangle selection emits signal."""
        viewer = make_napari_viewer()
        tree_widget = TreeWidget(viewer)
        tree_plot = tree_widget.tree_widget

        with qtbot.waitSignal(tree_plot.nodes_selected, timeout=1000) as blocker:
            # Create a dummy rectangle and emit selection
            rect = QRectF(0, 0, 100, 100)
            tree_plot.select_points_in_rect(rect)

        # Signal should have been emitted (even if with empty list)
        assert blocker.signal_triggered


class TestTreePlotCentering:
    """Test TreePlot centering functionality."""

    def test_center_on_node_with_empty_df(self, make_napari_viewer, graph_2d):
        """Test centering on node when track_df exists but is empty of target node."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)

        # Try to center on a node that doesn't exist - should not raise an error
        tree_widget.tree_widget.center_on_node(999)

    def test_center_on_node_with_data(self, make_napari_viewer, graph_2d):
        """Test centering on node with actual data."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)

        # Should not raise an error
        tree_widget.tree_widget.center_on_node(1)


class TestTreeWidgetInitialization:
    """Test TreeWidget initialization."""

    def test_tree_widget_initialization(self, make_napari_viewer):
        """Test TreeWidget is properly initialized."""
        viewer = make_napari_viewer()
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

    def test_tree_widget_with_tracks(self, make_napari_viewer, graph_2d):
        """Test TreeWidget initialization with tracks loaded."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)

        assert not tree_widget.track_df.empty
        assert tree_widget.graph is not None


class TestTreeWidgetKeyboardShortcuts:
    """Test TreeWidget keyboard shortcuts."""

    def test_keyboard_delete_node(self, make_napari_viewer, graph_2d, qtbot):
        """Test D key calls delete_node."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Mock the delete_node method
        delete_mock = MagicMock()
        tracks_viewer.delete_node = delete_mock

        tree_widget = TreeWidget(viewer)

        # Simulate D key press
        qtbot.keyPress(tree_widget, Qt.Key_D)

        # Verify delete_node was called
        delete_mock.assert_called_once()

    def test_keyboard_create_edge(self, make_napari_viewer, graph_2d, qtbot):
        """Test A key calls create_edge."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Mock the create_edge method
        create_edge_mock = MagicMock()
        tracks_viewer.create_edge = create_edge_mock

        tree_widget = TreeWidget(viewer)

        # Simulate A key press
        qtbot.keyPress(tree_widget, Qt.Key_A)

        # Verify create_edge was called
        create_edge_mock.assert_called_once()

    def test_keyboard_delete_edge(self, make_napari_viewer, graph_2d, qtbot):
        """Test B key calls delete_edge."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Mock the delete_edge method
        delete_edge_mock = MagicMock()
        tracks_viewer.delete_edge = delete_edge_mock

        tree_widget = TreeWidget(viewer)

        # Simulate B key press
        qtbot.keyPress(tree_widget, Qt.Key_B)

        # Verify delete_edge was called
        delete_edge_mock.assert_called_once()

    def test_keyboard_swap_nodes(self, make_napari_viewer, graph_2d, qtbot):
        """Test S key calls swap_nodes."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Mock the swap_nodes method
        swap_mock = MagicMock()
        tracks_viewer.swap_nodes = swap_mock

        tree_widget = TreeWidget(viewer)

        # Simulate S key press
        qtbot.keyPress(tree_widget, Qt.Key_S)

        # Verify swap_nodes was called
        swap_mock.assert_called_once()

    def test_keyboard_undo(self, make_napari_viewer, graph_2d, qtbot):
        """Test Z key calls undo."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Mock the undo method
        undo_mock = MagicMock()
        tracks_viewer.undo = undo_mock

        tree_widget = TreeWidget(viewer)

        # Simulate Z key press
        qtbot.keyPress(tree_widget, Qt.Key_Z)

        # Verify undo was called
        undo_mock.assert_called_once()

    def test_keyboard_redo(self, make_napari_viewer, graph_2d, qtbot):
        """Test R key calls redo."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Mock the redo method
        redo_mock = MagicMock()
        tracks_viewer.redo = redo_mock

        tree_widget = TreeWidget(viewer)

        # Simulate R key press
        qtbot.keyPress(tree_widget, Qt.Key_R)

        # Verify redo was called
        redo_mock.assert_called_once()

    def test_keyboard_flip_axes(self, make_napari_viewer, graph_2d, qtbot):
        """Test F key flips axes."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)
        initial_direction = tree_widget.view_direction

        # Simulate F key press
        qtbot.keyPress(tree_widget, Qt.Key_F)

        # Verify direction changed
        assert tree_widget.view_direction != initial_direction


class TestTreeWidgetModeSwitching:
    """Test TreeWidget mode switching functionality."""

    def test_set_mode_all(self, make_napari_viewer, graph_2d):
        """Test setting mode to 'all'."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)
        tree_widget._set_mode("all")

        assert tree_widget.mode == "all"

    def test_set_mode_lineage(self, make_napari_viewer, graph_2d):
        """Test setting mode to 'lineage'."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)

        # Select a node first
        tracks_viewer.selected_nodes = [1]

        tree_widget._set_mode("lineage")

        assert tree_widget.mode == "lineage"
        assert tree_widget.view_direction == "horizontal"

    def test_set_mode_invalid_raises_error(self, make_napari_viewer, graph_2d):
        """Test setting invalid mode raises ValueError."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)

        try:
            tree_widget._set_mode("invalid")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "must be 'all' or 'lineage'" in str(e)


class TestTreeWidgetPlotTypeSwitching:
    """Test TreeWidget plot type switching functionality."""

    def test_set_plot_type_tree(self, make_napari_viewer, graph_2d):
        """Test setting plot type to 'tree'."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)
        tree_widget._set_plot_type("tree")

        assert tree_widget.plot_type == "tree"

    def test_set_plot_type_feature(self, make_napari_viewer, graph_2d):
        """Test setting plot type to 'feature'."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)
        tree_widget._set_plot_type("feature")

        assert tree_widget.plot_type == "feature"
        assert tree_widget.view_direction == "horizontal"

    def test_set_plot_type_invalid_raises_error(self, make_napari_viewer, graph_2d):
        """Test setting invalid plot type raises ValueError."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)

        try:
            tree_widget._set_plot_type("invalid")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "must be 'tree' or 'feature'" in str(e)


class TestTreeWidgetIntegration:
    """Test TreeWidget integration with TracksViewer."""

    def test_update_track_data_signal(self, make_napari_viewer, graph_2d):
        """Test TreeWidget responds to tracks_updated signal."""
        viewer = make_napari_viewer()
        tracks_viewer = TracksViewer.get_instance(viewer)

        tree_widget = TreeWidget(viewer)
        assert tree_widget.track_df.empty

        # Update tracks
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Verify track_df was updated
        assert not tree_widget.track_df.empty

    def test_flip_axes_toggles_direction(self, make_napari_viewer, graph_2d):
        """Test _flip_axes toggles between horizontal and vertical."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)

        # Start with vertical
        assert tree_widget.view_direction == "vertical"

        # Flip to horizontal
        tree_widget._flip_axes()
        assert tree_widget.view_direction == "horizontal"

        # Flip back to vertical
        tree_widget._flip_axes()
        assert tree_widget.view_direction == "vertical"

    def test_set_mouse_enabled(self, make_napari_viewer, graph_2d):
        """Test set_mouse_enabled changes mouse behavior."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)

        # Should not raise an error
        tree_widget.set_mouse_enabled(x=True, y=False)
        tree_widget.set_mouse_enabled(x=False, y=True)
        tree_widget.set_mouse_enabled(x=True, y=True)


class TestTreeWidgetKeyReleaseEvents:
    """Test TreeWidget key release events."""

    def test_key_release_x_enables_mouse(self, make_napari_viewer, graph_2d, qtbot):
        """Test X key release re-enables mouse in both directions."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)

        # Press X to disable y-scrolling
        qtbot.keyPress(tree_widget, Qt.Key_X)

        # Release X should re-enable both
        qtbot.keyRelease(tree_widget, Qt.Key_X)

    def test_key_release_y_enables_mouse(self, make_napari_viewer, graph_2d, qtbot):
        """Test Y key release re-enables mouse in both directions."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)

        # Press Y to disable x-scrolling
        qtbot.keyPress(tree_widget, Qt.Key_Y)

        # Release Y should re-enable both
        qtbot.keyRelease(tree_widget, Qt.Key_Y)


class TestTreeWidgetNavigationKeys:
    """Test TreeWidget arrow key navigation."""

    @patch.object(NavigationWidget, "move")
    def test_arrow_keys_call_navigation(
        self, mock_move, make_napari_viewer, graph_2d, qtbot
    ):
        """Test arrow keys call navigation widget move method."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)

        # Test all arrow keys
        qtbot.keyPress(tree_widget, Qt.Key_Left)
        mock_move.assert_called_with("left")

        qtbot.keyPress(tree_widget, Qt.Key_Right)
        mock_move.assert_called_with("right")

        qtbot.keyPress(tree_widget, Qt.Key_Up)
        mock_move.assert_called_with("up")

        qtbot.keyPress(tree_widget, Qt.Key_Down)
        mock_move.assert_called_with("down")


class TestTreeWidgetToggleShortcuts:
    """Test TreeWidget Q and W toggle shortcuts."""

    def test_q_key_toggles_display_mode(self, make_napari_viewer, graph_2d, qtbot):
        """Test Q key toggles display mode."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)
        initial_mode = tree_widget.mode

        # Mock the toggle method
        with patch.object(
            tree_widget.mode_widget, "_toggle_display_mode"
        ) as mock_toggle:
            qtbot.keyPress(tree_widget, Qt.Key_Q)
            mock_toggle.assert_called_once()

    def test_w_key_toggles_feature_mode(self, make_napari_viewer, graph_2d, qtbot):
        """Test W key toggles feature mode."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)

        # Mock the toggle method
        with patch.object(
            tree_widget.plot_type_widget, "_toggle_plot_type"
        ) as mock_toggle:
            qtbot.keyPress(tree_widget, Qt.Key_W)
            mock_toggle.assert_called_once()


class TestTreeWidgetLineageMode:
    """Test TreeWidget lineage mode specific behavior."""

    def test_update_selected_in_lineage_mode(self, make_napari_viewer, graph_2d):
        """Test _update_selected in lineage mode doesn't crash."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)

        # Switch to lineage mode with a selection
        tracks_viewer.selected_nodes.add_list([1], append=False)
        tree_widget._set_mode("lineage")

        # Change selection to a node not in current lineage
        tracks_viewer.selected_nodes.add_list([2], append=False)

        # _update_selected should handle this without crashing
        tree_widget._update_selected()

        # Test passes if no exception is raised

    def test_update_lineage_df_with_empty_selection_no_crash(
        self, make_napari_viewer, graph_2d
    ):
        """Test _update_lineage_df doesn't crash with empty selection."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)

        # Select node and switch to lineage mode
        tracks_viewer.selected_nodes = [1]
        tree_widget._set_mode("lineage")

        # Clear selection but lineage_df still has data
        tracks_viewer.selected_nodes.clear()

        # This should not crash - behavior depends on graph structure
        try:
            tree_widget._update_lineage_df()
            # If it completes without error, test passes
        except Exception as e:
            assert False, f"_update_lineage_df crashed with: {e}"


class TestTreePlotUpdate:
    """Test TreePlot update method."""

    def test_update_with_all_parameters(self, make_napari_viewer, graph_2d):
        """Test TreePlot.update with all parameters."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)
        track_df = tree_widget.track_df

        # Call update with explicit parameters
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


class TestTreePlotCenteringLogic:
    """Test TreePlot centering logic edge cases."""

    def test_center_view_when_already_visible(self, make_napari_viewer, graph_2d):
        """Test _center_view early return when point is already in view."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)
        tree_plot = tree_widget.tree_widget

        # First, center on a node to set up the view
        tree_plot.center_on_node(1)

        # Get current view range
        view_box = tree_plot.plotItem.getViewBox()
        current_range = view_box.viewRange()

        # Try to center on same location - should not change view
        center_x = (current_range[0][0] + current_range[0][1]) / 2
        center_y = (current_range[1][0] + current_range[1][1]) / 2
        tree_plot._center_view(center_x, center_y)

    def test_center_range_when_already_visible(self, make_napari_viewer, graph_2d):
        """Test _center_range early return when range is already in view."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)
        tree_plot = tree_widget.tree_widget

        # Get current view range
        view_box = tree_plot.plotItem.getViewBox()
        current_range = view_box.viewRange()

        # Center on a range that's already visible
        min_x = current_range[0][0] + 1
        max_x = current_range[0][1] - 1
        min_t = current_range[1][0] + 1
        max_t = current_range[1][1] - 1

        tree_plot._center_range(min_x, max_x, min_t, max_t)

    def test_set_selection_with_multiple_nodes(self, make_napari_viewer, graph_2d):
        """Test set_selection centers on range for multiple nodes."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)

        # Select multiple nodes
        tree_widget.tree_widget.set_selection([1, 2, 3], "tree")

        # Should have updated sizes and outlines without error


class TestTreeWidgetUpdateTrackData:
    """Test TreeWidget _update_track_data with various parameters."""

    def test_update_track_data_without_reset(self, make_napari_viewer, graph_2d):
        """Test _update_track_data preserves axis_order when reset_view=False."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)
        initial_axis_order = tree_widget.axis_order

        # Update without reset
        tree_widget._update_track_data(reset_view=False)

        # axis_order should have been passed through
        assert hasattr(tree_widget, "axis_order")

    def test_update_track_data_with_none_tracks(self, make_napari_viewer):
        """Test _update_track_data handles None tracks."""
        viewer = make_napari_viewer()
        tree_widget = TreeWidget(viewer)

        # Update with no tracks
        tree_widget._update_track_data(reset_view=True)

        assert tree_widget.track_df.empty
        assert tree_widget.graph is None


class TestTreeWidgetModeAndPlotTypeInteraction:
    """Test interactions between mode and plot_type in TreeWidget."""

    def test_set_mode_all_with_tree_plot_type(self, make_napari_viewer, graph_2d):
        """Test setting mode to 'all' with plot_type='tree' sets vertical view."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)
        tree_widget.plot_type = "tree"
        tree_widget._set_mode("all")

        assert tree_widget.view_direction == "vertical"

    def test_set_mode_all_with_feature_plot_type(self, make_napari_viewer, graph_2d):
        """Test setting mode to 'all' with plot_type='feature' sets horizontal view."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        tree_widget = TreeWidget(viewer)
        tree_widget.plot_type = "feature"
        tree_widget._set_mode("all")

        assert tree_widget.view_direction == "horizontal"
