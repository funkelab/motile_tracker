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


class TestMenuWidgetInitialization:
    """Test MenuWidget initialization."""

    @patch("motile_tracker.application_menus.menu_widget.TracksViewer.get_instance")
    @patch("motile_tracker.application_menus.menu_widget.MotileWidget")
    @patch("motile_tracker.application_menus.menu_widget.EditingMenu")
    @patch("motile_tracker.application_menus.menu_widget.LabelVisualizationWidget")
    def test_initialization(
        self,
        mock_viz_widget,
        mock_editing_menu,
        mock_motile_widget,
        mock_get_instance,
        make_napari_viewer,
        qtbot,
        mock_tracks_viewer,
    ):
        """Test MenuWidget creates all components."""
        viewer = make_napari_viewer()
        mock_get_instance.return_value = mock_tracks_viewer

        # Make the widget constructors return actual QWidgets
        mock_motile_widget.return_value = QWidget()
        mock_editing_menu.return_value = QWidget()
        mock_viz_widget.return_value = QWidget()

        # Make the widget constructors return actual QWidgets
        mock_motile_widget.return_value = QWidget()
        mock_editing_menu.return_value = QWidget()
        mock_viz_widget.return_value = QWidget()

        widget = MenuWidget(viewer)
        qtbot.addWidget(widget)

        # Verify TracksViewer was retrieved
        mock_get_instance.assert_called_once_with(viewer)

        # Verify widgets were created
        mock_motile_widget.assert_called_once_with(viewer)
        mock_editing_menu.assert_called_once_with(viewer)
        mock_viz_widget.assert_called_once_with(viewer)

        # Verify signal connection
        mock_tracks_viewer.tracks_updated.connect.assert_called_once()

        # Verify tab widget exists
        assert widget.tabwidget is not None
        assert isinstance(widget.tabwidget, QTabWidget)

    @patch("motile_tracker.application_menus.menu_widget.TracksViewer.get_instance")
    @patch("motile_tracker.application_menus.menu_widget.MotileWidget")
    @patch("motile_tracker.application_menus.menu_widget.EditingMenu")
    @patch("motile_tracker.application_menus.menu_widget.LabelVisualizationWidget")
    def test_initialization_creates_four_tabs(
        self,
        mock_viz_widget,
        mock_editing_menu,
        mock_motile_widget,
        mock_get_instance,
        make_napari_viewer,
        qtbot,
        mock_tracks_viewer,
    ):
        """Test MenuWidget creates 4 initial tabs."""
        viewer = make_napari_viewer()
        mock_get_instance.return_value = mock_tracks_viewer

        # Make the widget constructors return actual QWidgets
        mock_motile_widget.return_value = QWidget()
        mock_editing_menu.return_value = QWidget()
        mock_viz_widget.return_value = QWidget()

        # Make the widget constructors return actual QWidgets
        mock_motile_widget.return_value = QWidget()
        mock_editing_menu.return_value = QWidget()
        mock_viz_widget.return_value = QWidget()

        widget = MenuWidget(viewer)
        qtbot.addWidget(widget)

        # Should have 4 tabs initially (no visualization tab)
        assert widget.tabwidget.count() == 4

    @patch("motile_tracker.application_menus.menu_widget.TracksViewer.get_instance")
    @patch("motile_tracker.application_menus.menu_widget.MotileWidget")
    @patch("motile_tracker.application_menus.menu_widget.EditingMenu")
    @patch("motile_tracker.application_menus.menu_widget.LabelVisualizationWidget")
    def test_initialization_tab_names(
        self,
        mock_viz_widget,
        mock_editing_menu,
        mock_motile_widget,
        mock_get_instance,
        make_napari_viewer,
        qtbot,
        mock_tracks_viewer,
    ):
        """Test MenuWidget creates tabs with correct names."""
        viewer = make_napari_viewer()
        mock_get_instance.return_value = mock_tracks_viewer

        # Make the widget constructors return actual QWidgets
        mock_motile_widget.return_value = QWidget()
        mock_editing_menu.return_value = QWidget()
        mock_viz_widget.return_value = QWidget()

        # Make the widget constructors return actual QWidgets
        mock_motile_widget.return_value = QWidget()
        mock_editing_menu.return_value = QWidget()
        mock_viz_widget.return_value = QWidget()

        widget = MenuWidget(viewer)
        qtbot.addWidget(widget)

        # Check tab names
        assert widget.tabwidget.tabText(0) == "Tracking"
        assert widget.tabwidget.tabText(1) == "Tracks List"
        assert widget.tabwidget.tabText(2) == "Edit Tracks"
        assert widget.tabwidget.tabText(3) == "Groups"

    @patch("motile_tracker.application_menus.menu_widget.TracksViewer.get_instance")
    @patch("motile_tracker.application_menus.menu_widget.MotileWidget")
    @patch("motile_tracker.application_menus.menu_widget.EditingMenu")
    @patch("motile_tracker.application_menus.menu_widget.LabelVisualizationWidget")
    def test_initialization_creates_header_with_links(
        self,
        mock_viz_widget,
        mock_editing_menu,
        mock_motile_widget,
        mock_get_instance,
        make_napari_viewer,
        qtbot,
        mock_tracks_viewer,
    ):
        """Test MenuWidget creates header with docs and keybindings links."""
        viewer = make_napari_viewer()
        mock_get_instance.return_value = mock_tracks_viewer

        # Make the widget constructors return actual QWidgets
        mock_motile_widget.return_value = QWidget()
        mock_editing_menu.return_value = QWidget()
        mock_viz_widget.return_value = QWidget()

        # Make the widget constructors return actual QWidgets
        mock_motile_widget.return_value = QWidget()
        mock_editing_menu.return_value = QWidget()
        mock_viz_widget.return_value = QWidget()

        widget = MenuWidget(viewer)
        qtbot.addWidget(widget)

        # Find header label
        labels = widget.findChildren(QLabel)
        header_labels = [label for label in labels if "Motile Tracker" in label.text()]
        assert len(header_labels) == 1

        header = header_labels[0]
        # Check that links are present
        assert "Docs" in header.text()
        assert "Keybindings" in header.text()
        assert "href=" in header.text()


class TestHasVisualizationTab:
    """Test _has_visualization_tab method."""

    @patch("motile_tracker.application_menus.menu_widget.TracksViewer.get_instance")
    @patch("motile_tracker.application_menus.menu_widget.MotileWidget")
    @patch("motile_tracker.application_menus.menu_widget.EditingMenu")
    @patch("motile_tracker.application_menus.menu_widget.LabelVisualizationWidget")
    def test_has_visualization_tab_returns_false_initially(
        self,
        mock_viz_widget,
        mock_editing_menu,
        mock_motile_widget,
        mock_get_instance,
        make_napari_viewer,
        qtbot,
        mock_tracks_viewer,
    ):
        """Test _has_visualization_tab returns False when tab not present."""
        viewer = make_napari_viewer()
        mock_get_instance.return_value = mock_tracks_viewer

        # Make the widget constructors return actual QWidgets
        mock_motile_widget.return_value = QWidget()
        mock_editing_menu.return_value = QWidget()
        mock_viz_widget.return_value = QWidget()

        widget = MenuWidget(viewer)
        qtbot.addWidget(widget)

        # Initially should not have visualization tab
        assert widget._has_visualization_tab() is False

    @patch("motile_tracker.application_menus.menu_widget.TracksViewer.get_instance")
    @patch("motile_tracker.application_menus.menu_widget.MotileWidget")
    @patch("motile_tracker.application_menus.menu_widget.EditingMenu")
    @patch("motile_tracker.application_menus.menu_widget.LabelVisualizationWidget")
    def test_has_visualization_tab_returns_true_when_present(
        self,
        mock_viz_widget,
        mock_editing_menu,
        mock_motile_widget,
        mock_get_instance,
        make_napari_viewer,
        qtbot,
        mock_tracks_viewer,
    ):
        """Test _has_visualization_tab returns True when tab is present."""
        viewer = make_napari_viewer()
        mock_get_instance.return_value = mock_tracks_viewer

        # Make the widget constructors return actual QWidgets
        mock_motile_widget.return_value = QWidget()
        mock_editing_menu.return_value = QWidget()
        mock_viz_widget.return_value = QWidget()

        widget = MenuWidget(viewer)
        qtbot.addWidget(widget)

        # Manually add visualization tab
        widget.tabwidget.addTab(widget.visualization_widget, "Visualization")

        assert widget._has_visualization_tab() is True


class TestToggleVisualizationWidget:
    """Test _toggle_visualization_widget method."""

    @patch("motile_tracker.application_menus.menu_widget.TracksViewer.get_instance")
    @patch("motile_tracker.application_menus.menu_widget.MotileWidget")
    @patch("motile_tracker.application_menus.menu_widget.EditingMenu")
    @patch("motile_tracker.application_menus.menu_widget.LabelVisualizationWidget")
    def test_toggle_adds_visualization_tab_when_seg_layer_exists(
        self,
        mock_viz_widget,
        mock_editing_menu,
        mock_motile_widget,
        mock_get_instance,
        make_napari_viewer,
        qtbot,
        mock_tracks_viewer,
    ):
        """Test _toggle_visualization_widget adds tab when seg_layer exists."""
        viewer = make_napari_viewer()
        mock_get_instance.return_value = mock_tracks_viewer

        # Make the widget constructors return actual QWidgets
        mock_motile_widget.return_value = QWidget()
        mock_editing_menu.return_value = QWidget()
        mock_viz_widget.return_value = QWidget()

        widget = MenuWidget(viewer)
        qtbot.addWidget(widget)

        # Initially no visualization tab
        assert widget.tabwidget.count() == 4

        # Set seg_layer to something (not None)
        mock_tracks_viewer.tracking_layers.seg_layer = MagicMock()

        # Call toggle
        widget._toggle_visualization_widget()

        # Should now have 5 tabs
        assert widget.tabwidget.count() == 5
        # Check the visualization tab was added at index 3
        assert widget.tabwidget.tabText(3) == "Visualization"

    @patch("motile_tracker.application_menus.menu_widget.TracksViewer.get_instance")
    @patch("motile_tracker.application_menus.menu_widget.MotileWidget")
    @patch("motile_tracker.application_menus.menu_widget.EditingMenu")
    @patch("motile_tracker.application_menus.menu_widget.LabelVisualizationWidget")
    def test_toggle_removes_visualization_tab_when_seg_layer_none(
        self,
        mock_viz_widget,
        mock_editing_menu,
        mock_motile_widget,
        mock_get_instance,
        make_napari_viewer,
        qtbot,
        mock_tracks_viewer,
    ):
        """Test _toggle_visualization_widget removes tab when seg_layer is None."""
        viewer = make_napari_viewer()
        mock_get_instance.return_value = mock_tracks_viewer

        # Make the widget constructors return actual QWidgets
        mock_motile_widget.return_value = QWidget()
        mock_editing_menu.return_value = QWidget()
        mock_viz_widget.return_value = QWidget()

        widget = MenuWidget(viewer)
        qtbot.addWidget(widget)

        # Add visualization tab first
        mock_tracks_viewer.tracking_layers.seg_layer = MagicMock()
        widget._toggle_visualization_widget()
        assert widget.tabwidget.count() == 5

        # Now remove seg_layer
        mock_tracks_viewer.tracking_layers.seg_layer = None
        widget._toggle_visualization_widget()

        # Should be back to 4 tabs
        assert widget.tabwidget.count() == 4
        # Visualization tab should be gone
        for i in range(widget.tabwidget.count()):
            assert widget.tabwidget.tabText(i) != "Visualization"

    @patch("motile_tracker.application_menus.menu_widget.TracksViewer.get_instance")
    @patch("motile_tracker.application_menus.menu_widget.MotileWidget")
    @patch("motile_tracker.application_menus.menu_widget.EditingMenu")
    @patch("motile_tracker.application_menus.menu_widget.LabelVisualizationWidget")
    def test_toggle_does_not_add_duplicate_tab(
        self,
        mock_viz_widget,
        mock_editing_menu,
        mock_motile_widget,
        mock_get_instance,
        make_napari_viewer,
        qtbot,
        mock_tracks_viewer,
    ):
        """Test _toggle_visualization_widget doesn't add duplicate tabs."""
        viewer = make_napari_viewer()
        mock_get_instance.return_value = mock_tracks_viewer

        # Make the widget constructors return actual QWidgets
        mock_motile_widget.return_value = QWidget()
        mock_editing_menu.return_value = QWidget()
        mock_viz_widget.return_value = QWidget()

        widget = MenuWidget(viewer)
        qtbot.addWidget(widget)

        # Set seg_layer
        mock_tracks_viewer.tracking_layers.seg_layer = MagicMock()

        # Call toggle twice
        widget._toggle_visualization_widget()
        assert widget.tabwidget.count() == 5

        widget._toggle_visualization_widget()
        # Should still be 5 tabs (not 6)
        assert widget.tabwidget.count() == 5

    @patch("motile_tracker.application_menus.menu_widget.TracksViewer.get_instance")
    @patch("motile_tracker.application_menus.menu_widget.MotileWidget")
    @patch("motile_tracker.application_menus.menu_widget.EditingMenu")
    @patch("motile_tracker.application_menus.menu_widget.LabelVisualizationWidget")
    def test_toggle_remembers_visualization_tab_index(
        self,
        mock_viz_widget,
        mock_editing_menu,
        mock_motile_widget,
        mock_get_instance,
        make_napari_viewer,
        qtbot,
        mock_tracks_viewer,
    ):
        """Test _toggle_visualization_widget remembers tab index when removing."""
        viewer = make_napari_viewer()
        mock_get_instance.return_value = mock_tracks_viewer

        # Make the widget constructors return actual QWidgets
        mock_motile_widget.return_value = QWidget()
        mock_editing_menu.return_value = QWidget()
        mock_viz_widget.return_value = QWidget()

        widget = MenuWidget(viewer)
        qtbot.addWidget(widget)

        # Add visualization tab
        mock_tracks_viewer.tracking_layers.seg_layer = MagicMock()
        widget._toggle_visualization_widget()
        viz_index = widget.tabwidget.indexOf(widget.visualization_widget)

        # Remove it
        mock_tracks_viewer.tracking_layers.seg_layer = None
        widget._toggle_visualization_widget()

        # Add it back
        mock_tracks_viewer.tracking_layers.seg_layer = MagicMock()
        widget._toggle_visualization_widget()

        # Should be at same index
        new_index = widget.tabwidget.indexOf(widget.visualization_widget)
        assert new_index == viz_index


class TestWidgetIntegration:
    """Test widget integration and signal connections."""

    @patch("motile_tracker.application_menus.menu_widget.TracksViewer.get_instance")
    @patch("motile_tracker.application_menus.menu_widget.MotileWidget")
    @patch("motile_tracker.application_menus.menu_widget.EditingMenu")
    @patch("motile_tracker.application_menus.menu_widget.LabelVisualizationWidget")
    def test_widget_is_resizable(
        self,
        mock_viz_widget,
        mock_editing_menu,
        mock_motile_widget,
        mock_get_instance,
        make_napari_viewer,
        qtbot,
        mock_tracks_viewer,
    ):
        """Test MenuWidget has resizable content."""
        viewer = make_napari_viewer()
        mock_get_instance.return_value = mock_tracks_viewer

        # Make the widget constructors return actual QWidgets
        mock_motile_widget.return_value = QWidget()
        mock_editing_menu.return_value = QWidget()
        mock_viz_widget.return_value = QWidget()

        widget = MenuWidget(viewer)
        qtbot.addWidget(widget)

        # Verify widget resizable is enabled
        assert widget.widgetResizable() is True

    @patch("motile_tracker.application_menus.menu_widget.TracksViewer.get_instance")
    @patch("motile_tracker.application_menus.menu_widget.MotileWidget")
    @patch("motile_tracker.application_menus.menu_widget.EditingMenu")
    @patch("motile_tracker.application_menus.menu_widget.LabelVisualizationWidget")
    def test_tracks_updated_signal_connected(
        self,
        mock_viz_widget,
        mock_editing_menu,
        mock_motile_widget,
        mock_get_instance,
        make_napari_viewer,
        qtbot,
        mock_tracks_viewer,
    ):
        """Test tracks_updated signal is connected to toggle method."""
        viewer = make_napari_viewer()
        mock_get_instance.return_value = mock_tracks_viewer

        # Make the widget constructors return actual QWidgets
        mock_motile_widget.return_value = QWidget()
        mock_editing_menu.return_value = QWidget()
        mock_viz_widget.return_value = QWidget()

        widget = MenuWidget(viewer)
        qtbot.addWidget(widget)

        # Verify connection was made
        mock_tracks_viewer.tracks_updated.connect.assert_called_once_with(
            widget._toggle_visualization_widget
        )
