"""Tests for force operations functionality in user interactions.

This module tests the force option dialog and the force parameter behavior
when performing operations like adding nodes and edges that would normally fail due to
conflicts.
"""

from unittest.mock import MagicMock, patch

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
    def __init__(self, value):
        self.value = value


def create_event_val(
    tp: int, z: tuple[int], y: tuple[int], x: tuple[int], old_val: int, target_val: int
) -> list[
    tuple[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray], np.ndarray, int]
]:
    """Create event values to simulate a paint event"""

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


@pytest.mark.parametrize(
    "button_index, expected",
    [
        (0, (True, True)),  # Yes, always
        (1, (True, False)),  # Yes
        (2, (False, False)),  # No
    ],
)
def test_confirm_force_operation_all_buttons(
    qtbot, monkeypatch, button_index, expected
):
    """Test confirm_force_operation for each button and print which was clicked."""

    clicked_texts = []  # Store clicked button labels for printing

    def mock_exec(self):
        # Simulate clicking one of the buttons based on param
        self._clicked_button = self.buttons()[button_index]
        clicked_texts.append(self._clicked_button.text())
        return 0

    # Patch QMessageBox behavior
    monkeypatch.setattr(QMessageBox, "exec_", mock_exec)
    monkeypatch.setattr(QMessageBox, "clickedButton", lambda self: self._clicked_button)

    # Run the dialog under test
    force, always_force = confirm_force_operation("Test operation conflict")

    # Print results
    print(f"Simulated click on: '{clicked_texts[0]}' → Returned: {force, always_force}")

    # Verify correctness
    assert (force, always_force) == expected


@pytest.mark.parametrize(
    "confirm_response, expect_force_retry",
    [
        ((True, True), True),  # User clicks "Yes, always"
        ((True, False), True),  # User clicks "Yes"
        ((False, False), False),  # User clicks "No"
    ],
)
def test_on_paint_invalid_action_upstream_division1_forceable(
    make_napari_viewer,
    graph_3d_with_division,
    segmentation_3d_boxes,
    monkeypatch,
    confirm_response,
    expect_force_retry,
):
    """Test paint event processing

    1) Paint with a the track_id (3) of node 4, at the time point of node 2. This is
        technically invalid, because node 2 has already divided upstream. Therefore, the
        force dialog should pop up.

    2) (Control) Setting tracks_viewer.selected_track to None should allow painting with
        a new track_id, therefore, no InvalidActionError should be raised, and no dialog
        should be triggered.


    TP
    0      1                   1            Control:        1                1
           |                   |                            |                |
    1      2       -1->        2   5                        2       -2->     2    5
          / \\     (force)     /    |                       / \\              / \
    2    3   4               3     4                      3   4            3   4

    """

    viewer = make_napari_viewer()

    # Create example tracks
    tracks = SolutionTracks(
        graph=graph_3d_with_division, segmentation=segmentation_3d_boxes, ndim=4
    )
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    ### 1) Simulate paint event with new label
    tracks_viewer.tracking_layers.seg_layer.mode = "paint"
    step = list(
        viewer.dims.current_step
    )  # make sure the viewer is at the correct dims step
    step[0] = 1
    viewer.dims.current_step = step
    tracks_viewer.selected_track = 3

    # use random target_value, will be overwritten automatically to ensure valid label
    event_val = create_event_val(
        tp=1, z=(15, 18), y=(45, 48), x=(75, 73), old_val=0, target_val=5
    )
    event = MockEvent(event_val)

    # Mock internals
    update_mock = MagicMock()
    seg_layer = tracks_viewer.tracking_layers.seg_layer

    # First call raises InvalidActionError(forceable=True)
    update_mock.side_effect = [
        InvalidActionError("Mock invalid action", forceable=True),
        None,  # second call (if retried)
    ]

    # Mock the confirm_force_operation dialog
    monkeypatch.setattr(
        "motile_tracker.data_views.views.layers.track_labels.confirm_force_operation",
        lambda message: confirm_response,
    )

    # Mock undo and refresh
    parent_class = seg_layer.__class__.__mro__[1]
    undo_mock = MagicMock(name="undo")
    monkeypatch.setattr(parent_class, "undo", undo_mock)
    seg_layer._refresh = MagicMock()
    seg_layer.tracks_viewer.force = False

    # Run test with patched UserUpdateSegmentation
    with patch(
        "motile_tracker.data_views.views.layers.track_labels.UserUpdateSegmentation",
        update_mock,
    ):
        seg_layer._on_paint(event)

    # Verify
    if expect_force_retry:
        # It should have called update_segmentations twice (retry with force)
        assert update_mock.call_count == 2
        # Force flag should match confirm_response[1]
        assert seg_layer.tracks_viewer.force == confirm_response[1]
        seg_layer._refresh.assert_not_called()
    else:
        # Only first call attempted, then undo + refresh
        assert update_mock.call_count == 1
        seg_layer._refresh.assert_called_once()
        parent_class.undo.assert_called_once()

    ### 2) Control case (no dialog triggered)
    # Reset mocks and behavior
    update_mock.reset_mock()
    undo_mock.reset_mock()
    seg_layer._refresh.reset_mock()

    # Make update_segmentations succeed immediately
    update_mock.side_effect = None

    # Control condition: no track selected
    tracks_viewer.selected_track = None

    with patch(
        "motile_tracker.data_views.views.layers.track_labels.UserUpdateSegmentation",
        update_mock,
    ):
        seg_layer._on_paint(event)

    # It should have been called exactly once, no InvalidActionError branch
    assert update_mock.call_count == 1, "update_segmentations should succeed normally"
    undo_mock.assert_not_called()
    seg_layer._refresh.assert_not_called()


@pytest.mark.parametrize(
    "confirm_response, expect_force_retry",
    [
        ((True, True), True),  # User clicks "Yes, always"
        ((True, False), True),  # User clicks "Yes"
        ((False, False), False),  # User clicks "No"
    ],
)
def test_on_paint_invalid_action_upstream_division2_forceable(
    make_napari_viewer,
    graph_3d_with_division,
    segmentation_3d_boxes,
    monkeypatch,
    confirm_response,
    expect_force_retry,
):
    """Test paint event processing

    1) Paint with the track_id of node 2 at time point 2. This is invalid, because node 2
        has already divided at time point 1.

    2) (Control) Setting tracks_viewer.selected_track to None should allow painting with
        a new track_id.

    0      1                   1            Control:        1                1
           |                   |                            |                |
    1      2       -1->        2                            2       -2->     2
          / \\     (force)      |                           / \\              / \
    2    3   4              3  5  4                       3   4            3   4  5

    """

    viewer = make_napari_viewer()

    # Create example tracks
    tracks = SolutionTracks(
        graph=graph_3d_with_division, segmentation=segmentation_3d_boxes, ndim=4
    )
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    ### 1) Simulate paint event with new label
    tracks_viewer.tracking_layers.seg_layer.mode = "paint"
    step = list(
        viewer.dims.current_step
    )  # make sure the viewer is at the correct dims step
    step[0] = 2
    viewer.dims.current_step = step
    tracks_viewer.selected_track = 1

    # use random target_value, will be overwritten automatically to ensure valid label
    event_val = create_event_val(
        tp=2, z=(15, 18), y=(45, 48), x=(75, 73), old_val=0, target_val=5
    )
    event = MockEvent(event_val)

    # Mock internals
    update_mock = MagicMock()
    seg_layer = tracks_viewer.tracking_layers.seg_layer

    # First call raises InvalidActionError(forceable=True)
    update_mock.side_effect = [
        InvalidActionError("Mock invalid action", forceable=True),
        None,  # second call (if retried)
    ]

    # Mock the confirm_force_operation dialog
    monkeypatch.setattr(
        "motile_tracker.data_views.views.layers.track_labels.confirm_force_operation",
        lambda message: confirm_response,
    )

    # Mock undo and refresh
    parent_class = seg_layer.__class__.__mro__[1]
    undo_mock = MagicMock(name="undo")
    monkeypatch.setattr(parent_class, "undo", undo_mock)
    seg_layer._refresh = MagicMock()
    seg_layer.tracks_viewer.force = False

    # Run test with patched UserUpdateSegmentation
    with patch(
        "motile_tracker.data_views.views.layers.track_labels.UserUpdateSegmentation",
        update_mock,
    ):
        seg_layer._on_paint(event)

    # Verify
    if expect_force_retry:
        # It should have called update_segmentations twice (retry with force)
        assert update_mock.call_count == 2
        # Force flag should match confirm_response[1]
        assert seg_layer.tracks_viewer.force == confirm_response[1]
        seg_layer._refresh.assert_not_called()
    else:
        # Only first call attempted, then undo + refresh
        assert update_mock.call_count == 1
        seg_layer._refresh.assert_called_once()
        parent_class.undo.assert_called_once()

    ### 2) Control case (no dialog triggered)
    # Reset mocks and behavior
    update_mock.reset_mock()
    undo_mock.reset_mock()
    seg_layer._refresh.reset_mock()

    # Make update_segmentations succeed immediately
    update_mock.side_effect = None

    # Control condition: no track selected
    tracks_viewer.selected_track = None

    with patch(
        "motile_tracker.data_views.views.layers.track_labels.UserUpdateSegmentation",
        update_mock,
    ):
        seg_layer._on_paint(event)

    # It should have been called exactly once, no InvalidActionError branch
    assert update_mock.call_count == 1, "update_segmentations should succeed normally"
    undo_mock.assert_not_called()
    seg_layer._refresh.assert_not_called()


@pytest.mark.parametrize(
    "confirm_response, expect_force_retry",
    [
        ((True, True), True),  # User clicks “Yes, always”
        ((True, False), True),  # User clicks “Yes”
        ((False, False), False),  # User clicks “No”
    ],
)
def test_invalid_edge_force(
    make_napari_viewer,
    graph_3d_with_division,
    segmentation_3d_boxes,
    monkeypatch,
    confirm_response,
    expect_force_retry,
):
    r"""Test paint event processing

    1) Add a new, disconnected node (5)
    2) Create an edge between node 5 and 4. This is invalid, because 4 already has an
        incoming edge. Therefore, the force dialog should be triggered.

    TP
    0      1                   1                   1
           |                   |                   |
    1      2       -1->        2    5   -2->       2   5
          / \                 / \      (force)     |   |
    2    3   4               3   4                 3   4


    """

    viewer = make_napari_viewer()

    # Create example tracks
    tracks = SolutionTracks(
        graph=graph_3d_with_division, segmentation=segmentation_3d_boxes, ndim=4
    )
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    ### 1) Simulate paint event with new label
    tracks_viewer.tracking_layers.seg_layer.mode = "paint"
    step = list(
        viewer.dims.current_step
    )  # make sure the viewer is at the correct dims step
    step[0] = 1
    viewer.dims.current_step = step
    tracks_viewer.selected_track = None  # paint with a new track_id

    # use random target_value, will be overwritten automatically to ensure valid label
    event_val = create_event_val(
        tp=1, z=(15, 17), y=(45, 47), x=(75, 78), old_val=0, target_val=5
    )
    event = MockEvent(event_val)
    assert len(tracks_viewer.tracks.graph.nodes) == 4  # 4 nodes before the paint event
    tracks_viewer.tracking_layers.seg_layer._on_paint(event)
    assert len(tracks_viewer.tracks.graph.nodes) == 5  # 5 nodes after the paint event

    ### 2) Add an invalid edge and verify that the dialog was called
    tracks_viewer.selected_nodes = [5, 4]

    # Mock UserAddEdge
    add_edges_mock = MagicMock()
    add_edges_mock.side_effect = [
        InvalidActionError("Mock invalid edge", forceable=True),  # first call fails
        None,  # second call (forced)
    ]

    # Mock dialog
    monkeypatch.setattr(
        "motile_tracker.data_views.views_coordinator.tracks_viewer.confirm_force_operation",
        lambda message: confirm_response,
    )

    # Run create_edge() with patched UserAddEdge
    with patch(
        "motile_tracker.data_views.views_coordinator.tracks_viewer.UserAddEdge",
        add_edges_mock,
    ):
        tracks_viewer.create_edge()

    if expect_force_retry:
        # Dialog triggered and retried
        assert add_edges_mock.call_count == 2
        assert tracks_viewer.force == confirm_response[1]
    else:
        # Not retried
        assert add_edges_mock.call_count == 1
        assert tracks_viewer.force is False

    # Check that the correct edge was attempted
    first_call = add_edges_mock.call_args_list[0]
    assert first_call[1]["source"] == 5
    assert first_call[1]["target"] == 4
