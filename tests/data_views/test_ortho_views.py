import numpy as np
import pytest
from napari.layers import Labels, Points
from napari_orthogonal_views.ortho_view_widget import OrthoViewWidget

from motile_tracker.data_views.views.layers.track_labels import TrackLabels
from motile_tracker.data_views.views.layers.track_points import TrackPoints
from motile_tracker.data_views.views.ortho_views import (
    initialize_ortho_views,
)
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


@pytest.fixture(autouse=True)
def clear_viewer_layers(viewer):
    """Clear viewer layers between tests."""
    yield
    viewer.layers.clear()


class MockEvent:
    def __init__(self, value):
        self.value = value


def test_ortho_views(viewer, qtbot, solution_tracks_3d_with_division):
    """Test if the tracks layers are correctly displayed on the orthoviews"""

    # Initalize orthogonal views
    m = initialize_ortho_views(viewer)

    # Create example tracks
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=solution_tracks_3d_with_division, name="test")

    assert isinstance(viewer.layers[-1], TrackLabels)
    assert isinstance(viewer.layers[-2], TrackPoints)

    # change attributes on the TrackLabels layer to check that they are correctly copied
    viewer.layers[-1].contour = 1
    viewer.layers[-1].mode = "erase"

    # show orthogonal views and check attributes
    m.show()
    qtbot.waitUntil(lambda: m.is_shown(), timeout=1000)
    assert isinstance(m.right_widget, OrthoViewWidget)
    assert isinstance(m.right_widget.vm_container.viewer_model.layers[-1], Labels)
    assert isinstance(m.bottom_widget.vm_container.viewer_model.layers[-1], Labels)
    assert isinstance(m.right_widget.vm_container.viewer_model.layers[-2], Points)
    assert isinstance(m.bottom_widget.vm_container.viewer_model.layers[-2], Points)
    assert (
        m.right_widget.vm_container.viewer_model.layers[-1].contour
        == viewer.layers[-1].contour
    )
    assert (
        m.right_widget.vm_container.viewer_model.layers[-1].mode
        == viewer.layers[-1].mode
    )

    # set to paint mode and test syncing
    viewer.layers[-1].mode = "paint"
    assert (
        viewer.layers[-1].mode
        == m.right_widget.vm_container.viewer_model.layers[-1].mode
        == m.bottom_widget.vm_container.viewer_model.layers[-1].mode
    )

    # Test paint event on main viewer (indices, orig value, target_value)
    event_val = [
        (
            (np.array([1]), np.array([15]), np.array([45]), np.array([75])),
            np.array([2], dtype=np.uint16),
            np.uint16(5),
        )
    ]
    event = MockEvent(event_val)
    step = list(viewer.dims.current_step)
    step[0] = 1
    viewer.dims.current_step = step
    viewer.layers[-1]._on_paint(event)

    assert int(np.asarray(viewer.layers[-1].data[1, 15, 45, 75])) == 5
    assert np.array_equal(
        np.asarray(viewer.layers[-1].data),
        np.asarray(m.right_widget.vm_container.viewer_model.layers[-1].data),
    )

    # test paint event on one of the ortho views and see if a new node is added
    assert tracks_viewer.tracks.graph.num_nodes() == 5
    step = list(viewer.dims.current_step)
    step[0] = 2
    viewer.dims.current_step = step
    m.right_widget.vm_container.viewer_model.layers[-1].paint(
        coord=(2, 63, 20, 30), new_label=6, refresh=True
    )
    assert tracks_viewer.tracks.graph.num_nodes() == 6

    # test syncing of properties
    viewer.layers[-1].selected_label = 7  # forward sync only
    assert (
        viewer.layers[-1].selected_label
        == m.right_widget.vm_container.viewer_model.layers[-1].selected_label
        == m.bottom_widget.vm_container.viewer_model.layers[-1].selected_label
    )

    m.cleanup()


def test_point_size_stable_when_editing_in_ortho_views(
    viewer, qtbot, solution_tracks_3d_without_segmentation, monkeypatch
):
    """Adding or selecting points in an orthogonal view must not change the point size.

    Selected points are drawn 30% larger, and napari copies the size of a selected point
    into current_size, which TrackPoints reads as a size slider change. Every add or
    selection made in an orthogonal view therefore used to grow the points by another
    30% (5 -> 7 -> 10 -> 13 -> ...).
    """

    monkeypatch.setattr(
        "motile_tracker.data_views.views.layers.track_points.confirm_force_operation",
        lambda message: (True, False),
    )

    m = initialize_ortho_views(viewer)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(
        tracks=solution_tracks_3d_without_segmentation, name="test"
    )
    m.show()
    qtbot.waitUntil(lambda: m.is_shown(), timeout=1000)

    points_layer = tracks_viewer.tracking_layers.points_layer
    right = m.right_widget.vm_container.viewer_model.layers[points_layer.name]
    bottom = m.bottom_widget.vm_container.viewer_model.layers[points_layer.name]
    default_size = points_layer.default_size

    # adding points in an orthogonal view
    for i in range(4):
        right.add(np.array([0, 20, 55 + i, 65 + i], dtype=float))
        assert points_layer.default_size == default_size

    # selecting points, in an orthogonal view and in the main viewer
    for index in range(3):
        bottom.selected_data = {index}
    assert points_layer.default_size == default_size
    for node in tracks_viewer.tracks.graph.node_ids()[:3]:
        tracks_viewer.selected_nodes.add(node, False)
    assert points_layer.default_size == default_size

    # a real size change still works, and reaches the orthogonal views
    points_layer.current_size = default_size + 3
    assert points_layer.default_size == default_size + 3
    for copied_layer in (right, bottom):
        assert np.array_equal(copied_layer.size, points_layer.size)

    m.cleanup()
