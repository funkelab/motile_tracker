from __future__ import annotations

from typing import Any

import napari.layers
import numpy as np
import pandas as pd
from funtracks.data_model import Tracks

from motile_tracker.data_views.node_type import NodeType


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
    parent_nodes = [
        n for n in solution_nx_graph.node_ids() if solution_nx_graph.out_degree(n) > 1
    ]
    end_nodes = [
        n for n in solution_nx_graph.node_ids() if solution_nx_graph.out_degree(n) == 0
    ]

    # BFS to collect tracklets, cutting edges at division (parent) nodes
    parent_node_set = set(parent_nodes)
    visited: set = set()
    tracklets: list[set] = []
    for start_node in solution_nx_graph.node_ids():
        if start_node in visited:
            continue
        component: set = set()
        queue = [start_node]
        while queue:
            node = queue.pop()
            if node in visited:
                continue
            visited.add(node)
            component.add(node)
            for pred in solution_nx_graph.predecessors(node):
                if pred not in visited and pred not in parent_node_set:
                    queue.append(pred)
            if node not in parent_node_set:
                for succ in solution_nx_graph.successors(node):
                    if succ not in visited:
                        queue.append(succ)
        tracklets.append(component)

    for node_set in tracklets:
        # Sort nodes in each weakly connected component by their time attribute to
        # ensure correct order
        sorted_nodes = sorted(
            node_set,
            key=lambda node: tracks.get_time(node),
        )

        # track_id and color are the same for all nodes in a node_set
        parent_track_id = None
        track_id = tracks.get_track_id(sorted_nodes[0])
        color = np.concatenate((colormap.map(track_id)[:3] * 255, [255]))

        for node in sorted_nodes:
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
                "parent_id": 0,
                "parent_track_id": 0,
                "state": state,
                "symbol": symbol,
            }

            for feature_key, feature in tracks.features.items():
                display_name = feature.get("display_name", feature_key)
                value_names = feature.get("value_names", None)
                val = tracks.get_node_attr(node, feature_key)
                num_values = feature.get("num_values", 1)
                if num_values > 1:
                    for i in range(num_values):
                        v = val[i]
                        if isinstance(display_name, list | tuple):
                            name = display_name[i]
                        elif (
                            isinstance(value_names, list)
                            and len(value_names) == num_values
                        ):
                            name = f"{value_names[i]}"
                        else:
                            name = f"{display_name}_{i}"
                        track_dict[name] = v
                else:
                    track_dict[display_name] = val

            # Determine parent_id and parent_track_id
            predecessors = list(solution_nx_graph.predecessors(node))
            if predecessors:
                parent_id = predecessors[
                    0
                ]  # There should be only one predecessor in a lineage tree
                track_dict["parent_id"] = parent_id

                if parent_track_id is None:
                    parent_track_id = solution_nx_graph.nodes[parent_id][
                        tracks.features.tracklet_key
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
    graph,
    tracklet_id_key: str = "tracklet_id",
    prev_axis_order: list[int] | None = None,
) -> list[Any]:
    """
    Extract the lineage tree plot order of the tracklet_ids on the graph, ensuring that
    each tracklet_id is placed in between its daughter tracklet_ids and adjacent to its
    parent track id.

    Args:
        graph: graph with a tracklet_id attribute on it.
        tracklet_id_key (str): tracklet_id key on the graph.

    Returns:
        list[Any] of ordered tracklet_ids.
    """

    # Topological sort via Kahn's algorithm (BFS from roots)
    in_degree = {n: graph.in_degree(n) for n in graph.node_ids()}
    queue = [n for n, d in in_degree.items() if d == 0]
    topo_order = []
    while queue:
        node = queue.pop(0)
        topo_order.append(node)
        for succ in graph.successors(node):
            in_degree[succ] -= 1
            if in_degree[succ] == 0:
                queue.append(succ)

    # Create tracklet_id to parent_tracklet_id mapping (0 if tracklet has no parent)
    tracklet_to_parent_tracklet = {}
    for node in topo_order:
        data = graph.nodes[node]
        tracklet = data[tracklet_id_key]
        if tracklet in tracklet_to_parent_tracklet:
            continue
        predecessors = list(graph.predecessors(node))
        if predecessors:
            parent_tracklet_id = graph.nodes[predecessors[0]][tracklet_id_key]
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


def extract_lineage_tree(graph, node_id: str) -> list[str]:
    """Extract the entire lineage tree including horizontal relations for a given node"""

    # go up the tree to identify the root node
    root_node = node_id
    while True:
        predecessors = list(graph.predecessors(root_node))
        if not predecessors:
            break
        root_node = predecessors[0]

    # BFS to collect all descendants
    nodes = set()
    queue = [root_node]
    while queue:
        node = queue.pop()
        if node in nodes:
            continue
        nodes.add(node)
        queue.extend(graph.successors(node))

    return list(nodes)


def get_features_from_tracks(
    tracks: Tracks | None = None, features_to_ignore: list[str] | None = None
) -> list[str]:
    """Extract the regionprops feature display names currently activated on Tracks.

    Args:
        tracks (Tracks | None): the Tracks instance to extract features from

    Returns:
        features_to_plot (list[str]): list of the feature names to plot, or an empty list
        if tracks is None
    """

    if features_to_ignore is None:
        features_to_ignore = []
    features_to_plot = []
    if tracks is not None:
        for feature in tracks.features.values():
            # Skip edge features - only show node features in dropdown
            if feature["feature_type"] == "edge":
                continue
            name = feature["display_name"]
            if feature["value_type"] in ("float", "int"):
                if feature["num_values"] > 1:
                    value_names = feature.get("value_names", None)
                    for i in range(feature["num_values"]):
                        if isinstance(name, list | tuple):
                            features_to_plot.append(name[i])
                        elif (
                            value_names is not None
                            and len(value_names) == feature["num_values"]
                        ):
                            features_to_plot.append(value_names[i])
                        else:
                            features_to_plot.append(f"{name}_{i}")
                else:
                    features_to_plot.append(name)

    features_to_plot = [
        feature for feature in features_to_plot if feature not in features_to_ignore
    ]
    return features_to_plot
