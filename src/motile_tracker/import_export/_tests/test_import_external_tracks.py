import os

import numpy as np
import pandas as pd
import pytest

from motile_tracker.data_views.graph_attributes import NodeAttr
from motile_tracker.import_export.load_tracks import (
    _test_valid,
    ensure_correct_labels,
    ensure_integer_ids,
    tracks_from_df,
)


class TestLoadTracks:
    def test_non_unique_ids(self):
        """Test that a ValueError is raised if the ids are not unique"""

        data = {
            "id": [1, 1, 2],
            "parent_id": [0, 0, 1],
            NodeAttr.TIME.value: [0, 1, 2],
            "y": [10, 20, 30],
            "x": [15, 25, 35],
        }
        df = pd.DataFrame(data)
        with pytest.raises(
            ValueError,
            match="The 'id' column must contain unique values",
        ):
            tracks_from_df(df)

    def test_string_ids(self):
        """Test that string ids are converted to unique integers"""

        data = {
            "id": ["a", "b", "c"],
            "parent_id": [None, "b", "c"],
            NodeAttr.TIME.value: [0, 1, 2],
            "y": [10, 20, 30],
            "x": [15, 25, 35],
        }
        df = pd.DataFrame(data)
        df = ensure_integer_ids(df)
        assert pd.api.types.is_integer_dtype(df["id"])
        assert (
            pd.to_numeric(df["parent_id"], errors="coerce")
            .dropna()
            .apply(lambda x: float(x).is_integer())
            .all()
        )
        assert df["id"].is_unique

    def test_set_scale(self):
        """Test that the scaling is correctly propagated to the tracks"""

        data = {
            "id": [1, 2, 3],
            "parent_id": [None, 1, 2],
            NodeAttr.TIME.value: [0, 1, 2],
            "y": [10, 20, 30],
            "x": [15, 25, 35],
        }
        df = pd.DataFrame(data)
        scale = [1, 2, 1]
        tracks = tracks_from_df(df, scale=scale)
        assert tracks.scale == scale

    def test_valid_segmentation(self):
        """Test that the segmentation value of the first node matches with its id"""

        data = {
            "id": [1, 2, 3],
            "parent_id": [-1, 1, 2],
            NodeAttr.TIME.value: [0, 1, 2],
            "y": [0.25, 2, 1.3333],
            "x": [0.75, 1.5, 1.6667],
            "seg_id": [1, 2, 3],
        }
        df = pd.DataFrame(data)
        segmentation = np.array(
            [
                [[1, 1, 1], [1, 3, 3], [2, 2, 3]],
                [[1, 1, 1], [1, 3, 3], [2, 2, 3]],
                [[1, 1, 1], [1, 3, 3], [2, 2, 3]],
            ]
        )

        assert _test_valid(df, segmentation, scale=[1, 1, 1])
        assert _test_valid(df, segmentation, scale=None)

        data = {
            "id": [1, 2, 3],
            "parent_id": [-1, 1, 2],
            NodeAttr.TIME.value: [0, 1, 2],
            "y": [1, 8, 5.3333],
            "x": [3, 6, 6.6667],
            "seg_id": [1, 2, 3],
        }
        df = pd.DataFrame(data)

        # test if False when scaling is applied incorrectly
        with pytest.warns(
            UserWarning, match="Could not get the segmentation value at index"
        ):
            output = _test_valid(df, segmentation, scale=[1, 1, 1])
            assert not output
        # test if True when scaling is applied correctly
        assert _test_valid(df, segmentation, scale=[1, 4, 4])
        # ndim of segmentation should match with the length of provided scale
        with pytest.warns(
            UserWarning,
            match=r"Dimensions of the segmentation image \(3\) do not match the number "
            r"of scale values given \(4\)",
        ):
            assert not _test_valid(df, segmentation, scale=[1, 4, 4, 1])

        data = {
            "id": [1, 2, 3],
            "parent_id": [-1, 1, 2],
            NodeAttr.TIME.value: [0, 1, 2],
            "z": [1, 1, 1],
            "y": [1, 8, 5.3333],
            "x": [3, 6, 6.6667],
            "seg_id": [1, 2, 3],
        }
        df = pd.DataFrame(data)
        # ndim of segmentation should match with the dims specified in the dataframe
        with pytest.warns(
            UserWarning,
            match=r"Dimensions of the segmentation \(3\) do not match the number "
            r"of positional dimensions \(4\)",
        ):
            assert not _test_valid(df, segmentation, scale=[1, 4, 4])

        # test actual 4D data
        data = {
            "id": [1, 2, 3],
            "parent_id": [-1, 1, 2],
            NodeAttr.TIME.value: [0, 1, 2],
            "z": [0, 0, 0],
            "y": [1, 8, 5.3333],
            "x": [3, 6, 6.6667],
            "seg_id": [1, 2, 3],
        }
        seg_4d = np.array([segmentation, segmentation, segmentation])
        df = pd.DataFrame(data)
        assert _test_valid(df, seg_4d, scale=[1, 1, 4, 4])
        tracks = tracks_from_df(df, seg_4d, scale=[1, 1, 4, 4])
        assert tracks.graph.number_of_nodes() == 3
        assert tracks.graph.number_of_edges() == 2

    def test_relabel_segmentation(self):
        """Test relabeling the segmentation if id != seg_id"""

        data = {
            NodeAttr.TIME.value: [0, 0, 0, 1],
            "seg_id": [1, 2, 3, 3],
            "id": [10, 20, 30, 40],
            "x": [0, 0, 1, 1],
            "y": [0, 2, 2, 2],
            "parent_id": [None, None, None, None],
        }
        df = pd.DataFrame(data)
        segmentation = np.array(
            [
                [[1, 1, 2], [2, 3, 3], [1, 2, 3]],
                [[0, 0, 0], [0, 3, 3], [0, 0, 3]],
            ]
        )
        new_segmentation = ensure_correct_labels(df, segmentation)
        expected_segmentation = np.array(
            [
                [[10, 10, 20], [20, 30, 30], [10, 20, 30]],
                [[0, 0, 0], [0, 40, 40], [0, 0, 40]],
            ]
        )

        np.testing.assert_array_equal(new_segmentation, expected_segmentation)
        tracks = tracks_from_df(df, segmentation)
        np.testing.assert_array_equal(tracks.segmentation, expected_segmentation)
        assert tracks.graph.number_of_nodes() == 4
        assert tracks.graph.number_of_edges() == 0

    def test_measurements(self):
        """Test if the area is measured correctly, taking scaling into account"""

        data = {
            NodeAttr.TIME.value: [0, 0, 0, 1],
            "seg_id": [1, 2, 3, 4],
            "id": [1, 2, 3, 4],
            "parent_id": [None, 1, 2, 3],
            "y": [0, 1.6667, 1.333, 1.333],
            "x": [1, 0.33333, 1.66667, 1.66667],
        }
        df = pd.DataFrame(data)
        segmentation = np.array(
            [[[1, 1, 1], [2, 3, 3], [2, 3, 3]], [[1, 1, 0], [2, 4, 4], [2, 2, 4]]]
        )

        tracks = tracks_from_df(
            df, segmentation, scale=(1, 1, 1), features={"Area": "Recompute"}
        )

        assert tracks.get_node_attr(1, NodeAttr.AREA.value) == 3
        assert tracks.get_node_attr(2, NodeAttr.AREA.value) == 2
        assert tracks.get_node_attr(3, NodeAttr.AREA.value) == 4
        assert tracks.get_node_attr(4, NodeAttr.AREA.value) == 3

        tracks = tracks_from_df(
            df, segmentation, scale=(1, 2, 1), features={"Area": "Recompute"}
        )

        assert tracks.get_node_attr(1, NodeAttr.AREA.value) == 6
        assert tracks.get_node_attr(2, NodeAttr.AREA.value) == 4
        assert tracks.get_node_attr(3, NodeAttr.AREA.value) == 8
        assert tracks.get_node_attr(4, NodeAttr.AREA.value) == 6

        tracks = tracks_from_df(
            df, segmentation=None, scale=(1, 2, 1), features={"Area": "Recompute"}
        )  # no seg provided, should return None

        assert tracks.get_node_attr(1, NodeAttr.AREA.value) is None

        tracks = tracks_from_df(
            df, segmentation, scale=(1, 2, 1), features={}
        )  # no area measurement provided, should return None.

        assert tracks.get_node_attr(1, NodeAttr.AREA.value) is None

        data = {
            NodeAttr.TIME.value: [0, 0, 0, 1],
            "seg_id": [1, 2, 3, 4],
            "id": [1, 2, 3, 4],
            "parent_id": [None, 1, 2, 3],
            "y": [0, 1.6667, 1.333, 1.333],
            "x": [1, 0.33333, 1.66667, 1.66667],
            "area": [1, 2, 3, 4],
        }
        df = pd.DataFrame(data)
        # Area column provided by the dataframe (import_external_tracks_dialog is in
        # charge of mapping a custom column to a column named 'area' (to be updated in
        # future version that supports additional measured features)
        tracks = tracks_from_df(
            df, segmentation, scale=(1, 1, 1), features={"Area": "area"}
        )

        assert tracks.get_node_attr(1, NodeAttr.AREA.value) == 1
        assert tracks.get_node_attr(2, NodeAttr.AREA.value) == 2
        assert tracks.get_node_attr(3, NodeAttr.AREA.value) == 3
        assert tracks.get_node_attr(4, NodeAttr.AREA.value) == 4

    def test_load_sample_data(self):
        test_dir = os.path.abspath(__file__)
        example_csv = os.path.abspath(
            os.path.join(test_dir, "../hela_example_tracks.csv")
        )

        df = pd.read_csv(example_csv)

        # Retrieve selected columns for each required field, and optional columns for
        # additional attributes
        name_map = {
            "time": "t",
        }
        # Create new columns for each feature based on the original column values
        for feature, column in name_map.items():
            df[feature] = df[column]

        tracks = tracks_from_df(df)
        for node in tracks.graph.nodes():
            assert isinstance(node, int)
