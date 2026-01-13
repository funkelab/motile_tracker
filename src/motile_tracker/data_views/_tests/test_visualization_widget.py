import pytest
from funtracks.data_model import SolutionTracks

from motile_tracker.application_menus.visualization_widget import (
    LabelVisualizationWidget,
)
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


@pytest.fixture
def visualization_widget(make_napari_viewer, graph_3d, segmentation_3d, qtbot):
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_3d, segmentation=segmentation_3d, ndim=4)

    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    widget = LabelVisualizationWidget(viewer)
    qtbot.addWidget(widget)

    assert tracks_viewer.tracking_layers.seg_layer is not None

    return widget, tracks_viewer


@pytest.mark.parametrize("mode", ["lineage", "group", "all"])
def test_switch_display_modes(visualization_widget, mode):
    """Test that checking the radio buttons changes the display mode"""

    widget, tracks_viewer = visualization_widget

    widget.mode_widget.button_for_mode(mode).setChecked(True)

    assert tracks_viewer.mode == mode
    assert widget.background_widget.isEnabled() is (mode != "all")


@pytest.mark.parametrize("mode", ["lineage", "group", "all"])
def test_mode_update_syncs_radio_buttons(visualization_widget, mode):
    """Check that the radio button states are updated when the tracks_viewer updates its
    display mode."""

    widget, tracks_viewer = visualization_widget

    tracks_viewer.set_display_mode(mode)
    widget._update_widget_availability()
    radio = widget.mode_widget.button_for_mode(mode)

    assert radio.isChecked()


def test_opacity_updates_seg_layer(visualization_widget):
    """Test that changing the opacity in the widget updates the highlighted/foreground/
    background opacity of the labels."""

    widget, tracks_viewer = visualization_widget
    layer = tracks_viewer.tracking_layers.seg_layer

    widget.highlight_widget.opacity.setValue(0.25)
    widget.foreground_widget.opacity.setValue(0.5)
    widget.background_widget.opacity.setValue(0.75)

    assert layer.highlight_opacity == pytest.approx(0.25)
    assert layer.foreground_opacity == pytest.approx(0.5)
    assert layer.background_opacity == pytest.approx(0.75)


def test_contour_checkbox_updates_layer(visualization_widget):
    """Test that contour (fill) checkboxes are hidden, unless in contour mode, and that
    toggling them changes the contour state on the seg_layer."""

    widget, tracks_viewer = visualization_widget
    layer = tracks_viewer.tracking_layers.seg_layer

    # mode where contour is not available
    widget.mode_widget.button_for_mode("all").setChecked(True)
    layer.contour = 0

    assert widget.highlight_widget.contour.isHidden()
    assert widget.foreground_widget.contour.isHidden()

    # still hidden, because contour is still 0
    widget.mode_widget.button_for_mode("lineage").setChecked(True)

    assert widget.highlight_widget.contour.isHidden()
    assert widget.foreground_widget.contour.isHidden()

    # Enable contours, ensure widgets are visible
    layer.contour = 1

    assert not widget.highlight_widget.contour.isHidden()
    assert not widget.foreground_widget.contour.isHidden()

    # Check = fill = contour OFF
    widget.highlight_widget.contour.setChecked(True)
    widget.foreground_widget.contour.setChecked(False)

    assert layer.highlight_contour is False
    assert layer.foreground_contour is True


@pytest.mark.parametrize(
    "mode", ["all", "visible_no_contours", "visible_with_contours"]
)
def test_update_label_colormap_when_selecting(
    make_napari_viewer,
    graph_3d,
    segmentation_3d,
    mode,
):
    """Test the actual values on the label colormap"""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(
        graph=graph_3d,
        segmentation=segmentation_3d,
        ndim=4,
    )

    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    seg_layer = tracks_viewer.tracking_layers.seg_layer
    assert hasattr(seg_layer, "update_label_colormap")

    cmap = seg_layer.colormap

    # Select specific labels for deterministic testing
    keys = list(cmap.color_dict.keys())
    numeric_keys = [k for k in keys if isinstance(k, int) and k != 0][:3]
    k0, k1, k2 = numeric_keys[:3]  # two labels for testing

    # Set a random starting value, to ensure it got updated
    for k in [k1, k2]:
        cmap.color_dict[k][-1] = 0.5

    assert seg_layer.background_opacity == 0.3
    assert seg_layer.foreground_opacity == 0.6
    assert seg_layer.highlight_opacity == 1.0

    # Make the viewer highlight one label
    tracks_viewer.selected_nodes = [k2]

    # Call update_label_colormap in each test mode
    if mode == "all":
        seg_layer.update_label_colormap("all")
        # visible == "all" → all non-0, non-None get alpha 0.6 (foreground opacity)
        assert seg_layer.colormap.color_dict[k0][-1] == pytest.approx(
            seg_layer.foreground_opacity
        )
        assert seg_layer.colormap.color_dict[k1][-1] == pytest.approx(
            seg_layer.foreground_opacity
        )
        assert seg_layer.colormap.color_dict[k2][-1] == seg_layer.highlight_opacity

        assert seg_layer.filled_labels == []

    elif mode == "visible_no_contours":
        visible = [k1]  # simulate lineage/group mode
        seg_layer.update_label_colormap(visible)

        # normal mode: background labels get 0.3, foreground labels get 0.6, highlighted gets 1
        assert seg_layer.colormap.color_dict[k0][-1] == pytest.approx(
            seg_layer.background_opacity
        )
        assert seg_layer.colormap.color_dict[k1][-1] == pytest.approx(
            seg_layer.foreground_opacity
        )
        assert seg_layer.colormap.color_dict[k2][-1] == seg_layer.highlight_opacity

        assert seg_layer.filled_labels == []

    elif mode == "visible_with_contours":
        seg_layer.contour = 1
        visible = [k1]
        seg_layer.update_label_colormap(visible)

        # contour mode: background labels have 0.3,
        assert seg_layer.colormap.color_dict[k0][-1] == pytest.approx(
            seg_layer.background_opacity
        )  # background
        assert seg_layer.colormap.color_dict[k1][-1] == pytest.approx(
            seg_layer.foreground_opacity
        )  # foreground
        assert seg_layer.colormap.color_dict[k2][-1] == pytest.approx(
            seg_layer.highlight_opacity
        )  # highlighted

        assert set(seg_layer.filled_labels) == {k1, k2}
