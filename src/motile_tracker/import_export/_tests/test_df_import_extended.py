"""Extended tests for DataFrame import via tracks_from_df."""

import numpy as np
import pandas as pd
import pytest
from funtracks.data_model import SolutionTracks
from motile_toolbox.candidate_graph.graph_attributes import NodeAttr

from motile_tracker.import_export import tracks_from_df
from motile_tracker.import_export.load_tracks import (
    ensure_correct_labels,
    ensure_integer_ids,
)


@pytest.fixture
def simple_df_2d():
    """Simple 2D DataFrame."""
    return pd.DataFrame(
        {
            NodeAttr.TIME.value: [0, 1, 1, 2],
            "y": [10.0, 20.0, 30.0, 40.0],
            "x": [15.0, 25.0, 35.0, 45.0],
            "id": [1, 2, 3, 4],
            "parent_id": [-1, 1, 1, 2],
        }
    )


@pytest.fixture
def df_3d():
    """3D DataFrame."""
    return pd.DataFrame(
        {
            NodeAttr.TIME.value: [0, 1, 1],
            "z": [5.0, 10.0, 15.0],
            "y": [10.0, 20.0, 30.0],
            "x": [15.0, 25.0, 35.0],
            "id": [1, 2, 3],
            "parent_id": [-1, 1, 1],
        }
    )


class TestDataFrameImportBasic:
    """Test basic DataFrame import."""

    def test_import_2d(self, simple_df_2d):
        """Test importing 2D DataFrame."""
        tracks = tracks_from_df(simple_df_2d)

        assert isinstance(tracks, SolutionTracks)
        assert tracks.graph.number_of_nodes() == 4
        assert tracks.graph.number_of_edges() == 3
        assert tracks.ndim == 3

    def test_import_3d(self, df_3d):
        """Test importing 3D DataFrame."""
        tracks = tracks_from_df(df_3d)

        assert tracks.ndim == 4
        assert tracks.graph.number_of_nodes() == 3
        # Check z coordinate
        pos = tracks.get_position(1)
        assert len(pos) == 3  # z, y, x
        assert pos[0] == 5.0  # z

    def test_with_scale(self, simple_df_2d):
        """Test importing with scale."""
        scale = [1.0, 2.0, 1.5]
        tracks = tracks_from_df(simple_df_2d, scale=scale)

        assert tracks.scale == scale

    def test_node_positions(self, simple_df_2d):
        """Test that node positions are correctly imported."""
        tracks = tracks_from_df(simple_df_2d)

        pos_1 = tracks.get_position(1)
        assert pos_1 == [10.0, 15.0]  # y, x

        pos_2 = tracks.get_position(2)
        assert pos_2 == [20.0, 25.0]

    def test_edges_created(self, simple_df_2d):
        """Test that edges are created from parent_id."""
        tracks = tracks_from_df(simple_df_2d)

        # Check specific edges exist
        assert tracks.graph.has_edge(1, 2)
        assert tracks.graph.has_edge(1, 3)
        assert tracks.graph.has_edge(2, 4)

        # Check node 1 has two children (division)
        assert len(list(tracks.graph.successors(1))) == 2


class TestStringIDHandling:
    """Test handling of string IDs."""

    def test_string_ids_converted(self):
        """Test that string IDs are converted to integers."""
        df = pd.DataFrame(
            {
                NodeAttr.TIME.value: [0, 1, 1],
                "y": [10.0, 20.0, 30.0],
                "x": [15.0, 25.0, 35.0],
                "id": ["cell_a", "cell_b", "cell_c"],
                "parent_id": [None, "cell_a", "cell_a"],
            }
        )

        # Pre-process DataFrame
        df = ensure_integer_ids(df)

        assert pd.api.types.is_integer_dtype(df["id"])
        assert df["id"].is_unique
        assert len(df["id"].unique()) == 3

        # Should be able to import now
        tracks = tracks_from_df(df)
        assert tracks.graph.number_of_nodes() == 3

    def test_string_id_relationships_preserved(self):
        """Test that parent-child relationships preserved after conversion."""
        df = pd.DataFrame(
            {
                NodeAttr.TIME.value: [0, 1, 1],
                "y": [10.0, 20.0, 30.0],
                "x": [15.0, 25.0, 35.0],
                "id": ["a", "b", "c"],
                "parent_id": [None, "a", "a"],
            }
        )

        df = ensure_integer_ids(df)
        tracks = tracks_from_df(df)

        # Should have two edges (a->b and a->c)
        assert tracks.graph.number_of_edges() == 2

        # Root should have two children
        roots = [n for n in tracks.graph.nodes() if tracks.graph.in_degree(n) == 0]
        assert len(roots) == 1
        root = roots[0]
        assert len(list(tracks.graph.successors(root))) == 2


class TestSegmentationHandling:
    """Test DataFrame import with segmentation."""

    def test_with_2d_segmentation(self, simple_df_2d):
        """Test importing with 2D segmentation."""
        # Add seg_id column (required when segmentation provided)
        df = simple_df_2d.copy()
        df["seg_id"] = df["id"]

        seg = np.zeros((3, 100, 100), dtype=np.uint16)
        seg[0, 10, 15] = 1
        seg[1, 20, 25] = 2
        seg[1, 30, 35] = 3
        seg[2, 40, 45] = 4

        tracks = tracks_from_df(df, seg)

        assert tracks.segmentation is not None
        assert tracks.segmentation.shape == (3, 100, 100)

    def test_relabeling_when_needed(self):
        """Test that segmentation is relabeled when seg_id != id."""
        df = pd.DataFrame(
            {
                NodeAttr.TIME.value: [0, 0],
                "y": [10.0, 20.0],
                "x": [15.0, 25.0],
                "id": [10, 20],  # Different from seg_id
                "seg_id": [1, 2],
                "parent_id": [-1, 10],
            }
        )

        seg = np.zeros((1, 100, 100), dtype=np.uint16)
        seg[0, 10, 15] = 1  # seg_id 1
        seg[0, 20, 25] = 2  # seg_id 2

        # Test relabeling function
        new_seg = ensure_correct_labels(df, seg)

        # Should relabel 1->10 and 2->20
        assert new_seg[0, 10, 15] == 10
        assert new_seg[0, 20, 25] == 20

        # Import should work with relabeling
        tracks = tracks_from_df(df, seg)
        assert tracks.segmentation is not None

    def test_seg_id_matches_id(self, simple_df_2d):
        """Test when seg_id matches id (no relabeling needed)."""
        # Add seg_id column matching id
        df = simple_df_2d.copy()
        df["seg_id"] = df["id"]

        seg = np.zeros((3, 100, 100), dtype=np.uint16)
        seg[0, 10, 15] = 1
        seg[1, 20, 25] = 2
        seg[1, 30, 35] = 3
        seg[2, 40, 45] = 4

        tracks = tracks_from_df(df, seg)
        assert tracks.segmentation is not None
        # Segmentation should not be relabeled
        assert tracks.segmentation[0, 10, 15] == 1


class TestFeatureHandling:
    """Test feature computation and loading."""

    def test_load_area_from_df(self):
        """Test loading pre-computed area from DataFrame."""
        df = pd.DataFrame(
            {
                NodeAttr.TIME.value: [0, 1],
                "y": [10.0, 20.0],
                "x": [15.0, 25.0],
                "id": [1, 2],
                "parent_id": [-1, 1],
                "area": [100.0, 200.0],
            }
        )

        tracks = tracks_from_df(df, features={"Area": "area"})

        # Area should be loaded from DataFrame
        assert tracks.get_node_attr(1, NodeAttr.AREA.value) == 100.0
        assert tracks.get_node_attr(2, NodeAttr.AREA.value) == 200.0

    def test_recompute_area_from_seg(self):
        """Test recomputing area from segmentation."""
        df = pd.DataFrame(
            {
                NodeAttr.TIME.value: [0, 1],
                "y": [10.0, 20.0],
                "x": [15.0, 25.0],
                "id": [1, 2],
                "parent_id": [-1, 1],
                "seg_id": [1, 2],  # Required when segmentation provided
            }
        )

        # Create segmentation with known areas
        seg = np.zeros((2, 100, 100), dtype=np.uint16)
        seg[0, 8:13, 13:18] = 1  # 5x5 = 25 pixels
        seg[1, 18:23, 23:28] = 2  # 5x5 = 25 pixels

        tracks = tracks_from_df(df, seg, features={"Area": "Recompute"})

        # Area should be computed from segmentation
        assert tracks.get_node_attr(1, NodeAttr.AREA.value) == 25
        assert tracks.get_node_attr(2, NodeAttr.AREA.value) == 25


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_node(self):
        """Test DataFrame with single node."""
        df = pd.DataFrame(
            {
                NodeAttr.TIME.value: [0],
                "y": [10.0],
                "x": [15.0],
                "id": [1],
                "parent_id": [-1],
            }
        )

        tracks = tracks_from_df(df)

        assert tracks.graph.number_of_nodes() == 1
        assert tracks.graph.number_of_edges() == 0

    def test_multiple_roots(self):
        """Test multiple independent lineages."""
        df = pd.DataFrame(
            {
                NodeAttr.TIME.value: [0, 0, 1, 1],
                "y": [10.0, 20.0, 15.0, 25.0],
                "x": [15.0, 25.0, 20.0, 30.0],
                "id": [1, 2, 3, 4],
                "parent_id": [-1, -1, 1, 2],  # Two roots
            }
        )

        tracks = tracks_from_df(df)

        assert tracks.graph.number_of_nodes() == 4
        assert tracks.graph.number_of_edges() == 2

        # Should have two root nodes
        roots = [n for n in tracks.graph.nodes() if tracks.graph.in_degree(n) == 0]
        assert len(roots) == 2

    def test_division_event(self):
        """Test cell division (one parent, two children)."""
        df = pd.DataFrame(
            {
                NodeAttr.TIME.value: [0, 1, 1],
                "y": [10.0, 20.0, 30.0],
                "x": [15.0, 25.0, 35.0],
                "id": [1, 2, 3],
                "parent_id": [-1, 1, 1],  # 1 divides into 2 and 3
            }
        )

        tracks = tracks_from_df(df)

        assert tracks.graph.number_of_nodes() == 3
        assert tracks.graph.number_of_edges() == 2

        # Node 1 should have two children
        children = list(tracks.graph.successors(1))
        assert len(children) == 2
        assert set(children) == {2, 3}

    def test_long_track(self):
        """Test a long track without divisions."""
        df = pd.DataFrame(
            {
                NodeAttr.TIME.value: list(range(10)),
                "y": [float(i * 10) for i in range(10)],
                "x": [float(i * 10) for i in range(10)],
                "id": list(range(1, 11)),
                "parent_id": [-1] + list(range(1, 10)),
            }
        )

        tracks = tracks_from_df(df)

        assert tracks.graph.number_of_nodes() == 10
        assert tracks.graph.number_of_edges() == 9

        # Should form a single linear chain
        roots = [n for n in tracks.graph.nodes() if tracks.graph.in_degree(n) == 0]
        assert len(roots) == 1

        # Each non-leaf node should have exactly one child
        non_leaves = [n for n in tracks.graph.nodes() if tracks.graph.out_degree(n) > 0]
        for node in non_leaves:
            assert tracks.graph.out_degree(node) == 1

    def test_orphaned_node_raises_error(self):
        """Test that node with invalid parent_id raises error."""
        df = pd.DataFrame(
            {
                NodeAttr.TIME.value: [0, 1],
                "y": [10.0, 20.0],
                "x": [15.0, 25.0],
                "id": [1, 2],
                "parent_id": [-1, 999],  # Parent 999 doesn't exist
            }
        )

        # tracks_from_df validates that parent exists
        with pytest.raises(AssertionError, match="not in graph"):
            tracks_from_df(df)


class TestValidationErrors:
    """Test that invalid data raises appropriate errors."""

    def test_non_unique_ids(self):
        """Test that non-unique IDs raise error."""
        df = pd.DataFrame(
            {
                NodeAttr.TIME.value: [0, 1],
                "y": [10.0, 20.0],
                "x": [15.0, 25.0],
                "id": [1, 1],  # Duplicate!
                "parent_id": [-1, -1],
            }
        )

        with pytest.raises(ValueError, match="unique"):
            tracks_from_df(df)

    def test_missing_required_column(self):
        """Test that missing required columns raise error."""
        df = pd.DataFrame(
            {
                # Missing 'time' column
                "y": [10.0, 20.0],
                "x": [15.0, 25.0],
                "id": [1, 2],
                "parent_id": [-1, 1],
            }
        )

        # tracks_from_df validates required columns
        with pytest.raises(AssertionError, match="Required column"):
            tracks_from_df(df)
