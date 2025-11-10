from __future__ import annotations

from typing import Any

import napari.layers
import networkx as nx
import numpy as np
import pandas as pd
from funtracks.data_model import NodeType, Tracks

from motile_tracker.data_views.graph_attributes import NodeAttr


def extract_sorted_tracks(
    tracks: Tracks,
    colormap: napari.utils.CyclicLabelColormap,
    prev_axis_order: list[int] | None = None,
) -> pd.DataFrame | None:
    """
    Extract the information of individual tracks required for constructing the pyqtgraph
    plot. Follows the same logic as the relabel_segmentation function from the Motile
    toolbox.

    Args:
        tracks (funtracks.data_model.Tracks): A tracks object containing a graph
            to be converted into a dataframe.
        colormap (napari.utils.CyclicLabelColormap): The colormap to use to
            extract the color of each node from the track ID
        prev_axis_order (list[int], Optional). The previous axis order.

    Returns:
        pd.DataFrame | None: data frame with all the information needed to
        construct the pyqtgraph plot. Columns are: 't', 'node_id', 'track_id',
        'color', 'x', 'y', ('z'), 'index', 'parent_id', 'parent_track_id',
        'state', 'symbol', and 'x_axis_pos'
    """

    if tracks is None or tracks.graph is None:
        return None

    solution_nx_graph = tracks.graph

    track_list = []
    parent_mapping = []

    # Identify parent nodes (nodes with more than one child)
    parent_nodes = [n for (n, d) in solution_nx_graph.out_degree() if d > 1]
    end_nodes = [n for (n, d) in solution_nx_graph.out_degree() if d == 0]

    # Make a copy of the graph and remove outgoing edges from parent nodes to isolate
    # tracks
    soln_copy = solution_nx_graph.copy()
    for parent_node in parent_nodes:
        out_edges = solution_nx_graph.out_edges(parent_node)
        soln_copy.remove_edges_from(out_edges)

    # Process each weakly connected component as a separate track
    for node_set in nx.weakly_connected_components(soln_copy):
        # Sort nodes in each weakly connected component by their time attribute to
        # ensure correct order
        sorted_nodes = sorted(
            node_set,
            key=lambda node: tracks.get_time(node),
        )
        positions = tracks.get_positions(sorted_nodes).tolist()

        # track_id and color are the same for all nodes in a node_set
        parent_track_id = None
        track_id = tracks.get_track_id(sorted_nodes[0])
        color = np.concatenate((colormap.map(track_id)[:3] * 255, [255]))

        for node, pos in zip(sorted_nodes, positions, strict=False):
            if node in parent_nodes:
                state = NodeType.SPLIT
                symbol = "t1"
            elif node in end_nodes:
                state = NodeType.END
                symbol = "x"
            else:
                state = NodeType.CONTINUE
                symbol = "o"

            track_dict = {
                "t": tracks.get_time(node),
                "node_id": node,
                "track_id": track_id,
                "color": color,
                "x": pos[-1],
                "y": pos[-2],
                "parent_id": 0,
                "parent_track_id": 0,
                "state": state,
                "symbol": symbol,
            }

            if tracks.get_area(node) is not None:
                track_dict["area"] = tracks.get_area(node)

            if len(pos) == 3:
                track_dict["z"] = pos[0]

            # Determine parent_id and parent_track_id
            predecessors = list(solution_nx_graph.predecessors(node))
            if predecessors:
                parent_id = predecessors[
                    0
                ]  # There should be only one predecessor in a lineage tree
                track_dict["parent_id"] = parent_id

                if parent_track_id is None:
                    parent_track_id = solution_nx_graph.nodes[parent_id][
                        NodeAttr.TRACK_ID.value
                    ]
                track_dict["parent_track_id"] = parent_track_id

            else:
                parent_track_id = 0
                track_dict["parent_id"] = 0
                track_dict["parent_track_id"] = parent_track_id

            track_list.append(track_dict)

        parent_mapping.append(
            {"track_id": track_id, "parent_track_id": parent_track_id, "node_id": node}
        )

    x_axis_order = get_sorted_track_ids(solution_nx_graph, "track_id", prev_axis_order)

    for node in track_list:
        node["x_axis_pos"] = x_axis_order.index(node["track_id"])

    df = pd.DataFrame(track_list)
    if "area" in df.columns:
        df["area"] = df["area"].fillna(0)

    return df, x_axis_order


def find_root(track_id: int, parent_map: dict) -> int:
    """Function to find the root associated with a track by tracing its lineage"""

    # Keep traversing a track is found where parent_track_id == 0 (i.e., it's a root)
    current_track = track_id
    while parent_map.get(current_track) != 0:
        current_track = parent_map.get(current_track)
    return current_track


def order_roots_by_prev(prev_axis_order: list[int], roots: list[int]) -> list[int]:
    """Order a list of root nodes by the previous order, insert missing orders immediately
    to the right of the closest smaller numerical element.

    Args:
        prev_axis_order (list[int]): the previous order of root nodes.
        roots (list[int]): the to be sorted list of root nodes.

    Returns:
        list[int]: sorted list of root nodes.
    """

    roots_in_prev = [r for r in prev_axis_order if r in roots]
    missing = sorted(set(roots) - set(roots_in_prev))

    for r in missing:
        # find the index of the rightmost smaller element in roots_in_prev
        smaller = [x for x in roots_in_prev if x < r]
        idx = roots_in_prev.index(max(smaller)) + 1 if smaller else 0
        roots_in_prev.insert(idx, r)

    return roots_in_prev


def get_sorted_track_ids(
    graph: nx.DiGraph,
    tracklet_id_key: str = "tracklet_id",
    prev_axis_order: list[int] | None = None,
) -> list[Any]:
    """
    Extract the lineage tree plot order of the tracklet_ids on the graph, ensuring that
    each tracklet_id is placed in between its daughter tracklet_ids and adjacent to its
    parent track id.

    Args:
        graph (nx.DiGraph): graph with a tracklet_id attribute on it.
        tracklet_id_key (str): tracklet_id key on the graph.

    Returns:
        list[Any] of ordered tracklet_ids.
    """

    # Create tracklet_id to parent_tracklet_id mapping (0 if tracklet has no parent)
    tracklet_to_parent_tracklet = {}
    for node in nx.topological_sort(graph):
        data = graph.nodes[node]
        tracklet = data[tracklet_id_key]
        if tracklet in tracklet_to_parent_tracklet:
            continue
        predecessor = next(graph.predecessors(node), None)
        if predecessor is not None:
            parent_tracklet_id = graph.nodes[predecessor][tracklet_id_key]
        else:
            parent_tracklet_id = 0
        tracklet_to_parent_tracklet[tracklet] = parent_tracklet_id

    # Final sorted order of roots
    roots = sorted(
        [tid for tid, ptid in tracklet_to_parent_tracklet.items() if ptid == 0]
    )

    # Optionally sort roots according to their position in prev_axis_order
    if prev_axis_order is not None:
        roots = order_roots_by_prev(prev_axis_order, roots)

    x_axis_order = list(roots)

    # Find the children of each of the starting points, and work down the tree.
    while len(roots) > 0:
        children_list = []
        for tracklet_id in roots:
            children = [
                tid
                for tid, ptid in tracklet_to_parent_tracklet.items()
                if ptid == tracklet_id
            ]
            for i, child in enumerate(children):
                [children_list.append(child)]
                x_axis_order.insert(x_axis_order.index(tracklet_id) + i, child)
        roots = children_list

    return x_axis_order


def extract_lineage_tree(graph: nx.DiGraph, node_id: str) -> list[str]:
    """Extract the entire lineage tree including horizontal relations for a given node"""

    # go up the tree to identify the root node
    root_node = node_id
    while True:
        predecessors = list(graph.predecessors(root_node))
        if not predecessors:
            break
        root_node = predecessors[0]

    # extract all descendants to get the full tree
    nodes = nx.descendants(graph, root_node)

    # include root
    nodes.add(root_node)

    return list(nodes)
