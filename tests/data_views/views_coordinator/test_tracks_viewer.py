"""Tests for TracksViewer - the central coordinator for track visualization.

Tests cover node operations, edge operations, display modes, and selection management.
"""

from unittest.mock import patch

import networkx as nx
import pytest
from funtracks.data_model import SolutionTracks

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

    def test_delete_single_node(self, tracks_viewer_setup):
        """Test deleting a single node actually removes it from the graph."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        node_to_delete = 6  # unconnected node in graph_2d
        tracks_viewer.selected_nodes.add(node_to_delete)

        tracks_viewer.delete_node()

        assert node_to_delete not in tracks.graph.nodes

    def test_delete_multiple_nodes(self, tracks_viewer_setup):
        """Test deleting multiple selected nodes removes all of them."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        # nodes 5 (terminal) and 6 (unconnected) are safe to delete independently
        nodes_to_delete = [5, 6]
        for node in nodes_to_delete:
            tracks_viewer.selected_nodes.add(node, append=True)

        tracks_viewer.delete_node()

        for node in nodes_to_delete:
            assert node not in tracks.graph.nodes

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

        tracks_viewer.delete_edge()

        # Verify the edge was actually deleted from the graph
        assert not tracks.graph.has_edge(source, target)

        # Test 2: Delete edge with wrong number of selections
        tracks_viewer.selected_nodes.reset()
        tracks_viewer.selected_nodes.add(list(tracks.graph.nodes)[0])

        edge_count_before = tracks.graph.number_of_edges()
        tracks_viewer.delete_edge()

        # Should not have deleted anything
        assert tracks.graph.number_of_edges() == edge_count_before

    def test_swap_nodes(self, make_napari_viewer):
        """Test swapping predecessors of two nodes updates the graph correctly."""
        # graph_2d has no valid swap scenario (all branches share a predecessor),
        # so create a minimal graph: A(t0)->C(t1) and B(t0)->D(t1)
        g = nx.DiGraph()
        g.add_nodes_from(
            [
                (1, {"pos": [0, 0], "time": 0, "area": 100, "track_id": 1}),
                (2, {"pos": [5, 0], "time": 0, "area": 100, "track_id": 2}),
                (3, {"pos": [0, 0], "time": 1, "area": 100, "track_id": 1}),
                (4, {"pos": [5, 0], "time": 1, "area": 100, "track_id": 2}),
            ]
        )
        g.add_edges_from([(1, 3), (2, 4)])
        tracks = SolutionTracks(graph=g, ndim=3)

        viewer = make_napari_viewer()
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Select nodes 3 and 4 (different predecessors: 1 and 2)
        tracks_viewer.selected_nodes.add(3)
        tracks_viewer.selected_nodes.add(4, append=True)

        tracks_viewer.swap_nodes()

        # After swap: predecessors are exchanged
        assert tracks.graph.has_edge(1, 4)
        assert tracks.graph.has_edge(2, 3)
        assert not tracks.graph.has_edge(1, 3)
        assert not tracks.graph.has_edge(2, 4)

    def test_create_edge_sorts_by_time(self, tracks_viewer_setup):
        """Test create_edge orders nodes by time (earlier -> later)."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        # Node 2 (t1, no successors) and node 6 (t4, no predecessors): valid free edge
        # Select in reverse time order to verify sorting
        tracks_viewer.selected_nodes.add(6)  # t4, selected first
        tracks_viewer.selected_nodes.add(2, append=True)  # t1, selected second

        tracks_viewer.create_edge()

        # Edge must go from earlier (2) to later (6), regardless of selection order
        assert tracks.graph.has_edge(2, 6)

    def test_create_edge_with_force(self, tracks_viewer_setup, monkeypatch):
        """Test create_edge handles forceable errors by retrying with force=True."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        # Node 4 (t2) already has incoming edge from node 3.
        # Adding edge 2(t1)->4 raises InvalidActionError(forceable=True).
        tracks_viewer.selected_nodes.add(2)
        tracks_viewer.selected_nodes.add(4, append=True)

        # Approve the force dialog automatically
        monkeypatch.setattr(
            "motile_tracker.data_views.views_coordinator.tracks_viewer.confirm_force_operation",
            lambda message: (True, False),
        )

        tracks_viewer.create_edge()

        # New edge should be in the graph
        assert tracks.graph.has_edge(2, 4)
        # Conflicting edge should have been removed by force
        assert not tracks.graph.has_edge(3, 4)


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
        """Test undo restores deleted node and redo removes it again."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        # Do a real action: delete unconnected node 6
        tracks_viewer.selected_nodes.add(6)
        tracks_viewer.delete_node()
        assert 6 not in tracks.graph.nodes

        # Undo: node 6 should be restored
        tracks_viewer.undo()
        assert 6 in tracks.graph.nodes

        # Redo: node 6 should be gone again
        tracks_viewer.redo()
        assert 6 not in tracks.graph.nodes

    def test_undo_redo_with_no_tracks(self, make_napari_viewer):
        """Test undo/redo do nothing when no tracks are loaded."""
        viewer = make_napari_viewer()
        tracks_viewer = TracksViewer.get_instance(viewer)

        # Should not raise errors
        tracks_viewer.undo()
        tracks_viewer.redo()
