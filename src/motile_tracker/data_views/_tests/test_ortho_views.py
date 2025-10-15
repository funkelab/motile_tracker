import numpy as np
from funtracks.data_model import SolutionTracks
from napari.layers import Labels, Points
from napari_orthogonal_views.ortho_view_widget import OrthoViewWidget

from motile_tracker.data_views.views.layers.track_labels import TrackLabels
from motile_tracker.data_views.views.layers.track_points import TrackPoints
from motile_tracker.data_views.views.ortho_views import (
    initialize_ortho_views,
)
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


class MockEvent:
    def __init__(self, value):
        self.value = value


def test_ortho_views(make_napari_viewer, qtbot, graph_3d, segmentation_3d):
    """Test if the tracks layers are correctly displayed on the orthoviews"""

    # Initalize orthogonal views
    viewer = make_napari_viewer()
    m = initialize_ortho_views(viewer)

    # Create example tracks
    tracks = SolutionTracks(graph=graph_3d, segmentation=segmentation_3d, ndim=4)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    assert isinstance(viewer.layers[-1], TrackPoints)
    assert isinstance(viewer.layers[-2], TrackLabels)

    # change attributes on the TrackLabels layer to check that they are correctly copied
    viewer.layers[-2].contour = 1
    viewer.layers[-2].mode = "erase"

    # show orthogonal views and check attributes
    m.show()
    qtbot.waitUntil(lambda: m.is_shown(), timeout=1000)
    assert isinstance(m.right_widget, OrthoViewWidget)
    assert isinstance(m.right_widget.vm_container.viewer_model.layers[-1], Points)
    assert isinstance(m.bottom_widget.vm_container.viewer_model.layers[-1], Points)
    assert isinstance(m.right_widget.vm_container.viewer_model.layers[-2], Labels)
    assert isinstance(m.bottom_widget.vm_container.viewer_model.layers[-2], Labels)
    assert (
        m.right_widget.vm_container.viewer_model.layers[-2].contour
        == viewer.layers[-2].contour
    )
    assert (
        m.right_widget.vm_container.viewer_model.layers[-2].mode
        == viewer.layers[-2].mode
    )

    # set to paint mode and test syncing
    viewer.layers[-2].mode = "paint"
    assert (
        viewer.layers[-2].mode
        == m.right_widget.vm_container.viewer_model.layers[-2].mode
        == m.bottom_widget.vm_container.viewer_model.layers[-2].mode
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
    viewer.layers[-2]._on_paint(event)

    assert viewer.layers[-2].data[1, 15, 45, 75] == 5
    assert np.array_equal(
        viewer.layers[-2].data, m.right_widget.vm_container.viewer_model.layers[-2].data
    )

    # test paint event on one of the ortho views and see if a new node is added
    assert len(tracks_viewer.tracks.graph.nodes) == 5
    step = list(viewer.dims.current_step)
    step[0] = 2
    viewer.dims.current_step = step
    m.right_widget.vm_container.viewer_model.layers[-2].paint(
        coord=(2, 63, 20, 30), new_label=6, refresh=True
    )
    assert len(tracks_viewer.tracks.graph.nodes) == 6

    # test syncing of properties
    viewer.layers[-2].selected_label = 7  # forward sync only
    assert (
        viewer.layers[-2].selected_label
        == m.right_widget.vm_container.viewer_model.layers[-2].selected_label
        == m.bottom_widget.vm_container.viewer_model.layers[-2].selected_label
    )

    m.cleanup()
