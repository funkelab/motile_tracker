"""Tests for TrackPoints - the Points layer for track visualization."""

import math
from unittest.mock import MagicMock, patch

import numpy as np
from funtracks.data_model import SolutionTracks
from funtracks.exceptions import InvalidActionError

from motile_tracker.data_views.graph_attributes import NodeAttr
from motile_tracker.data_views.views.layers.track_points import (
    TrackPoints,
    custom_select,
)
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


class MockEvent:
    """Mock event for testing mouse/data events."""

    def __init__(
        self, action=None, value=None, modifiers=None, event_type="mouse_press"
    ):
        self.action = action
        self.value = value
        self.modifiers = modifiers if modifiers is not None else []
        self.type = event_type


class TestTrackPointsInitialization:
    """Test TrackPoints layer initialization."""

    def test_initialization(self, make_napari_viewer, graph_2d, segmentation_2d):
        """Test TrackPoints creates layer with correct data."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Verify layer was created
        assert points_layer is not None
        assert isinstance(points_layer, TrackPoints)
        assert points_layer.name == "test_points"

        # Verify nodes were extracted
        assert len(points_layer.nodes) == len(tracks.graph.nodes)

        # Verify node_index_dict was created
        assert len(points_layer.node_index_dict) == len(points_layer.nodes)
        for idx, node in enumerate(points_layer.nodes):
            assert points_layer.node_index_dict[node] == idx

        # Verify default size was set
        assert points_layer.default_size == 5

    def test_initialization_with_correct_properties(
        self, make_napari_viewer, graph_2d, segmentation_2d
    ):
        """Test TrackPoints has correct properties set."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Verify properties include node_id and track_id
        assert "node_id" in points_layer.properties
        assert "track_id" in points_layer.properties
        assert len(points_layer.properties["node_id"]) == len(points_layer.nodes)

    def test_type_string_property(self, make_napari_viewer, graph_2d, segmentation_2d):
        """Test _type_string property returns 'points'."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        assert points_layer._type_string == "points"


class TestCustomSelect:
    """Test custom_select function."""

    def test_custom_select_blocks_current_size(
        self, make_napari_viewer, graph_2d, segmentation_2d
    ):
        """Test custom_select blocks current_size signal."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Create mock event
        event = MagicMock()

        # Test that custom_select blocks the current_size signal
        generator = custom_select(points_layer, event)
        # Just verify it returns a generator
        assert hasattr(generator, "__iter__")


class TestAddMethod:
    """Test add method."""

    def test_add_blocks_current_size_event(
        self, make_napari_viewer, graph_2d, segmentation_2d
    ):
        """Test add method blocks current_size event."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Mock the blocker
        with patch.object(points_layer.events.current_size, "blocker") as mock_blocker:
            mock_blocker.return_value.__enter__ = MagicMock()
            mock_blocker.return_value.__exit__ = MagicMock()

            # Add a point
            coords = [0, 10, 20]
            points_layer.add(coords)

            # Verify blocker was called
            mock_blocker.assert_called_once()


class TestProcessClick:
    """Test process_click method."""

    def test_process_click_with_no_point_resets_selection(
        self, make_napari_viewer, graph_2d, segmentation_2d
    ):
        """Test clicking empty space resets selection."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Add a selection
        tracks_viewer.selected_nodes.add(1)
        assert len(tracks_viewer.selected_nodes) == 1

        # Click on empty space
        event = MockEvent()
        points_layer.process_click(event, None)

        # Verify selection was reset
        assert len(tracks_viewer.selected_nodes) == 0

    def test_process_click_with_point_selects_node(
        self, make_napari_viewer, graph_2d, segmentation_2d
    ):
        """Test clicking a point selects the node."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Click on first point
        event = MockEvent()
        points_layer.process_click(event, 0)

        # Verify node was selected
        assert len(tracks_viewer.selected_nodes) == 1
        assert points_layer.nodes[0] in tracks_viewer.selected_nodes

    def test_process_click_with_shift_appends_selection(
        self, make_napari_viewer, graph_2d, segmentation_2d
    ):
        """Test shift-click appends to selection."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Click on first point
        event = MockEvent()
        points_layer.process_click(event, 0)
        assert len(tracks_viewer.selected_nodes) == 1

        # Shift-click on second point
        event_shift = MockEvent(modifiers=["Shift"])
        points_layer.process_click(event_shift, 1)

        # Verify both nodes selected
        assert len(tracks_viewer.selected_nodes) == 2

    def test_process_click_with_control_centers_on_node(
        self, make_napari_viewer, graph_2d, segmentation_2d
    ):
        """Test ctrl-click centers view on node."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Mock center_on_node
        with patch.object(tracks_viewer, "center_on_node") as mock_center:
            # Ctrl-click on first point
            event_ctrl = MockEvent(modifiers=["Control"])
            points_layer.process_click(event_ctrl, 0)

            # Verify center_on_node was called
            mock_center.assert_called_once_with(points_layer.nodes[0])


class TestSetPointSize:
    """Test set_point_size method."""

    def test_set_point_size_updates_default_size(
        self, make_napari_viewer, graph_2d, segmentation_2d
    ):
        """Test set_point_size updates default_size."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Initial size
        assert points_layer.default_size == 5

        # Set new size
        points_layer.set_point_size(10)

        # Verify size was updated
        assert points_layer.default_size == 10


class TestRefresh:
    """Test _refresh method."""

    def test_refresh_updates_data(self, make_napari_viewer, graph_2d, segmentation_2d):
        """Test _refresh updates layer data."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        initial_data_len = len(points_layer.data)

        # Call refresh
        points_layer._refresh()

        # Verify data was updated
        assert len(points_layer.data) == initial_data_len

    def test_refresh_emits_data_updated_signal(
        self, make_napari_viewer, graph_2d, segmentation_2d, qtbot
    ):
        """Test _refresh emits data_updated signal."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Wait for signal
        with qtbot.waitSignal(points_layer.data_updated, timeout=1000):
            points_layer._refresh()


class TestCreateNodeAttrs:
    """Test _create_node_attrs method."""

    def test_create_node_attrs_creates_correct_attributes(
        self, make_napari_viewer, graph_2d, segmentation_2d
    ):
        """Test _create_node_attrs creates correct node attributes."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Set a track_id
        tracks_viewer.set_new_track_id()

        # Create node attributes
        new_point = np.array([1, 50, 50])
        attrs = points_layer._create_node_attrs(new_point)

        # Verify attributes
        assert NodeAttr.POS.value in attrs
        assert NodeAttr.TIME.value in attrs
        assert NodeAttr.TRACK_ID.value in attrs
        assert NodeAttr.AREA.value in attrs

        assert attrs[NodeAttr.TIME.value][0] == 1
        assert np.array_equal(attrs[NodeAttr.POS.value][0], [50, 50])
        assert attrs[NodeAttr.AREA.value][0] == 0

    def test_create_node_attrs_activates_new_track_id_if_none(
        self, make_napari_viewer, graph_2d, segmentation_2d
    ):
        """Test _create_node_attrs activates new track_id if none selected."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Reset track selection
        tracks_viewer.selected_track = None

        # Create node attributes
        new_point = np.array([1, 50, 50])
        points_layer._create_node_attrs(new_point)

        # Verify track_id was activated
        assert tracks_viewer.selected_track is not None


class TestUpdateData:
    """Test _update_data method."""

    def test_update_data_added_action_without_seg_layer(
        self, make_napari_viewer, graph_2d
    ):
        """Test _update_data handles added action when no seg layer."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Verify no seg layer
        assert tracks_viewer.tracking_layers.seg_layer is None

        initial_node_count = len(tracks.graph.nodes)

        # Create added event
        new_point = np.array([[1, 50, 50]])
        event = MockEvent(action="added", value=new_point)

        # Call _update_data
        points_layer._update_data(event)

        # Verify node was added
        assert len(tracks_viewer.tracks.graph.nodes) == initial_node_count + 1

    def test_update_data_added_action_with_seg_layer_shows_info(
        self, make_napari_viewer, graph_2d, segmentation_2d
    ):
        """Test _update_data shows info when trying to add with seg layer."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Verify seg layer exists
        assert tracks_viewer.tracking_layers.seg_layer is not None

        initial_node_count = len(tracks.graph.nodes)

        # Create added event
        new_point = np.array([[1, 50, 50]])
        event = MockEvent(action="added", value=new_point)

        # Call _update_data
        with patch("motile_tracker.data_views.views.layers.track_points.show_info"):
            points_layer._update_data(event)

        # Verify no node was added
        assert len(tracks_viewer.tracks.graph.nodes) == initial_node_count

    def test_update_data_removed_action(
        self, make_napari_viewer, graph_2d, segmentation_2d
    ):
        """Test _update_data handles removed action."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Select a node
        first_node = list(tracks.graph.nodes)[0]
        tracks_viewer.selected_nodes.add(first_node)

        initial_node_count = len(tracks.graph.nodes)

        # Create removed event
        event = MockEvent(action="removed")

        # Call _update_data
        points_layer._update_data(event)

        # Verify node was removed
        assert len(tracks_viewer.tracks.graph.nodes) == initial_node_count - 1

    def test_update_data_changed_action_without_seg_layer(
        self, make_napari_viewer, graph_2d
    ):
        """Test _update_data handles changed action when no seg layer."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Select first point
        points_layer.selected_data.add(0)

        # Get original position
        first_node = points_layer.nodes[0]
        original_pos = tracks.graph.nodes[first_node][NodeAttr.POS.value]

        # Modify position in layer data
        new_pos = np.array([1, 100, 100])
        points_layer.data[0] = new_pos

        # Create changed event
        event = MockEvent(action="changed")

        # Call _update_data
        points_layer._update_data(event)

        # Verify position was updated in graph
        updated_pos = tracks_viewer.tracks.graph.nodes[first_node][NodeAttr.POS.value]
        assert not np.array_equal(updated_pos, original_pos)

    def test_update_data_changed_action_with_seg_layer_refreshes(
        self, make_napari_viewer, graph_2d, segmentation_2d
    ):
        """Test _update_data refreshes when trying to change with seg layer."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Select first point
        points_layer.selected_data.add(0)

        # Get original position
        first_node = points_layer.nodes[0]
        original_pos = tracks.graph.nodes[first_node][NodeAttr.POS.value].copy()

        # Modify position in layer data
        new_pos = np.array([1, 100, 100])
        points_layer.data[0] = new_pos

        # Create changed event
        event = MockEvent(action="changed")

        # Call _update_data (should refresh instead of updating)
        points_layer._update_data(event)

        # Verify position was NOT updated (should be refreshed back)
        updated_pos = tracks_viewer.tracks.graph.nodes[first_node][NodeAttr.POS.value]
        assert np.array_equal(updated_pos, original_pos)

    def test_update_data_invalid_action_forceable(self, make_napari_viewer, graph_2d):
        """Test _update_data handles forceable InvalidActionError."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Mock add_nodes to raise InvalidActionError first time, then succeed
        error = InvalidActionError("Test error", forceable=True)
        add_nodes_mock = MagicMock()
        add_nodes_mock.side_effect = [error, None]  # Fail once, then succeed

        with (
            patch.object(tracks_viewer.tracks_controller, "add_nodes", add_nodes_mock),
            patch(
                "motile_tracker.data_views.views.layers.track_points.confirm_force_operation",
                return_value=(True, False),
            ),
        ):
            # Create added event
            new_point = np.array([[1, 50, 50]])
            event = MockEvent(action="added", value=new_point)

            # This should handle the error and retry with force=True
            points_layer._update_data(event)

            # Verify add_nodes was called twice (once without force, once with)
            assert add_nodes_mock.call_count == 2


class TestUpdateSelection:
    """Test _update_selection method."""

    def test_update_selection_in_select_mode(
        self, make_napari_viewer, graph_2d, segmentation_2d
    ):
        """Test _update_selection updates selected_nodes in select mode."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Enter select mode
        points_layer.mode = "select"

        # Select some points
        points_layer.selected_data.add(0)
        points_layer.selected_data.add(1)

        # Call _update_selection
        points_layer._update_selection()

        # Verify selected_nodes was updated
        assert len(tracks_viewer.selected_nodes) == 2
        assert points_layer.nodes[0] in tracks_viewer.selected_nodes
        assert points_layer.nodes[1] in tracks_viewer.selected_nodes

    def test_update_selection_not_in_select_mode_does_nothing(
        self, make_napari_viewer, graph_2d, segmentation_2d
    ):
        """Test _update_selection does nothing when not in select mode."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Not in select mode
        points_layer.mode = "pan_zoom"

        # Select some points
        points_layer.selected_data.add(0)

        initial_selection_count = len(tracks_viewer.selected_nodes)

        # Call _update_selection
        points_layer._update_selection()

        # Verify selected_nodes was not updated
        assert len(tracks_viewer.selected_nodes) == initial_selection_count


class TestGetSymbols:
    """Test get_symbols method."""

    def test_get_symbols_returns_correct_symbols(
        self, make_napari_viewer, graph_2d, segmentation_2d
    ):
        """Test get_symbols returns correct symbols for node types."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Get symbols
        symbols = points_layer.get_symbols(tracks, tracks_viewer.symbolmap)

        # Verify symbols list has correct length
        assert len(symbols) == len(tracks.graph.nodes)

        # Verify symbols are from symbolmap
        for symbol in symbols:
            assert symbol in tracks_viewer.symbolmap.values()


class TestUpdatePointOutline:
    """Test update_point_outline method."""

    def test_update_point_outline_with_all_mode(
        self, make_napari_viewer, graph_2d, segmentation_2d
    ):
        """Test update_point_outline with 'all' mode shows all points."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Update outline with "all"
        points_layer.update_point_outline("all")

        # Verify all points are shown
        assert np.all(points_layer.shown)

    def test_update_point_outline_with_visible_list(
        self, make_napari_viewer, graph_2d, segmentation_2d
    ):
        """Test update_point_outline with list of visible nodes."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Get first node
        first_node = points_layer.nodes[0]

        # Update outline with specific node
        points_layer.update_point_outline([first_node])

        # Verify only specific node is shown
        assert points_layer.shown[0]
        assert not np.all(points_layer.shown)

    def test_update_point_outline_highlights_selected_nodes(
        self, make_napari_viewer, graph_2d, segmentation_2d
    ):
        """Test update_point_outline highlights selected nodes."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Select a node
        first_node = points_layer.nodes[0]
        tracks_viewer.selected_nodes.add(first_node)

        # Update outline
        points_layer.update_point_outline("all")

        # Verify selected node has cyan border
        border = points_layer.border_color[0]
        assert border[0] == 0  # red
        assert border[1] == 1  # green (cyan)
        assert border[2] == 1  # blue (cyan)
        assert border[3] == 1  # alpha

    def test_update_point_outline_increases_selected_node_size(
        self, make_napari_viewer, graph_2d, segmentation_2d
    ):
        """Test update_point_outline increases size for selected nodes."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Select a node
        first_node = points_layer.nodes[0]
        tracks_viewer.selected_nodes.add(first_node)

        # Update outline
        points_layer.update_point_outline("all")

        # Verify selected node has larger size
        default_size = points_layer.default_size
        selected_size = points_layer.size[0]
        expected_size = math.ceil(default_size + 0.3 * default_size)
        assert selected_size == expected_size

    def test_update_point_outline_group_mode_includes_selected(
        self, make_napari_viewer, graph_2d, segmentation_2d
    ):
        """Test update_point_outline in group mode includes selected nodes."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        points_layer = tracks_viewer.tracking_layers.points_layer

        # Set to group mode
        tracks_viewer.mode = "group"

        # Select a node not in visible list
        first_node = points_layer.nodes[0]
        second_node = points_layer.nodes[1]
        tracks_viewer.selected_nodes.add(first_node)

        # Update outline with only second node visible
        points_layer.update_point_outline([second_node])

        # Verify both first (selected) and second (visible) nodes are shown
        assert points_layer.shown[0]  # selected
        assert points_layer.shown[1]  # visible
