import pytest
from funtracks.data_model import SolutionTracks

from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


@pytest.mark.parametrize(
    "mode", ["all", "visible_no_contours", "visible_with_contours"]
)
def test_update_label_colormap(
    make_napari_viewer,
    graph_3d,
    segmentation_3d,
    mode,
):
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

    # Ensure known starting alpha
    for k in [k1, k2]:
        cmap.color_dict[k][-1] = 0.3

    # Make the viewer highlight one label
    tracks_viewer.selected_nodes = [k2]

    # Call update_label_colormap in each test mode
    if mode == "all":
        seg_layer.update_label_colormap("all")
        # visible == "all" → all non-0, non-None get alpha 0.6
        assert seg_layer.colormap.color_dict[k0][-1] == pytest.approx(0.6)
        assert seg_layer.colormap.color_dict[k1][-1] == pytest.approx(0.6)
        assert seg_layer.colormap.color_dict[k2][-1] == 1.0  # because highlighted

    elif mode == "visible_no_contours":
        tracks_viewer.use_contours = False
        visible = [k1]
        seg_layer.update_label_colormap(visible)

        # normal mode: non visible labels get 0, visible labels get 0.6, highlighted gets 1
        assert seg_layer.colormap.color_dict[k0][-1] == pytest.approx(0)
        assert seg_layer.colormap.color_dict[k1][-1] == pytest.approx(0.6)
        assert seg_layer.colormap.color_dict[k2][-1] == 1.0  # highlight overrides

    elif mode == "visible_with_contours":
        tracks_viewer.use_contours = True
        visible = [k1]
        seg_layer.update_label_colormap(visible)

        # contour mode: everything gets 0.6 except highlighted
        assert seg_layer.colormap.color_dict[k0][-1] == pytest.approx(0.6)
        assert seg_layer.colormap.color_dict[k1][-1] == pytest.approx(0.6)
        assert seg_layer.colormap.color_dict[k2][-1] == pytest.approx(1.0)

        # contour flag should have been activated
        assert seg_layer.contour in (1, True)
