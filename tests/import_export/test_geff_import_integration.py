"""Integration test for GEFF import workflow.

Tests the full round-trip: export tracks using motile_tracker's method,
then import them back through the import dialog.
"""

import zarr
from funtracks.data_model import Tracks
from funtracks.import_export.export_to_geff import export_to_geff

from motile_tracker.import_export.menus.import_from_geff.geff_import_dialog import (
    ImportGeffDialog,
)


def test_geff_import_2d_with_segmentation(qtbot, tmp_path, graph_2d, segmentation_2d):
    """Test exporting and re-importing 2D tracks with segmentation.

    This tests whether the full workflow works end-to-end.
    """
    # Create tracks and export to GEFF (as motile_tracker does in tracks_list.py:237)
    tracks = Tracks(graph_2d, segmentation=segmentation_2d, ndim=3)
    geff_path = tmp_path / "test_tracks.zarr"
    export_to_geff(tracks, geff_path)

    # Create import dialog and load the GEFF file
    dialog = ImportGeffDialog()
    qtbot.addWidget(dialog)

    # Load the geff file
    dialog.geff_widget._load_geff(geff_path)

    # Verify geff root was loaded
    assert dialog.geff_widget.root is not None, "Failed to load GEFF root"

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

    # Import the tracks
    dialog._finish()

    # Verify tracks were imported successfully
    assert hasattr(dialog, "tracks"), "Dialog should have tracks attribute after import"
    assert dialog.tracks is not None, "Tracks should not be None"
    assert dialog.tracks.graph.number_of_nodes() == graph_2d.number_of_nodes()
    assert dialog.tracks.graph.number_of_edges() == graph_2d.number_of_edges()
    assert dialog.tracks.ndim == 3


def test_geff_import_3d_with_segmentation(qtbot, tmp_path, graph_3d, segmentation_3d):
    """Test exporting and re-importing 3D tracks with segmentation."""
    # Create tracks and export to GEFF
    tracks = Tracks(graph_3d, segmentation=segmentation_3d, ndim=4)
    geff_path = tmp_path / "test_tracks_3d.zarr"
    export_to_geff(tracks, geff_path)

    # Create import dialog and load the GEFF file
    dialog = ImportGeffDialog()
    qtbot.addWidget(dialog)

    # Load the geff file
    dialog.geff_widget._load_geff(geff_path)

    # Verify geff root was loaded
    assert dialog.geff_widget.root is not None, "Failed to load GEFF root"

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

    # Import the tracks
    dialog._finish()

    # Verify tracks were imported successfully
    assert hasattr(dialog, "tracks"), "Dialog should have tracks attribute after import"
    assert dialog.tracks is not None, "Tracks should not be None"
    assert dialog.tracks.graph.number_of_nodes() == graph_3d.number_of_nodes()
    assert dialog.tracks.graph.number_of_edges() == graph_3d.number_of_edges()
    assert dialog.tracks.ndim == 4


def test_geff_import_without_segmentation(qtbot, tmp_path, graph_2d):
    """Test importing without segmentation."""
    # Create tracks and export to GEFF (no segmentation)
    tracks = Tracks(graph_2d, segmentation=None, ndim=3)
    geff_path = tmp_path / "test_tracks_no_seg.zarr"
    export_to_geff(tracks, geff_path)

    # Create import dialog and load the GEFF file
    dialog = ImportGeffDialog()
    qtbot.addWidget(dialog)

    # Load the geff file
    dialog.geff_widget._load_geff(geff_path)

    # Verify geff root was loaded
    assert dialog.geff_widget.root is not None, "Failed to load GEFF root"

    # Select "None" for segmentation (should be default)
    assert dialog.segmentation_widget.none_radio.isChecked() is True

    # Verify finish button is enabled (segmentation is optional)
    assert dialog.finish_button.isEnabled() is True

    # Import the tracks
    dialog._finish()

    # Verify tracks were imported successfully
    assert hasattr(dialog, "tracks"), "Dialog should have tracks attribute after import"
    assert dialog.tracks is not None, "Tracks should not be None"
    assert dialog.tracks.graph.number_of_nodes() == graph_2d.number_of_nodes()
