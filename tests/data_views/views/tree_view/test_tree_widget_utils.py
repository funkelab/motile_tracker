import napari
import pandas as pd
import polars as pl
from funtracks.annotators import TrackAnnotator
from funtracks.data_model import SolutionTracks
from funtracks.features import Feature

from motile_tracker.data_views.views.tree_view.tree_widget_utils import (
    extract_sorted_tracks,
)


def test_track_df(graph_2d):
    tracks = SolutionTracks(graph=graph_2d, ndim=3, time_attr="t")
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
