"""Tests for RunEditor - the UI for configuring and starting tracking runs."""

import dask.array as da
import networkx as nx
import numpy as np
import pytest

from motile_tracker.motile.backend import MotileRun, SolverParams
from motile_tracker.motile.menus.run_editor import RunEditor


def test_run_editor_initialization(make_napari_viewer, segmentation_2d):
    """Test RunEditor widget initialization."""
    # Test 1: RunEditor creates all UI elements correctly
    viewer = make_napari_viewer()
    editor = RunEditor(viewer)
    assert editor.viewer is viewer
    assert editor.solver_params_widget is not None
    assert editor.run_name is not None
    assert editor.layer_selection_box is not None
    assert editor.run_name.text() == "new_run"

    # Test 2: RunEditor populates layer dropdown when layers exist
    viewer.add_labels(segmentation_2d, name="seg1")
    viewer.add_labels(segmentation_2d, name="seg2")
    editor2 = RunEditor(viewer)
    assert editor2.layer_selection_box.count() == 2
    assert editor2.layer_selection_box.itemText(0) in ["seg1", "seg2"]


def test_layer_management(make_napari_viewer, segmentation_2d, qtbot):
    """Test layer selection and management functionality."""
    viewer = make_napari_viewer()

    # Test 1: update_labels_layers adds new Labels layers
    editor = RunEditor(viewer)
    assert editor.layer_selection_box.count() == 0
    viewer.add_labels(segmentation_2d, name="seg1")
    assert editor.layer_selection_box.count() == 1
    assert editor.layer_selection_box.itemText(0) == "seg1"

    # Test 2: update_labels_layers adds Points layers
    points_data = np.array([[0, 10, 20], [1, 30, 40]])
    viewer.add_points(points_data, name="points1")
    assert editor.layer_selection_box.count() == 2
    assert "points1" in [editor.layer_selection_box.itemText(i) for i in range(2)]

    # Test 3: update_labels_layers ignores Image layers
    viewer.add_image(segmentation_2d.astype(float), name="image1")
    assert editor.layer_selection_box.count() == 2

    # Test 4: update_labels_layers preserves current selection
    viewer.add_labels(segmentation_2d, name="seg2")
    editor2 = RunEditor(viewer)
    editor2.layer_selection_box.setCurrentText("seg2")
    assert editor2.layer_selection_box.currentText() == "seg2"
    viewer.add_labels(segmentation_2d, name="seg3")
    assert editor2.layer_selection_box.currentText() == "seg2"

    # Test 5: get_input_layer returns the selected layer
    layer = viewer.add_labels(segmentation_2d, name="seg4")
    editor3 = RunEditor(viewer)
    editor3.layer_selection_box.setCurrentText("seg4")
    result = editor3.get_input_layer()
    assert result is layer

    # Test 6: get_input_layer returns None when nothing selected
    editor4 = RunEditor(make_napari_viewer())
    result = editor4.get_input_layer()
    assert result is None

    # Test 7: update_layer_selection enables IoU cost for Labels layers
    viewer2 = make_napari_viewer()
    viewer2.add_labels(segmentation_2d, name="seg_iou")
    editor5 = RunEditor(viewer2)
    qtbot.addWidget(editor5)
    editor5.show()
    editor5.layer_selection_box.setCurrentText("seg_iou")
    editor5.update_layer_selection()
    assert editor5.solver_params_widget.iou_row.isVisible()

    # Test 8: update_layer_selection disables IoU cost for Points layers
    viewer3 = make_napari_viewer()
    viewer3.add_points(points_data, name="points_iou")
    editor6 = RunEditor(viewer3)
    qtbot.addWidget(editor6)
    editor6.show()
    editor6.layer_selection_box.setCurrentText("points_iou")
    editor6.update_layer_selection()
    assert not editor6.solver_params_widget.iou_row.isVisible()


def test_duplicate_id_detection(segmentation_2d):
    """Test duplicate label ID detection."""
    # Test 1: _has_duplicate_ids returns False when no duplicates
    assert not RunEditor._has_duplicate_ids(segmentation_2d)

    # Test 2: _has_duplicate_ids returns True when duplicates exist
    seg_with_dups = segmentation_2d.copy()
    frame = seg_with_dups[1].copy()
    frame[frame == 2] = 1
    seg_with_dups[1] = frame
    assert RunEditor._has_duplicate_ids(seg_with_dups)

    # Test 3: _has_duplicate_ids returns False for single frame
    single_frame = np.zeros((1, 100, 100), dtype="int32")
    single_frame[0, 10:20, 10:20] = 1
    assert not RunEditor._has_duplicate_ids(single_frame)


def test_run_creation(make_napari_viewer, segmentation_2d):
    """Test creating MotileRun objects from editor state."""
    # Test 1: get_run creates run with Labels layer
    viewer = make_napari_viewer()
    viewer.add_labels(segmentation_2d, name="seg1", scale=(1, 2, 3))
    editor = RunEditor(viewer)
    editor.run_name.setText("test_run")
    editor.layer_selection_box.setCurrentText("seg1")
    run = editor.get_run()
    assert run is not None
    assert run.run_name == "test_run"
    assert run.segmentation is not None
    assert np.array_equal(run.segmentation, segmentation_2d)
    assert run.input_points is None
    assert tuple(run.scale) == (1, 2, 3)
    assert isinstance(run.graph, nx.DiGraph)

    # Test 2: get_run creates run with Points layer
    points_data = np.array([[0, 10, 20], [1, 30, 40]])
    viewer.add_points(points_data, name="points1", scale=(1, 2, 3))
    editor.run_name.setText("points_run")
    editor.layer_selection_box.setCurrentText("points1")
    run2 = editor.get_run()
    assert run2 is not None
    assert run2.run_name == "points_run"
    assert run2.segmentation is None
    assert run2.input_points is not None
    assert np.array_equal(run2.input_points, points_data)
    assert tuple(run2.scale) == (1, 2, 3)

    # Test 3: get_run returns None when no layer selected
    viewer2 = make_napari_viewer()
    editor2 = RunEditor(viewer2)
    with pytest.warns(UserWarning, match="No input layer selected"):
        run3 = editor2.get_run()
    assert run3 is None

    # Test 4: get_run raises error for 2D segmentation
    viewer3 = make_napari_viewer()
    seg_2d = np.zeros((100, 100), dtype="int32")
    viewer3.add_labels(seg_2d, name="seg1")
    editor3 = RunEditor(viewer3)
    editor3.layer_selection_box.setCurrentText("seg1")
    with pytest.raises(ValueError, match="Expected segmentation to be at least 3D"):
        editor3.get_run()

    # Test 5: get_run raises error for 5D segmentation
    viewer4 = make_napari_viewer()
    seg_5d = np.zeros((2, 2, 10, 100, 100), dtype="int32")
    viewer4.add_labels(seg_5d, name="seg1")
    editor4 = RunEditor(viewer4)
    editor4.layer_selection_box.setCurrentText("seg1")
    with pytest.raises(ValueError, match="Expected segmentation to be at most 4D"):
        editor4.get_run()

    # Test 6: get_run automatically relabels duplicate IDs
    viewer5 = make_napari_viewer()
    seg_with_dups = segmentation_2d.copy()
    frame = seg_with_dups[1].copy()
    frame[frame == 2] = 1
    seg_with_dups[1] = frame
    viewer5.add_labels(seg_with_dups, name="seg1")
    editor5 = RunEditor(viewer5)
    editor5.layer_selection_box.setCurrentText("seg1")
    run6 = editor5.get_run()
    assert run6 is not None
    assert not RunEditor._has_duplicate_ids(run6.segmentation)

    # Test 7: get_run converts dask array to numpy
    viewer6 = make_napari_viewer()
    dask_seg = da.from_array(segmentation_2d, chunks=(1, 50, 50))
    viewer6.add_labels(dask_seg, name="seg1")
    editor6 = RunEditor(viewer6)
    editor6.layer_selection_box.setCurrentText("seg1")
    run7 = editor6.get_run()
    assert run7 is not None
    assert isinstance(run7.segmentation, np.ndarray)
    assert not isinstance(run7.segmentation, da.Array)

    # Test 8: get_run uses solver params from the editor
    viewer.add_labels(segmentation_2d, name="seg_params")
    editor7 = RunEditor(viewer)
    editor7.layer_selection_box.setCurrentText("seg_params")
    editor7.solver_params_widget.solver_params.max_edge_distance = 123.0
    run8 = editor7.get_run()
    assert run8 is not None
    assert run8.solver_params.max_edge_distance == 123.0


def test_signal_emission(make_napari_viewer, segmentation_2d, qtbot):
    """Test signal emission when starting runs."""
    viewer = make_napari_viewer()

    # Test 1: emit_run emits start_run signal when run is valid
    viewer.add_labels(segmentation_2d, name="seg1")
    editor = RunEditor(viewer)
    editor.layer_selection_box.setCurrentText("seg1")
    with qtbot.waitSignal(editor.start_run, timeout=1000) as blocker:
        editor.emit_run()
    run = blocker.args[0]
    assert isinstance(run, MotileRun)

    # Test 2: emit_run doesn't emit signal when no layer selected
    viewer2 = make_napari_viewer()
    editor2 = RunEditor(viewer2)
    with qtbot.assertNotEmitted(editor2.start_run), pytest.warns(UserWarning):
        editor2.emit_run()


def test_new_run(make_napari_viewer, segmentation_2d, qtbot):
    """Test loading existing runs into editor."""
    viewer = make_napari_viewer()
    editor = RunEditor(viewer)

    # Test: new_run loads run name and solver params
    custom_params = SolverParams(max_edge_distance=999.0, max_children=5)
    existing_run = MotileRun(
        graph=nx.DiGraph(),
        segmentation=segmentation_2d,
        run_name="existing_run",
        solver_params=custom_params,
    )
    editor.new_run(existing_run)
    assert editor.run_name.text() == "existing_run"
    qtbot.wait(100)
    assert editor.solver_params_widget.solver_params.max_edge_distance == 999.0
    assert editor.solver_params_widget.solver_params.max_children == 5


def test_max_frames_update(make_napari_viewer, segmentation_2d):
    """Test updating max frame constraint from viewer dims."""
    viewer = make_napari_viewer()
    viewer.add_labels(segmentation_2d, name="seg1")

    # Test: _update_max_frames updates constraint based on viewer dims
    editor = RunEditor(viewer)
    editor._update_max_frames()
    max_frame = int(viewer.dims.range[0].stop)
    assert (
        editor.solver_params_widget.single_window_start_row.param_value.maximum()
        == max_frame - 1
    )
