from __future__ import annotations

import logging
import time
from collections.abc import Callable

import networkx as nx
import numpy as np
from motile import Solver, TrackGraph
from motile.constraints import MaxChildren, MaxParents, Pin
from motile.costs import Appear, EdgeDistance, EdgeSelection, Split
from motile_toolbox.candidate_graph import (
    EdgeAttr,
    NodeAttr,
    compute_graph_from_points_list,
    compute_graph_from_seg,
    graph_to_nx,
)

from .solver_params import SolverParams

logger = logging.getLogger(__name__)

PIN_ATTR = "pinned"


def solve(
    solver_params: SolverParams,
    input_data: np.ndarray,
    on_solver_update: Callable | None = None,
    scale: list | None = None,
) -> nx.DiGraph:
    """Get a tracking solution for the given segmentation and parameters.

    Constructs a candidate graph from the segmentation, a solver from
    the parameters, and then runs solving and returns a networkx graph
    with the solution. Most of this functionality is implemented in the
    motile toolbox.

    Args:
        solver_params (SolverParams): The solver parameters to use when
            initializing the solver
        input_data (np.ndarray): The input segmentation or points list to run
            tracking on. If 2D, assumed to be a list of points, otherwise a
            segmentation.
        on_solver_update (Callable, optional): A function that is called
            whenever the motile solver emits an event. The function should take
            a dictionary of event data, and can be used to track progress of
            the solver. Defaults to None.
        scale (list, optional): The scale of the data in each dimension.

    Returns:
        nx.DiGraph: A solution graph where the ids of the nodes correspond to
            the time and ids of the passed in segmentation labels. See the
            motile_toolbox for exact implementation details.
    """
    if input_data.ndim == 2:
        cand_graph = compute_graph_from_points_list(
            input_data, solver_params.max_edge_distance, scale=scale
        )
    else:
        cand_graph = compute_graph_from_seg(
            input_data,
            solver_params.max_edge_distance,
            iou=solver_params.iou_cost is not None,
            scale=scale,
        )
    logger.debug("Cand graph has %d nodes", cand_graph.number_of_nodes())

    # Check if single window mode or chunked solving is enabled
    if solver_params.window_size is not None:
        if solver_params.single_window_start is not None:
            return _solve_single_window(cand_graph, solver_params, on_solver_update)
        return _solve_chunked(cand_graph, solver_params, on_solver_update)

    return _solve_full(cand_graph, solver_params, on_solver_update)


def _solve_full(
    cand_graph: nx.DiGraph,
    solver_params: SolverParams,
    on_solver_update: Callable | None = None,
) -> nx.DiGraph:
    """Solve the tracking problem on the full candidate graph at once."""
    solver = construct_solver(cand_graph, solver_params)
    start_time = time.time()
    solution = solver.solve(verbose=False, on_event=on_solver_update)
    logger.info("Solution took %.2f seconds", time.time() - start_time)

    solution_graph = solver.get_selected_subgraph(solution=solution)
    solution_nx_graph = graph_to_nx(solution_graph)
    logger.debug("Solution graph has %d nodes", solution_nx_graph.number_of_nodes())
    return solution_nx_graph


def _solve_window(
    window_subgraph: nx.DiGraph,
    solver_params: SolverParams,
    on_solver_update: Callable | None = None,
) -> nx.DiGraph | None:
    """Solve a single window subgraph.

    This is the core solving logic shared by both single window mode and
    chunked solving.

    Args:
        window_subgraph: The subgraph for this window. If any nodes or edges
            have the PIN_ATTR attribute set, a Pin constraint will be used.
        solver_params: The solver parameters.
        on_solver_update: Callback for solver progress updates.

    Returns:
        The solution graph for this window, or None if the window has no nodes.
    """
    if window_subgraph.number_of_nodes() == 0:
        return None

    # Handle edge case: if no edges, we can't solve (motile requires edges)
    # Just return all nodes directly
    if window_subgraph.number_of_edges() == 0:
        logger.info(
            "Window has no edges (%d nodes), returning nodes directly",
            window_subgraph.number_of_nodes(),
        )
        return window_subgraph.copy()

    # Construct and solve
    solver = construct_solver(window_subgraph, solver_params)
    solution = solver.solve(verbose=False, on_event=on_solver_update)
    solution_graph = solver.get_selected_subgraph(solution=solution)
    return graph_to_nx(solution_graph)


def _solve_single_window(
    cand_graph: nx.DiGraph,
    solver_params: SolverParams,
    on_solver_update: Callable | None = None,
) -> nx.DiGraph:
    """Solve just a single window for interactive parameter testing.

    This is useful for quickly testing solver parameters on a small portion
    of the data before running on the full dataset.

    Args:
        cand_graph: The full candidate graph with all nodes and edges.
        solver_params: The solver parameters including window_size and single_window_start.
        on_solver_update: Callback for solver progress updates.

    Returns:
        The solution graph for just the single window.
    """
    window_size = solver_params.window_size
    window_start = solver_params.single_window_start

    # Get the frame range from the candidate graph
    times = [cand_graph.nodes[n][NodeAttr.TIME.value] for n in cand_graph.nodes]
    if not times:
        return nx.DiGraph()

    min_time = min(times)
    max_time = max(times)

    # Validate window_start
    if window_start < min_time:
        logger.warning(
            "single_window_start (%d) is before first frame (%d), using first frame",
            window_start,
            min_time,
        )
        window_start = min_time

    window_end = min(window_start + window_size, max_time + 1)

    logger.info(
        "Solving single window: frames %d to %d (exclusive)",
        window_start,
        window_end,
    )

    # Extract and solve
    window_subgraph = _extract_window_subgraph(cand_graph, window_start, window_end)
    start_time = time.time()
    solution = _solve_window(window_subgraph, solver_params, on_solver_update)
    logger.info("Single window solution took %.2f seconds", time.time() - start_time)

    if solution is None:
        logger.warning("Window has no nodes")
        return nx.DiGraph()

    logger.debug(
        "Single window solution has %d nodes, %d edges",
        solution.number_of_nodes(),
        solution.number_of_edges(),
    )
    return solution


def _solve_chunked(
    cand_graph: nx.DiGraph,
    solver_params: SolverParams,
    on_solver_update: Callable | None = None,
) -> nx.DiGraph:
    """Solve the tracking problem in chunks using a sliding window approach.

    This function solves the tracking problem in windows of `window_size` frames,
    with `overlap_size` frames of overlap between consecutive windows. The overlap
    region from the previous window is pinned (fixed) when solving the next window
    to maintain consistency across windows.

    Args:
        cand_graph: The full candidate graph with all nodes and edges.
        solver_params: The solver parameters including window_size and overlap_size.
        on_solver_update: Callback for solver progress updates.

    Returns:
        The combined solution graph from all windows.
    """
    window_size = solver_params.window_size
    overlap_size = solver_params.overlap_size or 0

    if overlap_size >= window_size:
        raise ValueError(
            f"overlap_size ({overlap_size}) must be less than window_size ({window_size})"
        )

    # Get the frame range from the candidate graph
    times = [cand_graph.nodes[n][NodeAttr.TIME.value] for n in cand_graph.nodes]
    if not times:
        return nx.DiGraph()

    min_time = min(times)
    max_time = max(times)
    total_frames = max_time - min_time + 1

    logger.info(
        "Starting chunked solve: %d frames, window_size=%d, overlap_size=%d",
        total_frames,
        window_size,
        overlap_size,
    )

    # Initialize the combined solution graph
    combined_solution = nx.DiGraph()

    window_start = min_time
    window_num = 0
    start_time = time.time()

    while window_start <= max_time:
        window_end = min(window_start + window_size, max_time + 1)
        window_num += 1

        logger.info(
            "Solving window %d: frames %d to %d (exclusive)",
            window_num,
            window_start,
            window_end,
        )

        # Extract subgraph for this window (includes PIN_ATTR if set on cand_graph)
        window_subgraph = _extract_window_subgraph(cand_graph, window_start, window_end)

        # Solve this window
        window_solution_nx = _solve_window(
            window_subgraph,
            solver_params,
            on_solver_update,
        )

        if window_solution_nx is None:
            logger.warning("Window %d has no nodes, skipping", window_num)
            window_start += window_size - overlap_size
            continue

        logger.debug(
            "Window %d solution has %d nodes, %d edges",
            window_num,
            window_solution_nx.number_of_nodes(),
            window_solution_nx.number_of_edges(),
        )

        # Determine which part of this window to add to the combined solution
        # We only add nodes/edges that are not in the overlap region of the previous window
        overlap_start = window_start + window_size - overlap_size
        if window_num == 1:
            # First window: add everything
            _add_to_combined_solution(combined_solution, window_solution_nx)
        else:
            # Subsequent windows: only add nodes/edges after the pinned region
            # The pinned region spans frames [window_start, window_start + overlap_size)
            pin_end = window_start + overlap_size
            _add_to_combined_solution(
                combined_solution, window_solution_nx, from_frame=pin_end
            )

        # Set PIN_ATTR on candidate graph for the overlap region (for next window)
        if window_end <= max_time:
            _set_pinning_on_graph(
                cand_graph, window_solution_nx, overlap_start, window_end
            )

        # Move window
        window_start += window_size - overlap_size

    logger.info(
        "Chunked solve complete: %d windows, %.2f seconds total",
        window_num,
        time.time() - start_time,
    )
    logger.debug(
        "Combined solution has %d nodes, %d edges",
        combined_solution.number_of_nodes(),
        combined_solution.number_of_edges(),
    )

    return combined_solution


def _extract_window_subgraph(
    cand_graph: nx.DiGraph, start_frame: int, end_frame: int
) -> nx.DiGraph:
    """Extract a subgraph containing only nodes in the given frame range.

    Args:
        cand_graph: The full candidate graph.
        start_frame: The start frame (inclusive).
        end_frame: The end frame (exclusive).

    Returns:
        A new DiGraph containing nodes in [start_frame, end_frame) and
        edges between them.
    """
    # Get nodes in the frame range
    nodes_in_window = [
        n
        for n in cand_graph.nodes
        if start_frame <= cand_graph.nodes[n][NodeAttr.TIME.value] < end_frame
    ]

    # Create subgraph with these nodes
    subgraph = cand_graph.subgraph(nodes_in_window).copy()
    return subgraph


def _set_pinning_on_graph(
    cand_graph: nx.DiGraph,
    solution_graph: nx.DiGraph,
    overlap_start: int,
    overlap_end: int,
) -> None:
    """Set PIN_ATTR on candidate graph nodes/edges in the overlap region.

    For all nodes and edges in the overlap region [overlap_start, overlap_end),
    sets PIN_ATTR to True if selected in the solution, False if not selected.

    Args:
        cand_graph: The full candidate graph to modify in place.
        solution_graph: The solution graph from the current window.
        overlap_start: Start frame of overlap region (inclusive).
        overlap_end: End frame of overlap region (exclusive).
    """
    solution_nodes = set(solution_graph.nodes)
    solution_edges = set(solution_graph.edges)

    # Pin nodes in the overlap region
    for node in cand_graph.nodes:
        node_time = cand_graph.nodes[node][NodeAttr.TIME.value]
        if overlap_start <= node_time < overlap_end:
            cand_graph.nodes[node][PIN_ATTR] = node in solution_nodes

    # Pin edges where both endpoints are in the overlap region
    for u, v in cand_graph.edges:
        u_time = cand_graph.nodes[u][NodeAttr.TIME.value]
        v_time = cand_graph.nodes[v][NodeAttr.TIME.value]
        if (
            overlap_start <= u_time < overlap_end
            and overlap_start <= v_time < overlap_end
        ):
            cand_graph.edges[u, v][PIN_ATTR] = (u, v) in solution_edges


def _add_to_combined_solution(
    combined: nx.DiGraph,
    window_solution: nx.DiGraph,
    from_frame: int | None = None,
) -> None:
    """Add nodes and edges from window solution to the combined solution.

    Args:
        combined: The combined solution graph to add to.
        window_solution: The window solution to add from.
        from_frame: If specified, only add nodes at or after this frame.
    """
    for node, data in window_solution.nodes(data=True):
        if from_frame is not None:
            node_time = data.get(NodeAttr.TIME.value)
            if node_time is not None and node_time < from_frame:
                continue
        if node not in combined:
            combined.add_node(node, **data)

    for u, v, data in window_solution.edges(data=True):
        # Add edge if both nodes are in the combined graph
        if u in combined and v in combined and not combined.has_edge(u, v):
            combined.add_edge(u, v, **data)


def construct_solver(cand_graph: nx.DiGraph, solver_params: SolverParams) -> Solver:
    """Construct a motile solver with the parameters specified in the solver
    params object.

    Args:
        cand_graph (nx.DiGraph): The candidate graph to use in the solver
        solver_params (SolverParams): The costs and constraints to use in
            the solver

    Returns:
        Solver: A motile solver with the specified graph, costs, and
            constraints.
    """
    solver = Solver(TrackGraph(cand_graph, frame_attribute=NodeAttr.TIME.value))
    solver.add_constraint(MaxChildren(solver_params.max_children))
    solver.add_constraint(MaxParents(1))
    solver.add_constraint(Pin(PIN_ATTR))

    # Using EdgeDistance instead of EdgeSelection for the constant cost because
    # the attribute is not optional for EdgeSelection (yet)
    if solver_params.edge_selection_cost is not None:
        solver.add_cost(
            EdgeDistance(
                weight=0,
                position_attribute=NodeAttr.POS.value,
                constant=solver_params.edge_selection_cost,
            ),
            name="edge_const",
        )
    if solver_params.appear_cost is not None:
        solver.add_cost(Appear(solver_params.appear_cost))
    if solver_params.division_cost is not None:
        solver.add_cost(Split(constant=solver_params.division_cost))

    if solver_params.distance_cost is not None:
        solver.add_cost(
            EdgeDistance(
                position_attribute=NodeAttr.POS.value,
                weight=solver_params.distance_cost,
            ),
            name="distance",
        )
    if solver_params.iou_cost is not None:
        solver.add_cost(
            EdgeSelection(
                weight=solver_params.iou_cost,
                attribute=EdgeAttr.IOU.value,
            ),
            name="iou",
        )
    return solver
