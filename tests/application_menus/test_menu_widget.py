"""Tests for MenuWidget - main tabbed menu container."""

from unittest.mock import MagicMock, patch

import pytest
from qtpy.QtWidgets import QLabel, QTabWidget, QWidget

from motile_tracker.application_menus.menu_widget import MenuWidget


@pytest.fixture
def mock_tracks_viewer(qtbot):
    """Mock TracksViewer singleton."""
    mock_viewer = MagicMock()
    # Create actual QWidget instances for the components
    tracks_list = QWidget()
    qtbot.addWidget(tracks_list)
    collection_widget = QWidget()
    qtbot.addWidget(collection_widget)

    mock_viewer.tracks_list = tracks_list
    mock_viewer.collection_widget = collection_widget
    mock_viewer.tracking_layers = MagicMock()
    mock_viewer.tracking_layers.seg_layer = None
    mock_viewer.tracks_updated = MagicMock()
    mock_viewer.tracks_updated.connect = MagicMock()
    return mock_viewer


@patch("motile_tracker.application_menus.menu_widget.TracksViewer.get_instance")
@patch("motile_tracker.application_menus.menu_widget.MotileWidget")
@patch("motile_tracker.application_menus.menu_widget.EditingMenu")
@patch("motile_tracker.application_menus.menu_widget.LabelVisualizationWidget")
def test_menu_widget_initialization(
    mock_viz_widget,
    mock_editing_menu,
    mock_motile_widget,
    mock_get_instance,
    make_napari_viewer,
    qtbot,
    mock_tracks_viewer,
):
    """Test MenuWidget initialization, tabs, and header."""
    viewer = make_napari_viewer()
    mock_get_instance.return_value = mock_tracks_viewer

    # Make the widget constructors return actual QWidgets
    mock_motile_widget.return_value = QWidget()
    mock_editing_menu.return_value = QWidget()
    mock_viz_widget.return_value = QWidget()

    widget = MenuWidget(viewer)
    qtbot.addWidget(widget)

    # Test 1: Verify all components created
    mock_get_instance.assert_called_once_with(viewer)
    mock_motile_widget.assert_called_once_with(viewer)
    mock_editing_menu.assert_called_once_with(viewer)
    mock_viz_widget.assert_called_once_with(viewer)
    mock_tracks_viewer.tracks_updated.connect.assert_called_once()
    assert widget.tabwidget is not None
    assert isinstance(widget.tabwidget, QTabWidget)

    # Test 2: Verify 4 initial tabs with correct names
    assert widget.tabwidget.count() == 4
    assert widget.tabwidget.tabText(0) == "Tracking"
    assert widget.tabwidget.tabText(1) == "Tracks List"
    assert widget.tabwidget.tabText(2) == "Edit Tracks"
    assert widget.tabwidget.tabText(3) == "Groups"

    # Test 3: Verify header with docs and keybindings links
    labels = widget.findChildren(QLabel)
    header_labels = [label for label in labels if "Motile Tracker" in label.text()]
    assert len(header_labels) == 1
    header = header_labels[0]
    assert "Docs" in header.text()
    assert "Keybindings" in header.text()
    assert "href=" in header.text()


@patch("motile_tracker.application_menus.menu_widget.TracksViewer.get_instance")
@patch("motile_tracker.application_menus.menu_widget.MotileWidget")
@patch("motile_tracker.application_menus.menu_widget.EditingMenu")
@patch("motile_tracker.application_menus.menu_widget.LabelVisualizationWidget")
def test_has_visualization_tab(
    mock_viz_widget,
    mock_editing_menu,
    mock_motile_widget,
    mock_get_instance,
    make_napari_viewer,
    qtbot,
    mock_tracks_viewer,
):
    """Test _has_visualization_tab method."""
    viewer = make_napari_viewer()
    mock_get_instance.return_value = mock_tracks_viewer

    # Make the widget constructors return actual QWidgets
    mock_motile_widget.return_value = QWidget()
    mock_editing_menu.return_value = QWidget()
    mock_viz_widget.return_value = QWidget()

    widget = MenuWidget(viewer)
    qtbot.addWidget(widget)

    # Test 1: Initially returns False when tab not present
    assert widget._has_visualization_tab() is False

    # Test 2: Returns True when tab is present
    widget.tabwidget.addTab(widget.visualization_widget, "Visualization")
    assert widget._has_visualization_tab() is True


@patch("motile_tracker.application_menus.menu_widget.TracksViewer.get_instance")
@patch("motile_tracker.application_menus.menu_widget.MotileWidget")
@patch("motile_tracker.application_menus.menu_widget.EditingMenu")
@patch("motile_tracker.application_menus.menu_widget.LabelVisualizationWidget")
def test_toggle_visualization_widget(
    mock_viz_widget,
    mock_editing_menu,
    mock_motile_widget,
    mock_get_instance,
    make_napari_viewer,
    qtbot,
    mock_tracks_viewer,
):
    """Test _toggle_visualization_widget adds/removes tab based on seg_layer."""
    viewer = make_napari_viewer()
    mock_get_instance.return_value = mock_tracks_viewer

    # Make the widget constructors return actual QWidgets
    mock_motile_widget.return_value = QWidget()
    mock_editing_menu.return_value = QWidget()
    mock_viz_widget.return_value = QWidget()

    widget = MenuWidget(viewer)
    qtbot.addWidget(widget)

    # Initially no visualization tab
    assert widget._has_visualization_tab() is False
    assert widget.tabwidget.count() == 4

    # Set seg_layer to something (not None)
    mock_tracks_viewer.tracking_layers.seg_layer = MagicMock()

    # Call toggle
    widget._toggle_visualization_widget()

    # Should now have 5 tabs
    assert widget._has_visualization_tab() is True
    assert widget.tabwidget.count() == 5
    # Check the visualization tab was added at index 3
    assert widget.tabwidget.tabText(3) == "Visualization"

    # Call toggle again - should not add duplicate
    widget._toggle_visualization_widget()
    assert widget.tabwidget.count() == 5  # still 5 tabs
    viz_index = widget.tabwidget.indexOf(widget.visualization_widget)

    # Now remove seg_layer again
    mock_tracks_viewer.tracking_layers.seg_layer = None
    widget._toggle_visualization_widget()

    # Should be back to 4 tabs
    assert widget.tabwidget.count() == 4
    # Visualization tab should be gone
    for i in range(widget.tabwidget.count()):
        assert widget.tabwidget.tabText(i) != "Visualization"

    # Add it back once more
    mock_tracks_viewer.tracking_layers.seg_layer = MagicMock()
    widget._toggle_visualization_widget()

    # Should be at same index
    new_index = widget.tabwidget.indexOf(widget.visualization_widget)
    assert new_index == viz_index


@patch("motile_tracker.application_menus.menu_widget.TracksViewer.get_instance")
@patch("motile_tracker.application_menus.menu_widget.MotileWidget")
@patch("motile_tracker.application_menus.menu_widget.EditingMenu")
@patch("motile_tracker.application_menus.menu_widget.LabelVisualizationWidget")
def test_widget_integration(
    mock_viz_widget,
    mock_editing_menu,
    mock_motile_widget,
    mock_get_instance,
    make_napari_viewer,
    qtbot,
    mock_tracks_viewer,
):
    """Test widget integration and signal connections."""
    viewer = make_napari_viewer()
    mock_get_instance.return_value = mock_tracks_viewer

    # Make the widget constructors return actual QWidgets
    mock_motile_widget.return_value = QWidget()
    mock_editing_menu.return_value = QWidget()
    mock_viz_widget.return_value = QWidget()

    widget = MenuWidget(viewer)
    qtbot.addWidget(widget)

    # Test 1: Verify widget resizable is enabled
    assert widget.widgetResizable() is True

    # Test 2: Verify tracks_updated signal is connected to toggle method
    mock_tracks_viewer.tracks_updated.connect.assert_called_once_with(
        widget._toggle_visualization_widget
    )
