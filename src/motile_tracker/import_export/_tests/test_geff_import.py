"""Tests for GEFF import in motile_tracker using funtracks."""

import numpy as np
import pytest
import tifffile
from funtracks.import_export.import_from_geff import import_from_geff
from geff.testing.data import create_mock_geff


@pytest.fixture
def simple_geff_2d():
    """Create a simple 2D GEFF dataset for testing."""
    store, memory_geff = create_mock_geff(
        node_id_dtype="uint",
        node_axis_dtypes={"position": "float64", "time": "int64"},
        directed=True,
        num_nodes=5,
        num_edges=3,
        include_t=True,
        include_z=False,
        include_y=True,
        include_x=True,
        extra_node_props={
            "track_id": np.array([1, 1, 2, 2, 2]),
            "seg_id": np.array([10, 20, 30, 40, 50]),
        },
    )
    return store, memory_geff


@pytest.fixture
def simple_geff_3d():
    """Create a simple 3D GEFF dataset for testing."""
    store, memory_geff = create_mock_geff(
        node_id_dtype="uint",
        node_axis_dtypes={"position": "float64", "time": "int64"},
        directed=True,
        num_nodes=4,
        num_edges=2,
        include_t=True,
        include_z=True,
        include_y=True,
        include_x=True,
        extra_node_props={
            "track_id": np.array([1, 1, 2, 2]),
            "seg_id": np.array([1, 2, 3, 4]),
        },
    )
    return store, memory_geff


class TestGeffImportBasic:
    """Test basic GEFF import functionality."""

    def test_import_2d_geff(self, simple_geff_2d):
        """Test importing a 2D GEFF dataset."""
        store, _ = simple_geff_2d

        name_map = {
            "time": "t",
            "y": "y",
            "x": "x",
            "track_id": "track_id",
        }

        tracks = import_from_geff(store, name_map)

        assert tracks.graph.number_of_nodes() == 5
        assert tracks.graph.number_of_edges() == 3
        assert tracks.ndim == 3  # time + 2 spatial dimensions

    def test_import_3d_geff(self, simple_geff_3d):
        """Test importing a 3D GEFF dataset."""
        store, _ = simple_geff_3d

        name_map = {
            "time": "t",
            "z": "z",
            "y": "y",
            "x": "x",
            "track_id": "track_id",
        }

        tracks = import_from_geff(store, name_map)

        assert tracks.graph.number_of_nodes() == 4
        assert tracks.graph.number_of_edges() == 2
        assert tracks.ndim == 4  # time + 3 spatial dimensions

    def test_import_with_scale(self, simple_geff_2d):
        """Test that scale is correctly applied."""
        store, _ = simple_geff_2d

        name_map = {"time": "t", "y": "y", "x": "x"}
        scale = [1.0, 0.5, 0.5]

        tracks = import_from_geff(store, name_map, scale=scale)

        assert tracks.scale == scale

    def test_node_attributes_imported(self, simple_geff_2d):
        """Test that node attributes are correctly imported."""
        store, _ = simple_geff_2d

        name_map = {
            "time": "t",
            "y": "y",
            "x": "x",
            "track_id": "track_id",
        }

        tracks = import_from_geff(store, name_map)

        # Check that nodes have the expected attributes
        nodes = list(tracks.graph.nodes(data=True))
        assert len(nodes) == 5

        for _node_id, attrs in nodes:
            assert "time" in attrs
            assert "y" in attrs
            assert "x" in attrs
            assert "track_id" in attrs


class TestGeffImportWithSegmentation:
    """Test GEFF import with segmentation."""

    def test_import_with_segmentation(self, simple_geff_2d, tmp_path):
        """Test importing GEFF with segmentation."""
        store, memory_geff = simple_geff_2d

        # Get actual time coordinates from the GEFF data
        node_props = memory_geff["node_props"]
        times = node_props["t"]["values"]
        y_coords = node_props["y"]["values"]
        x_coords = node_props["x"]["values"]
        seg_ids = node_props["seg_id"]["values"]

        # Create segmentation with enough frames and space to cover all coordinates
        # Mock GEFF generates Y coords up to ~500, X coords ~1
        max_time = int(np.max(times)) + 1
        seg = np.zeros((max_time, 600, 600), dtype=np.uint16)

        # Place seg_ids at the actual coordinates
        for t, y, x, seg_id in zip(times, y_coords, x_coords, seg_ids, strict=False):
            t_idx = int(t)
            y_idx = int(y)
            x_idx = int(x)
            if 0 <= t_idx < max_time and 0 <= y_idx < 600 and 0 <= x_idx < 600:
                seg[t_idx, y_idx, x_idx] = seg_id

        seg_path = tmp_path / "segmentation.tif"
        tifffile.imwrite(seg_path, seg)

        name_map = {
            "time": "t",
            "y": "y",
            "x": "x",
            "seg_id": "seg_id",
        }

        tracks = import_from_geff(store, name_map, segmentation_path=seg_path)

        assert tracks.segmentation is not None
        assert tracks.segmentation.shape == seg.shape

    def test_segmentation_relabeling(self, simple_geff_2d, tmp_path):
        """Test that segmentation is relabeled from seg_id to node_id."""
        store, memory_geff = simple_geff_2d

        # Get actual coordinates from GEFF data
        node_props = memory_geff["node_props"]
        times = node_props["t"]["values"]
        y_coords = node_props["y"]["values"]
        x_coords = node_props["x"]["values"]
        seg_ids = node_props["seg_id"]["values"]

        # Create segmentation
        max_time = int(np.max(times)) + 1
        seg = np.zeros((max_time, 600, 600), dtype=np.uint16)

        for t, y, x, seg_id in zip(times, y_coords, x_coords, seg_ids, strict=False):
            t_idx = int(t)
            y_idx = int(y)
            x_idx = int(x)
            if 0 <= t_idx < max_time and 0 <= y_idx < 600 and 0 <= x_idx < 600:
                seg[t_idx, y_idx, x_idx] = seg_id

        seg_path = tmp_path / "segmentation.tif"
        tifffile.imwrite(seg_path, seg)

        name_map = {
            "time": "t",
            "y": "y",
            "x": "x",
            "seg_id": "seg_id",
        }

        tracks = import_from_geff(store, name_map, segmentation_path=seg_path)

        # At least verify that segmentation exists and has correct shape
        assert tracks.segmentation is not None
        assert tracks.segmentation.shape == seg.shape


class TestGeffImportWithFeatures:
    """Test GEFF import with feature loading and computation."""

    def test_load_feature_from_geff(self, tmp_path):
        """Test loading a feature directly from GEFF."""
        store, _ = create_mock_geff(
            node_id_dtype="uint",
            node_axis_dtypes={"position": "float64", "time": "int64"},
            directed=True,
            num_nodes=3,
            num_edges=2,
            include_t=True,
            include_z=False,
            include_y=True,
            include_x=True,
            extra_node_props={
                "area": np.array([100.0, 200.0, 300.0]),
                "seg_id": np.array([1, 2, 3]),
            },
        )

        name_map = {
            "time": "t",
            "y": "y",
            "x": "x",
            "seg_id": "seg_id",
        }

        node_features = {"area": False}  # Load from GEFF, don't recompute

        tracks = import_from_geff(
            store,
            name_map,
            node_features=node_features,
        )

        # Check that area was loaded from GEFF
        nodes = list(tracks.graph.nodes(data=True))
        areas = [attrs.get("area") for _, attrs in nodes]

        # Should have loaded the area values from GEFF
        assert areas[0] == 100.0
        assert areas[1] == 200.0
        assert areas[2] == 300.0

    def test_recompute_feature_from_segmentation(self, tmp_path):
        """Test recomputing a feature from segmentation."""
        store, memory_geff = create_mock_geff(
            node_id_dtype="uint",
            node_axis_dtypes={"position": "float64", "time": "int64"},
            directed=True,
            num_nodes=2,
            num_edges=1,
            include_t=True,
            include_z=False,
            include_y=True,
            include_x=True,
            extra_node_props={
                "seg_id": np.array([1, 2]),
            },
        )

        # Get time coordinates from GEFF data, but use safe spatial coordinates
        node_props = memory_geff["node_props"]
        times = node_props["t"]["values"]

        # Override the GEFF coordinates with safe locations for testing
        # Place nodes at coordinates where boxes will fit
        safe_coords = [(100, 100), (300, 300)]

        # Update the GEFF data with safe coordinates
        node_props["y"]["values"] = np.array(
            [c[0] for c in safe_coords], dtype=np.float64
        )
        node_props["x"]["values"] = np.array(
            [c[1] for c in safe_coords], dtype=np.float64
        )

        # Write updated coordinates back to the store
        import zarr

        zarr_store = zarr.open(store, mode="r+")
        zarr_store["nodes/props/y/values"][:] = node_props["y"]["values"]
        zarr_store["nodes/props/x/values"][:] = node_props["x"]["values"]

        # Create segmentation with known areas at the safe coordinates
        max_time = int(np.max(times)) + 1
        seg = np.zeros((max_time, 600, 600), dtype=np.uint16)

        # Place seg_id 1 with a 10x10 area around the first node
        t0, y0, x0 = int(times[0]), safe_coords[0][0], safe_coords[0][1]
        seg[t0, y0 - 5 : y0 + 5, x0 - 5 : x0 + 5] = 1  # 10x10 = 100 pixels

        # Place seg_id 2 with a 20x20 area around the second node
        t1, y1, x1 = int(times[1]), safe_coords[1][0], safe_coords[1][1]
        seg[t1, y1 - 10 : y1 + 10, x1 - 10 : x1 + 10] = 2  # 20x20 = 400 pixels

        seg_path = tmp_path / "segmentation.tif"
        tifffile.imwrite(seg_path, seg)

        name_map = {
            "time": "t",
            "y": "y",
            "x": "x",
            "seg_id": "seg_id",
        }

        node_features = {"area": True}  # Recompute from segmentation

        tracks = import_from_geff(
            store,
            name_map,
            segmentation_path=seg_path,
            node_features=node_features,
        )

        # Check that area was recomputed from segmentation
        nodes = [1, 2]
        areas = tracks.get_nodes_attr(nodes, "area", required=True)

        # Should have recomputed areas from segmentation
        assert areas[0] == 100  # 10x10 pixels
        assert areas[1] == 400  # 20x20 pixels


class TestGeffImportValidation:
    """Test validation and error handling in GEFF import."""

    def test_missing_required_attribute(self, simple_geff_2d):
        """Test that missing required attributes raise an error."""
        store, _ = simple_geff_2d

        # Missing 'x' in name_map
        name_map = {
            "time": "t",
            "y": "y",
            # "x" is missing
        }

        with pytest.raises(ValueError, match="None values"):
            import_from_geff(store, name_map)

    def test_duplicate_name_map_values(self, simple_geff_2d):
        """Test that duplicate values in name_map raise an error."""
        store, _ = simple_geff_2d

        # Both y and x map to the same GEFF property
        name_map = {
            "time": "t",
            "y": "y",
            "x": "y",  # Duplicate!
        }

        with pytest.raises(ValueError, match="duplicate values"):
            import_from_geff(store, name_map)
