"""Tests for force operations functionality in user interactions.

This module tests the force option dialog and the force parameter behavior
when performing operations like adding nodes, adding edges, and updating
segmentations that would normally fail due to conflicts.
"""

import numpy as np
import pytest
from funtracks.data_model import SolutionTracks
from funtracks.exceptions import InvalidActionError
from qtpy.QtWidgets import QMessageBox

from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer
from motile_tracker.data_views.views_coordinator.user_dialogs import (
    confirm_force_operation,
)


class MockEvent:
    """Mock event for simulating paint/edit events."""

    def __init__(self, value):
        self.value = value


def create_event_val(
    tp: int, z: tuple[int], y: tuple[int], x: tuple[int], old_val: int, target_val: int
) -> list[
    tuple[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray], np.ndarray, int]
]:
    """Create event values to simulate a paint event."""
    # construct coordinate lists
    z = np.arange(z[0], z[1])
    y = np.arange(y[0], y[1])
    x = np.arange(x[0], x[1])

    # Create all combinations of x, y, z indices
    Z, Y, X = np.meshgrid(z, y, x, indexing="ij")

    # Flatten to 1D
    tp_idx = np.full(X.size, tp)
    z_idx = Z.ravel()
    y_idx = Y.ravel()
    x_idx = X.ravel()

    old_vals = np.full_like(tp_idx, old_val, dtype=np.uint16)

    # create the event value
    event_val = [
        (
            (
                tp_idx,
                z_idx,
                y_idx,
                x_idx,
            ),  # flattened coordinate arrays, all same length
            old_vals,  # same length, pretend that it is equal to old_val
            target_val,  # new value, will be overwritten
        )
    ]

    return event_val


def test_confirm_force_operation_yes(qtbot, monkeypatch):
    """Test the confirm_force_operation dialog when user clicks 'Yes'."""

    # Mock the message box exec_ to automatically click 'Yes'
    def mock_exec(self):
        # Simulate clicking the first button (Yes)
        self._clicked_button = self.buttons()[0]
        return 0

    monkeypatch.setattr(QMessageBox, "exec_", mock_exec)
    monkeypatch.setattr(QMessageBox, "clickedButton", lambda self: self._clicked_button)

    force, always_force = confirm_force_operation("Test operation conflict")
    assert force is True
    assert always_force is False


def test_confirm_force_operation_yes_always(qtbot, monkeypatch):
    """Test the confirm_force_operation dialog when user clicks 'Yes, always'."""

    # Mock the message box exec_ to automatically click 'Yes, always'
    def mock_exec(self):
        # Simulate clicking the second button (Yes, always)
        self._clicked_button = self.buttons()[1]
        return 0

    monkeypatch.setattr(QMessageBox, "exec_", mock_exec)
    monkeypatch.setattr(QMessageBox, "clickedButton", lambda self: self._clicked_button)

    force, always_force = confirm_force_operation("Test operation conflict")
    assert force is True
    assert always_force is True


def test_confirm_force_operation_no(qtbot, monkeypatch):
    """Test the confirm_force_operation dialog when user clicks 'No'."""

    # Mock the message box exec_ to automatically click 'No'
    def mock_exec(self):
        # Simulate clicking the third button (No)
        self._clicked_button = self.buttons()[2]
        return 0

    monkeypatch.setattr(QMessageBox, "exec_", mock_exec)
    monkeypatch.setattr(QMessageBox, "clickedButton", lambda self: self._clicked_button)

    force, always_force = confirm_force_operation("Test operation conflict")
    assert force is False
    assert always_force is False


def test_add_nodes_force_on_conflict(make_napari_viewer, graph_3d, segmentation_3d):
    """Test adding a node at an existing time point with force=True.

    This should normally fail but succeed when force=True.
    """
    viewer = make_napari_viewer()

    # Create example tracks
    tracks = SolutionTracks(graph=graph_3d, segmentation=segmentation_3d, ndim=4)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    # Node 2 exists at time 1 with track_id 1
    # Try to add another node at time 1 with the same track_id
    # This should fail without force
    attributes = {
        "track_id": 1,
        "t": 1,
        "z": 30,
        "y": 30,
        "x": 30,
        "area": 500,
    }

    # Should raise InvalidActionError without force
    with pytest.raises(InvalidActionError) as exc_info:
        tracks_viewer.tracks_controller.add_nodes([attributes], force=False)
    assert exc_info.value.forceable is True

    # Should succeed with force=True
    initial_node_count = len(tracks_viewer.tracks.graph.nodes)
    tracks_viewer.tracks_controller.add_nodes([attributes], force=True)
    assert len(tracks_viewer.tracks.graph.nodes) == initial_node_count + 1


def test_add_edges_force_on_conflict(make_napari_viewer, graph_3d, segmentation_3d):
    """Test adding an edge that creates a conflict with force=True.

    Adding edge (3, 4) would create a division from node 2 (which already
    has children 3 and 4), resulting in a node with 3 children.
    This should fail without force but succeed with force=True.
    """
    viewer = make_napari_viewer()

    # Create example tracks with edges: (1, 2), (2, 3), (2, 4)
    tracks = SolutionTracks(graph=graph_3d, segmentation=segmentation_3d, ndim=4)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    # Try to add edge (3, 4) which would give node 2 three children
    # This should fail without force
    edge = np.array([[3, 4]])

    with pytest.raises(InvalidActionError) as exc_info:
        tracks_viewer.tracks_controller.add_edges(edges=edge, force=False)
    assert exc_info.value.forceable is True

    # Should succeed with force=True
    initial_edge_count = len(tracks_viewer.tracks.graph.edges)
    tracks_viewer.tracks_controller.add_edges(edges=edge, force=True)
    assert len(tracks_viewer.tracks.graph.edges) == initial_edge_count + 1
    assert (3, 4) in tracks_viewer.tracks.graph.edges


def test_update_segmentations_force_on_conflict(
    make_napari_viewer, graph_3d, segmentation_3d
):
    """Test updating segmentation that would create invalid state with force=True."""
    viewer = make_napari_viewer()

    # Create example tracks
    tracks = SolutionTracks(graph=graph_3d, segmentation=segmentation_3d, ndim=4)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    # Try to paint over node 3 with a label that has a different track_id
    # and would create an invalid connection
    tracks_viewer.selected_track = 2  # different from node 3's track_id

    # Get the pixels for node 3
    time = 2
    pixels = np.where(segmentation_3d[time] == 3)
    updated_pixels = np.stack([np.full(len(pixels[0]), time), *pixels])

    # This should raise InvalidActionError without force
    with pytest.raises(InvalidActionError) as exc_info:
        tracks_viewer.tracks_controller.update_segmentations(
            target_value=0,  # erasing
            updated_pixels=updated_pixels,
            time=time,
            track_id=tracks_viewer.selected_track,
            force=False,
        )
    assert exc_info.value.forceable is True

    # Should succeed with force=True
    tracks_viewer.tracks_controller.update_segmentations(
        target_value=0,  # erasing
        updated_pixels=updated_pixels,
        time=time,
        track_id=tracks_viewer.selected_track,
        force=True,
    )


def test_paint_with_force_dialog_yes(
    make_napari_viewer, qtbot, monkeypatch, graph_3d, segmentation_3d
):
    """Test paint operation that triggers force dialog and user clicks 'Yes'."""
    viewer = make_napari_viewer()

    # Create example tracks
    tracks = SolutionTracks(graph=graph_3d, segmentation=segmentation_3d, ndim=4)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    # Mock the dialog to return 'Yes' (force=True, always_force=False)
    def mock_confirm(message):
        return True, False

    monkeypatch.setattr(
        "motile_tracker.data_views.views.layers.track_labels.confirm_force_operation",
        mock_confirm,
    )

    # Select track 1 and try to paint at time 1 where node 2 already exists
    tracks_viewer.selected_track = 1
    tracks_viewer.tracking_layers.seg_layer.selected_label = 5

    step = list(viewer.dims.current_step)
    step[0] = 1
    viewer.dims.current_step = step

    # Try to paint where node 2 already exists (should trigger conflict)
    event_val = create_event_val(
        tp=1, z=(15, 25), y=(45, 55), x=(75, 85), old_val=2, target_val=5
    )
    event = MockEvent(event_val)
    tracks_viewer.tracking_layers.seg_layer.mode = "paint"

    tracks_viewer.tracking_layeSrs.seg_layer._on_paint(event)

    # The operation should have been forced through
    # Node 2 should be modified or replaced
    assert tracks_viewer.force is False  # should remain False for 'Yes' option


def test_paint_with_force_dialog_yes_always(
    make_napari_viewer, qtbot, monkeypatch, graph_3d, segmentation_3d
):
    """Test paint operation with 'Yes, always' sets the force flag permanently."""
    viewer = make_napari_viewer()

    # Create example tracks
    tracks = SolutionTracks(graph=graph_3d, segmentation=segmentation_3d, ndim=4)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    # Mock the dialog to return 'Yes, always' (force=True, always_force=True)
    def mock_confirm(message):
        return True, True

    monkeypatch.setattr(
        "motile_tracker.data_views.views.layers.track_labels.confirm_force_operation",
        mock_confirm,
    )

    # Verify force is initially False
    assert tracks_viewer.force is False

    # Select track 1 and try to paint at time 1 where node 2 already exists
    tracks_viewer.selected_track = 1
    tracks_viewer.tracking_layers.seg_layer.selected_label = 5

    step = list(viewer.dims.current_step)
    step[0] = 1
    viewer.dims.current_step = step

    # Try to paint where node 2 already exists
    event_val = create_event_val(
        tp=1, z=(15, 25), y=(45, 55), x=(75, 85), old_val=2, target_val=5
    )
    event = MockEvent(event_val)
    tracks_viewer.tracking_layers.seg_layer.mode = "paint"

    tracks_viewer.tracking_layers.seg_layer._on_paint(event)

    # The force flag should now be set to True permanently
    assert tracks_viewer.force is True


def test_paint_with_force_dialog_no(
    make_napari_viewer, qtbot, monkeypatch, graph_3d, segmentation_3d
):
    """Test paint operation that triggers force dialog and user clicks 'No'."""
    viewer = make_napari_viewer()

    # Create example tracks
    tracks = SolutionTracks(graph=graph_3d, segmentation=segmentation_3d, ndim=4)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    # Mock the dialog to return 'No' (force=False, always_force=False)
    def mock_confirm(message):
        return False, False

    monkeypatch.setattr(
        "motile_tracker.data_views.views.layers.track_labels.confirm_force_operation",
        mock_confirm,
    )

    # Select track 1 and try to paint at time 1 where node 2 already exists
    tracks_viewer.selected_track = 1
    tracks_viewer.tracking_layers.seg_layer.selected_label = 5

    step = list(viewer.dims.current_step)
    step[0] = 1
    viewer.dims.current_step = step

    # Try to paint where node 2 already exists
    event_val = create_event_val(
        tp=1, z=(15, 25), y=(45, 55), x=(75, 85), old_val=2, target_val=5
    )
    event = MockEvent(event_val)
    tracks_viewer.tracking_layers.seg_layer.mode = "paint"

    initial_node_count = len(tracks_viewer.tracks.graph.nodes)
    tracks_viewer.tracking_layers.seg_layer._on_paint(event)

    # The operation should have been cancelled
    # Node count should remain the same
    assert len(tracks_viewer.tracks.graph.nodes) == initial_node_count
    assert tracks_viewer.force is False


def test_add_point_with_force_dialog(
    make_napari_viewer, qtbot, monkeypatch, graph_3d, segmentation_3d
):
    """Test adding a point that triggers force dialog."""
    viewer = make_napari_viewer()

    # Create tracks without segmentation to enable point adding
    tracks = SolutionTracks(graph=graph_3d, segmentation=None, ndim=4)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    # Mock the dialog to return 'Yes'
    def mock_confirm(message):
        return True, False

    monkeypatch.setattr(
        "motile_tracker.data_views.views.layers.track_points.confirm_force_operation",
        mock_confirm,
    )

    # Try to add a point at time 1 with track_id 1 (where node 2 already exists)
    tracks_viewer.selected_track = 1

    step = list(viewer.dims.current_step)
    step[0] = 1
    viewer.dims.current_step = step

    # Simulate adding a point
    initial_node_count = len(tracks_viewer.tracks.graph.nodes)
    new_point = np.array([[1, 30, 30, 30]])  # t, z, y, x

    # Manually set up the point data to trigger the add
    tracks_viewer.tracking_layers.graph_layer.data = np.vstack(
        [tracks_viewer.tracking_layers.graph_layer.data, new_point]
    )

    # Create a mock event to trigger _update_data
    class MockPointEvent:
        def __init__(self):
            self.action = "added"
            self.data_indices = [
                len(tracks_viewer.tracking_layers.graph_layer.data) - 1
            ]
            self.value = new_point

    event = MockPointEvent()
    tracks_viewer.tracking_layers.graph_layer._update_data(event)

    # The operation should have been forced through
    assert len(tracks_viewer.tracks.graph.nodes) > initial_node_count


def test_add_edge_with_force_through_viewer(
    make_napari_viewer, qtbot, monkeypatch, graph_3d, segmentation_3d
):
    """Test adding an edge through the viewer that triggers force dialog."""
    viewer = make_napari_viewer()

    # Create example tracks
    tracks = SolutionTracks(graph=graph_3d, segmentation=segmentation_3d, ndim=4)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    # Mock the dialog to return 'Yes'
    def mock_confirm(message):
        return True, False

    monkeypatch.setattr(
        "motile_tracker.data_views.views_coordinator.tracks_viewer.confirm_force_operation",
        mock_confirm,
    )

    # Try to create an edge that would cause a conflict
    # Add edge (3, 4) which would give node 2 three children
    tracks_viewer.node_selection_list.selected_ids = [3, 4]

    initial_edge_count = len(tracks_viewer.tracks.graph.edges)
    tracks_viewer.link_nodes()

    # The operation should have been forced through
    assert len(tracks_viewer.tracks.graph.edges) > initial_edge_count
    assert (3, 4) in tracks_viewer.tracks.graph.edges


def test_force_flag_persists_across_operations(
    make_napari_viewer, qtbot, monkeypatch, graph_3d, segmentation_3d
):
    """Test that the force flag persists across multiple operations when set."""
    viewer = make_napari_viewer()

    # Create example tracks
    tracks = SolutionTracks(graph=graph_3d, segmentation=segmentation_3d, ndim=4)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    # Set force to True
    tracks_viewer.force = True

    # Try operations that would normally fail - they should succeed without dialog
    # 1. Add node at conflicting time
    attributes = {
        "track_id": 1,
        "t": 1,
        "z": 30,
        "y": 30,
        "x": 30,
        "area": 500,
    }

    initial_node_count = len(tracks_viewer.tracks.graph.nodes)
    tracks_viewer.tracks_controller.add_nodes([attributes], force=True)
    assert len(tracks_viewer.tracks.graph.nodes) == initial_node_count + 1

    # 2. Add conflicting edge
    new_node_id = max(tracks_viewer.tracks.graph.nodes) + 1
    edge = np.array([[3, new_node_id]])

    initial_edge_count = len(tracks_viewer.tracks.graph.edges)
    tracks_viewer.tracks_controller.add_edges(edges=edge, force=True)
    assert len(tracks_viewer.tracks.graph.edges) == initial_edge_count + 1

    # Force flag should still be True
    assert tracks_viewer.force is True
