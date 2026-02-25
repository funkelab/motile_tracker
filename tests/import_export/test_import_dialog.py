"""Integration test for CSV and GEFF import workflow.
Tests the full round-trip: export tracks using motile_tracker's method,
then import them back through the import dialog.
Also test for the visibility of various widgets based on 2D/3D and
segmentation inclusion.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest
import tifffile
import zarr
from funtracks.data_model import SolutionTracks, Tracks
from funtracks.import_export import export_to_csv, export_to_geff

from motile_tracker.import_export.menus.import_dialog import ImportDialog


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
        combo.setCurrentIndex(combo.count() - 1)
        assert combo.currentText() == "Custom"
        assert optional["area"]["recompute"].isEnabled() is False
        combo.setCurrentIndex(0)
        if include_seg:
            assert optional["area"]["recompute"].isEnabled() is True
        else:
            assert optional["area"]["recompute"].isEnabled() is False


def test_csv_import_2d_with_segmentation(
    qtbot, tmp_path, graph_2d, segmentation_2d, monkeypatch
):
    """Test exporting and re-importing 2D tracks with segmentation.
    This tests whether the full workflow works end-to-end.
    """
    # Mock _resize_dialog to avoid screen access in headless CI
    monkeypatch.setattr(ImportDialog, "_resize_dialog", lambda self: None)

    # Create tracks and export to CSV (as motile_tracker does in tracks_list.py:208)
    tracks = SolutionTracks(graph_2d, segmentation=segmentation_2d, ndim=3)
    csv_path = tmp_path / "test_tracks.csv"
    export_to_csv(tracks, csv_path)

    # Also save the segmentation
    tifffile.imwrite(tmp_path / "segmentation.tif", segmentation_2d)

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

    # Set seg_id mapping to "None" since node id == seg_id (automapping is incorrect)
    prop_map = dialog.prop_map_widget
    seg_combo = prop_map.mapping_widgets["seg_id"]
    seg_combo.setCurrentText("ID")

    # Import the tracks
    dialog._finish()

    # Verify tracks were imported successfully
    assert hasattr(dialog, "tracks"), "Dialog should have tracks attribute after import"
    assert dialog.tracks is not None, "Tracks should not be None"
    assert dialog.tracks.graph.number_of_nodes() == graph_2d.number_of_nodes()
    assert dialog.tracks.graph.number_of_edges() == graph_2d.number_of_edges()
    assert dialog.tracks.ndim == 3


def test_csv_import_3d_with_segmentation(
    qtbot, tmp_path, graph_3d, segmentation_3d, monkeypatch
):
    """Test exporting and re-importing 2D tracks with segmentation.
    This tests whether the full workflow works end-to-end.
    """
    # Mock _resize_dialog to avoid screen access in headless CI
    monkeypatch.setattr(ImportDialog, "_resize_dialog", lambda self: None)

    # Create tracks and export to CSV (as motile_tracker does in tracks_list.py:208)
    tracks = SolutionTracks(graph_3d, segmentation=segmentation_3d, ndim=4)
    csv_path = tmp_path / "test_tracks.csv"
    export_to_csv(tracks, csv_path)

    # Also save the segmentation
    tifffile.imwrite(tmp_path / "segmentation.tif", segmentation_3d)

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
    seg_combo.setCurrentText("ID")
    prop_map._update_props_left()

    # Import the tracks
    dialog._finish()

    # Verify tracks were imported successfully
    assert hasattr(dialog, "tracks"), "Dialog should have tracks attribute after import"
    assert dialog.tracks is not None, "Tracks should not be None"
    assert dialog.tracks.graph.number_of_nodes() == graph_3d.number_of_nodes()
    assert dialog.tracks.graph.number_of_edges() == graph_3d.number_of_edges()
    assert dialog.tracks.ndim == 4


def test_csv_import_without_segmentation(qtbot, tmp_path, graph_2d, monkeypatch):
    """Test importing without segmentation."""
    # Mock _resize_dialog to avoid screen access in headless CI
    monkeypatch.setattr(ImportDialog, "_resize_dialog", lambda self: None)

    # Create tracks and export to CSV (as motile_tracker does in tracks_list.py:208)
    tracks = SolutionTracks(graph_2d, segmentation=None, ndim=3)
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
    assert dialog.tracks.graph.number_of_nodes() == graph_2d.number_of_nodes()
    assert dialog.tracks.graph.number_of_edges() == graph_2d.number_of_edges()
    assert dialog.tracks.ndim == 3


def test_geff_import_2d_with_segmentation(
    qtbot, tmp_path, graph_2d, segmentation_2d, monkeypatch
):
    """Test exporting and re-importing 2D tracks with segmentation.
    This tests whether the full workflow works end-to-end.
    """
    # Mock _resize_dialog to avoid screen access in headless CI
    monkeypatch.setattr(ImportDialog, "_resize_dialog", lambda self: None)

    # Create tracks and export to GEFF (as motile_tracker does in tracks_list.py:237)
    tracks = Tracks(graph_2d, segmentation=segmentation_2d, ndim=3)
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
    zarr.save_array(seg_path, segmentation_2d)
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
    assert dialog.tracks.graph.number_of_nodes() == graph_2d.number_of_nodes()
    assert dialog.tracks.graph.number_of_edges() == graph_2d.number_of_edges()
    assert dialog.tracks.ndim == 3


def test_geff_import_3d_with_segmentation(
    qtbot, tmp_path, graph_3d, segmentation_3d, monkeypatch
):
    """Test exporting and re-importing 3D tracks with segmentation."""
    # Mock _resize_dialog to avoid screen access in headless CI
    monkeypatch.setattr(ImportDialog, "_resize_dialog", lambda self: None)

    # Create tracks and export to GEFF
    tracks = Tracks(graph_3d, segmentation=segmentation_3d, ndim=4)
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
    zarr.save_array(seg_path, segmentation_3d)
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
    assert dialog.tracks.graph.number_of_nodes() == graph_3d.number_of_nodes()
    assert dialog.tracks.graph.number_of_edges() == graph_3d.number_of_edges()
    assert dialog.tracks.ndim == 4


def test_geff_import_without_segmentation(qtbot, tmp_path, graph_2d, monkeypatch):
    """Test importing without segmentation."""
    # Mock _resize_dialog to avoid screen access in headless CI
    monkeypatch.setattr(ImportDialog, "_resize_dialog", lambda self: None)

    # Create tracks and export to GEFF (no segmentation)
    tracks = Tracks(graph_2d, segmentation=None, ndim=3)
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
    assert dialog.tracks.graph.number_of_nodes() == graph_2d.number_of_nodes()


def test_geff_import_without_axes_metadata(
    qtbot, tmp_path, graph_2d, segmentation_2d, monkeypatch
):
    """Test importing a geff that has no axes metadata.
    This tests the automatic axes generation when metadata is missing.
    """
    # Mock _resize_dialog to avoid screen access in headless CI
    monkeypatch.setattr(ImportDialog, "_resize_dialog", lambda self: None)

    # Create tracks and export to GEFF (this creates valid axes metadata)
    tracks = Tracks(graph_2d, segmentation=segmentation_2d, ndim=3)
    geff_path = tmp_path / "test_tracks_no_axes.zarr"
    export_to_geff(tracks, geff_path)

    # Remove axes metadata from the geff file
    root = zarr.open_group(geff_path / "tracks", mode="r+")
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
    zarr.save_array(seg_path, segmentation_2d)
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
    assert dialog.tracks.graph.number_of_nodes() == graph_2d.number_of_nodes()
    assert dialog.tracks.graph.number_of_edges() == graph_2d.number_of_edges()
    assert dialog.tracks.ndim == 3

    # Verify axes metadata was generated
    final_metadata = dict(dialog.import_widget.root.attrs.get("geff", {}))
    assert "axes" in final_metadata, "Axes should have been generated"
    assert len(final_metadata["axes"]) == 3, "Should have 3 axes for 2D+time"
