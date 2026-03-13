import numpy as np
import pytest
from funtracks.data_model import SolutionTracks, Tracks
from funtracks.utils.tracksdata_utils import assert_node_attrs_equal_with_masks

from motile_tracker.motile.backend import SolverParams, solve


@pytest.fixture
def segmentation_2d(graph_2d):
    return np.asarray(Tracks(graph_2d, ndim=3, time_attr="t").segmentation)


@pytest.fixture
def segmentation_3d(graph_3d):
    return np.asarray(Tracks(graph_3d, ndim=4, time_attr="t").segmentation)


# capsys is a pytest fixture that captures stdout and stderr output streams
def test_solve_2d(graph_2d, segmentation_2d):
    params = SolverParams()
    params.appear_cost = None
    soln_graph = solve(params, segmentation_2d)

    # remove nodes that don't make the solution
    # node 4 is too far from node 3
    # node 5 is two frames from node 4
    # node 6 is isolated and has no edges
    for node in [4, 5, 6]:
        graph_2d.remove_node(node)
    assert set(soln_graph.node_ids()) == set(graph_2d.node_ids())


def test_solve_3d(graph_3d, segmentation_3d):
    params = SolverParams()
    params.appear_cost = None
    soln_graph = solve(params, segmentation_3d)
    assert set(soln_graph.node_ids()) == set(graph_3d.node_ids())


def test_solve_chunked(segmentation_3d):
    """Test that chunked solving produces same results as full solve."""
    # First solve without chunking
    params = SolverParams()
    params.appear_cost = None
    full_solution = solve(params, segmentation_3d)

    # Then solve with chunking
    params_chunked = SolverParams()
    params_chunked.appear_cost = None
    params_chunked.window_size = 3
    params_chunked.overlap_size = 1
    chunked_solution = solve(params_chunked, segmentation_3d)

    # Solutions should have the same nodes and edges
    assert set(full_solution.node_ids()) == set(chunked_solution.node_ids())
    assert_node_attrs_equal_with_masks(
        full_solution, chunked_solution, check_row_order=False
    )
    assert {tuple(e) for e in full_solution.edge_list()} == {
        tuple(e) for e in chunked_solution.edge_list()
    }


def test_solve_chunked_overlap_required():
    """Test that overlap_size must be at least 1."""
    params = SolverParams()
    params.window_size = 3

    with pytest.raises(ValueError, match="overlap_size must be at least 1"):
        params.overlap_size = 0


def test_solve_single_window(graph_3d):
    """Test solving just a single window for interactive testing."""
    params = SolverParams()
    params.appear_cost = None
    params.window_size = 3
    params.single_window_start = 1  # Start at frame 1

    segmentation_3d = np.asarray(
        SolutionTracks(graph_3d, ndim=4, time_attr="t").segmentation
    )

    solution = solve(params, segmentation_3d)

    # Should only have nodes from frames 1, 2, 3
    assert solution.num_nodes() > 0
    # Verify all nodes are within the window
    for node in solution.node_ids():
        node_time = solution.nodes[node]["t"]
        assert 1 <= node_time < 4, f"Node {node} has time {node_time}, expected 1-3"


def test_solve_single_window_invalid_start(graph_3d):
    """Test that invalid window_start raises ValueError."""

    segmentation_3d = np.asarray(
        SolutionTracks(graph_3d, ndim=4, time_attr="t").segmentation
    )

    params = SolverParams()
    params.appear_cost = None
    params.window_size = 3
    params.single_window_start = 100  # Beyond data range (5 frames)

    with pytest.raises(ValueError, match="beyond last frame"):
        solve(params, segmentation_3d)
