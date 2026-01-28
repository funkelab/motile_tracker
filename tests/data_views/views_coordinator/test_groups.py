"""Tests for CollectionButton and CollectionWidget - group management UI.

Tests cover button states, group creation/deletion, node/track/lineage operations,
selection operations, and export functionality.
"""

from unittest.mock import MagicMock, patch

from funtracks.data_model import SolutionTracks
from PyQt6.QtCore import Qt

from motile_tracker.data_views.views_coordinator.groups import (
    CollectionButton,
    CollectionWidget,
)
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


def test_collection_button(make_napari_viewer):
    """Test CollectionButton widget initialization, node count updates, and size."""
    make_napari_viewer()  # Create Qt context
    button = CollectionButton("test_group")

    # Test 1: Verify initialization and UI elements
    assert button.name.text() == "test_group"
    assert button.name.height() == 20

    # Verify collection starts empty
    assert len(button.collection) == 0
    assert isinstance(button.collection, set)

    # Verify node count label
    assert button.node_count.text() == "0 nodes"

    # Verify buttons exist
    assert button.delete is not None
    assert button.export is not None
    assert button.export.toolTip() == "Export nodes in this group to CSV or geff"

    # Test 2: Update node count with multiple nodes
    button.collection = {1, 2, 3, 4, 5}
    button.update_node_count()
    assert button.node_count.text() == "5 nodes"

    # Remove some nodes
    button.collection = {1, 2}
    button.update_node_count()
    assert button.node_count.text() == "2 nodes"

    # Test 3: Size hint returns correct height
    hint = button.sizeHint()
    assert hint.height() == 30


def test_collection_widget_initialization(make_napari_viewer, graph_2d):
    """Test CollectionWidget initializes correctly and has correct initial button states."""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    widget = CollectionWidget(tracks_viewer)

    # Test 1: Verify initialization
    assert widget.tracks_viewer == tracks_viewer
    assert widget.collection_list is not None
    assert widget.selected_collection is None

    # Verify buttons exist
    assert widget.select_btn is not None
    assert widget.invert_btn is not None
    assert widget.deselect_btn is not None
    assert widget.reselect_btn is not None
    assert widget.add_nodes_btn is not None
    assert widget.remove_node_btn is not None
    assert widget.new_group_button is not None

    # Test 2: Initial button states when no groups exist
    # Edit buttons should be disabled (no group selected)
    assert not widget.add_nodes_btn.isEnabled()
    assert not widget.remove_node_btn.isEnabled()
    assert not widget.select_btn.isEnabled()

    # Selection buttons should be disabled (no nodes selected)
    assert not widget.deselect_btn.isEnabled()
    assert not widget.jump_to_next_btn.isEnabled()
    assert not widget.jump_to_previous_btn.isEnabled()

    # New group button should be enabled (tracks exist)
    assert widget.new_group_button.isEnabled()


def test_group_creation_and_deletion(make_napari_viewer, graph_2d, qtbot):
    """Test creating groups (including duplicates) and deleting groups."""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    widget = CollectionWidget(tracks_viewer)

    # Test 1: Create a new group
    widget.group_name.setText("my_test_group")
    qtbot.mouseClick(widget.new_group_button, Qt.MouseButton.LeftButton)

    assert widget.collection_list.count() == 1

    # Verify group name
    item = widget.collection_list.item(0)
    button = widget.collection_list.itemWidget(item)
    assert button.name.text() == "my_test_group"

    # Verify feature was added to tracks
    assert "my_test_group" in tracks_viewer.tracks.features
    feature = tracks_viewer.tracks.features["my_test_group"]
    assert feature["value_type"] == "bool"
    assert feature["feature_type"] == "node"

    # Test 2: Create group with duplicate name appends _1
    widget.group_name.setText("duplicate")
    qtbot.mouseClick(widget.new_group_button, Qt.MouseButton.LeftButton)

    widget.group_name.setText("duplicate")
    qtbot.mouseClick(widget.new_group_button, Qt.MouseButton.LeftButton)

    # Verify both groups exist with different names
    assert widget.collection_list.count() == 3

    item1 = widget.collection_list.item(1)
    button1 = widget.collection_list.itemWidget(item1)
    assert button1.name.text() == "duplicate"

    item2 = widget.collection_list.item(2)
    button2 = widget.collection_list.itemWidget(item2)
    assert button2.name.text() == "duplicate_1"

    # Test 3: Delete a group
    widget.group_name.setText("to_delete")
    qtbot.mouseClick(widget.new_group_button, Qt.MouseButton.LeftButton)

    assert widget.collection_list.count() == 4
    assert "to_delete" in tracks_viewer.tracks.features

    # Delete the group
    item = widget.collection_list.item(3)
    button = widget.collection_list.itemWidget(item)
    qtbot.mouseClick(button.delete, Qt.MouseButton.LeftButton)

    # Verify group was removed
    assert widget.collection_list.count() == 3
    assert "to_delete" not in tracks_viewer.tracks.features


def test_button_states(make_napari_viewer, graph_2d, qtbot):
    """Test button enable/disable states based on selection and group state."""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    widget = CollectionWidget(tracks_viewer)

    # Test 1: Navigation buttons initially disabled
    assert not widget.deselect_btn.isEnabled()
    assert not widget.jump_to_next_btn.isEnabled()
    assert not widget.jump_to_previous_btn.isEnabled()

    # Select nodes - navigation buttons now enabled
    tracks_viewer.selected_nodes.add_list([1, 2], append=False)
    assert widget.deselect_btn.isEnabled()
    assert widget.jump_to_next_btn.isEnabled()
    assert widget.jump_to_previous_btn.isEnabled()

    # Test 2: Edit buttons enabled when group selected and nodes selected
    # Create a group
    widget.group_name.setText("test_group")
    qtbot.mouseClick(widget.new_group_button, Qt.MouseButton.LeftButton)

    # Verify edit buttons are enabled
    assert widget.add_nodes_btn.isEnabled()
    assert widget.add_track_btn.isEnabled()
    assert widget.add_lineage_btn.isEnabled()
    assert widget.remove_node_btn.isEnabled()
    assert widget.remove_track_btn.isEnabled()
    assert widget.remove_lineage_btn.isEnabled()

    # Test 3: Select button only enabled when selected group has nodes
    # Select button should be disabled (no nodes in group yet)
    assert not widget.select_btn.isEnabled()

    # Add nodes to group
    qtbot.mouseClick(widget.add_nodes_btn, Qt.MouseButton.LeftButton)

    # Select button should now be enabled
    assert widget.select_btn.isEnabled()


def test_add_remove_nodes(make_napari_viewer, graph_2d, qtbot):
    """Test adding and removing individual nodes to/from groups."""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    widget = CollectionWidget(tracks_viewer)

    # Create a group
    widget.group_name.setText("test_group")
    qtbot.mouseClick(widget.new_group_button, Qt.MouseButton.LeftButton)

    # Test 1: Add nodes to group
    tracks_viewer.selected_nodes.add_list([1, 2, 3], append=False)
    qtbot.mouseClick(widget.add_nodes_btn, Qt.MouseButton.LeftButton)

    # Verify nodes were added to collection
    assert 1 in widget.selected_collection.collection
    assert 2 in widget.selected_collection.collection
    assert 3 in widget.selected_collection.collection
    assert len(widget.selected_collection.collection) == 3
    assert widget.selected_collection.node_count.text() == "3 nodes"

    # Test 2: Remove some nodes
    tracks_viewer.selected_nodes.add_list([2], append=False)
    qtbot.mouseClick(widget.remove_node_btn, Qt.MouseButton.LeftButton)

    # Verify node was removed
    assert 1 in widget.selected_collection.collection
    assert 2 not in widget.selected_collection.collection
    assert 3 in widget.selected_collection.collection
    assert len(widget.selected_collection.collection) == 2


def test_add_remove_tracks(make_napari_viewer, graph_2d, qtbot):
    """Test adding and removing entire tracks to/from groups."""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    widget = CollectionWidget(tracks_viewer)

    # Create a group
    widget.group_name.setText("test_group")
    qtbot.mouseClick(widget.new_group_button, Qt.MouseButton.LeftButton)

    # Test 1: Add entire track to group
    tracks_viewer.selected_nodes.add_list([1], append=False)
    qtbot.mouseClick(widget.add_track_btn, Qt.MouseButton.LeftButton)

    # Verify all nodes in the track were added
    track_id = tracks_viewer.tracks.get_track_id(1)
    track_nodes = tracks_viewer.tracks.track_annotator.tracklet_id_to_nodes[track_id]

    for node in track_nodes:
        assert node in widget.selected_collection.collection

    initial_count = len(widget.selected_collection.collection)
    assert initial_count > 0

    # Test 2: Remove the entire track
    tracks_viewer.selected_nodes.add_list([1], append=False)
    qtbot.mouseClick(widget.remove_track_btn, Qt.MouseButton.LeftButton)

    # Verify track was removed
    for node in track_nodes:
        assert node not in widget.selected_collection.collection


def test_add_remove_lineages(make_napari_viewer, graph_2d, qtbot):
    """Test adding and removing entire lineages to/from groups."""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    widget = CollectionWidget(tracks_viewer)

    # Create a group
    widget.group_name.setText("test_group")
    qtbot.mouseClick(widget.new_group_button, Qt.MouseButton.LeftButton)

    # Test 1: Add entire lineage to group
    tracks_viewer.selected_nodes.add_list([1], append=False)
    qtbot.mouseClick(widget.add_lineage_btn, Qt.MouseButton.LeftButton)

    # Verify lineage nodes were added (at least the selected node)
    assert 1 in widget.selected_collection.collection
    assert len(widget.selected_collection.collection) > 0

    initial_count = len(widget.selected_collection.collection)

    # Test 2: Remove the lineage
    tracks_viewer.selected_nodes.add_list([1], append=False)
    qtbot.mouseClick(widget.remove_lineage_btn, Qt.MouseButton.LeftButton)

    # Verify lineage was removed (should be empty or much smaller)
    assert len(widget.selected_collection.collection) < initial_count


def test_selection_operations(make_napari_viewer, graph_2d, qtbot):
    """Test selection operations: select, deselect, invert, restore."""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    widget = CollectionWidget(tracks_viewer)

    # Create a group and add nodes
    widget.group_name.setText("test_group")
    qtbot.mouseClick(widget.new_group_button, Qt.MouseButton.LeftButton)

    tracks_viewer.selected_nodes.add_list([1, 2, 3], append=False)
    qtbot.mouseClick(widget.add_nodes_btn, Qt.MouseButton.LeftButton)

    # Test 1: Select all nodes in group
    tracks_viewer.selected_nodes.reset()
    assert len(tracks_viewer.selected_nodes) == 0

    qtbot.mouseClick(widget.select_btn, Qt.MouseButton.LeftButton)

    # Verify nodes were selected
    assert 1 in tracks_viewer.selected_nodes
    assert 2 in tracks_viewer.selected_nodes
    assert 3 in tracks_viewer.selected_nodes

    # Test 2: Deselect all nodes
    qtbot.mouseClick(widget.deselect_btn, Qt.MouseButton.LeftButton)
    assert len(tracks_viewer.selected_nodes) == 0

    # Test 3: Restore previous selection
    qtbot.mouseClick(widget.reselect_btn, Qt.MouseButton.LeftButton)
    assert 1 in tracks_viewer.selected_nodes
    assert 2 in tracks_viewer.selected_nodes
    assert 3 in tracks_viewer.selected_nodes

    # Test 4: Invert selection
    all_nodes = set(tracks.graph.nodes)
    selected = [1, 2, 3]

    qtbot.mouseClick(widget.invert_btn, Qt.MouseButton.LeftButton)

    # Verify selection was inverted
    expected = all_nodes - set(selected)
    actual = set(tracks_viewer.selected_nodes.as_list)
    assert actual == expected


def test_node_navigation(make_napari_viewer, graph_2d, qtbot):
    """Test jumping to next/previous selected nodes."""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    # Mock center_on_node to verify it's called
    center_mock = MagicMock()
    tracks_viewer.center_on_node = center_mock

    widget = CollectionWidget(tracks_viewer)

    # Select multiple nodes
    tracks_viewer.selected_nodes.add_list([1, 2, 3], append=False)

    # Test 1: Jump to next node
    qtbot.mouseClick(widget.jump_to_next_btn, Qt.MouseButton.LeftButton)
    center_mock.assert_called_once()

    # Test 2: Jump to previous node
    center_mock.reset_mock()
    qtbot.mouseClick(widget.jump_to_previous_btn, Qt.MouseButton.LeftButton)
    center_mock.assert_called_once()


class TestRetrieveExistingGroups:
    """Test retrieving groups from track features."""

    def test_retrieve_existing_groups(self, make_napari_viewer, graph_2d):
        """Test retrieving groups that exist as features on tracks."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Add a boolean feature to tracks (simulates existing group)
        from funtracks.features import Feature

        tracks.features["existing_group"] = Feature(
            feature_type="node",
            value_type="bool",
            num_values=1,
        )

        # Set some nodes to True for this feature
        tracks.graph.nodes[1]["existing_group"] = True
        tracks.graph.nodes[2]["existing_group"] = True

        widget = CollectionWidget(tracks_viewer)
        widget.retrieve_existing_groups()

        # Verify group was created in the list
        assert widget.collection_list.count() == 1

        # Verify group has correct nodes
        item = widget.collection_list.item(0)
        button = widget.collection_list.itemWidget(item)
        assert button.name.text() == "existing_group"
        assert 1 in button.collection
        assert 2 in button.collection

    def test_refresh_removes_deleted_nodes(self, make_napari_viewer, graph_2d, qtbot):
        """Test refresh removes nodes that no longer exist in graph."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        widget = CollectionWidget(tracks_viewer)

        # Create a group and add nodes
        widget.group_name.setText("test_group")
        qtbot.mouseClick(widget.new_group_button, Qt.MouseButton.LeftButton)

        tracks_viewer.selected_nodes.add_list([1, 2], append=False)
        qtbot.mouseClick(widget.add_nodes_btn, Qt.MouseButton.LeftButton)

        assert len(widget.selected_collection.collection) == 2

        # Remove a node from the graph
        tracks.graph.remove_node(1)

        # Refresh
        widget._refresh()

        # Verify node was removed from collection
        assert 1 not in widget.selected_collection.collection
        assert 2 in widget.selected_collection.collection
        assert len(widget.selected_collection.collection) == 1

        assert 2 in widget.selected_collection.collection
        assert len(widget.selected_collection.collection) == 1


@patch("motile_tracker.data_views.views_coordinator.groups.ExportDialog")
def test_export_button_shows_dialog(
    mock_export_dialog, make_napari_viewer, graph_2d, qtbot
):
    """Test export button shows export dialog."""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    widget = CollectionWidget(tracks_viewer)

    # Create a group and add nodes
    widget.group_name.setText("export_test")
    qtbot.mouseClick(widget.new_group_button, Qt.MouseButton.LeftButton)

    tracks_viewer.selected_nodes.add_list([1, 2], append=False)
    qtbot.mouseClick(widget.add_nodes_btn, Qt.MouseButton.LeftButton)

    # Click export button
    item = widget.collection_list.item(0)
    button = widget.collection_list.itemWidget(item)
    qtbot.mouseClick(button.export, Qt.MouseButton.LeftButton)

    # Verify export dialog was called
    mock_export_dialog.show_export_dialog.assert_called_once()

    # Verify correct parameters were passed
    call_args = mock_export_dialog.show_export_dialog.call_args
    assert call_args.kwargs["name"] == "export_test"
    assert call_args.kwargs["tracks"] == tracks
    assert 1 in call_args.kwargs["nodes_to_keep"]
    assert 2 in call_args.kwargs["nodes_to_keep"]
