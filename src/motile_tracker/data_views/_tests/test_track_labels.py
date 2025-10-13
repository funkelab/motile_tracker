import numpy as np
from funtracks.data_model import SolutionTracks

from motile_tracker.data_views.views.layers.track_labels import new_label
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


class MockEvent:
    def __init__(self, value):
        self.value = value


def create_event_val(
    tp: int, z: tuple[int], y: tuple[int], x: tuple[int], old_val: int, target_val: int
):
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

    # create the event
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


def test_paint_event(make_napari_viewer, graph_3d, segmentation_3d):
    """Test paint event processing"""

    viewer = make_napari_viewer()

    # Create example tracks
    tracks = SolutionTracks(graph=graph_3d, segmentation=segmentation_3d, ndim=4)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    # Test selecting a new label
    new_label(tracks_viewer.tracking_layers.seg_layer)
    assert tracks_viewer.tracking_layers.seg_layer.selected_label == 4
    assert tracks_viewer.selected_track == 4  # new track id

    # 1) Simulate paint event with new label
    tracks_viewer.tracking_layers.seg_layer.mode = "paint"
    step = list(
        viewer.dims.current_step
    )  # make sure the viewer is at the correct dims step
    step[0] = 2
    viewer.dims.current_step = step

    # use random target_value, will be overwritten automatically to ensure valid label
    event_val = create_event_val(
        tp=2, z=(15, 20), y=(45, 50), x=(75, 80), old_val=0, target_val=60
    )
    event = MockEvent(event_val)
    assert len(tracks_viewer.tracks.graph.nodes) == 3  # 3 nodes before the paint event
    tracks_viewer.tracking_layers.seg_layer._on_paint(event)

    assert tracks_viewer.tracking_layers.seg_layer.data[2, 15, 45, 75] == 4  # the new
    # selected label
    assert (
        tracks_viewer.tracks.get_track_id(4) == 4
    )  # test that the node is present and
    # has the correct track id.
    assert len(tracks_viewer.tracks.graph.nodes) == 4  # 4 nodes after paint event

    # 2) Simulate paint event that overwrites an existing node with a new track id. Below
    # event aims to completely replace node 2 with a new label, that has track id 4, since
    # this is currently still selected

    # first remove the current values (with a true paint event this happens automatically,
    # but since were are simulating here we have to set it ourselves.)
    tracks_viewer.tracking_layers.seg_layer.data[1, 15:25, 45:55, 75:85] = 0
    event_val = create_event_val(
        tp=1, z=(15, 25), y=(45, 55), x=(75, 85), old_val=2, target_val=60
    )
    event = MockEvent(event_val)

    # ensure we are acting at the right dims step
    step = list(viewer.dims.current_step)
    step[0] = 1
    viewer.dims.current_step = step

    # run event and evaluate
    assert len(tracks_viewer.tracks.graph.nodes) == 4  # 4 nodes before paint event
    tracks_viewer.tracking_layers.seg_layer._on_paint(event)
    assert (
        len(tracks_viewer.tracks.graph.nodes) == 4
    )  # still 4 nodes after paint event (node 2 has been replaced entirely)
    assert 2 not in tracks_viewer.tracks.graph.nodes  # node 2 is removed
    assert (
        tracks_viewer.tracking_layers.seg_layer.data[1, 15, 45, 75] == 5
    )  # next available value
    assert tracks_viewer.tracks.get_track_id(4) == 4  # the selected track id

    # 3) simulate an erase event (paint event with label 0) that removes part of label 5
    event_val = create_event_val(
        tp=1, z=(15, 17), y=(45, 48), x=(75, 78), old_val=5, target_val=0
    )
    event = MockEvent(event_val)

    # run event and evaluate
    assert len(tracks_viewer.tracks.graph.nodes) == 4  # 4 nodes before paint event
    tracks_viewer.tracking_layers.seg_layer.mode = (
        "erase"  # to correctly interpret painting with 0
    )
    tracks_viewer.tracking_layers.seg_layer._on_paint(event)
    assert (
        len(tracks_viewer.tracks.graph.nodes) == 4
    )  # still 4 nodes after paint event (node 4 is now smaller)
    assert tracks_viewer.tracks.graph.nodes[5]["area"] < 1000
    assert tracks_viewer.tracking_layers.seg_layer.data[1, 15, 45, 75] == 0  # erased
