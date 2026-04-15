import numpy as np
import pytest

from motile_tracker.data_views.views.layers.track_labels import new_label
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


@pytest.fixture(autouse=True)
def clear_viewer_layers(viewer):
    """Clear viewer layers between tests."""
    yield
    viewer.layers.clear()


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


def test_paint_event(viewer, solution_tracks_3d_with_division):
    """Test paint event processing

    1) Paint with a new label (4), new track id (4)
    2) Replace node 3 with new label 6, breaking edge (2,3), establishing edge (5,6)
    3) Erase part of node 6
    4) Undo erase event

    TP
    0      1                   1                   1               1              1
           |                   |                   |               |              |
    1      2       -1->        2       -2->        2     -3->      2      -4->    2
          / \\                / \\                  \\              \\             \
    2    3   4               3   4               6   4          <6   4          6   4
                                                 |               |              |
    3                        5                   5               5              5
    """

    # Create example tracks
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=solution_tracks_3d_with_division, name="test")

    # Test selecting a new label
    new_label(tracks_viewer.tracking_layers.seg_layer)
    assert tracks_viewer.tracking_layers.seg_layer.selected_label == 5
    assert tracks_viewer.selected_track == 4  # new track id

    ### 1) Simulate paint event with new label
    tracks_viewer.tracking_layers.seg_layer.mode = "paint"
    step = list(
        viewer.dims.current_step
    )  # make sure the viewer is at the correct dims step
    step[0] = 3
    viewer.dims.current_step = step

    # use random target_value, will be overwritten automatically to ensure valid label
    event_val = create_event_val(
        tp=3, z=(15, 20), y=(45, 50), x=(75, 80), old_val=0, target_val=60
    )
    event = MockEvent(event_val)
    assert tracks_viewer.tracks.graph.num_nodes() == 4  # 4 nodes before the paint event
    tracks_viewer.tracking_layers.seg_layer._on_paint(event)

    # verify the new selected label is now at painted pixels.
    assert (
        int(np.asarray(tracks_viewer.tracking_layers.seg_layer.data[3, 15, 45, 75]))
        == 5
    )
    # verfiy that the node is present and has the correct track id.
    assert tracks_viewer.tracks.get_track_id(5) == 4
    assert tracks_viewer.tracks.graph.num_nodes() == 5  # 5 nodes after paint event
    assert tracks_viewer.tracks.graph.num_edges() == 3  # no new edges

    ### 2) Simulate paint event that overwrites an existing node with a new track id. Below
    # event aims to completely replace node 3 with a new label, that has track id 4, since
    # this is currently still the selected_track.

    event_val = create_event_val(
        tp=2, z=(55, 65), y=(45, 55), x=(40, 50), old_val=3, target_val=60
    )
    event = MockEvent(event_val)

    # Ensure we are acting at the right dims step
    step = list(viewer.dims.current_step)
    step[0] = 2
    viewer.dims.current_step = step

    # Run event and evaluate
    assert tracks_viewer.tracks.graph.num_nodes() == 5  # 5 nodes before paint event
    tracks_viewer.tracking_layers.seg_layer._on_paint(event)
    assert (
        tracks_viewer.tracks.graph.num_nodes() == 5
    )  # still 5 nodes after paint event
    # (node 3 has been replaced entirely)
    assert 3 not in tracks_viewer.tracks.graph.node_ids()  # node 3 is removed
    assert (
        int(np.asarray(tracks_viewer.tracking_layers.seg_layer.data[2, 55, 45, 40]))
        == 6
    )  # next
    # available value
    assert tracks_viewer.tracks.get_track_id(6) == 4  # the selected track id
    assert not tracks_viewer.tracks.graph.has_edge(2, 3)
    assert tracks_viewer.tracks.graph.has_edge(6, 5)

    ### 3) simulate an erase event (paint event with label 0) that removes part of label 6
    event_val = create_event_val(
        tp=2, z=(55, 57), y=(45, 48), x=(40, 42), old_val=6, target_val=0
    )
    event = MockEvent(event_val)

    # Run event and evaluate
    assert tracks_viewer.tracks.graph.num_nodes() == 5  # 5 nodes before paint event
    tracks_viewer.tracking_layers.seg_layer.mode = "erase"  # to correctly interpret
    # painting with 0

    tracks_viewer.tracking_layers.seg_layer._on_paint(event)
    assert (
        tracks_viewer.tracks.graph.num_nodes() == 5
    )  # still 5 nodes after paint event
    # (node 6 is now smaller)
    assert tracks_viewer.tracks.graph.nodes[6]["area"] < 1000
    assert (
        int(np.asarray(tracks_viewer.tracking_layers.seg_layer.data[2, 55, 45, 40]))
        == 0
    )  # erased

    ### 4) Test undoing the last paint event
    tracks_viewer.tracking_layers.seg_layer.undo()
    assert tracks_viewer.tracks.graph.nodes[6]["area"] == 1000
    assert (
        int(np.asarray(tracks_viewer.tracking_layers.seg_layer.data[2, 55, 45, 40]))
        == 6
    )  # back at 5


def test_ensure_valid_label(viewer, solution_tracks_3d_with_division):

    # Create example tracks
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=solution_tracks_3d_with_division, name="test")

    # Assert a valid selected_track is selected from the start
    assert tracks_viewer.tracking_layers.seg_layer.selected_label == 5
    assert tracks_viewer.selected_track == 4

    # Change the viewer dims and set the label to a value that is not allowed here (1)
    # because it exists at a different time point (0). When calling _ensure_valid_label,
    # we expect that the value is updated to 2, since node 1 and 2 have the same track id
    step = list(viewer.dims.current_step)
    step[0] = 1
    viewer.dims.current_step = step

    tracks_viewer.tracking_layers.seg_layer.selected_label = 1
    assert tracks_viewer.tracking_layers.seg_layer.selected_label == 2  # updated to 2
    assert tracks_viewer.selected_track == 1  # updated to 1, the track id of node 1

    # Change to a label that is new and note that it is reset to the label matching the
    # active track. A new label should be started via the new_label function.
    tracks_viewer.tracking_layers.seg_layer.selected_label = 6
    assert (
        tracks_viewer.tracking_layers.seg_layer.selected_label == 2
    )  # back to 2, since
    # we get the label corresponding to the active selected track
    assert tracks_viewer.selected_track == 1  # still at 1, track id of node 2

    # If no selected_track is known, a new one will be assigned to the selected_label if
    # selected_label is not yet associated with any track...
    tracks_viewer.selected_track = None  # set to None first
    tracks_viewer.tracking_layers.seg_layer.selected_label = 6
    assert tracks_viewer.tracking_layers.seg_layer.selected_label == 6  # still at 6
    assert (
        tracks_viewer.selected_track == 4
    )  # updated to 4, new track id (track id 4 was
    # reserved during initialization but never used, so it's still available)

    # ...otherwise the selected_track will be updated to the track associated with
    # selected_label
    tracks_viewer.selected_track = None  # set to None first
    tracks_viewer.tracking_layers.seg_layer.selected_label = 2
    assert tracks_viewer.tracking_layers.seg_layer.selected_label == 2  # still at 2
    assert tracks_viewer.selected_track == 1  # updated to 1, matching label 2

    # Verify starting a new track via the new_label function
    new_label(tracks_viewer.tracking_layers.seg_layer)
    assert tracks_viewer.tracking_layers.seg_layer.selected_label == 5  # next available
    # value
    assert tracks_viewer.selected_track == 4  # new track id (still unused)


def test_data_setitem_empty_indices_does_not_raise(
    viewer, solution_tracks_3d_with_division
):
    """Regression: painting outside the array bounds produces empty index arrays.

    napari clips brush pixels to the array bounds before calling data_setitem.
    When all pixels are outside the bounds the resulting index arrays are empty,
    and ``min()`` on an empty sequence raised ``ValueError``.
    The fix returns early when any index array is empty.
    """
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=solution_tracks_3d_with_division, name="test")
    seg_layer = tracks_viewer.tracking_layers.seg_layer

    # Empty index arrays simulate the case where the brush was fully outside the image.
    empty_indices = tuple(
        np.array([], dtype=np.int64) for _ in range(seg_layer.data.ndim)
    )

    # Must not raise ValueError ("min() iterable argument is empty")
    with seg_layer.block_history():
        seg_layer.data_setitem(empty_indices, 1)


def test_undo_on_readonly_data_does_not_fire_paint_event(
    viewer, solution_tracks_3d_with_division
):
    """Regression: undo() on a layer with read-only data must restore the display
    buffer directly, without firing events.paint.

    Before the fix, undo() fell through to Labels.undo() which called
    data_setitem(), which in turn fired events.paint for read-only (GraphArrayView)
    data.  In the ortho-view scenario that paint event triggered a recursive revert
    producing a TypeError.  The fix overrides undo() to restore the display buffer
    directly without emitting any paint event.
    """
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=solution_tracks_3d_with_division, name="test")
    seg_layer = tracks_viewer.tracking_layers.seg_layer

    # Put a synthetic atom directly into _undo_history to avoid running the full
    # paint pipeline (which has its own side-effects on the track graph).
    # Atom format: (indices, old_values, new_value)
    indices = (
        np.array([0], dtype=np.int64),
        np.array([50], dtype=np.int64),
        np.array([50], dtype=np.int64),
        np.array([50], dtype=np.int64),
    )
    old_values = np.array([0], dtype=np.int64)
    seg_layer._undo_history.append([(indices, old_values, 1)])

    paint_events_fired = []
    seg_layer.events.paint.connect(lambda event: paint_events_fired.append(event))

    # Must not fire a paint event (and must not raise).
    seg_layer.undo()

    assert paint_events_fired == [], (
        "undo() on read-only data must restore the display buffer directly "
        "without emitting events.paint"
    )
