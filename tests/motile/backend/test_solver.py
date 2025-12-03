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


def test_solve_chunked_no_overlap(segmentation_3d, graph_3d):
    """Test chunked solving with no overlap."""
    params = SolverParams()
    params.appear_cost = None
    # full_solution = solve(params, segmentation_3d)

    params_chunked = SolverParams()
    params_chunked.appear_cost = None
    params_chunked.window_size = 3
    params_chunked.overlap_size = 0
    chunked_solution = solve(params_chunked, segmentation_3d)

    # Without overlap, the solutions may differ because there's no continuity
    # constraint between windows. We just check that it runs without error
    # and produces a valid graph.
    assert chunked_solution.number_of_nodes() > 0


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
    from motile_toolbox.candidate_graph import NodeAttr

    for node in solution.nodes:
        node_time = solution.nodes[node].get(NodeAttr.TIME.value)
        assert 1 <= node_time < 4, f"Node {node} has time {node_time}, expected 1-3"
