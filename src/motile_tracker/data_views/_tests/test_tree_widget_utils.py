from typing import Any

import napari
import networkx as nx
import pandas as pd
import pytest
from funtracks.data_model import EdgeAttr, NodeAttr, SolutionTracks

from motile_tracker.data_views.views.tree_view.tree_widget_utils import (
    extract_sorted_tracks,
)


@pytest.fixture
def graph_2d():
    graph = nx.DiGraph()
    nodes = [
        (
            1,
            {
                NodeAttr.POS.value: [50, 50],
                NodeAttr.TIME.value: 0,
                NodeAttr.AREA.value: 1245,
                NodeAttr.TRACK_ID.value: 1,
            },
        ),
        (
            2,
            {
                NodeAttr.POS.value: [20, 80],
                NodeAttr.TIME.value: 1,
                NodeAttr.TRACK_ID.value: 2,
                NodeAttr.AREA.value: 305,
            },
        ),
        (
            3,
            {
                NodeAttr.POS.value: [60, 45],
                NodeAttr.TIME.value: 1,
                NodeAttr.AREA.value: 697,
                NodeAttr.TRACK_ID.value: 3,
            },
        ),
        (
            4,
            {
                NodeAttr.POS.value: [1.5, 1.5],
                NodeAttr.TIME.value: 2,
                NodeAttr.AREA.value: 16,
                NodeAttr.TRACK_ID.value: 3,
            },
        ),
        (
            5,
            {
                NodeAttr.POS.value: [1.5, 1.5],
                NodeAttr.TIME.value: 4,
                NodeAttr.AREA.value: 16,
                NodeAttr.TRACK_ID.value: 3,
            },
        ),
        # unconnected node
        (
            6,
            {
                NodeAttr.POS.value: [97.5, 97.5],
                NodeAttr.TIME.value: 4,
                NodeAttr.AREA.value: 16,
                NodeAttr.TRACK_ID.value: 5,
            },
        ),
    ]
    edges = [
        (1, 2, {EdgeAttr.IOU.value: 0.0}),
        (1, 3, {EdgeAttr.IOU.value: 0.395}),
        (
            3,
            4,
            {EdgeAttr.IOU.value: 0.0},
        ),
        (
            4,
            5,
            {EdgeAttr.IOU.value: 1.0},
        ),
    ]
    graph.add_nodes_from(nodes)
    graph.add_edges_from(edges)
    return graph


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
    del tracks.graph.nodes[2]["area"]

    assert tracks.get_area(1) == 1245
    assert tracks.get_area(2) is None

    tracks.graph, _, _ = assign_tracklet_ids(tracks.graph)

    colormap = napari.utils.colormaps.label_colormap(
        49,
        seed=0.5,
        background_value=0,
    )

    track_df = extract_sorted_tracks(tracks, colormap)
    assert isinstance(track_df, pd.DataFrame)
    assert track_df.loc[track_df["node_id"] == 1, "area"].values[0] == 1245
    assert track_df.loc[track_df["node_id"] == 2, "area"].values[0] == 0
    assert track_df["area"].notna().all()
