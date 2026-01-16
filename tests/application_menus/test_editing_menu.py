"""Tests for EditingMenu - the track editing UI widget.

Tests cover button states, button interactions, and track ID display.
"""

from unittest.mock import MagicMock

from funtracks.data_model import SolutionTracks
from PyQt6.QtCore import Qt

from motile_tracker.application_menus.editing_menu import EditingMenu
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


class TestButtonStates:
    """Test button enable/disable states based on selection."""

    def test_buttons_disabled_no_selection(self, make_napari_viewer, graph_2d):
        """Verify buttons disabled when nothing selected."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Create editing menu
        editing_menu = EditingMenu(viewer)

        # Verify all edit buttons are disabled when no selection
        assert not editing_menu.delete_node_btn.isEnabled()
        assert not editing_menu.swap_nodes_btn.isEnabled()
        assert not editing_menu.delete_edge_btn.isEnabled()
        assert not editing_menu.create_edge_btn.isEnabled()

    def test_update_buttons_with_empty_selection(self, make_napari_viewer, graph_2d):
        """Verify update_buttons() disables all buttons when selection is cleared."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        editing_menu = EditingMenu(viewer)

        # First select nodes to enable buttons
        tracks_viewer.selected_nodes = [1, 2]
        editing_menu.update_buttons()
        assert editing_menu.delete_node_btn.isEnabled()

        # Now clear selection and call update_buttons
        tracks_viewer.selected_nodes = []
        editing_menu.update_buttons()

        # Verify all edit buttons are disabled
        assert not editing_menu.delete_node_btn.isEnabled()
        assert not editing_menu.swap_nodes_btn.isEnabled()
        assert not editing_menu.delete_edge_btn.isEnabled()
        assert not editing_menu.create_edge_btn.isEnabled()

    def test_buttons_with_single_selection(self, make_napari_viewer, graph_2d):
        """Verify only delete button enabled with single node selection."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        editing_menu = EditingMenu(viewer)

        # Select a single node and trigger button update
        tracks_viewer.selected_nodes = [1]
        editing_menu.update_buttons()

        # Verify only delete is enabled, others disabled
        assert editing_menu.delete_node_btn.isEnabled()
        assert not editing_menu.delete_edge_btn.isEnabled()
        assert not editing_menu.create_edge_btn.isEnabled()

    def test_buttons_with_two_selections(self, make_napari_viewer, graph_2d):
        """Verify all buttons enabled when two nodes selected."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        editing_menu = EditingMenu(viewer)

        # Select two nodes and trigger button update
        tracks_viewer.selected_nodes = [1, 2]
        editing_menu.update_buttons()

        # Verify all edit buttons are enabled
        assert editing_menu.delete_node_btn.isEnabled()
        assert editing_menu.swap_nodes_btn.isEnabled()
        assert editing_menu.delete_edge_btn.isEnabled()
        assert editing_menu.create_edge_btn.isEnabled()

    def test_buttons_with_multiple_selections(self, make_napari_viewer, graph_2d):
        """Verify only delete button enabled with 3+ nodes selected."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        editing_menu = EditingMenu(viewer)

        # Select three nodes and trigger button update
        tracks_viewer.selected_nodes = [1, 2, 3]
        editing_menu.update_buttons()

        # Verify only delete is enabled, others disabled
        assert editing_menu.delete_node_btn.isEnabled()
        assert not editing_menu.delete_edge_btn.isEnabled()
        assert not editing_menu.create_edge_btn.isEnabled()


class TestButtonInteractions:
    """Test button click handlers."""

    def test_delete_node_button_calls_tracks_viewer(
        self, make_napari_viewer, graph_2d, qtbot
    ):
        """Test Delete Node button calls tracks_viewer.delete_node()."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Mock the delete_node method before creating EditingMenu
        delete_mock = MagicMock()
        tracks_viewer.delete_node = delete_mock

        editing_menu = EditingMenu(viewer)

        # Enable the button by simulating selection
        tracks_viewer.selected_nodes = [1]
        editing_menu.update_buttons()

        # Trigger the button click
        qtbot.mouseClick(editing_menu.delete_node_btn, Qt.MouseButton.LeftButton)

        # Verify the method was called
        delete_mock.assert_called_once()

    def test_add_edge_button_calls_create_edge(
        self, make_napari_viewer, graph_2d, qtbot
    ):
        """Test Add Edge button calls tracks_viewer.create_edge()."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Mock the create_edge method before creating EditingMenu
        create_edge_mock = MagicMock()
        tracks_viewer.create_edge = create_edge_mock

        editing_menu = EditingMenu(viewer)

        # Enable the button by simulating selection of 2 nodes
        tracks_viewer.selected_nodes = [1, 2]
        editing_menu.update_buttons()

        # Trigger the button click
        qtbot.mouseClick(editing_menu.create_edge_btn, Qt.MouseButton.LeftButton)

        # Verify the method was called
        create_edge_mock.assert_called_once()

    def test_swap_nodes_button_calls_swap_nodes(
        self, make_napari_viewer, graph_2d, qtbot
    ):
        """Test Swap Nodes button calls tracks_viewer.swap_nodes()."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Mock the swap_nodes method before creating EditingMenu
        swap_mock = MagicMock()
        tracks_viewer.swap_nodes = swap_mock

        editing_menu = EditingMenu(viewer)

        # Enable the button by simulating selection of 2 nodes
        tracks_viewer.selected_nodes = [1, 2]
        editing_menu.update_buttons()

        # Trigger the button click
        qtbot.mouseClick(editing_menu.swap_nodes_btn, Qt.MouseButton.LeftButton)

        # Verify the method was called
        swap_mock.assert_called_once()

    def test_break_edge_button_calls_delete_edge(
        self, make_napari_viewer, graph_2d, qtbot
    ):
        """Test Break Edge button calls tracks_viewer.delete_edge()."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Mock the delete_edge method before creating EditingMenu
        delete_edge_mock = MagicMock()
        tracks_viewer.delete_edge = delete_edge_mock

        editing_menu = EditingMenu(viewer)

        # Enable the button by simulating selection of 2 nodes
        tracks_viewer.selected_nodes = [1, 2]
        editing_menu.update_buttons()

        # Trigger the button click
        qtbot.mouseClick(editing_menu.delete_edge_btn, Qt.MouseButton.LeftButton)

        # Verify the method was called
        delete_edge_mock.assert_called_once()

    def test_start_new_track_button_calls_request_new_track(
        self, make_napari_viewer, graph_2d, qtbot
    ):
        """Test Start New Track button calls tracks_viewer.request_new_track()."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Mock the request_new_track method before creating EditingMenu
        new_track_mock = MagicMock()
        tracks_viewer.request_new_track = new_track_mock

        editing_menu = EditingMenu(viewer)

        # Find and click the "Start new" button
        new_track_btn = None
        for child in editing_menu.children():
            if hasattr(child, "text") and child.text() == "Start new":
                new_track_btn = child
                break

        assert new_track_btn is not None, "Could not find 'Start new' button"
        qtbot.mouseClick(new_track_btn, Qt.MouseButton.LeftButton)

        # Verify the method was called
        new_track_mock.assert_called_once()

    def test_undo_button_calls_undo(self, make_napari_viewer, graph_2d, qtbot):
        """Test Undo button calls tracks_viewer.undo()."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Mock the undo method before creating EditingMenu
        undo_mock = MagicMock()
        tracks_viewer.undo = undo_mock

        editing_menu = EditingMenu(viewer)

        # Trigger the button click
        qtbot.mouseClick(editing_menu.undo_btn, Qt.MouseButton.LeftButton)

        # Verify the method was called
        undo_mock.assert_called_once()

    def test_redo_button_calls_redo(self, make_napari_viewer, graph_2d, qtbot):
        """Test Redo button calls tracks_viewer.redo()."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        # Mock the redo method before creating EditingMenu
        redo_mock = MagicMock()
        tracks_viewer.redo = redo_mock

        editing_menu = EditingMenu(viewer)

        # Trigger the button click
        qtbot.mouseClick(editing_menu.redo_btn, Qt.MouseButton.LeftButton)

        # Verify the method was called
        redo_mock.assert_called_once()


class TestTrackIDDisplay:
    """Test track ID label updates."""

    def test_track_id_label_initial_display(self, make_napari_viewer, graph_2d):
        """Test track ID label shows initial track ID on creation."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        editing_menu = EditingMenu(viewer)

        # Verify label contains the track ID text
        assert "Current Track ID:" in editing_menu.label.text()

    def test_track_id_label_updates_on_signal(self, make_napari_viewer, graph_2d):
        """Test track ID label updates when update_track_id signal is emitted."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        editing_menu = EditingMenu(viewer)

        # Change the selected track
        tracks_viewer.selected_track = 2

        # Emit the signal
        tracks_viewer.update_track_id.emit()

        # Verify label was updated
        assert "Current Track ID: 2" in editing_menu.label.text()

    def test_track_id_label_has_border_styling(self, make_napari_viewer, graph_2d):
        """Test track ID label gets border styling when signal emitted."""
        viewer = make_napari_viewer()
        tracks = SolutionTracks(graph=graph_2d, ndim=3)
        tracks_viewer = TracksViewer.get_instance(viewer)
        tracks_viewer.update_tracks(tracks=tracks, name="test")

        editing_menu = EditingMenu(viewer)

        # Emit the signal to trigger styling
        tracks_viewer.update_track_id.emit()

        # Verify label has styling applied
        style = editing_menu.label.styleSheet()
        assert "border:" in style
        assert "color:" in style
        assert "rgba(" in style
