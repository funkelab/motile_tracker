"""Tests for TracksViewer - the central coordinator for track visualization.

Tests cover node operations, edge operations, display modes, and selection management.
"""

from unittest.mock import patch

import numpy as np
import pytest
from funtracks.data_model import SolutionTracks, Tracks

from motile_tracker.data_views.views.layers.track_graph import TrackGraph
from motile_tracker.data_views.views.layers.track_labels import TrackLabels
from motile_tracker.data_views.views.layers.track_points import TrackPoints
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer
from motile_tracker.motile.backend.motile_run import MotileRun


@pytest.fixture(autouse=True)
def clear_viewer_layers(viewer):
    """Clear viewer layers between tests."""
    yield
    viewer.layers.clear()


@pytest.fixture
def tracks_viewer_setup(viewer, graph_2d):
    """Fixture that creates a tracks_viewer with tracks loaded.

    Returns tuple of (viewer, tracks_viewer, tracks) for reuse across tests.
    """
    tracks = MotileRun(graph=graph_2d, run_name="test", ndim=3, time_attr="t")
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")
    return viewer, tracks_viewer, tracks


class TestNodeOperations:
    """Tests for node manipulation operations."""

    def test_delete_single_node(self, tracks_viewer_setup, click_node):
        """Test deleting a single node actually removes it from the graph."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        node_to_delete = 6  # unconnected node in graph_2d
        click_node(tracks_viewer, node_to_delete)

        tracks_viewer.delete_node()

        assert not tracks.graph.has_node(node_to_delete)

    def test_delete_multiple_nodes(self, tracks_viewer_setup, click_node):
        """Test deleting multiple selected nodes removes all of them."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        # nodes 5 (terminal) and 6 (unconnected) are safe to delete independently
        nodes_to_delete = [5, 6]
        click_node(tracks_viewer, nodes_to_delete[0])
        for node in nodes_to_delete[1:]:
            click_node(tracks_viewer, node, append=True)

        tracks_viewer.delete_node()

        for node in nodes_to_delete:
            assert not tracks.graph.has_node(node)

    def test_delete_node_with_no_tracks(self, viewer):
        """Test delete_node does nothing when no tracks are loaded."""
        tracks_viewer = TracksViewer.get_instance(viewer)

        # Should not raise an error
        tracks_viewer.delete_node()


class TestEdgeOperations:
    """Tests for edge manipulation operations."""

    def test_delete_edge(self, tracks_viewer_setup, click_node):
        """Test deleting edges with various selection scenarios."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        # Test 1: Delete edge between two connected nodes
        edges = tracks.graph.edge_list()
        if not edges:
            pytest.skip("No edges in test graph")

        source, target = edges[0]
        click_node(tracks_viewer, source)
        click_node(tracks_viewer, target, append=True)

        tracks_viewer.delete_edge()

        # Verify the edge was actually deleted from the graph
        assert not tracks.graph.has_edge(source, target)

        # Test 2: Delete edge with wrong number of selections
        single_node = list(tracks.graph.node_ids())[0]
        click_node(tracks_viewer, single_node)

        edge_count_before = tracks.graph.num_edges()
        tracks_viewer.delete_edge()

        # Should not have deleted anything
        assert tracks.graph.num_edges() == edge_count_before

    def test_swap_nodes(self, viewer, graph_2d_without_segmentation, click_node):
        """Test swapping predecessors of two nodes updates the graph correctly.

        Extends graph_2d by adding node 7 (t=3) as a predecessor for node 6 (t=4).
        Nodes 5 and 6 are then at the same timepoint with different predecessors
        (4 and 7 respectively), creating a valid swap scenario.
        """
        graph_2d_without_segmentation.bulk_add_nodes(
            nodes=[
                {
                    "t": 3,
                    "pos": [95.0, 95.0],
                    "area": 100.0,
                    "track_id": 5,
                    "lineage_id": 2,
                    "solution": 1,
                }
            ],
            indices=[7],
        )
        graph_2d_without_segmentation.bulk_add_edges(
            [{"source_id": 7, "target_id": 6, "solution": 1}]
        )

        tracks = SolutionTracks(
            graph=graph_2d_without_segmentation, ndim=3, time_attr="t"
        )
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Select nodes 5 and 6 (both t=4, predecessors 4 and 7 respectively)
        click_node(tracks_viewer, 5)
        click_node(tracks_viewer, 6, append=True)

        tracks_viewer.swap_nodes()

        # After swap: predecessors are exchanged (4->6, 7->5)
        assert tracks.graph.has_edge(4, 6)
        assert tracks.graph.has_edge(7, 5)
        assert not tracks.graph.has_edge(4, 5)
        assert not tracks.graph.has_edge(7, 6)

    def test_create_edge_sorts_by_time(self, viewer, graph_2d, click_node):
        """Test create_edge orders nodes by time (earlier -> later).

        Uses graph_2d (with segmentation) so click_node goes through TrackLabels,
        which returns np.int64 node IDs — matching the real UI path.
        Uses MotileRun so edge attributes like 'iou' are registered in features.
        """
        tracks = MotileRun(graph=graph_2d, run_name="test", ndim=3, time_attr="t")
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Node 2 (t1, no successors) and node 6 (t4, no predecessors): valid free edge
        # Select in reverse time order to verify sorting
        click_node(tracks_viewer, 6)  # t4, clicked first
        click_node(tracks_viewer, 2, append=True)  # t1, shift-clicked second

        tracks_viewer.create_edge()

        # Edge must go from earlier (2) to later (6), regardless of selection order
        assert tracks.graph.has_edge(2, 6)

    def test_create_edge_with_force(self, viewer, graph_2d, monkeypatch, click_node):
        """Test create_edge handles forceable errors by retrying with force=True.

        Uses graph_2d (with segmentation) so click_node goes through TrackLabels,
        which returns np.int64 node IDs — matching the real UI path.
        Uses MotileRun so edge attributes like 'iou' are registered in features.
        """
        tracks = MotileRun(graph=graph_2d, run_name="test", ndim=3, time_attr="t")
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Node 4 (t2) already has incoming edge from node 3.
        # Adding edge 2(t1)->4 raises InvalidActionError(forceable=True).
        click_node(tracks_viewer, 2)
        click_node(tracks_viewer, 4, append=True)

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

    def test_display_modes(self, tracks_viewer_setup, click_node):
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
        node = list(tracks.graph.node_ids())[0]
        click_node(tracks_viewer, node)
        tracks_viewer.set_display_mode("lineage")
        assert tracks_viewer.mode == "lineage"
        assert isinstance(tracks_viewer.visible, list)
        assert node in tracks_viewer.visible

        # Test 4: Group mode (no group selected)
        tracks_viewer.set_display_mode("group")
        assert tracks_viewer.mode == "group"
        assert tracks_viewer.visible == []

    def test_filter_visible_nodes_preserves_previous_lineage(
        self, tracks_viewer_setup, click_node
    ):
        """Test lineage mode preserves previous visible nodes when selection cleared."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        # Select a node and switch to lineage mode
        node = list(tracks.graph.node_ids())[0]
        click_node(tracks_viewer, node)
        tracks_viewer.set_display_mode("lineage")

        # Clear selection
        tracks_viewer.selected_nodes.reset()
        tracks_viewer.filter_visible_nodes()

        # Should keep showing the previous lineage
        assert len(tracks_viewer.visible) > 0


class TestSelectionManagement:
    """Tests for selection tracking and updates."""

    def test_update_selection_centering(self, tracks_viewer_setup, click_node):
        """Test update_selection centering behavior with different selections."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        # Test 1: Center on single node
        node = list(tracks.graph.node_ids())[0]
        click_node(tracks_viewer, node)

        with patch.object(tracks_viewer, "center_on_node") as center_mock:
            tracks_viewer.update_selection(set_view=True)
            # Should center on the selected node
            center_mock.assert_called_once_with(node)

        # Test 2: No centering with multiple nodes
        tracks_viewer.selected_nodes.reset()
        nodes = list(tracks.graph.node_ids())[:2]
        for i, node in enumerate(nodes):
            click_node(tracks_viewer, node, append=(i > 0))

        with patch.object(tracks_viewer, "center_on_node") as center_mock:
            tracks_viewer.update_selection(set_view=True)
            # Should NOT center
            center_mock.assert_not_called()

    def test_selected_track_management(self, tracks_viewer_setup, click_node):
        """Test selected_track updates and clearing."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        # Test 1: Update selected_track from selection
        node = list(tracks.graph.node_ids())[0]
        click_node(tracks_viewer, node)
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

    def test_undo_redo_operations(self, tracks_viewer_setup, click_node):
        """Test undo restores deleted node and redo removes it again."""
        viewer, tracks_viewer, tracks = tracks_viewer_setup

        # Do a real action: delete unconnected node 3
        click_node(tracks_viewer, 3)
        tracks_viewer.delete_node()
        assert not tracks.graph.has_node(3)

        # Undo: node 3 should be restored
        tracks_viewer.undo()
        assert tracks.graph.has_node(3)

        # Redo: node 3 should be gone again
        tracks_viewer.redo()
        assert not tracks.graph.has_node(3)

        tracks_viewer.undo()
        assert tracks.graph.has_node(3)

    def test_undo_redo_with_no_tracks(self, viewer):
        """Test undo/redo do nothing when no tracks are loaded."""
        tracks_viewer = TracksViewer.get_instance(viewer)

        # Should not raise errors
        tracks_viewer.undo()
        tracks_viewer.redo()


class TestLayerCreation:
    """Tests that the correct napari layers are created after loading tracks."""

    def test_layers_present_after_update_tracks(self, viewer, solution_tracks_2d):
        """Test that points, tracks graph, and seg layers are added to the viewer
        after calling update_tracks with a SolutionTracks that has segmentation."""
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=solution_tracks_2d, name="test")

        layer_names = [layer.name for layer in viewer.layers]
        assert "test_points" in layer_names
        assert "test_tracks" in layer_names
        assert "test_seg" in layer_names

    def test_layer_types_after_update_tracks(self, viewer, solution_tracks_2d):
        """Test that the created layers have the correct types."""
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=solution_tracks_2d, name="test")

        layers_by_name = {layer.name: layer for layer in viewer.layers}
        assert isinstance(layers_by_name["test_points"], TrackPoints)
        assert isinstance(layers_by_name["test_tracks"], TrackGraph)
        assert isinstance(layers_by_name["test_seg"], TrackLabels)

    def test_layers_present_after_solve(self, viewer, segmentation_2d):
        """End-to-end test: solve on a segmentation, wrap result in MotileRun,
        load into TracksViewer, and verify all three layer types are present."""
        from motile_tracker.motile.backend import MotileRun, SolverParams, solve

        segmentation = segmentation_2d
        params = SolverParams()
        params.appear_cost = None
        solution_graph = solve(params, segmentation)

        run = MotileRun(
            graph=solution_graph,
            run_name="solve_test",
            input_segmentation=segmentation,
            ndim=3,
        )

        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=run, name="solve_test")

        layer_names = [layer.name for layer in viewer.layers]
        assert "solve_test_points" in layer_names
        assert "solve_test_tracks" in layer_names
        assert "solve_test_seg" in layer_names
