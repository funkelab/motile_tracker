"""Tests for center_view functionality with different scale configurations."""

import networkx as nx
import numpy as np
from funtracks.data_model import NodeAttr, SolutionTracks

from motile_tracker.data_views.views.ortho_views import initialize_ortho_views
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


class TestCenterViewWithScale:
    """Test center_view correctly handles scaled data.

    The key thing to understand:
    - Node positions in the graph are in WORLD coordinates (scaled)
    - viewer.dims.point is in WORLD coordinates
    - viewer.dims.current_step is an index into the dims range
    - center_view should position the viewer at the node's world coordinates
    """

    def test_center_view_with_z_scale_less_than_one(self, make_napari_viewer):
        """Test center_view when z-scale < 1 (common for anisotropic z).

        With z-scale = 0.5:
        - Segmentation pixel z=50 corresponds to world z=25
        - Node at world z=25 should display correctly
        """
        viewer = make_napari_viewer()

        # Create graph - positions are in WORLD coordinates
        graph = nx.DiGraph()
        # Node at world position [25, 50, 50]
        nodes = [
            (
                1,
                {
                    NodeAttr.POS.value: [25, 50, 50],  # world coords
                    NodeAttr.TIME.value: 0,
                    NodeAttr.AREA.value: 1000,
                },
            ),
        ]
        graph.add_nodes_from(nodes)

        # Create segmentation (100 pixels in z)
        # With z-scale=0.5, world z-extent is 0-50
        segmentation = np.zeros((2, 100, 100, 100), dtype="int32")
        segmentation[0, 45:55, 45:55, 45:55] = 1  # pixel z=50, world z=25

        scale = [1.0, 0.5, 1.0, 1.0]  # t, z, y, x
        tracks = SolutionTracks(
            graph=graph,
            segmentation=segmentation,
            scale=scale,
            ndim=4,
        )

        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Get the point index for node 1
        points_layer = tracks_viewer.tracking_layers.points_layer
        node_index = points_layer.node_index_dict[1]

        # Center on node 1 at world position [25, 50, 50]
        tracks_viewer.tracking_layers.center_view(node=1)

        # Verify viewer is positioned at world z=25
        new_point = viewer.dims.point
        assert abs(new_point[1] - 25) < 1, f"Expected world z≈25, got {new_point[1]}"

        # Verify point is visible using _indices_view
        visible_indices = points_layer._indices_view
        assert node_index in visible_indices, (
            f"Point index {node_index} not in visible indices {visible_indices}. "
            f"Viewer dims.point={viewer.dims.point}"
        )

    def test_center_view_with_z_scale_greater_than_one(self, make_napari_viewer):
        """Test center_view when z-scale > 1.

        With z-scale = 2.0:
        - Segmentation pixel z=25 corresponds to world z=50
        """
        viewer = make_napari_viewer()

        graph = nx.DiGraph()
        # Node at world position [50, 50, 50]
        nodes = [
            (
                1,
                {
                    NodeAttr.POS.value: [50, 50, 50],  # world coords
                    NodeAttr.TIME.value: 0,
                    NodeAttr.AREA.value: 1000,
                },
            ),
        ]
        graph.add_nodes_from(nodes)

        # Segmentation with 50 pixels in z, scale=2 -> world z-extent 0-100
        segmentation = np.zeros((2, 50, 100, 100), dtype="int32")
        segmentation[0, 20:30, 45:55, 45:55] = 1  # pixel z=25, world z=50

        scale = [1.0, 2.0, 1.0, 1.0]
        tracks = SolutionTracks(
            graph=graph,
            segmentation=segmentation,
            scale=scale,
            ndim=4,
        )

        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Get the point index for node 1
        points_layer = tracks_viewer.tracking_layers.points_layer
        node_index = points_layer.node_index_dict[1]

        tracks_viewer.tracking_layers.center_view(node=1)

        # Verify viewer is positioned at world z=50
        new_point = viewer.dims.point
        assert abs(new_point[1] - 50) < 1, f"Expected world z≈50, got {new_point[1]}"

        # Verify point is visible using _indices_view
        visible_indices = points_layer._indices_view
        assert node_index in visible_indices, (
            f"Point index {node_index} not in visible indices {visible_indices}. "
            f"Viewer dims.point={viewer.dims.point}"
        )

    def test_center_view_with_image_layer_different_scale(self, make_napari_viewer):
        """Test center_view when image layer has different scale than tracks seg layer.

        Image layer: scale [1,1,1,1], 100 z-pixels -> world z 0-100
        Seg layer: scale [1,0.5,1,1], 100 z-pixels -> world z 0-50
        """
        viewer = make_napari_viewer()

        # Add an image layer with no scale (1.0 for all dims)
        image_data = np.random.rand(2, 100, 100, 100)
        viewer.add_image(image_data, name="raw_image")

        graph = nx.DiGraph()
        # Node at world z=25
        nodes = [
            (
                1,
                {
                    NodeAttr.POS.value: [25, 50, 50],
                    NodeAttr.TIME.value: 0,
                    NodeAttr.AREA.value: 1000,
                },
            ),
        ]
        graph.add_nodes_from(nodes)

        segmentation = np.zeros((2, 100, 100, 100), dtype="int32")
        segmentation[0, 45:55, 45:55, 45:55] = 1

        scale = [1.0, 0.5, 1.0, 1.0]
        tracks = SolutionTracks(
            graph=graph,
            segmentation=segmentation,
            scale=scale,
            ndim=4,
        )

        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Get the point index for node 1
        points_layer = tracks_viewer.tracking_layers.points_layer
        node_index = points_layer.node_index_dict[1]

        tracks_viewer.tracking_layers.center_view(node=1)

        # Verify viewer is positioned at world z=25
        new_point = viewer.dims.point
        assert abs(new_point[1] - 25) < 1, f"Expected world z≈25, got {new_point[1]}"

        # Verify point is visible using _indices_view
        visible_indices = points_layer._indices_view
        assert node_index in visible_indices, (
            f"Point index {node_index} not in visible indices {visible_indices}. "
            f"Viewer dims.point={viewer.dims.point}"
        )

    def test_center_view_no_scale(self, make_napari_viewer):
        """Test center_view when no scale is set (defaults to 1.0)."""
        viewer = make_napari_viewer()

        graph = nx.DiGraph()
        nodes = [
            (
                1,
                {
                    NodeAttr.POS.value: [50, 50, 50],
                    NodeAttr.TIME.value: 0,
                    NodeAttr.AREA.value: 1000,
                },
            ),
        ]
        graph.add_nodes_from(nodes)

        segmentation = np.zeros((2, 100, 100, 100), dtype="int32")
        segmentation[0, 45:55, 45:55, 45:55] = 1

        tracks = SolutionTracks(
            graph=graph,
            segmentation=segmentation,
            ndim=4,
        )

        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Get the point index for node 1
        points_layer = tracks_viewer.tracking_layers.points_layer
        node_index = points_layer.node_index_dict[1]

        tracks_viewer.tracking_layers.center_view(node=1)

        # With no scale, world coords = pixel coords
        new_point = viewer.dims.point
        assert new_point[0] == 0  # time
        assert new_point[1] == 50  # z
        assert new_point[2] == 50  # y
        assert new_point[3] == 50  # x

        # Verify point is visible using _indices_view
        visible_indices = points_layer._indices_view
        assert node_index in visible_indices, (
            f"Point index {node_index} not in visible indices {visible_indices}. "
            f"Viewer dims.point={viewer.dims.point}"
        )

    def test_center_view_no_segmentation_with_scaled_image(self, make_napari_viewer):
        """Test center_view when there is no segmentation, only points and an image layer.

        Image layer: scale [1, 0.5, 1, 1], 100 z-pixels -> world z 0-50
        Points: in world coordinates at z=25
        No segmentation layer.
        """
        viewer = make_napari_viewer()

        # Add image layer with z-scale=0.5
        image_data = np.random.rand(2, 100, 100, 100)
        viewer.add_image(image_data, name="raw_image", scale=[1.0, 0.5, 1.0, 1.0])

        graph = nx.DiGraph()
        # Node at world position [25, 50, 50]
        nodes = [
            (
                1,
                {
                    NodeAttr.POS.value: [25, 50, 50],  # world coords
                    NodeAttr.TIME.value: 0,
                    NodeAttr.AREA.value: 1000,
                },
            ),
        ]
        graph.add_nodes_from(nodes)

        # No segmentation
        tracks = SolutionTracks(
            graph=graph,
            segmentation=None,
            scale=[1.0, 0.5, 1.0, 1.0],
            ndim=4,
        )

        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Get the point index for node 1
        points_layer = tracks_viewer.tracking_layers.points_layer
        node_index = points_layer.node_index_dict[1]

        tracks_viewer.tracking_layers.center_view(node=1)

        # Verify viewer is positioned at world z=25
        new_point = viewer.dims.point
        assert abs(new_point[1] - 25) < 1, f"Expected world z≈25, got {new_point[1]}"

        # Verify point is visible using _indices_view
        visible_indices = points_layer._indices_view
        assert node_index in visible_indices, (
            f"Point index {node_index} not in visible indices {visible_indices}. "
            f"Viewer dims.point={viewer.dims.point}"
        )

    def test_center_view_no_segmentation_mismatched_scales(self, make_napari_viewer):
        """Test center_view with no segmentation and mismatched image/points scales.

        Image layer: scale [1, 1, 1, 1], 100 z-pixels -> world z 0-100
        Points: scale [1, 0.5, 1, 1], positions at world z=25
        No segmentation layer.

        This tests the case where the image and points have different scales,
        which affects how dims.range is computed.
        """
        viewer = make_napari_viewer()

        # Add image layer with no z-scale (1.0)
        image_data = np.random.rand(2, 100, 100, 100)
        viewer.add_image(image_data, name="raw_image")

        graph = nx.DiGraph()
        # Node at world position [25, 50, 50]
        nodes = [
            (
                1,
                {
                    NodeAttr.POS.value: [25, 50, 50],  # world coords
                    NodeAttr.TIME.value: 0,
                    NodeAttr.AREA.value: 1000,
                },
            ),
        ]
        graph.add_nodes_from(nodes)

        # No segmentation, but tracks have scale
        tracks = SolutionTracks(
            graph=graph,
            segmentation=None,
            scale=[1.0, 0.5, 1.0, 1.0],
            ndim=4,
        )

        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Get the point index for node 1
        points_layer = tracks_viewer.tracking_layers.points_layer
        node_index = points_layer.node_index_dict[1]

        tracks_viewer.tracking_layers.center_view(node=1)

        # Verify viewer is positioned at world z=25
        new_point = viewer.dims.point
        assert abs(new_point[1] - 25) < 1, f"Expected world z≈25, got {new_point[1]}"

        # Verify point is visible using _indices_view
        visible_indices = points_layer._indices_view
        assert node_index in visible_indices, (
            f"Point index {node_index} not in visible indices {visible_indices}. "
            f"Viewer dims.point={viewer.dims.point}"
        )

    def test_center_view_syncs_ortho_views(self, make_napari_viewer, qtbot):
        """Test that center_view properly syncs ortho views so points are visible.

        When center_view is called, the ortho views should also update their
        dims.current_step so that the point is visible in all views.
        """
        viewer = make_napari_viewer()

        # Initialize orthogonal views
        ortho_manager = initialize_ortho_views(viewer)

        graph = nx.DiGraph()
        # Node at world position [25, 50, 50]
        nodes = [
            (
                1,
                {
                    NodeAttr.POS.value: [25, 50, 50],  # world coords
                    NodeAttr.TIME.value: 0,
                    NodeAttr.AREA.value: 1000,
                },
            ),
        ]
        graph.add_nodes_from(nodes)

        segmentation = np.zeros((2, 100, 100, 100), dtype="int32")
        segmentation[0, 45:55, 45:55, 45:55] = 1

        scale = [1.0, 0.5, 1.0, 1.0]  # z-scale = 0.5
        tracks = SolutionTracks(
            graph=graph,
            segmentation=segmentation,
            scale=scale,
            ndim=4,
        )

        # Show orthogonal views BEFORE adding tracks so they get the layers
        ortho_manager.show()
        qtbot.waitUntil(lambda: ortho_manager.is_shown(), timeout=1000)

        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Wait for layers to sync to ortho views
        qtbot.wait(50)

        # Get the point index for node 1 from main points layer
        main_points_layer = tracks_viewer.tracking_layers.points_layer
        node_index = main_points_layer.node_index_dict[1]

        # Center on the node
        tracks_viewer.tracking_layers.center_view(node=1)

        # Wait for Qt event loop to process the dims sync
        qtbot.wait(50)

        # Verify main viewer point is visible
        main_visible = main_points_layer._indices_view
        assert node_index in main_visible, (
            f"Point not visible in main viewer. "
            f"Index {node_index} not in {main_visible}"
        )

        # Get ortho view points layers and verify point is visible in each
        right_vm = ortho_manager.right_widget.vm_container.viewer_model
        bottom_vm = ortho_manager.bottom_widget.vm_container.viewer_model
        right_points = right_vm.layers[-1]
        bottom_points = bottom_vm.layers[-1]

        # The ortho views use copied Points layers (not TrackPoints), so we check
        # _indices_view on those as well
        right_visible = right_points._indices_view
        bottom_visible = bottom_points._indices_view

        assert node_index in right_visible, (
            f"Point not visible in right ortho view. "
            f"Index {node_index} not in {right_visible}. "
            f"Ortho dims.point={right_vm.dims.point}"
        )
        assert node_index in bottom_visible, (
            f"Point not visible in bottom ortho view. "
            f"Index {node_index} not in {bottom_visible}. "
            f"Ortho dims.point={bottom_vm.dims.point}"
        )

        ortho_manager.cleanup()
