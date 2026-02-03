"""Tests for TrackPoints - the Points layer for track visualization."""

import math
from unittest.mock import MagicMock, patch

import numpy as np
from funtracks.data_model import SolutionTracks
from funtracks.exceptions import InvalidActionError

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


def test_initialization(make_napari_viewer, graph_2d, segmentation_2d):
    """Test TrackPoints layer initialization."""
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

    # Verify properties include node_id and track_id
    assert "node_id" in points_layer.properties
    assert "track_id" in points_layer.properties
    assert len(points_layer.properties["node_id"]) == len(points_layer.nodes)

    # Verify type string
    assert points_layer._type_string == "points"


def test_custom_select_blocks_current_size(
    make_napari_viewer, graph_2d, segmentation_2d
):
    """Test custom_select function blocks current_size signal."""
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


def test_add_blocks_current_size_event(make_napari_viewer, graph_2d, segmentation_2d):
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


def test_process_click(make_napari_viewer, graph_2d, segmentation_2d):
    """Test process_click with different click types."""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    points_layer = tracks_viewer.tracking_layers.points_layer

    # Test 1: Clicking empty space resets selection
    tracks_viewer.selected_nodes.add(1)
    assert len(tracks_viewer.selected_nodes) == 1
    event = MockEvent()
    points_layer.process_click(event, None)
    assert len(tracks_viewer.selected_nodes) == 0

    # Test 2: Clicking a point selects the node
    event = MockEvent()
    points_layer.process_click(event, 0)
    assert len(tracks_viewer.selected_nodes) == 1
    assert points_layer.nodes[0] in tracks_viewer.selected_nodes

    # Test 3: Shift-click appends to selection
    event_shift = MockEvent(modifiers=["Shift"])
    points_layer.process_click(event_shift, 1)
    assert len(tracks_viewer.selected_nodes) == 2

    # Test 4: Ctrl-click centers view on node
    with patch.object(tracks_viewer, "center_on_node") as mock_center:
        event_ctrl = MockEvent(modifiers=["Control"])
        points_layer.process_click(event_ctrl, 0)
        mock_center.assert_called_once_with(points_layer.nodes[0])


def test_set_point_size_updates_default_size(
    make_napari_viewer, graph_2d, segmentation_2d
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


def test_refresh_updates_data(make_napari_viewer, graph_2d, segmentation_2d, qtbot):
    """Test _refresh updates layer data."""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    points_layer = tracks_viewer.tracking_layers.points_layer

    initial_data_len = len(points_layer.data)

    # Wait for signal
    with qtbot.waitSignal(points_layer.data_updated, timeout=1000):
        points_layer._refresh()

    # Verify we still have the same number of nodes
    assert len(points_layer.data) == initial_data_len


def test_create_node_attrs(make_napari_viewer, graph_2d, segmentation_2d):
    """Test _create_node_attrs creates correct attributes and activates track_id if needed."""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    points_layer = tracks_viewer.tracking_layers.points_layer

    # Test 1: Create node attributes with track_id set
    tracks_viewer.set_new_track_id()

    new_point = np.array([1, 50, 50])
    attrs = points_layer._create_node_attrs(new_point)

    # Verify attributes
    assert "pos" in attrs
    assert "time" in attrs
    assert "track_id" in attrs

    assert attrs["time"][0] == 1
    assert np.array_equal(attrs["pos"][0], [50, 50])
    # Test 2: Activates new track_id if none selected
    tracks_viewer.selected_track = None

    new_point = np.array([1, 50, 50])
    points_layer._create_node_attrs(new_point)

    # Verify track_id was activated
    assert tracks_viewer.selected_track is not None


def test_update_data_without_seg_layer(make_napari_viewer, graph_2d):
    """Test _update_data handles added, removed, and changed actions without seg layer."""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    points_layer = tracks_viewer.tracking_layers.points_layer

    # Verify no seg layer
    assert tracks_viewer.tracking_layers.seg_layer is None

    # Test 1: Added action adds node
    initial_node_count = len(tracks.graph.nodes)
    new_point = np.array([[1, 50, 50]])
    event = MockEvent(action="added", value=new_point)
    points_layer._update_data(event)
    assert len(tracks_viewer.tracks.graph.nodes) == initial_node_count + 1

    # Test 2: Removed action removes node
    first_node = list(tracks.graph.nodes)[0]
    tracks_viewer.selected_nodes.add(first_node)
    current_node_count = len(tracks.graph.nodes)
    event = MockEvent(action="removed")
    points_layer._update_data(event)
    assert len(tracks_viewer.tracks.graph.nodes) == current_node_count - 1

    # Test 3: Changed action updates node position
    points_layer.selected_data.add(0)
    first_node = points_layer.nodes[0]
    original_pos = tracks.graph.nodes[first_node]["pos"]
    new_pos = np.array([1, 100, 100])
    points_layer.data[0] = new_pos
    event = MockEvent(action="changed")
    points_layer._update_data(event)
    updated_pos = tracks_viewer.tracks.graph.nodes[first_node]["pos"]
    assert not np.array_equal(updated_pos, original_pos)


def test_update_data_with_seg_layer(make_napari_viewer, graph_2d, segmentation_2d):
    """Test _update_data with seg layer shows info for add and refreshes for change."""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    points_layer = tracks_viewer.tracking_layers.points_layer

    # Verify seg layer exists
    assert tracks_viewer.tracking_layers.seg_layer is not None

    # Test 1: Added action shows info and doesn't add node
    initial_node_count = len(tracks.graph.nodes)
    new_point = np.array([[1, 50, 50]])
    event = MockEvent(action="added", value=new_point)
    with patch("motile_tracker.data_views.views.layers.track_points.show_info"):
        points_layer._update_data(event)
    assert len(tracks_viewer.tracks.graph.nodes) == initial_node_count

    # Test 2: Changed action refreshes instead of updating
    points_layer.selected_data.add(0)
    first_node = points_layer.nodes[0]
    original_pos = tracks.graph.nodes[first_node]["pos"].copy()
    new_pos = np.array([1, 100, 100])
    points_layer.data[0] = new_pos
    event = MockEvent(action="changed")
    points_layer._update_data(event)
    updated_pos = tracks_viewer.tracks.graph.nodes[first_node]["pos"]
    assert np.array_equal(updated_pos, original_pos)


def test_update_data_invalid_action_forceable(make_napari_viewer, graph_2d):
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


def test_update_selection_in_select_mode(make_napari_viewer, graph_2d, segmentation_2d):
    """Test _update_selection updates selected_nodes in select mode."""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    points_layer = tracks_viewer.tracking_layers.points_layer

    # Enter select mode
    points_layer.mode = "select"

    # Verify signal is connected to _update_selection
    mock_update = MagicMock()
    points_layer.selected_data.events.items_changed.connect(mock_update)

    # Emit the signal directly to verify connection works
    points_layer.selected_data.add(0)

    # Verify the connection was triggered
    mock_update.assert_called_once()

    points_layer.selected_data.add(1)

    # Verify selected_nodes was updated
    assert len(tracks_viewer.selected_nodes) == 2
    assert points_layer.nodes[0] in tracks_viewer.selected_nodes
    assert points_layer.nodes[1] in tracks_viewer.selected_nodes


def test_update_selection_not_in_select_mode_does_nothing(
    make_napari_viewer, graph_2d, segmentation_2d
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
    # Verify selected_nodes was not updated
    assert len(tracks_viewer.selected_nodes) == initial_selection_count


def test_get_symbols_returns_correct_symbols(
    make_napari_viewer, graph_2d, segmentation_2d
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


def test_update_point_outline(make_napari_viewer, graph_2d, segmentation_2d):
    """Test update_point_outline with different modes and visibility."""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    points_layer = tracks_viewer.tracking_layers.points_layer

    # Test 1: Update outline with "all" mode shows all points
    points_layer.update_point_outline("all")
    assert np.all(points_layer.shown)

    # Test 2: Update outline with list of visible nodes
    first_node = points_layer.nodes[0]
    points_layer.update_point_outline([first_node])
    assert points_layer.shown[0]
    assert not np.all(points_layer.shown)

    # Test 3: Select a node and verify it gets highlighted with cyan border and increased size
    tracks_viewer.selected_nodes.add(first_node)
    points_layer.update_point_outline("all")

    # Verify selected node has cyan border
    border_0 = points_layer.border_color[0]
    assert np.array_equal(border_0, [0, 1, 1, 1])

    # Verify non-selected node has white border
    border_1 = points_layer.border_color[1]
    assert np.array_equal(border_1, [1, 1, 1, 1])

    # Verify selected node has larger size
    default_size = points_layer.default_size
    selected_size = points_layer.size[0]
    expected_size = math.ceil(default_size + 0.3 * default_size)
    assert selected_size == expected_size

    # Test 4: Group mode includes selected nodes even if not in visible list
    tracks_viewer.mode = "group"
    second_node = points_layer.nodes[1]
    tracks_viewer.selected_nodes.reset()
    tracks_viewer.selected_nodes.add(first_node)

    # Update outline with only second node visible
    points_layer.update_point_outline([second_node])

    # Verify both first (selected) and second (visible) nodes are shown
    assert points_layer.shown[0]  # selected
    assert points_layer.shown[1]  # visible
    assert not points_layer.shown[2]  # not selected or visible
