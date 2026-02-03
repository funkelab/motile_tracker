from typing import Any

import napari
import networkx as nx
import numpy as np
import pandas as pd
from funtracks.data_model import EdgeAttr, NodeAttr, SolutionTracks
from funtracks.features import Feature

from motile_tracker.data_views.views.tree_view.tree_widget_utils import (
    extract_sorted_tracks,
)

def assign_tracklet_ids(graph: nx.DiGraph) -> tuple[nx.DiGraph, list[Any], int]:
    """Add a track_id attribute to a graph by removing division edges,
    assigning one id to each connected component.
    Designed as a helper for visualizing the graph in the napari Tracks layer.

    Args:
        graph (nx.DiGraph): A networkx graph with a tracking solution

    Returns:
        nx.DiGraph, list[Any], int: The same graph with the track_id assigned. Probably
        occurrs in place but returned just to be clear. Also returns a list of edges
        that are between tracks (e.g. at divisions), and the max track ID that was
        assigned
    """
    graph_copy = graph.copy()

    parents = [node for node, degree in graph.out_degree() if degree >= 2]
    intertrack_edges = []

    # Remove all intertrack edges from a copy of the original graph
    for parent in parents:
        daughters = [child for p, child in graph.out_edges(parent)]
        for daughter in daughters:
            graph_copy.remove_edge(parent, daughter)
            intertrack_edges.append((parent, daughter))

    track_id = 1
    for tracklet in nx.weakly_connected_components(graph_copy):
        nx.set_node_attributes(
            graph, {node: {"track_id": track_id} for node in tracklet}
        )
        track_id += 1
    return graph, intertrack_edges, track_id


def test_track_df(graph_2d):
    tracks = SolutionTracks(graph=graph_2d, ndim=3)
    for node in tracks.graph.nodes():
        if node != 2:
            tracks.graph.nodes[node]["custom_attr"] = node * 10
    tracks.features["custom_attr"] = Feature(
        feature_type="node",
        value_type="int",
        num_values=1,
    )

    tracks.graph, _, _ = assign_tracklet_ids(tracks.graph)

    colormap = napari.utils.colormaps.label_colormap(
        49,
        seed=0.5,
        background_value=0,
    )

    track_df, _ = extract_sorted_tracks(tracks, colormap)
    assert isinstance(track_df, pd.DataFrame)
    assert track_df.loc[track_df["node_id"] == 1, "custom_attr"].values[0] == 10
    assert np.isnan(track_df.loc[track_df["node_id"] == 2, "custom_attr"].values[0])
