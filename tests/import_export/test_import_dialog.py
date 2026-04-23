"""Integration test for CSV and GEFF import workflow.
Tests the full round-trip: export tracks using motile_tracker's method,
then import them back through the import dialog.
Also test for the visibility of various widgets based on 2D/3D and
segmentation inclusion.
"""

from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest
import tifffile
import zarr
from funtracks.data_model import Tracks
from funtracks.import_export import export_to_csv, export_to_geff

from motile_tracker.import_export.menus.import_dialog import ImportDialog
from motile_tracker.import_export.menus.segmentation_widgets import (
    geff_has_embedded_segmentation,
)
from motile_tracker.motile.backend.motile_run import MotileRun
from motile_tracker.motile.backend.solver_params import SolverParams


@pytest.fixture(autouse=True)
def mock_qmessagebox(monkeypatch):
    """Mock QMessageBox to prevent blocking popups in all tests.

    Raises AssertionError if a critical dialog is shown, surfacing the error message.
    """
    mock_msgbox = MagicMock()

    def critical_side_effect(parent, title, message):
        raise AssertionError(f"Unexpected error dialog: {title} - {message}")

    mock_msgbox.critical.side_effect = critical_side_effect
    monkeypatch.setattr(
        "motile_tracker.import_export.menus.import_dialog.QMessageBox",
        mock_msgbox,
    )
    monkeypatch.setattr(
        "motile_tracker.import_export.menus.geff_import_widget.QMessageBox",
        mock_msgbox,
    )
    return mock_msgbox


@pytest.fixture
def small_csv(tmp_path: Path) -> Path:
    p = tmp_path / "test.csv"
    df = pd.DataFrame(
        {
            "id": [1, 2],
            "parent_id": [None, 1],
            "time": [0, 1],
            "y": [10.0, 20.0],
            "x": [5.0, 15.0],
            "area": [100.0, 150.0],
            "group": [True, False],
        }
    )
    df.to_csv(p, index=False)
    return p


@pytest.mark.parametrize("dim_3d", [False, True])
@pytest.mark.parametrize("include_seg", [False, True])
def test_import_dialog_csv(qtbot, small_csv, dim_3d, include_seg):
    """Test CSV import, 2D/3D, with/without segmentation."""

    dialog = ImportDialog(import_type="csv")
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitExposed(dialog)

    # Prepare import
    dialog.import_widget._load_csv(str(small_csv))

    # Set dimensions & segmentation state
    if include_seg:
        dialog.segmentation_widget.include_seg = lambda: True
    else:
        dialog.segmentation_widget.include_seg = lambda: False
    dialog.dimension_widget.incl_z = dim_3d

    # Trigger update
    dialog._update_field_map_and_scale(not include_seg)

    # Assertions
    # Scale widget visibility
    assert dialog.scale_widget.isVisible() is (include_seg)
    # seg_id visibility
    assert dialog.prop_map_widget.mapping_widgets["seg_id"].isVisible() is include_seg
    # z field included in 3D
    if dim_3d:
        assert "z" in dialog.prop_map_widget.standard_fields
    else:
        assert "z" not in dialog.prop_map_widget.standard_fields

    # Optional features behavior
    optional = dialog.prop_map_widget.optional_features
    if "area" in optional:
        combo = optional["area"]["feature_option"]
        # "Custom" is always index 0 (default)
        assert combo.currentIndex() == 0
        assert combo.currentText() == "Custom"
        assert optional["area"]["recompute"].isEnabled() is False
        if include_seg:
            # First regionprops feature is at index 1
            combo.setCurrentIndex(1)
            assert optional["area"]["recompute"].isEnabled() is True
        else:
            assert combo.count() == 1  # only "Custom", no regionprops options


class TestPropMapWidgetKeys:
    """Test that prop_map_widget methods return correct feature keys."""

    def _setup_dialog(self, qtbot, small_csv, include_seg=True):
        """Helper to set up a dialog with the small_csv loaded."""
        dialog = ImportDialog(import_type="csv")
        qtbot.addWidget(dialog)
        dialog.show()
        qtbot.waitExposed(dialog)
        dialog.import_widget._load_csv(str(small_csv))

        if include_seg:
            dialog.segmentation_widget.include_seg = lambda: True
        else:
            dialog.segmentation_widget.include_seg = lambda: False
        dialog.dimension_widget.incl_z = False
        dialog._update_field_map_and_scale(not include_seg)
        return dialog

    def test_get_node_features_uses_default_keys(self, qtbot, small_csv):
        """When a computed feature is selected, get_node_features should use
        the annotator's default key (e.g. 'area'), not the source property name."""
        dialog = self._setup_dialog(qtbot, small_csv, include_seg=True)
        prop_map = dialog.prop_map_widget
        optional = prop_map.optional_features

        # "area" column exists and is mapped to the "Area" regionprops feature
        assert "area" in optional
        combo = optional["area"]["feature_option"]
        # Select "Area" (first regionprops option)
        combo.setCurrentIndex(0)
        assert combo.currentText() == "Area"
        optional["area"]["attr_checkbox"].setChecked(True)

        result = prop_map.get_node_features()
        # Key should be the default key "area", not the source property name
        assert "area" in result
        assert isinstance(result["area"], bool)

    def test_get_features_uses_default_keys(self, qtbot, small_csv):
        """When a computed feature is selected, get_features should use
        the annotator's default key, not the display name."""
        dialog = self._setup_dialog(qtbot, small_csv, include_seg=True)
        prop_map = dialog.prop_map_widget
        optional = prop_map.optional_features

        assert "area" in optional
        combo = optional["area"]["feature_option"]
        combo.setCurrentIndex(0)
        assert combo.currentText() == "Area"
        optional["area"]["attr_checkbox"].setChecked(True)
        optional["area"]["recompute"].setChecked(True)

        result = prop_map.get_features()
        # Key should be "area" (default key), not "Area" (display name)
        assert "area" in result
        assert result["area"] == "Recompute"

    def test_get_features_load_from_column(self, qtbot, small_csv):
        """When loading a computed feature from a column, get_features should
        map default_key -> column_name."""
        dialog = self._setup_dialog(qtbot, small_csv, include_seg=True)
        prop_map = dialog.prop_map_widget
        optional = prop_map.optional_features

        assert "area" in optional
        combo = optional["area"]["feature_option"]
        combo.setCurrentIndex(0)
        optional["area"]["attr_checkbox"].setChecked(True)
        optional["area"]["recompute"].setChecked(False)

        result = prop_map.get_features()
        assert "area" in result
        assert result["area"] == "area"  # column name

    def test_custom_feature_no_collision(self, qtbot, small_csv):
        """Custom feature with a name that doesn't collide uses its own name
        in get_name_map, and is excluded from get_features/get_node_features."""
        dialog = self._setup_dialog(qtbot, small_csv, include_seg=True)
        prop_map = dialog.prop_map_widget
        optional = prop_map.optional_features

        # "group" column doesn't collide with any default key
        assert "group" in optional
        combo = optional["group"]["feature_option"]
        combo.setCurrentText("Custom")
        optional["group"]["attr_checkbox"].setChecked(True)

        name_map = prop_map.get_name_map()
        assert "group" in name_map
        assert name_map["group"] == "group"

        # Custom features are only in name_map, not in features/node_features
        assert "group" not in prop_map.get_node_features()
        assert "group" not in prop_map.get_features()

    def test_custom_feature_collision_gets_prefixed(self, qtbot, small_csv):
        """Custom feature whose name collides with a default key gets
        'custom_' prefix in get_name_map."""
        dialog = self._setup_dialog(qtbot, small_csv, include_seg=True)
        prop_map = dialog.prop_map_widget
        optional = prop_map.optional_features

        # "area" collides with the default area key
        assert "area" in optional
        combo = optional["area"]["feature_option"]
        combo.setCurrentText("Custom")
        optional["area"]["attr_checkbox"].setChecked(True)

        name_map = prop_map.get_name_map()
        assert "custom_area" in name_map
        assert name_map["custom_area"] == "area"
        assert "area" not in name_map or name_map.get("area") != "area"

        # Custom features are only in name_map, not in features/node_features
        assert "custom_area" not in prop_map.get_node_features()
        assert "custom_area" not in prop_map.get_features()


def test_csv_import_2d_with_segmentation(
    qtbot, tmp_path, solution_tracks_2d, monkeypatch
):
    """Test exporting and re-importing 2D tracks with segmentation.
    This tests whether the full workflow works end-to-end.
    """
    # Mock _resize_dialog to avoid screen access in headless CI
    monkeypatch.setattr(ImportDialog, "_resize_dialog", lambda self: None)

    # Create tracks and export to CSV (as motile_tracker does in tracks_list.py:208)
    tracks = solution_tracks_2d
    csv_path = tmp_path / "test_tracks.csv"
    export_to_csv(tracks, csv_path)

    # Also save the segmentation
    tifffile.imwrite(tmp_path / "segmentation.tif", np.asarray(tracks.segmentation))

    # Create import dialog and load the GEFF file
    dialog = ImportDialog(import_type="csv")
    qtbot.addWidget(dialog)

    # Load the CSV file
    dialog.import_widget._load_csv(csv_path)

    # Verify CSV root was loaded
    assert dialog.import_widget.df is not None, "Failed to load CSV df"

    # Select "Use external segmentation" option and set path
    dialog.segmentation_widget.external_segmentation_radio.setChecked(True)
    seg_path = tmp_path / "segmentation.tif"
    dialog.segmentation_widget.segmentation_widget.image_path_line.setText(
        str(seg_path)
    )
    dialog.segmentation_widget.segmentation_widget.valid = True
    dialog.segmentation_widget.segmentation_widget.seg_path_updated.emit()

    # Verify that seg and incl_z are True
    assert dialog.seg is True
    assert dialog.incl_z is False

    # Verify finish button is enabled
    assert dialog.finish_button.isEnabled() is True, (
        "Finish button should be enabled with valid CSV and segmentation"
    )

    # Map seg_id to the node "id" column since node id == seg_id
    prop_map = dialog.prop_map_widget
    seg_combo = prop_map.mapping_widgets["seg_id"]
    seg_combo.setCurrentText("id")

    # Import the tracks
    dialog._finish()

    # Verify tracks were imported successfully
    assert hasattr(dialog, "tracks"), "Dialog should have tracks attribute after import"
    assert dialog.tracks is not None, "Tracks should not be None"
    assert dialog.tracks.graph.num_nodes() == solution_tracks_2d.graph.num_nodes()
    assert dialog.tracks.graph.num_edges() == solution_tracks_2d.graph.num_edges()
    assert dialog.tracks.ndim == 3


def test_csv_import_3d_with_segmentation(
    qtbot, tmp_path, solution_tracks_3d, monkeypatch
):
    """Test exporting and re-importing 3D tracks with segmentation.
    This tests whether the full workflow works end-to-end.
    """
    # Mock _resize_dialog to avoid screen access in headless CI
    monkeypatch.setattr(ImportDialog, "_resize_dialog", lambda self: None)

    # Create tracks and export to CSV (as motile_tracker does in tracks_list.py:208)
    tracks = solution_tracks_3d
    csv_path = tmp_path / "test_tracks.csv"
    export_to_csv(tracks, csv_path)

    # Also save the segmentation
    tifffile.imwrite(tmp_path / "segmentation.tif", np.asarray(tracks.segmentation))

    # Create import dialog and load the GEFF file
    dialog = ImportDialog(import_type="csv")
    qtbot.addWidget(dialog)

    # Load the CSV file
    dialog.import_widget._load_csv(csv_path)

    # Verify CSV root was loaded
    assert dialog.import_widget.df is not None, "Failed to load CSV df"

    # Make sure the dimension is set to 3D
    dialog.dimension_widget.radio_3D.setChecked(True)

    # Select "Use external segmentation" option and set path
    dialog.segmentation_widget.external_segmentation_radio.setChecked(True)
    seg_path = tmp_path / "segmentation.tif"
    dialog.segmentation_widget.segmentation_widget.image_path_line.setText(
        str(seg_path)
    )
    dialog.segmentation_widget.segmentation_widget.valid = True
    dialog.segmentation_widget.segmentation_widget.seg_path_updated.emit()

    # Verify that seg and incl_z are True
    assert dialog.seg is True
    assert dialog.incl_z is True

    # Verify finish button is enabled
    assert dialog.finish_button.isEnabled() is True, (
        "Finish button should be enabled with valid CSV and segmentation"
    )

    # Set seg_id mapping to "None" since node id == seg_id (automapping is incorrect)
    prop_map = dialog.prop_map_widget
    seg_combo = prop_map.mapping_widgets["seg_id"]
    seg_combo.setCurrentText("id")
    prop_map._update_props_left()

    # Import the tracks
    dialog._finish()

    # Verify tracks were imported successfully
    assert hasattr(dialog, "tracks"), "Dialog should have tracks attribute after import"
    assert dialog.tracks is not None, "Tracks should not be None"
    assert dialog.tracks.graph.num_nodes() == solution_tracks_3d.graph.num_nodes()
    assert dialog.tracks.graph.num_edges() == solution_tracks_3d.graph.num_edges()
    assert dialog.tracks.ndim == 4


def test_csv_import_without_segmentation(
    qtbot, tmp_path, solution_tracks_2d_without_segmentation, monkeypatch
):
    """Test importing without segmentation."""
    # Mock _resize_dialog to avoid screen access in headless CI
    monkeypatch.setattr(ImportDialog, "_resize_dialog", lambda self: None)

    # Create tracks and export to CSV (as motile_tracker does in tracks_list.py:208)
    tracks = solution_tracks_2d_without_segmentation
    csv_path = tmp_path / "test_tracks.csv"
    export_to_csv(tracks, csv_path)

    # Create import dialog and load the GEFF file
    dialog = ImportDialog(import_type="csv")
    qtbot.addWidget(dialog)

    # Load the CSV file
    dialog.import_widget._load_csv(csv_path)

    # Verify CSV root was loaded
    assert dialog.import_widget.df is not None, "Failed to load CSV df"

    # Select None for the segmentation, assert seg and incl_z are False, assert seg_id
    # mapping is hidden
    dialog.segmentation_widget.none_radio.setChecked(True)
    assert not dialog.seg
    assert not dialog.incl_z

    # Verify finish button is enabled
    assert dialog.finish_button.isEnabled() is True, (
        "Finish button should be enabled with valid CSV and segmentation"
    )

    # Import the tracks
    dialog._finish()

    # Verify tracks were imported successfully
    assert hasattr(dialog, "tracks"), "Dialog should have tracks attribute after import"
    assert dialog.tracks is not None, "Tracks should not be None"
    assert (
        dialog.tracks.graph.num_nodes()
        == solution_tracks_2d_without_segmentation.graph.num_nodes()
    )
    assert (
        dialog.tracks.graph.num_edges()
        == solution_tracks_2d_without_segmentation.graph.num_edges()
    )
    assert dialog.tracks.ndim == 3


def test_geff_import_2d_with_segmentation(qtbot, tmp_path, graph_2d, monkeypatch):
    """Test exporting and re-importing 2D tracks with segmentation.
    This tests whether the full workflow works end-to-end.
    """
    # Mock _resize_dialog to avoid screen access in headless CI
    monkeypatch.setattr(ImportDialog, "_resize_dialog", lambda self: None)

    # Create tracks and export to GEFF (as motile_tracker does in tracks_list.py:237)
    tracks = Tracks(graph_2d, ndim=3, time_attr="t")
    geff_path = tmp_path / "test_tracks.zarr"
    export_to_geff(tracks, geff_path)

    # Create import dialog and load the GEFF file
    dialog = ImportDialog(import_type="geff")
    qtbot.addWidget(dialog)

    # Load the geff file
    dialog.import_widget._load_geff(geff_path)

    # Verify geff root was loaded
    assert dialog.import_widget.root is not None, "Failed to load GEFF root"

    # Select "Use external segmentation" option and set path
    dialog.segmentation_widget.external_segmentation_radio.setChecked(True)
    seg_path = tmp_path / "segmentation.zarr"
    zarr.save_array(seg_path, np.asarray(tracks.segmentation))
    dialog.segmentation_widget.segmentation_widget.image_path_line.setText(
        str(seg_path)
    )
    dialog.segmentation_widget.segmentation_widget.seg_path_updated.emit()

    # Verify finish button is enabled
    assert dialog.finish_button.isEnabled() is True, (
        "Finish button should be enabled with valid GEFF and segmentation"
    )

    # Set seg_id mapping to "None" since node id == seg_id (automapping is incorrect)
    prop_map = dialog.prop_map_widget
    seg_combo = prop_map.mapping_widgets["seg_id"]
    seg_combo.setCurrentText("None")
    prop_map._update_props_left()

    # Import the tracks
    dialog._finish()

    # Verify tracks were imported successfully
    assert hasattr(dialog, "tracks"), "Dialog should have tracks attribute after import"
    assert dialog.tracks is not None, "Tracks should not be None"
    assert dialog.tracks.graph.num_nodes() == graph_2d.num_nodes()
    assert dialog.tracks.graph.num_edges() == graph_2d.num_edges()
    assert dialog.tracks.ndim == 3
    for node_id in dialog.tracks.graph.node_ids():
        dialog.tracks.get_time(node_id)


def test_geff_import_3d_with_segmentation(
    qtbot, tmp_path, solution_tracks_3d, monkeypatch
):
    """Test exporting and re-importing 3D tracks with segmentation."""
    # Mock _resize_dialog to avoid screen access in headless CI
    monkeypatch.setattr(ImportDialog, "_resize_dialog", lambda self: None)

    # Create tracks and export to GEFF
    tracks = solution_tracks_3d
    geff_path = tmp_path / "test_tracks_3d.zarr"
    export_to_geff(tracks, geff_path)

    # Create import dialog and load the GEFF file
    dialog = ImportDialog(import_type="geff")
    qtbot.addWidget(dialog)

    # Load the geff file
    dialog.import_widget._load_geff(geff_path)

    # Verify geff root was loaded
    assert dialog.import_widget.root is not None, "Failed to load GEFF root"

    # Select "Use external segmentation" option and set path
    dialog.segmentation_widget.external_segmentation_radio.setChecked(True)
    seg_path = tmp_path / "segmentation_3d.zarr"
    zarr.save_array(seg_path, np.asarray(tracks.segmentation))
    dialog.segmentation_widget.segmentation_widget.image_path_line.setText(
        str(seg_path)
    )
    dialog.segmentation_widget.segmentation_widget.seg_path_updated.emit()

    # Verify finish button is enabled
    assert dialog.finish_button.isEnabled() is True

    # Set seg_id mapping to "None" since node id == seg_id (automapping is incorrect)
    prop_map = dialog.prop_map_widget
    seg_combo = prop_map.mapping_widgets["seg_id"]
    seg_combo.setCurrentText("None")
    prop_map._update_props_left()

    # Import the tracks
    dialog._finish()

    # Verify tracks were imported successfully
    assert hasattr(dialog, "tracks"), "Dialog should have tracks attribute after import"
    assert dialog.tracks is not None, "Tracks should not be None"
    assert dialog.tracks.graph.num_nodes() == solution_tracks_3d.graph.num_nodes()
    assert dialog.tracks.graph.num_edges() == solution_tracks_3d.graph.num_edges()
    assert dialog.tracks.ndim == 4
    for node_id in dialog.tracks.graph.node_ids():
        dialog.tracks.get_time(node_id)


def test_geff_import_without_segmentation(
    qtbot, tmp_path, solution_tracks_2d_without_segmentation, monkeypatch
):
    """Test importing without segmentation."""
    # Mock _resize_dialog to avoid screen access in headless CI
    monkeypatch.setattr(ImportDialog, "_resize_dialog", lambda self: None)

    # Create tracks and export to GEFF (no segmentation)
    tracks = solution_tracks_2d_without_segmentation
    geff_path = tmp_path / "test_tracks_no_seg.zarr"
    export_to_geff(tracks, geff_path)

    # Create import dialog and load the GEFF file
    dialog = ImportDialog(import_type="geff")
    qtbot.addWidget(dialog)

    # Load the geff file
    dialog.import_widget._load_geff(geff_path)

    # Verify geff root was loaded
    assert dialog.import_widget.root is not None, "Failed to load GEFF root"

    # Select "None" for segmentation (should be default)
    assert dialog.segmentation_widget.none_radio.isChecked() is True

    # Verify finish button is enabled (segmentation is optional)
    assert dialog.finish_button.isEnabled() is True

    # Set seg_id mapping to "None" since node id == seg_id (automapping is incorrect)
    prop_map = dialog.prop_map_widget
    seg_combo = prop_map.mapping_widgets["seg_id"]
    seg_combo.setCurrentText("None")
    prop_map._update_props_left()

    # Import the tracks
    dialog._finish()

    # Verify tracks were imported successfully
    assert hasattr(dialog, "tracks"), "Dialog should have tracks attribute after import"
    assert dialog.tracks is not None, "Tracks should not be None"
    assert dialog.tracks.graph.num_nodes() == tracks.graph.num_nodes()
    assert dialog.tracks.graph.num_edges() == tracks.graph.num_edges()
    for node_id in dialog.tracks.graph.node_ids():
        dialog.tracks.get_time(node_id)


def test_geff_import_without_axes_metadata(qtbot, tmp_path, graph_2d, monkeypatch):
    """Test importing a geff that has no axes metadata.
    This tests the automatic axes generation when metadata is missing.
    """
    # Mock _resize_dialog to avoid screen access in headless CI
    monkeypatch.setattr(ImportDialog, "_resize_dialog", lambda self: None)

    # Create tracks and export to GEFF (this creates valid axes metadata)
    tracks = Tracks(graph_2d, ndim=3, time_attr="t")
    geff_path = tmp_path / "test_tracks_no_axes.zarr"
    export_to_geff(tracks, geff_path)

    # Remove axes metadata from the geff file
    root = zarr.open_group(geff_path / "tracks.geff", mode="r+")
    geff_metadata = dict(root.attrs.get("geff", {}))
    del geff_metadata["axes"]
    root.attrs["geff"] = geff_metadata

    # Create import dialog and load the GEFF file
    dialog = ImportDialog(import_type="geff")
    qtbot.addWidget(dialog)

    # Load the geff file
    dialog.import_widget._load_geff(geff_path)

    # Verify geff root was loaded
    assert dialog.import_widget.root is not None, "Failed to load GEFF root"

    # Verify axes metadata is missing
    loaded_metadata = dict(dialog.import_widget.root.attrs.get("geff", {}))
    assert "axes" not in loaded_metadata, "Axes should be missing from metadata"

    # Select "Use external segmentation" option and set path
    dialog.segmentation_widget.external_segmentation_radio.setChecked(True)
    seg_path = tmp_path / "segmentation.zarr"
    zarr.save_array(seg_path, np.asarray(tracks.segmentation))
    dialog.segmentation_widget.segmentation_widget.image_path_line.setText(
        str(seg_path)
    )
    dialog.segmentation_widget.segmentation_widget.seg_path_updated.emit()

    # Verify finish button is enabled
    assert dialog.finish_button.isEnabled() is True

    # Set seg_id mapping to "None" since node id == seg_id (automapping is incorrect)
    prop_map = dialog.prop_map_widget
    seg_combo = prop_map.mapping_widgets["seg_id"]
    seg_combo.setCurrentText("None")
    prop_map._update_props_left()

    # Import the tracks (this should auto-generate axes metadata)
    dialog._finish()

    # Verify tracks were imported successfully
    assert hasattr(dialog, "tracks"), "Dialog should have tracks attribute after import"
    assert dialog.tracks is not None, "Tracks should not be None"
    assert dialog.tracks.graph.num_nodes() == graph_2d.num_nodes()
    assert dialog.tracks.graph.num_edges() == graph_2d.num_edges()
    assert dialog.tracks.ndim == 3

    # Verify axes metadata was generated
    final_metadata = dict(dialog.import_widget.root.attrs.get("geff", {}))
    assert "axes" in final_metadata, "Axes should have been generated"
    assert len(final_metadata["axes"]) == 3, "Should have 3 axes for 2D+time"
    for node_id in dialog.tracks.graph.node_ids():
        dialog.tracks.get_time(node_id)


def test_geff_import_embedded_segmentation(qtbot, tmp_path, graph_2d, monkeypatch):
    """Test that embedded segmentation (mask/bbox + segmentation_shape) is reconstructed.

    Regression test for the bug where mask/bbox were not included in the name_map
    passed to import_from_geff, causing tracks.segmentation to be None even though
    the GEFF contained embedded mask data and a segmentation_shape zarr attribute.
    """
    monkeypatch.setattr(ImportDialog, "_resize_dialog", lambda self: None)

    tracks = Tracks(graph_2d, ndim=3, time_attr="t")
    geff_path = tmp_path / "test_embedded_seg.zarr"
    export_to_geff(tracks, geff_path, save_segmentation=False)

    # Verify that the geff has embedded segmentation (precondition)
    import zarr as _zarr

    root = _zarr.open_group(geff_path / "tracks.geff", mode="r")
    assert geff_has_embedded_segmentation(root), (
        "Precondition: geff should have mask/bbox and segmentation_shape"
    )

    dialog = ImportDialog(import_type="geff")
    qtbot.addWidget(dialog)
    dialog.import_widget._load_geff(geff_path)

    assert dialog.import_widget.root is not None

    # Embedded segmentation detected: info label shown, radios hidden.
    # Use isHidden() because the dialog itself is not shown (parent is hidden),
    # so isVisible() would return False for all children regardless.
    assert not dialog.segmentation_widget._embedded_info_label.isHidden()
    assert dialog.segmentation_widget.external_segmentation_radio.isHidden()

    # mask/bbox should not appear as optional features (they are handled automatically)
    assert "mask" not in dialog.prop_map_widget.optional_features
    assert "bbox" not in dialog.prop_map_widget.optional_features

    # Even though include_seg() returns False (no external seg path), regionprops options
    # should be available for numeric features because embedded segmentation is present.
    assert dialog.prop_map_widget.seg_for_features is True
    assert dialog.prop_map_widget.seg is False  # scale widget / seg_id still hidden

    # Recompute must be disabled for embedded segmentation: funtracks does not register
    # a RegionPropsAnnotator when segmentation_path=None, so recompute would fail.
    for widgets in dialog.prop_map_widget.optional_features.values():
        assert not widgets["recompute"].isEnabled()

    assert dialog.finish_button.isEnabled()

    dialog._finish()

    assert dialog.tracks is not None
    assert dialog.tracks.segmentation is not None, (
        "Segmentation should be reconstructed from embedded mask/bbox data"
    )
    assert dialog.tracks.graph.num_nodes() == graph_2d.num_nodes()
    assert dialog.tracks.graph.num_edges() == graph_2d.num_edges()


def test_geff_import_old_geff_warning(qtbot, tmp_path, graph_2d, monkeypatch):
    """Test that the old GEFF warning is shown when mask/bbox is present but
    segmentation_shape is missing (simulating a GEFF exported by an older funtracks).
    """
    monkeypatch.setattr(ImportDialog, "_resize_dialog", lambda self: None)

    tracks = Tracks(graph_2d, ndim=3, time_attr="t")
    geff_path = tmp_path / "old_geff.zarr"
    export_to_geff(tracks, geff_path, save_segmentation=False)

    # Remove segmentation_shape to simulate old funtracks export
    root = zarr.open_group(geff_path / "tracks.geff", mode="r+")
    del root.attrs["segmentation_shape"]

    dialog = ImportDialog(import_type="geff")
    qtbot.addWidget(dialog)
    dialog.import_widget._load_geff(geff_path)

    assert dialog.import_widget.root is not None

    # Old GEFF warning should be shown (mask/bbox present, no segmentation_shape)
    assert not dialog.segmentation_widget._old_geff_warning_label.isHidden()
    assert dialog.segmentation_widget._embedded_info_label.isHidden()
    assert not dialog.segmentation_widget.none_radio.isHidden()
    assert not dialog.segmentation_widget.external_segmentation_radio.isHidden()

    # None radio is the default (no related_objects since save_segmentation=False)
    assert dialog.segmentation_widget.none_radio.isChecked()
    assert dialog.finish_button.isEnabled()

    dialog._finish()

    assert dialog.tracks is not None
    assert dialog.tracks.graph.num_nodes() == graph_2d.num_nodes()
    assert dialog.tracks.graph.num_edges() == graph_2d.num_edges()


def test_geff_import_with_related_data(qtbot, tmp_path, graph_2d, monkeypatch):
    """Test that related object radio buttons are shown for old GEFF with
    related_objects metadata, and that selecting one loads the segmentation.
    """
    monkeypatch.setattr(ImportDialog, "_resize_dialog", lambda self: None)

    tracks = Tracks(graph_2d, ndim=3, time_attr="t")
    geff_path = tmp_path / "old_geff_with_related.zarr"
    # save_segmentation=True writes segmentation + adds related_objects to geff metadata.
    # seg_label_attr=None preserves node IDs as pixel values (consistent with other tests).
    export_to_geff(tracks, geff_path, save_segmentation=True, seg_label_attr=None)

    # Remove segmentation_shape to simulate old funtracks export
    root = zarr.open_group(geff_path / "tracks.geff", mode="r+")
    del root.attrs["segmentation_shape"]

    dialog = ImportDialog(import_type="geff")
    qtbot.addWidget(dialog)
    dialog.import_widget._load_geff(geff_path)

    assert dialog.import_widget.root is not None

    # Old GEFF warning visible; related radio buttons populated
    assert not dialog.segmentation_widget._old_geff_warning_label.isHidden()
    assert len(dialog.segmentation_widget.related_object_radio_buttons) > 0

    # Related radio is auto-checked → include_seg() is True
    assert dialog.segmentation_widget.include_seg() is True

    # Resolved path must exist on disk
    seg_path = dialog.segmentation_widget.get_segmentation_path()
    assert seg_path is not None
    assert seg_path.exists()

    assert dialog.finish_button.isEnabled()

    # seg_id is visible; map it to None (node id == seg id, funtracks handles it)
    prop_map = dialog.prop_map_widget
    seg_combo = prop_map.mapping_widgets["seg_id"]
    seg_combo.setCurrentText("None")
    prop_map._update_props_left()

    dialog._finish()

    assert dialog.tracks is not None
    assert dialog.tracks.segmentation is not None
    assert dialog.tracks.graph.num_nodes() == graph_2d.num_nodes()
    assert dialog.tracks.graph.num_edges() == graph_2d.num_edges()


def test_geff_import_no_mask_with_segmentation_shape(
    qtbot, tmp_path, graph_2d_without_segmentation, monkeypatch
):
    """Test that injecting segmentation_shape without mask/bbox shows the normal
    flow (no warning, no embedded info) and produces no segmentation on import.
    """
    monkeypatch.setattr(ImportDialog, "_resize_dialog", lambda self: None)

    tracks = Tracks(graph_2d_without_segmentation, ndim=3, time_attr="t")
    geff_path = tmp_path / "no_mask_with_shape.zarr"
    export_to_geff(tracks, geff_path, save_segmentation=False)

    # Manually inject segmentation_shape even though no mask/bbox exist
    root = zarr.open_group(geff_path / "tracks.geff", mode="r+")
    attrs = dict(root.attrs)
    attrs["segmentation_shape"] = [5, 100, 100]
    root.attrs["segmentation_shape"] = [5, 100, 100]

    dialog = ImportDialog(import_type="geff")
    qtbot.addWidget(dialog)
    dialog.import_widget._load_geff(geff_path)

    assert dialog.import_widget.root is not None

    # Normal flow: no warning, no embedded info
    assert dialog.segmentation_widget._embedded_info_label.isHidden()
    assert dialog.segmentation_widget._old_geff_warning_label.isHidden()
    assert not dialog.segmentation_widget.none_radio.isHidden()
    assert not dialog.segmentation_widget.external_segmentation_radio.isHidden()

    # None radio is the default
    assert dialog.segmentation_widget.none_radio.isChecked()
    assert dialog.finish_button.isEnabled()

    dialog._finish()

    assert dialog.tracks is not None
    assert dialog.tracks.segmentation is None
    assert dialog.tracks.graph.num_nodes() == graph_2d_without_segmentation.num_nodes()
    assert dialog.tracks.graph.num_edges() == graph_2d_without_segmentation.num_edges()


def test_motile_run_save_load(tmp_path, graph_2d):
    """Test full MotileRun save/load round-trip."""
    run = MotileRun(
        graph=graph_2d,
        run_name="test_run",
        solver_params=SolverParams(),
        ndim=3,
        time_attr="t",
    )
    run_dir = run.save(tmp_path)

    assert (run_dir / "tracks.geff").exists()
    assert (run_dir / "solver_params.json").exists()
    assert (run_dir / "attrs.json").exists()

    loaded = MotileRun.load(run_dir)
    assert loaded.run_name == run.run_name
    assert loaded.graph.num_nodes() == graph_2d.num_nodes()
    assert loaded.graph.num_edges() == graph_2d.num_edges()
    assert loaded.solver_params is not None


def test_motile_run_load_backward_compat(tmp_path, graph_2d):
    """Test that MotileRun.load falls back to 'tracks' when 'tracks.geff' is absent."""
    run = MotileRun(
        graph=graph_2d,
        run_name="old_run",
        solver_params=SolverParams(),
        ndim=3,
        time_attr="t",
    )
    run_dir = run.save(tmp_path)

    # Simulate old save format: rename tracks.geff → tracks
    (run_dir / "tracks.geff").rename(run_dir / "tracks")
    assert not (run_dir / "tracks.geff").exists()

    loaded = MotileRun.load(run_dir)
    assert loaded.run_name == "old_run"
    assert loaded.graph.num_nodes() == graph_2d.num_nodes()
    assert loaded.graph.num_edges() == graph_2d.num_edges()
