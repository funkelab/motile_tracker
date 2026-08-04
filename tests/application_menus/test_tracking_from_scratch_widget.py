"""Tests for TrackingFromScratch - creating tracks from an empty graph.

The 'track from scratch' flow is the only place where a Tracks object is displayed
with *zero* nodes, so it exercises code paths (layer construction, colormaps, tree
view, table) that every other flow only ever sees with data in them. These tests
guard that empty-graph path end to end: creating the empty tracks, connecting a
source layer, copying detections in, and undoing back to empty again.
"""

import numpy as np
import pytest
from napari.layers import Labels, Points

from motile_tracker.application_menus.tracking_from_scratch_widget import (
    TrackingFromScratch,
)
from motile_tracker.data_views.views.layers.track_labels import TrackLabels
from motile_tracker.data_views.views.layers.track_points import TrackPoints
from motile_tracker.data_views.views.table.custom_table_widget import (
    ColoredTableWidget,
)
from motile_tracker.data_views.views.tree_view.tree_widget import TreeWidget


def _source_labels(shape=(5, 10, 10)) -> np.ndarray:
    """Segmentation with one 3x3 label per frame, a different value in each frame."""

    data = np.zeros(shape, dtype=np.uint16)
    for t in range(shape[0]):
        data[t, 2:5, 2:5] = t + 1
    return data


def _source_points(n_frames=5) -> np.ndarray:
    return np.array([[t, 3.0, 4.0] for t in range(n_frames)])


@pytest.fixture
def scratch_app(make_napari_viewer):
    """A viewer with a size layer, the from-scratch widget, and the two data views
    that also have to cope with an empty graph (tree view and table)."""

    viewer = make_napari_viewer()
    viewer.add_image(np.zeros((5, 10, 10), dtype=np.uint16), name="img")
    widget = TrackingFromScratch(viewer)
    table = ColoredTableWidget(viewer)
    tree = TreeWidget(viewer)
    return viewer, widget, table, tree


@pytest.mark.parametrize(
    ("mode", "layer_type"), [("points", TrackPoints), ("labels", TrackLabels)]
)
def test_start_tracking_creates_empty_tracks(scratch_app, mode, layer_type):
    """Creating empty tracks must build the track layers without raising.

    Regression guard: TrackPoints used to hand napari a (0, 4) face-color array for
    an empty graph, which crashes in `transform_color` ('zero-size array to reduction
    operation minimum').
    """

    _viewer, widget, table, _tree = scratch_app
    widget.size_layer_dropdown.setCurrentText("img")
    widget._start_tracking(mode)

    tracks_viewer = widget.tracks_viewer
    assert tracks_viewer.tracks is not None
    assert tracks_viewer.tracks.graph.num_nodes() == 0
    assert widget._mode == mode
    assert widget.chain_btn.isEnabled()

    # the track layers exist and are empty
    points_layer = tracks_viewer.tracking_layers.points_layer
    assert isinstance(points_layer, TrackPoints)
    assert len(points_layer.data) == 0
    if mode == "labels":
        assert isinstance(tracks_viewer.tracking_layers.seg_layer, layer_type)
    else:
        assert tracks_viewer.tracking_layers.seg_layer is None

    # the table view survives an empty graph
    assert table._model.rowCount() == 0
    assert table._id_to_row == {}


def test_source_dropdown_follows_mode(scratch_app):
    """The source dropdown offers Labels for a segmentation-backed tree and Points
    for a points-only tree, in both cases excluding the track layers themselves."""

    _viewer, widget, _table, _tree = scratch_app
    widget.size_layer_dropdown.setCurrentText("img")

    widget._start_tracking("labels")
    assert widget.source_layer_dropdown.layer_types == (Labels,)
    assert widget.source_layer_dropdown.exclude_types == (TrackLabels,)

    widget._start_tracking("points")
    assert widget.source_layer_dropdown.layer_types == (Points,)
    assert widget.source_layer_dropdown.exclude_types == (TrackPoints,)


def test_copy_labels_from_source(scratch_app):
    """Copying labels from a connected source layer grows the tracks and the views."""

    viewer, widget, table, _tree = scratch_app
    source = viewer.add_labels(_source_labels(), name="src")

    widget.size_layer_dropdown.setCurrentText("img")
    widget._start_tracking("labels")
    widget.source_layer_dropdown.setCurrentText("src")
    widget.chain_btn.setChecked(True)

    assert widget._source_layer is source
    assert widget.copy_controls_box.isVisibleTo(widget)

    tracks = widget.tracks_viewer.tracks
    for t in range(3):
        frame = np.asarray(source.data[t])
        widget._add_segmentation_node(t, np.where(frame == t + 1))

    assert tracks.graph.num_nodes() == 3
    assert table._model.rowCount() == 3
    # all copies share the current tracklet id
    track_ids = {tracks.get_track_id(node) for node in tracks.graph.node_ids()}
    assert track_ids == {widget.tracks_viewer.selected_track}


def test_copy_labels_as_new_track(scratch_app):
    """With 'copy as new track' checked, copying into a frame that already holds a
    node of the current tracklet starts a new tracklet instead of growing it."""

    viewer, widget, _table, _tree = scratch_app
    source = viewer.add_labels(_source_labels(), name="src")

    widget.size_layer_dropdown.setCurrentText("img")
    widget._start_tracking("labels")
    widget.source_layer_dropdown.setCurrentText("src")
    widget.chain_btn.setChecked(True)

    tracks = widget.tracks_viewer.tracks
    frame = np.asarray(source.data[0])
    widget._add_segmentation_node(0, np.where(frame == 1))
    first_track_id = widget.tracks_viewer.selected_track

    # copy a non-overlapping label into the same frame
    widget.new_track_on_copy_checkbox.setChecked(True)
    widget._add_segmentation_node(0, (np.array([7, 7, 8]), np.array([7, 8, 7])))

    assert tracks.graph.num_nodes() == 2
    assert widget.tracks_viewer.selected_track != first_track_id


def test_copy_points_from_source(scratch_app):
    """Copying points from a connected Points source layer adds point nodes."""

    viewer, widget, table, _tree = scratch_app
    source = viewer.add_points(_source_points(), name="src_pts")

    widget.size_layer_dropdown.setCurrentText("img")
    widget._start_tracking("points")
    widget.source_layer_dropdown.setCurrentText("src_pts")
    widget.chain_btn.setChecked(True)

    assert widget._source_layer is source

    tracks = widget.tracks_viewer.tracks
    for t in range(3):
        widget._add_node(t, position=np.array([3.0, 4.0]))

    assert tracks.graph.num_nodes() == 3
    assert table._model.rowCount() == 3


def test_undo_back_to_empty(scratch_app):
    """Undoing every copy returns the tracks (and the views) to the empty state."""

    viewer, widget, table, _tree = scratch_app
    source = viewer.add_labels(_source_labels(), name="src")

    widget.size_layer_dropdown.setCurrentText("img")
    widget._start_tracking("labels")
    widget.source_layer_dropdown.setCurrentText("src")
    widget.chain_btn.setChecked(True)

    tracks_viewer = widget.tracks_viewer
    for t in range(3):
        frame = np.asarray(source.data[t])
        widget._add_segmentation_node(t, np.where(frame == t + 1))
    assert tracks_viewer.tracks.graph.num_nodes() == 3

    for _ in range(3):
        tracks_viewer.undo()

    assert tracks_viewer.tracks.graph.num_nodes() == 0
    assert table._model.rowCount() == 0
    assert len(tracks_viewer.tracking_layers.points_layer.data) == 0

    for _ in range(3):
        tracks_viewer.redo()
    assert tracks_viewer.tracks.graph.num_nodes() == 3


def test_chain_toggle_connects_and_disconnects(scratch_app):
    """Toggling the chain button attaches and detaches the source-layer callbacks."""

    viewer, widget, _table, _tree = scratch_app
    source = viewer.add_labels(_source_labels(), name="src")

    widget.size_layer_dropdown.setCurrentText("img")
    widget._start_tracking("labels")
    widget.source_layer_dropdown.setCurrentText("src")

    widget.chain_btn.setChecked(True)
    assert widget._source_layer is source
    assert widget._source_callback in source.mouse_drag_callbacks
    assert hasattr(source, "_manual_copy_detection")

    widget.chain_btn.setChecked(False)
    assert widget._source_layer is None
    assert not hasattr(source, "_manual_copy_detection")
    assert not widget.copy_controls_box.isVisibleTo(widget)


def test_switch_layer_toggles_active_layer(scratch_app):
    """The switch button flips the active layer between source and target."""

    viewer, widget, _table, _tree = scratch_app
    source = viewer.add_labels(_source_labels(), name="src")

    widget.size_layer_dropdown.setCurrentText("img")
    widget._start_tracking("labels")
    widget.source_layer_dropdown.setCurrentText("src")
    widget.chain_btn.setChecked(True)

    target = widget._get_target_layer()
    assert viewer.layers.selection.active is source

    widget._switch_layer()
    assert viewer.layers.selection.active is target

    widget._switch_layer()
    assert viewer.layers.selection.active is source


def test_new_tracks_reset_the_connection(scratch_app):
    """Creating a second empty tree drops the source connection of the first one."""

    viewer, widget, _table, _tree = scratch_app
    source = viewer.add_labels(_source_labels(), name="src")

    widget.size_layer_dropdown.setCurrentText("img")
    widget._start_tracking("labels")
    widget.source_layer_dropdown.setCurrentText("src")
    widget.chain_btn.setChecked(True)
    assert widget._source_layer is source

    widget._start_tracking("labels")
    assert widget._source_layer is None
    assert not widget.chain_btn.isChecked()
