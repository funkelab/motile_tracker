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


class TestCollectionButton:
    """Test CollectionButton widget initialization and UI elements."""

    def test_initialization(self, make_napari_viewer):
        """Test CollectionButton creates all UI elements correctly."""
        make_napari_viewer()  # Create Qt context
        button = CollectionButton("test_group")

        # Verify name label
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

    def test_update_node_count(self, make_napari_viewer):
        """Test update_node_count updates the label correctly."""
        make_napari_viewer()  # Create Qt context
        button = CollectionButton("test_group")

        # Add nodes to collection
        button.collection = {1, 2, 3, 4, 5}
        button.update_node_count()

        assert button.node_count.text() == "5 nodes"

        # Remove some nodes
        button.collection = {1, 2}
        button.update_node_count()

        assert button.node_count.text() == "2 nodes"

    def test_size_hint(self, make_napari_viewer):
        """Test size hint returns correct height."""
        make_napari_viewer()  # Create Qt context
        button = CollectionButton("test_group")
        hint = button.sizeHint()

        assert hint.height() == 30


class TestCollectionWidgetInitialization:
    """Test CollectionWidget initialization and setup."""

    def test_initialization(self, make_napari_viewer, graph_2d):
        """Test CollectionWidget initializes correctly."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        widget = CollectionWidget(tracks_viewer)

        # Verify tracks_viewer is set
        assert widget.tracks_viewer == tracks_viewer

        # Verify list widget exists
        assert widget.collection_list is not None

        # Verify selected collection is None initially
        assert widget.selected_collection is None

        # Verify buttons exist
        assert widget.select_btn is not None
        assert widget.invert_btn is not None
        assert widget.deselect_btn is not None
        assert widget.reselect_btn is not None
        assert widget.add_nodes_btn is not None
        assert widget.remove_node_btn is not None
        assert widget.new_group_button is not None

    def test_initial_button_states_no_groups(self, make_napari_viewer, graph_2d):
        """Test buttons are disabled when no groups exist."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        widget = CollectionWidget(tracks_viewer)

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


class TestGroupCreationAndDeletion:
    """Test creating and deleting groups."""

    def test_create_new_group(self, make_napari_viewer, graph_2d, qtbot):
        """Test creating a new group."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        widget = CollectionWidget(tracks_viewer)

        # Set group name and create
        widget.group_name.setText("my_test_group")
        qtbot.mouseClick(widget.new_group_button, Qt.MouseButton.LeftButton)

        # Verify group was created
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

    def test_create_group_with_duplicate_name(
        self, make_napari_viewer, graph_2d, qtbot
    ):
        """Test creating groups with duplicate names appends _1."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        widget = CollectionWidget(tracks_viewer)

        # Create first group
        widget.group_name.setText("duplicate")
        qtbot.mouseClick(widget.new_group_button, Qt.MouseButton.LeftButton)

        # Create second group with same name
        widget.group_name.setText("duplicate")
        qtbot.mouseClick(widget.new_group_button, Qt.MouseButton.LeftButton)

        # Verify both groups exist with different names
        assert widget.collection_list.count() == 2

        item1 = widget.collection_list.item(0)
        button1 = widget.collection_list.itemWidget(item1)
        assert button1.name.text() == "duplicate"

        item2 = widget.collection_list.item(1)
        button2 = widget.collection_list.itemWidget(item2)
        assert button2.name.text() == "duplicate_1"

    def test_delete_group(self, make_napari_viewer, graph_2d, qtbot):
        """Test deleting a group removes it from list and tracks features."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        widget = CollectionWidget(tracks_viewer)

        # Create a group
        widget.group_name.setText("to_delete")
        qtbot.mouseClick(widget.new_group_button, Qt.MouseButton.LeftButton)

        assert widget.collection_list.count() == 1
        assert "to_delete" in tracks_viewer.tracks.features

        # Delete the group
        item = widget.collection_list.item(0)
        button = widget.collection_list.itemWidget(item)
        qtbot.mouseClick(button.delete, Qt.MouseButton.LeftButton)

        # Verify group was removed
        assert widget.collection_list.count() == 0
        assert "to_delete" not in tracks_viewer.tracks.features


class TestButtonStates:
    """Test button enable/disable states based on selection and group state."""

    def test_edit_buttons_enabled_with_group_and_selection(
        self, make_napari_viewer, graph_2d, qtbot
    ):
        """Test edit buttons enabled when group selected and nodes selected."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        widget = CollectionWidget(tracks_viewer)

        # Create a group
        widget.group_name.setText("test_group")
        qtbot.mouseClick(widget.new_group_button, Qt.MouseButton.LeftButton)

        # Select nodes
        tracks_viewer.selected_nodes.add_list([1, 2], append=False)

        # Verify edit buttons are enabled
        assert widget.add_nodes_btn.isEnabled()
        assert widget.add_track_btn.isEnabled()
        assert widget.add_lineage_btn.isEnabled()
        assert widget.remove_node_btn.isEnabled()
        assert widget.remove_track_btn.isEnabled()
        assert widget.remove_lineage_btn.isEnabled()

    def test_select_button_enabled_when_group_has_nodes(
        self, make_napari_viewer, graph_2d, qtbot
    ):
        """Test select button only enabled when selected group has nodes."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        widget = CollectionWidget(tracks_viewer)

        # Create a group
        widget.group_name.setText("test_group")
        qtbot.mouseClick(widget.new_group_button, Qt.MouseButton.LeftButton)

        # Select button should be disabled (no nodes in group)
        assert not widget.select_btn.isEnabled()

        # Add nodes to group
        tracks_viewer.selected_nodes.add_list([1], append=False)
        qtbot.mouseClick(widget.add_nodes_btn, Qt.MouseButton.LeftButton)

        # Select button should now be enabled
        assert widget.select_btn.isEnabled()

    def test_navigation_buttons_enabled_with_selection(
        self, make_napari_viewer, graph_2d
    ):
        """Test navigation buttons enabled when nodes selected."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        widget = CollectionWidget(tracks_viewer)

        # Initially disabled
        assert not widget.deselect_btn.isEnabled()
        assert not widget.jump_to_next_btn.isEnabled()
        assert not widget.jump_to_previous_btn.isEnabled()

        # Select nodes
        tracks_viewer.selected_nodes.add_list([1, 2], append=False)

        # Now enabled
        assert widget.deselect_btn.isEnabled()
        assert widget.jump_to_next_btn.isEnabled()
        assert widget.jump_to_previous_btn.isEnabled()


class TestAddRemoveNodes:
    """Test adding and removing individual nodes to/from groups."""

    def test_add_nodes_to_group(self, make_napari_viewer, graph_2d, qtbot):
        """Test adding nodes to a group."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        widget = CollectionWidget(tracks_viewer)

        # Create a group
        widget.group_name.setText("test_group")
        qtbot.mouseClick(widget.new_group_button, Qt.MouseButton.LeftButton)

        # Select nodes and add to group
        tracks_viewer.selected_nodes.add_list([1, 2], append=False)
        qtbot.mouseClick(widget.add_nodes_btn, Qt.MouseButton.LeftButton)

        # Verify nodes were added to collection
        assert 1 in widget.selected_collection.collection
        assert 2 in widget.selected_collection.collection
        assert len(widget.selected_collection.collection) == 2

        # Verify node count updated
        assert widget.selected_collection.node_count.text() == "2 nodes"

    def test_remove_nodes_from_group(self, make_napari_viewer, graph_2d, qtbot):
        """Test removing nodes from a group."""
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

        assert len(widget.selected_collection.collection) == 3

        # Remove some nodes
        tracks_viewer.selected_nodes.add_list([2], append=False)
        qtbot.mouseClick(widget.remove_node_btn, Qt.MouseButton.LeftButton)

        # Verify node was removed
        assert 1 in widget.selected_collection.collection
        assert 2 not in widget.selected_collection.collection
        assert 3 in widget.selected_collection.collection
        assert len(widget.selected_collection.collection) == 2


class TestAddRemoveTracks:
    """Test adding and removing entire tracks to/from groups."""

    def test_add_track_to_group(self, make_napari_viewer, graph_2d, qtbot):
        """Test adding entire track(s) to a group."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        widget = CollectionWidget(tracks_viewer)

        # Create a group
        widget.group_name.setText("test_group")
        qtbot.mouseClick(widget.new_group_button, Qt.MouseButton.LeftButton)

        # Select a node and add its track
        tracks_viewer.selected_nodes.add_list([1], append=False)
        qtbot.mouseClick(widget.add_track_btn, Qt.MouseButton.LeftButton)

        # Verify all nodes in the track were added
        track_id = tracks_viewer.tracks.get_track_id(1)
        track_nodes = tracks_viewer.tracks.track_annotator.tracklet_id_to_nodes[
            track_id
        ]

        for node in track_nodes:
            assert node in widget.selected_collection.collection

    def test_remove_track_from_group(self, make_napari_viewer, graph_2d, qtbot):
        """Test removing entire track(s) from a group."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        widget = CollectionWidget(tracks_viewer)

        # Create a group and add track
        widget.group_name.setText("test_group")
        qtbot.mouseClick(widget.new_group_button, Qt.MouseButton.LeftButton)

        tracks_viewer.selected_nodes.add_list([1], append=False)
        qtbot.mouseClick(widget.add_track_btn, Qt.MouseButton.LeftButton)

        initial_count = len(widget.selected_collection.collection)
        assert initial_count > 0

        # Remove the track
        tracks_viewer.selected_nodes.add_list([1], append=False)
        qtbot.mouseClick(widget.remove_track_btn, Qt.MouseButton.LeftButton)

        # Verify track was removed
        track_id = tracks_viewer.tracks.get_track_id(1)
        track_nodes = tracks_viewer.tracks.track_annotator.tracklet_id_to_nodes[
            track_id
        ]

        for node in track_nodes:
            assert node not in widget.selected_collection.collection


class TestAddRemoveLineages:
    """Test adding and removing entire lineages to/from groups."""

    def test_add_lineage_to_group(self, make_napari_viewer, graph_2d, qtbot):
        """Test adding entire lineage(s) to a group."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        widget = CollectionWidget(tracks_viewer)

        # Create a group
        widget.group_name.setText("test_group")
        qtbot.mouseClick(widget.new_group_button, Qt.MouseButton.LeftButton)

        # Select a node and add its lineage
        tracks_viewer.selected_nodes.add_list([1], append=False)
        qtbot.mouseClick(widget.add_lineage_btn, Qt.MouseButton.LeftButton)

        # Verify lineage nodes were added (at least the selected node)
        assert 1 in widget.selected_collection.collection
        assert len(widget.selected_collection.collection) > 0

    def test_remove_lineage_from_group(self, make_napari_viewer, graph_2d, qtbot):
        """Test removing entire lineage(s) from a group."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        widget = CollectionWidget(tracks_viewer)

        # Create a group and add lineage
        widget.group_name.setText("test_group")
        qtbot.mouseClick(widget.new_group_button, Qt.MouseButton.LeftButton)

        tracks_viewer.selected_nodes.add_list([1], append=False)
        qtbot.mouseClick(widget.add_lineage_btn, Qt.MouseButton.LeftButton)

        initial_count = len(widget.selected_collection.collection)
        assert initial_count > 0

        # Remove the lineage
        tracks_viewer.selected_nodes.add_list([1], append=False)
        qtbot.mouseClick(widget.remove_lineage_btn, Qt.MouseButton.LeftButton)

        # Verify lineage was removed (should be empty or much smaller)
        assert len(widget.selected_collection.collection) < initial_count


class TestSelectionOperations:
    """Test selection operations: select, deselect, invert, restore."""

    def test_select_nodes_in_group(self, make_napari_viewer, graph_2d, qtbot):
        """Test selecting all nodes in a group."""
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

        # Clear selection
        tracks_viewer.selected_nodes.reset()
        assert len(tracks_viewer.selected_nodes) == 0

        # Click select button
        qtbot.mouseClick(widget.select_btn, Qt.MouseButton.LeftButton)

        # Verify nodes were selected
        assert 1 in tracks_viewer.selected_nodes
        assert 2 in tracks_viewer.selected_nodes
        assert 3 in tracks_viewer.selected_nodes

    def test_deselect_nodes(self, make_napari_viewer, graph_2d, qtbot):
        """Test deselecting all nodes."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        widget = CollectionWidget(tracks_viewer)

        # Select some nodes
        tracks_viewer.selected_nodes.add_list([1, 2, 3], append=False)
        assert len(tracks_viewer.selected_nodes) == 3

        # Click deselect button
        qtbot.mouseClick(widget.deselect_btn, Qt.MouseButton.LeftButton)

        # Verify selection was cleared
        assert len(tracks_viewer.selected_nodes) == 0

    def test_restore_selection(self, make_napari_viewer, graph_2d, qtbot):
        """Test restoring previous selection."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        widget = CollectionWidget(tracks_viewer)

        # Select and deselect
        tracks_viewer.selected_nodes.add_list([1, 2], append=False)
        qtbot.mouseClick(widget.deselect_btn, Qt.MouseButton.LeftButton)
        assert len(tracks_viewer.selected_nodes) == 0

        # Restore selection
        qtbot.mouseClick(widget.reselect_btn, Qt.MouseButton.LeftButton)

        # Verify nodes were restored
        assert 1 in tracks_viewer.selected_nodes
        assert 2 in tracks_viewer.selected_nodes

    def test_invert_selection(self, make_napari_viewer, graph_2d, qtbot):
        """Test inverting selection."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        widget = CollectionWidget(tracks_viewer)

        # Select some nodes
        all_nodes = set(tracks.graph.nodes)
        selected = [1, 2]
        tracks_viewer.selected_nodes.add_list(selected, append=False)

        # Invert selection
        qtbot.mouseClick(widget.invert_btn, Qt.MouseButton.LeftButton)

        # Verify selection was inverted
        expected = all_nodes - set(selected)
        actual = set(tracks_viewer.selected_nodes.as_list)
        assert actual == expected


class TestNodeNavigation:
    """Test jumping to next/previous selected nodes."""

    def test_jump_to_next_node(self, make_napari_viewer, graph_2d, qtbot):
        """Test jumping to next selected node."""
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

        # Jump to next
        qtbot.mouseClick(widget.jump_to_next_btn, Qt.MouseButton.LeftButton)

        # Verify center_on_node was called
        center_mock.assert_called_once()

    def test_jump_to_previous_node(self, make_napari_viewer, graph_2d, qtbot):
        """Test jumping to previous selected node."""
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

        # Jump to previous
        qtbot.mouseClick(widget.jump_to_previous_btn, Qt.MouseButton.LeftButton)

        # Verify center_on_node was called
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


class TestExportDialog:
    """Test export dialog integration."""

    @patch("motile_tracker.data_views.views_coordinator.groups.ExportDialog")
    def test_export_button_shows_dialog(
        self, mock_export_dialog, make_napari_viewer, graph_2d, qtbot
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
