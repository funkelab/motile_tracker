"""Tests for update_napari_tracks with the graph returned by solve()."""

from funtracks.data_model import SolutionTracks

from motile_tracker.data_views.views.layers.track_graph import update_napari_tracks
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
