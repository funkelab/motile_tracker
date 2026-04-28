"""Tests for update_napari_tracks with the graph returned by solve()."""

import numpy as np
from funtracks.data_model import SolutionTracks

from motile_tracker.data_views.views.layers.track_graph import update_napari_tracks
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer
from motile_tracker.motile.backend import SolverParams, solve


def test_update_napari_tracks_with_solve_output(segmentation_2d):
    """update_napari_tracks must work with the graph returned by solve().

    solve() returns a GraphView whose _root is a SQLGraph. Previously,
    update_napari_tracks called graph.detach() which triggered
    SQLGraph.metadata() and crashed with OperationalError if the Metadata
    table was missing (databases from older tracksdata versions).
    """
    params = SolverParams()
    params.appear_cost = None
    soln_graph = solve(params, segmentation_2d)

    tracks = SolutionTracks(graph=soln_graph, ndim=3, time_attr="t")
    data, edges = update_napari_tracks(tracks)

    assert data.shape[0] == soln_graph.num_nodes()
    assert data.shape[1] == 4  # track_id, t, y, x
    assert isinstance(edges, dict)


def test_scale_propagated_to_tracks_layer(viewer, graph_3d):
    """TrackGraph must forward tracks.scale to the napari Tracks constructor.

    With anisotropic scale (z-step != xy-step), pixel and world coordinates
    differ. Without the fix, Tracks silently defaults to scale=[1,1,1,1] and
    appears misaligned with the Labels layer in the viewer.
    """
    scale = [1.0, 2.0, 1.0, 1.0]  # anisotropic z
    tracks = SolutionTracks(graph=graph_3d, scale=scale, ndim=4, time_attr="t")
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    tracks_layer = tracks_viewer.tracking_layers.tracks_layer
    assert np.allclose(tracks_layer.scale, scale)
