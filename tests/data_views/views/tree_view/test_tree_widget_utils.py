import napari
import pandas as pd
import polars as pl
from funtracks.annotators import TrackAnnotator
from funtracks.data_model import SolutionTracks
from funtracks.features import Feature
from funtracks.utils.tracksdata_utils import create_empty_graphview_graph

from motile_tracker.data_views.views.tree_view.tree_widget_utils import (
    extract_sorted_tracks,
)


def test_track_df(solution_tracks_2d):
    tracks = solution_tracks_2d
    ann = TrackAnnotator(tracks, lineage_key="lineage_id", tracklet_key="track_id")
    tracks.graph.add_node_attr_key("custom_attr", default_value=0, dtype=pl.Int64)

    for node in tracks.graph.node_ids():
        if node != 2:
            tracks.graph.nodes[node]["custom_attr"] = node * 10
    tracks.features["custom_attr"] = Feature(
        feature_type="node",
        value_type="int",
        num_values=1,
    )

    ann.compute()

    colormap = napari.utils.colormaps.label_colormap(
        49,
        seed=0.5,
        background_value=0,
    )

    track_df, _ = extract_sorted_tracks(tracks, colormap)
    assert isinstance(track_df, pd.DataFrame)
    assert track_df.loc[track_df["node_id"] == 1, "custom_attr"].values[0] == 10
    assert track_df.loc[track_df["node_id"] == 2, "custom_attr"].values[0] == 0


def test_extract_sorted_tracks_incomplete_lineage():
    """BFS must not merge tracklets across track_id boundaries in incomplete graphs.

    Full lineage: A(tk=1) -> B(tk=1, divides) -> C(tk=2) and B -> D(tk=3).
    Loaded subset: only A, B, C (D is missing). B appears to have a single child
    (C), so topology alone does not identify it as a division node. Without the
    track_id guard the BFS follows A->B->C and merges all three into one tracklet.
    With the fix, the BFS stops at the B->C edge (track_id 1 != 2), producing
    separate tracklets {A, B} and {C}.
    """
    graph = create_empty_graphview_graph(
        node_attributes=["pos", "track_id"],
        ndim=3,
    )
    graph.bulk_add_nodes(
        nodes=[
            {"t": 0, "pos": [0.0, 0.0], "track_id": 1, "solution": 1},  # A, node 1
            {"t": 1, "pos": [0.0, 0.0], "track_id": 1, "solution": 1},  # B, node 2
            {"t": 2, "pos": [0.0, 0.0], "track_id": 2, "solution": 1},  # C, node 3
        ],
        indices=[1, 2, 3],
    )
    graph.bulk_add_edges(
        [
            {"source_id": 1, "target_id": 2, "solution": 1},  # A -> B
            {"source_id": 2, "target_id": 3, "solution": 1},  # B -> C (cross boundary)
        ]
    )
    tracks = SolutionTracks(graph=graph, ndim=3, time_attr="t")

    colormap = napari.utils.colormaps.label_colormap(49, seed=0.5, background_value=0)
    track_df, _ = extract_sorted_tracks(tracks, colormap)

    # C (node 3) must be in its own tracklet with track_id=2, not merged into A+B (track_id=1)
    node_c_track_id = track_df.loc[track_df["node_id"] == 3, "track_id"].values[0]
    assert node_c_track_id == 2, (
        f"Node C was merged into track {node_c_track_id} instead of its own track (2). "
        "BFS crossed a track_id boundary in an incomplete lineage."
    )
