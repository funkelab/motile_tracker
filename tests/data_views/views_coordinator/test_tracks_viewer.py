"""Tests for TracksViewer - the central coordinator for track visualization.

Tests cover node operations, edge operations, display modes, and selection management.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from funtracks.data_model import SolutionTracks
from funtracks.exceptions import InvalidActionError

from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


@pytest.fixture
def tracks_viewer_setup(make_napari_viewer, graph_2d):
    """Fixture that creates a viewer and tracks_viewer with tracks loaded.

    Returns tuple of (viewer, tracks_viewer, tracks) for reuse across tests.
    """
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")
    return viewer, tracks_viewer, tracks


class TestNodeOperations:
    """Tests for node manipulation operations."""

    def test_delete_node(self, tracks_viewer_setup):
        """Test deleting single and multiple nodes."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        # Test 1: Delete a single node
        node_to_delete = list(tracks.graph.nodes)[0]
        tracks_viewer.selected_nodes.add(node_to_delete)

        with patch(
            "motile_tracker.data_views.views_coordinator.tracks_viewer.UserDeleteNode"
        ) as delete_mock:
            tracks_viewer.delete_node()

            # Verify UserDeleteNode was called with the selected node
            delete_mock.assert_called_once()
            call_args = delete_mock.call_args
            assert call_args[0][0] == tracks  # First arg is tracks
            assert call_args[1]["node"] == node_to_delete

        # Test 2: Delete multiple nodes
        tracks_viewer.selected_nodes.reset()
        nodes_to_delete = list(tracks.graph.nodes)[:2]
        for node in nodes_to_delete:
            tracks_viewer.selected_nodes.add(node, append=True)

        with patch(
            "motile_tracker.data_views.views_coordinator.tracks_viewer.UserDeleteNode"
        ) as delete_mock:
            tracks_viewer.delete_node()

            # Should be called once for each selected node
            assert delete_mock.call_count == len(nodes_to_delete)

    def test_delete_node_with_no_tracks(self, make_napari_viewer):
        """Test delete_node does nothing when no tracks are loaded."""
        viewer = make_napari_viewer()
        tracks_viewer = TracksViewer.get_instance(viewer)

        # Should not raise an error
        tracks_viewer.delete_node()


class TestEdgeOperations:
    """Tests for edge manipulation operations."""

    def test_delete_edge(self, tracks_viewer_setup):
        """Test deleting edges with various selection scenarios."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        # Test 1: Delete edge between two connected nodes
        edges = list(tracks.graph.edges)
        if not edges:
            pytest.skip("No edges in test graph")

        source, target = edges[0]
        tracks_viewer.selected_nodes.add(source)
        tracks_viewer.selected_nodes.add(target, append=True)

        with patch(
            "motile_tracker.data_views.views_coordinator.tracks_viewer.UserDeleteEdge"
        ) as delete_mock:
            tracks_viewer.delete_edge()

            # Verify edge deletion was attempted
            delete_mock.assert_called_once()
            call_args = delete_mock.call_args
            assert call_args[0][0] == tracks
            # Check source/target (order may be swapped by time)
            called_source = call_args[1]["source"]
            called_target = call_args[1]["target"]
            assert {called_source, called_target} == {source, target}

        # Test 2: Delete edge with wrong number of selections
        tracks_viewer.selected_nodes.reset()
        tracks_viewer.selected_nodes.add(list(tracks.graph.nodes)[0])

        with patch(
            "motile_tracker.data_views.views_coordinator.tracks_viewer.UserDeleteEdge"
        ) as delete_mock:
            tracks_viewer.delete_edge()

            # Should not be called
            delete_mock.assert_not_called()

    def test_swap_nodes(self, tracks_viewer_setup):
        """Test swapping predecessors of two nodes."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        # Select two nodes
        nodes = list(tracks.graph.nodes)[:2]
        for i, node in enumerate(nodes):
            tracks_viewer.selected_nodes.add(node, append=(i > 0))

        # Swap nodes
        with patch(
            "motile_tracker.data_views.views_coordinator.tracks_viewer.UserSwapPredecessors"
        ) as swap_mock:
            tracks_viewer.swap_nodes()

            # Verify swap was called
            swap_mock.assert_called_once()
            call_args = swap_mock.call_args
            assert call_args[0][0] == tracks
            # Check both nodes are in the call
            called_nodes = call_args[1]["nodes"]
            assert set(called_nodes) == set(nodes)

    def test_create_edge_sorts_by_time(self, tracks_viewer_setup):
        """Test create_edge orders nodes by time (earlier -> later)."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        # Find two nodes at different times
        nodes_with_time = [(n, tracks.get_time(n)) for n in tracks.graph.nodes]
        nodes_with_time.sort(key=lambda x: x[1])

        if len(nodes_with_time) < 2:
            pytest.skip("Need at least 2 nodes at different times")

        # Select in reverse time order
        later_node = nodes_with_time[-1][0]
        earlier_node = nodes_with_time[0][0]
        tracks_viewer.selected_nodes.add(later_node)
        tracks_viewer.selected_nodes.add(earlier_node, append=True)

        # Create edge
        with patch(
            "motile_tracker.data_views.views_coordinator.tracks_viewer.UserAddEdge"
        ) as add_mock:
            tracks_viewer.create_edge()

            # Verify source is earlier, target is later
            call_args = add_mock.call_args
            assert call_args[1]["source"] == earlier_node
            assert call_args[1]["target"] == later_node

    def test_create_edge_with_force(self, tracks_viewer_setup, monkeypatch):
        """Test create_edge handles forceable errors."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        # Select two nodes
        nodes = list(tracks.graph.nodes)[:2]
        for i, node in enumerate(nodes):
            tracks_viewer.selected_nodes.add(node, append=(i > 0))

        # Mock UserAddEdge to raise forceable error on first call
        with patch(
            "motile_tracker.data_views.views_coordinator.tracks_viewer.UserAddEdge"
        ) as add_mock:
            add_mock.side_effect = [
                InvalidActionError("Test conflict", forceable=True),
                None,  # second call succeeds
            ]

            # Mock the dialog to return (force=True, always_force=False)
            monkeypatch.setattr(
                "motile_tracker.data_views.views_coordinator.tracks_viewer.confirm_force_operation",
                lambda message: (True, False),
            )

            tracks_viewer.create_edge()

            # Should be called twice - once without force, once with
            assert add_mock.call_count == 2

            # Check first call had force=False (default)
            first_call = add_mock.call_args_list[0]
            assert first_call[1].get("force", False) == False

            # Check second call had force=True
            second_call = add_mock.call_args_list[1]
            assert second_call[1]["force"] == True


class TestDisplayModes:
    """Tests for display mode switching and filtering."""

    def test_toggle_display_mode_cycles_modes(self, tracks_viewer_setup):
        """Test toggle_display_mode cycles through modes."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        # Start in "all" mode
        tracks_viewer.set_display_mode("all")
        assert tracks_viewer.mode == "all"

        # Toggle to lineage
        tracks_viewer.toggle_display_mode()
        assert tracks_viewer.mode == "lineage"

        # Toggle to group
        tracks_viewer.toggle_display_mode()
        assert tracks_viewer.mode == "group"

        # Toggle back to all
        tracks_viewer.toggle_display_mode()
        assert tracks_viewer.mode == "all"

    def test_display_modes(self, tracks_viewer_setup):
        """Test all display modes and filtering behavior."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        # Test 1: Set display mode to 'all'
        tracks_viewer.set_display_mode("all")
        assert tracks_viewer.mode == "all"
        assert tracks_viewer.visible == "all"

        # Test 2: Filter in all mode
        tracks_viewer.filter_visible_nodes()
        assert tracks_viewer.visible == "all"

        # Test 3: Lineage mode with selection
        node = list(tracks.graph.nodes)[0]
        tracks_viewer.selected_nodes.add(node)
        tracks_viewer.set_display_mode("lineage")
        assert tracks_viewer.mode == "lineage"
        assert isinstance(tracks_viewer.visible, list)
        assert node in tracks_viewer.visible

        # Test 4: Group mode (no group selected)
        tracks_viewer.set_display_mode("group")
        assert tracks_viewer.mode == "group"
        assert tracks_viewer.visible == []

    def test_filter_visible_nodes_preserves_previous_lineage(self, tracks_viewer_setup):
        """Test lineage mode preserves previous visible nodes when selection cleared."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        # Select a node and switch to lineage mode
        node = list(tracks.graph.nodes)[0]
        tracks_viewer.selected_nodes.add(node)
        tracks_viewer.set_display_mode("lineage")

        # Remember the visible nodes
        previous_visible = tracks_viewer.visible.copy()

        # Clear selection
        tracks_viewer.selected_nodes.reset()
        tracks_viewer.filter_visible_nodes()

        # Should keep showing the previous lineage
        assert len(tracks_viewer.visible) > 0


class TestSelectionManagement:
    """Tests for selection tracking and updates."""

    def test_update_selection_centering(self, tracks_viewer_setup):
        """Test update_selection centering behavior with different selections."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        # Test 1: Center on single node
        node = list(tracks.graph.nodes)[0]
        tracks_viewer.selected_nodes.add(node)

        with patch.object(tracks_viewer, "center_on_node") as center_mock:
            tracks_viewer.update_selection(set_view=True)
            # Should center on the selected node
            center_mock.assert_called_once_with(node)

        # Test 2: No centering with multiple nodes
        tracks_viewer.selected_nodes.reset()
        nodes = list(tracks.graph.nodes)[:2]
        for i, node in enumerate(nodes):
            tracks_viewer.selected_nodes.add(node, append=(i > 0))

        with patch.object(tracks_viewer, "center_on_node") as center_mock:
            tracks_viewer.update_selection(set_view=True)
            # Should NOT center
            center_mock.assert_not_called()

    def test_selected_track_management(self, tracks_viewer_setup):
        """Test selected_track updates and clearing."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        # Test 1: Update selected_track from selection
        node = list(tracks.graph.nodes)[0]
        tracks_viewer.selected_nodes.add(node)
        tracks_viewer.update_selection()

        # selected_track should be set to the track ID of the selected node
        expected_track_id = tracks.get_track_id(node)
        assert tracks_viewer.selected_track == expected_track_id

        # Test 2: Clear selected_track when selection cleared
        tracks_viewer.selected_nodes.reset()
        tracks_viewer.update_selection()

        # selected_track should be None
        assert tracks_viewer.selected_track is None


class TestUndoRedo:
    """Tests for undo/redo functionality."""

    def test_undo_redo_operations(self, tracks_viewer_setup):
        """Test undo and redo delegate to tracks correctly."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        # Test undo
        with patch.object(tracks, "undo") as undo_mock:
            tracks_viewer.undo()
            undo_mock.assert_called_once()

        # Test redo
        with patch.object(tracks, "redo") as redo_mock:
            tracks_viewer.redo()
            redo_mock.assert_called_once()

    def test_undo_redo_with_no_tracks(self, make_napari_viewer):
        """Test undo/redo do nothing when no tracks are loaded."""
        viewer = make_napari_viewer()
        tracks_viewer = TracksViewer.get_instance(viewer)

        # Should not raise errors
        tracks_viewer.undo()
        tracks_viewer.redo()
