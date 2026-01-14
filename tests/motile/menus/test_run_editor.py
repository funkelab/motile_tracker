"""Tests for RunEditor - the UI for configuring and starting tracking runs."""

import dask.array as da
import networkx as nx
import numpy as np
import pytest

from motile_tracker.motile.backend import MotileRun, SolverParams
from motile_tracker.motile.menus.run_editor import RunEditor


class TestRunEditorInitialization:
    """Test RunEditor widget initialization."""

    def test_initialization(self, make_napari_viewer):
        """Test RunEditor creates all UI elements correctly."""
        viewer = make_napari_viewer()
        editor = RunEditor(viewer)

        # Verify main components exist
        assert editor.viewer is viewer
        assert editor.solver_params_widget is not None
        assert editor.run_name is not None
        assert editor.layer_selection_box is not None

        # Verify default run name
        assert editor.run_name.text() == "new_run"

    def test_initialization_with_layers(self, make_napari_viewer, segmentation_2d):
        """Test RunEditor populates layer dropdown when layers exist."""
        viewer = make_napari_viewer()
        viewer.add_labels(segmentation_2d, name="seg1")
        viewer.add_labels(segmentation_2d, name="seg2")

        editor = RunEditor(viewer)

        # Verify layers were added to dropdown
        assert editor.layer_selection_box.count() == 2
        assert editor.layer_selection_box.itemText(0) in ["seg1", "seg2"]


class TestLayerManagement:
    """Test layer selection and management functionality."""

    def test_update_labels_layers_adds_labels(
        self, make_napari_viewer, segmentation_2d
    ):
        """Test update_labels_layers adds new Labels layers."""
        viewer = make_napari_viewer()
        editor = RunEditor(viewer)

        # Initially no layers
        assert editor.layer_selection_box.count() == 0

        # Add labels layer
        viewer.add_labels(segmentation_2d, name="seg1")

        # Should have been added automatically via signal
        assert editor.layer_selection_box.count() == 1
        assert editor.layer_selection_box.itemText(0) == "seg1"

    def test_update_labels_layers_adds_points(self, make_napari_viewer):
        """Test update_labels_layers adds Points layers."""
        viewer = make_napari_viewer()
        editor = RunEditor(viewer)

        # Add points layer
        points_data = np.array([[0, 10, 20], [1, 30, 40]])
        viewer.add_points(points_data, name="points1")

        # Should have been added
        assert editor.layer_selection_box.count() == 1
        assert editor.layer_selection_box.itemText(0) == "points1"

    def test_update_labels_layers_ignores_image_layers(
        self, make_napari_viewer, segmentation_2d
    ):
        """Test update_labels_layers ignores Image layers."""
        viewer = make_napari_viewer()
        editor = RunEditor(viewer)

        # Add image layer (should be ignored)
        viewer.add_image(segmentation_2d.astype(float), name="image1")

        # Should not be added
        assert editor.layer_selection_box.count() == 0

    def test_update_labels_layers_preserves_selection(
        self, make_napari_viewer, segmentation_2d
    ):
        """Test update_labels_layers preserves current selection."""
        viewer = make_napari_viewer()
        viewer.add_labels(segmentation_2d, name="seg1")
        viewer.add_labels(segmentation_2d, name="seg2")

        editor = RunEditor(viewer)

        # Select seg2
        editor.layer_selection_box.setCurrentText("seg2")
        assert editor.layer_selection_box.currentText() == "seg2"

        # Add another layer
        viewer.add_labels(segmentation_2d, name="seg3")

        # Selection should still be seg2
        assert editor.layer_selection_box.currentText() == "seg2"

    def test_get_input_layer_returns_selected_layer(
        self, make_napari_viewer, segmentation_2d
    ):
        """Test get_input_layer returns the selected layer."""
        viewer = make_napari_viewer()
        layer = viewer.add_labels(segmentation_2d, name="seg1")

        editor = RunEditor(viewer)
        editor.layer_selection_box.setCurrentText("seg1")

        result = editor.get_input_layer()
        assert result is layer

    def test_get_input_layer_returns_none_when_no_selection(self, make_napari_viewer):
        """Test get_input_layer returns None when nothing selected."""
        viewer = make_napari_viewer()
        editor = RunEditor(viewer)

        result = editor.get_input_layer()
        assert result is None

    def test_update_layer_selection_enables_iou_for_labels(
        self, make_napari_viewer, segmentation_2d, qtbot
    ):
        """Test update_layer_selection enables IoU cost for Labels layers."""
        viewer = make_napari_viewer()
        viewer.add_labels(segmentation_2d, name="seg1")

        editor = RunEditor(viewer)
        qtbot.addWidget(editor)
        editor.show()
        editor.layer_selection_box.setCurrentText("seg1")
        editor.update_layer_selection()

        # IoU row should be visible for Labels
        assert editor.solver_params_widget.iou_row.isVisible()

    def test_update_layer_selection_disables_iou_for_points(
        self, make_napari_viewer, qtbot
    ):
        """Test update_layer_selection disables IoU cost for Points layers."""
        viewer = make_napari_viewer()
        points_data = np.array([[0, 10, 20], [1, 30, 40]])
        viewer.add_points(points_data, name="points1")

        editor = RunEditor(viewer)
        qtbot.addWidget(editor)
        editor.show()
        editor.layer_selection_box.setCurrentText("points1")
        editor.update_layer_selection()

        # IoU row should be hidden for Points
        assert not editor.solver_params_widget.iou_row.isVisible()


class TestDuplicateIDDetection:
    """Test duplicate label ID detection."""

    def test_has_duplicate_ids_no_duplicates(self, segmentation_2d):
        """Test _has_duplicate_ids returns False when no duplicates."""
        assert not RunEditor._has_duplicate_ids(segmentation_2d)

    def test_has_duplicate_ids_with_duplicates(self, segmentation_2d):
        """Test _has_duplicate_ids returns True when duplicates exist."""
        # Make frame 2 have same label as frame 1
        frame = segmentation_2d[1].copy()
        frame[frame == 2] = 1
        segmentation_2d[1] = frame

        assert RunEditor._has_duplicate_ids(segmentation_2d)

    def test_has_duplicate_ids_single_frame(self):
        """Test _has_duplicate_ids returns False for single frame."""
        single_frame = np.zeros((1, 100, 100), dtype="int32")
        single_frame[0, 10:20, 10:20] = 1

        assert not RunEditor._has_duplicate_ids(single_frame)


class TestRunCreation:
    """Test creating MotileRun objects from editor state."""

    def test_get_run_with_labels_layer(self, make_napari_viewer, segmentation_2d):
        """Test get_run creates run with Labels layer."""
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

    def test_get_run_with_points_layer(self, make_napari_viewer):
        """Test get_run creates run with Points layer."""
        viewer = make_napari_viewer()
        points_data = np.array([[0, 10, 20], [1, 30, 40]])
        viewer.add_points(points_data, name="points1", scale=(1, 2, 3))

        editor = RunEditor(viewer)
        editor.run_name.setText("points_run")
        editor.layer_selection_box.setCurrentText("points1")

        run = editor.get_run()

        assert run is not None
        assert run.run_name == "points_run"
        assert run.segmentation is None
        assert run.input_points is not None
        assert np.array_equal(run.input_points, points_data)
        assert tuple(run.scale) == (1, 2, 3)

    def test_get_run_with_no_layer_returns_none(self, make_napari_viewer):
        """Test get_run returns None when no layer selected."""
        viewer = make_napari_viewer()
        editor = RunEditor(viewer)

        with pytest.warns(UserWarning, match="No input layer selected"):
            run = editor.get_run()

        assert run is None

    def test_get_run_with_invalid_dimensions_too_few(self, make_napari_viewer):
        """Test get_run raises error for 2D segmentation."""
        viewer = make_napari_viewer()
        # 2D segmentation (missing time dimension)
        seg_2d = np.zeros((100, 100), dtype="int32")
        viewer.add_labels(seg_2d, name="seg1")

        editor = RunEditor(viewer)
        editor.layer_selection_box.setCurrentText("seg1")

        with pytest.raises(ValueError, match="Expected segmentation to be at least 3D"):
            editor.get_run()

    def test_get_run_with_invalid_dimensions_too_many(self, make_napari_viewer):
        """Test get_run raises error for 5D segmentation."""
        viewer = make_napari_viewer()
        # 5D segmentation (too many dimensions)
        seg_5d = np.zeros((2, 2, 10, 100, 100), dtype="int32")
        viewer.add_labels(seg_5d, name="seg1")

        editor = RunEditor(viewer)
        editor.layer_selection_box.setCurrentText("seg1")

        with pytest.raises(ValueError, match="Expected segmentation to be at most 4D"):
            editor.get_run()

    def test_get_run_relabels_duplicates(self, make_napari_viewer, segmentation_2d):
        """Test get_run automatically relabels duplicate IDs."""
        viewer = make_napari_viewer()

        # Create segmentation with duplicate IDs across frames
        seg_with_dups = segmentation_2d.copy()
        frame = seg_with_dups[1].copy()
        frame[frame == 2] = 1  # Make label 1 appear in both frames
        seg_with_dups[1] = frame

        viewer.add_labels(seg_with_dups, name="seg1")

        editor = RunEditor(viewer)
        editor.layer_selection_box.setCurrentText("seg1")

        run = editor.get_run()

        # Should succeed and relabel duplicates
        assert run is not None
        # Verify IDs are unique across frames
        assert not RunEditor._has_duplicate_ids(run.segmentation)

    def test_get_run_with_dask_array(self, make_napari_viewer, segmentation_2d):
        """Test get_run converts dask array to numpy."""
        viewer = make_napari_viewer()

        # Create dask array from numpy
        dask_seg = da.from_array(segmentation_2d, chunks=(1, 50, 50))
        viewer.add_labels(dask_seg, name="seg1")

        editor = RunEditor(viewer)
        editor.layer_selection_box.setCurrentText("seg1")

        run = editor.get_run()

        # Should succeed and convert to numpy
        assert run is not None
        assert isinstance(run.segmentation, np.ndarray)
        assert not isinstance(run.segmentation, da.Array)

    def test_get_run_uses_current_solver_params(
        self, make_napari_viewer, segmentation_2d
    ):
        """Test get_run uses solver params from the editor."""
        viewer = make_napari_viewer()
        viewer.add_labels(segmentation_2d, name="seg1")

        editor = RunEditor(viewer)
        editor.layer_selection_box.setCurrentText("seg1")

        # Modify solver params
        editor.solver_params_widget.solver_params.max_edge_distance = 123.0

        run = editor.get_run()

        assert run is not None
        assert run.solver_params.max_edge_distance == 123.0


class TestSignalEmission:
    """Test signal emission when starting runs."""

    def test_emit_run_emits_signal_when_run_valid(
        self, make_napari_viewer, segmentation_2d, qtbot
    ):
        """Test emit_run emits start_run signal when run is valid."""
        viewer = make_napari_viewer()
        viewer.add_labels(segmentation_2d, name="seg1")

        editor = RunEditor(viewer)
        editor.layer_selection_box.setCurrentText("seg1")

        with qtbot.waitSignal(editor.start_run, timeout=1000) as blocker:
            editor.emit_run()

        # Signal should have been emitted with a MotileRun
        run = blocker.args[0]
        assert isinstance(run, MotileRun)

    def test_emit_run_does_not_emit_when_no_layer(self, make_napari_viewer, qtbot):
        """Test emit_run doesn't emit signal when no layer selected."""
        viewer = make_napari_viewer()
        editor = RunEditor(viewer)

        # Should not emit signal
        with qtbot.assertNotEmitted(editor.start_run), pytest.warns(UserWarning):
            editor.emit_run()


class TestNewRun:
    """Test loading existing runs into editor."""

    def test_new_run_loads_name_and_params(
        self, make_napari_viewer, segmentation_2d, qtbot
    ):
        """Test new_run loads run name and solver params."""
        viewer = make_napari_viewer()
        editor = RunEditor(viewer)

        # Create a run with custom params
        custom_params = SolverParams(max_edge_distance=999.0, max_children=5)
        existing_run = MotileRun(
            graph=nx.DiGraph(),
            segmentation=segmentation_2d,
            run_name="existing_run",
            solver_params=custom_params,
        )

        # Load the run into editor
        editor.new_run(existing_run)

        # Verify name was loaded
        assert editor.run_name.text() == "existing_run"

        # Verify params were loaded (wait for signal propagation)
        qtbot.wait(100)
        assert editor.solver_params_widget.solver_params.max_edge_distance == 999.0
        assert editor.solver_params_widget.solver_params.max_children == 5


class TestMaxFramesUpdate:
    """Test updating max frame constraint from viewer dims."""

    def test_update_max_frames_from_viewer_dims(
        self, make_napari_viewer, segmentation_2d
    ):
        """Test _update_max_frames updates constraint based on viewer dims."""
        viewer = make_napari_viewer()
        viewer.add_labels(segmentation_2d, name="seg1")

        editor = RunEditor(viewer)

        # Call _update_max_frames to update the constraint
        editor._update_max_frames()

        # Verify max_frame constraint was set correctly
        max_frame = int(viewer.dims.range[0].stop)
        assert (
            editor.solver_params_widget.single_window_start_row.param_value.maximum()
            == max_frame - 1
        )
