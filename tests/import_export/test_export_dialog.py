from unittest.mock import MagicMock, patch

import pytest

from motile_tracker.import_export.menus.export_dialog import ExportDialog


@pytest.fixture
def mock_tracks():
    """Create a mock Tracks object with a fake export_tracks method."""
    tracks = MagicMock()
    tracks.export_tracks = MagicMock()
    return tracks


@pytest.fixture
def fake_parent(qtbot):
    """Return a dummy QWidget parent for dialogs."""
    from qtpy.QtWidgets import QWidget

    parent = QWidget()
    qtbot.addWidget(parent)
    return parent


@pytest.fixture
def mock_colormap():
    cmap = MagicMock()
    cmap.map.side_effect = lambda tid: [tid, tid, tid, 255]
    return cmap


def test_export_dialog_cancel(mock_tracks, fake_parent):
    """Should return False if user cancels export type selection."""
    mock_dialog = MagicMock()
    mock_dialog.exec_.return_value = 0  # QDialog.Rejected
    with patch(
        "motile_tracker.import_export.menus.export_dialog.ExportTypeDialog",
        return_value=mock_dialog,
    ):
        result = ExportDialog.show_export_dialog(
            fake_parent,
            mock_tracks,
            name="TestGroup",
            nodes_to_keep={1, 2},
            colormap=mock_colormap,
        )
    assert result is False
    mock_tracks.export_tracks.assert_not_called()


def test_export_dialog_csv(mock_tracks, fake_parent, tmp_path, mock_colormap):
    """Simulate CSV export with single file dialog."""
    test_file = tmp_path / "test_export.csv"

    # --- Setup mock_tracks to have a graph and track IDs ---
    mock_tracks.graph = MagicMock()
    mock_tracks.graph.nodes.return_value = [1, 2]
    mock_tracks.get_track_id.side_effect = lambda node: node  # identity mapping

    # --- Mock ExportTypeDialog to return CSV and relabel=False ---
    mock_dialog = MagicMock()
    mock_dialog.exec_.return_value = 1  # QDialog.Accepted
    mock_dialog.export_type = "CSV"
    mock_dialog.relabel_by_tracklet_id = False

    # --- Mock QFileDialog for CSV ---
    mock_file_dialog = MagicMock()
    mock_file_dialog.exec_.return_value = True
    mock_file_dialog.selectedFiles.return_value = [str(test_file)]

    expected_color_dict = {
        1: [1, 1, 1, 255],
        2: [2, 2, 2, 255],
        None: [0, 0, 0, 0],
    }

    with (
        patch(
            "motile_tracker.import_export.menus.export_dialog.ExportTypeDialog",
            return_value=mock_dialog,
        ),
        patch(
            "motile_tracker.import_export.menus.export_dialog.QFileDialog",
            return_value=mock_file_dialog,
        ),
        patch(
            "motile_tracker.import_export.menus.export_dialog.export_to_csv"
        ) as mock_export_csv,
    ):
        result = ExportDialog.show_export_dialog(
            fake_parent,
            mock_tracks,
            name="MyGroup",
            nodes_to_keep={1, 2},
            colormap=mock_colormap,  # pass fixture
        )

    # --- Assertions ---
    assert result is True
    mock_export_csv.assert_called_once_with(
        tracks=mock_tracks,
        outfile=test_file,
        color_dict=expected_color_dict,
        node_ids={1, 2},
        use_display_names=True,
        export_seg=False,
        seg_path=None,
    )


def test_export_dialog_csv_with_seg(mock_tracks, fake_parent, tmp_path, mock_colormap):
    """CSV export with segmentation — both dialogs mocked."""
    csv_file = tmp_path / "test_tracks.csv"
    tif_file = tmp_path / "test_tracks.tif"

    # --- Setup mock_tracks to have a graph and track IDs ---
    mock_tracks.graph = MagicMock()
    mock_tracks.graph.nodes.return_value = [1, 2]
    mock_tracks.get_track_id.side_effect = lambda node: node  # identity mapping

    # --- Mock ExportTypeDialog to return CSV and relabel=True ---
    mock_dialog = MagicMock()
    mock_dialog.exec_.return_value = 1
    mock_dialog.export_type = "CSV"
    mock_dialog.relabel_by_tracklet_id = True

    # --- Mock two QFileDialog instances ---
    mock_csv_dialog = MagicMock()
    mock_csv_dialog.exec_.return_value = True
    mock_csv_dialog.selectedFiles.return_value = [str(csv_file)]

    mock_tif_dialog = MagicMock()
    mock_tif_dialog.exec_.return_value = True
    mock_tif_dialog.selectedFiles.return_value = [str(tif_file)]

    # Patch QFileDialog constructor to return first CSV, then TIF dialog
    mock_file_dialog_class = MagicMock(side_effect=[mock_csv_dialog, mock_tif_dialog])

    # Expected color dict
    expected_color_dict = {
        1: [1, 1, 1, 255],
        2: [2, 2, 2, 255],
        None: [0, 0, 0, 0],
    }

    with (
        patch(
            "motile_tracker.import_export.menus.export_dialog.ExportTypeDialog",
            return_value=mock_dialog,
        ),
        patch(
            "motile_tracker.import_export.menus.export_dialog.QFileDialog",
            mock_file_dialog_class,
        ),
        patch(
            "motile_tracker.import_export.menus.export_dialog.export_to_csv"
        ) as mock_export_csv,
    ):
        result = ExportDialog.show_export_dialog(
            fake_parent,
            mock_tracks,
            name="MyGroup",
            nodes_to_keep={1, 2},
            colormap=mock_colormap,
        )

    # --- Assertions ---
    assert result is True
    mock_export_csv.assert_called_once_with(
        tracks=mock_tracks,
        outfile=csv_file,
        color_dict=expected_color_dict,
        node_ids={1, 2},
        use_display_names=True,
        export_seg=True,
        seg_path=tif_file,
    )

    # Ensure two dialogs were created
    assert mock_file_dialog_class.call_count == 2


def test_export_dialog_geff(mock_tracks, fake_parent, tmp_path):
    """Should call export_to_geff when geff is selected and confirmed."""
    geff_file = tmp_path / "test_export.zarr"

    mock_dialog = MagicMock()
    mock_dialog.exec_.return_value = 1  # QDialog.Accepted
    mock_dialog.export_type = "geff"
    mock_dialog.relabel_by_tracklet_id = False  # irrelevant for geff

    mock_file_dialog = MagicMock()
    mock_file_dialog.exec_.return_value = True
    mock_file_dialog.selectedFiles.return_value = [str(geff_file)]

    with (
        patch(
            "motile_tracker.import_export.menus.export_dialog.ExportTypeDialog",
            return_value=mock_dialog,
        ),
        patch(
            "motile_tracker.import_export.menus.export_dialog.QFileDialog",
            return_value=mock_file_dialog,
        ),
        patch(
            "motile_tracker.import_export.menus.export_dialog.export_to_geff"
        ) as mock_export_geff,
    ):
        result = ExportDialog.show_export_dialog(
            fake_parent,
            mock_tracks,
            name="MyGroup",
            nodes_to_keep={1, 2},
            colormap=mock_colormap,
        )

    assert result is True
    mock_export_geff.assert_called_once_with(
        mock_tracks, geff_file, overwrite=True, node_ids={1, 2}
    )


def test_export_dialog_geff_error(mock_tracks, fake_parent, tmp_path):
    """Should show a QMessageBox if export_to_geff raises ValueError."""
    test_file = tmp_path / "error_case.zarr"

    # Mock ExportTypeDialog to return geff
    mock_dialog = MagicMock()
    mock_dialog.exec_.return_value = 1  # QDialog.Accepted
    mock_dialog.export_type = "geff"
    mock_dialog.relabel_by_tracklet_id = False

    # Mock QFileDialog
    mock_file_dialog = MagicMock()
    mock_file_dialog.exec_.return_value = True
    mock_file_dialog.selectedFiles.return_value = [str(test_file)]

    # Patch export_to_geff to raise ValueError, and intercept QMessageBox.warning
    with (
        patch(
            "motile_tracker.import_export.menus.export_dialog.ExportTypeDialog",
            return_value=mock_dialog,
        ),
        patch(
            "motile_tracker.import_export.menus.export_dialog.QFileDialog",
            return_value=mock_file_dialog,
        ),
        patch(
            "motile_tracker.import_export.menus.export_dialog.export_to_geff",
            side_effect=ValueError("Export Error"),
        ),
        patch(
            "motile_tracker.import_export.menus.export_dialog.QMessageBox.warning"
        ) as mock_warning,
    ):
        result = ExportDialog.show_export_dialog(
            fake_parent,
            mock_tracks,
            name="ErrGroup",
            nodes_to_keep={3},
            colormap=mock_colormap,
        )

    assert result is False
    mock_warning.assert_called_once()
    # Ensure the file dialog was shown
    mock_file_dialog.exec_.assert_called_once()
