import pytest

from motile_tracker.motile.backend import SolverParams, solve


# capsys is a pytest fixture that captures stdout and stderr output streams
def test_solve_2d(segmentation_2d, graph_2d):
    graph_2d.remove_nodes_from([4, 5, 6])
    params = SolverParams()
    params.appear_cost = None
    soln_graph = solve(params, segmentation_2d)
    assert set(soln_graph.nodes) == set(graph_2d.nodes)


def test_solve_3d(segmentation_3d, graph_3d):
    params = SolverParams()
    params.appear_cost = None
    soln_graph = solve(params, segmentation_3d)
    assert set(soln_graph.nodes) == set(graph_3d.nodes)


def test_solve_chunked(segmentation_3d, graph_3d):
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
    assert set(full_solution.nodes) == set(chunked_solution.nodes)
    assert set(full_solution.edges) == set(chunked_solution.edges)


def test_solve_chunked_overlap_required():
    """Test that overlap_size must be at least 1."""
    params = SolverParams()
    params.window_size = 3

    with pytest.raises(ValueError, match="overlap_size must be at least 1"):
        params.overlap_size = 0


def test_solve_single_window(segmentation_3d):
    """Test solving just a single window for interactive testing."""
    params = SolverParams()
    params.appear_cost = None
    params.window_size = 3
    params.single_window_start = 1  # Start at frame 1

    solution = solve(params, segmentation_3d)

    # Should only have nodes from frames 1, 2, 3
    assert solution.number_of_nodes() > 0
    # Verify all nodes are within the window
    from funtracks.data_model.graph_attributes import NodeAttr

    for node in solution.nodes:
        node_time = solution.nodes[node].get(NodeAttr.TIME.value)
        assert 1 <= node_time < 4, f"Node {node} has time {node_time}, expected 1-3"


def test_solve_single_window_invalid_start(segmentation_3d):
    """Test that invalid window_start raises ValueError."""
    params = SolverParams()
    params.appear_cost = None
    params.window_size = 3
    params.single_window_start = 100  # Beyond data range (5 frames)

    with pytest.raises(ValueError, match="beyond last frame"):
        solve(params, segmentation_3d)
