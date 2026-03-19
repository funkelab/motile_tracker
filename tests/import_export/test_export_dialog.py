from unittest.mock import MagicMock, patch

import pytest

from motile_tracker.import_export.menus.export_dialog import (
    ExportDialog,
    ExportTypeDialog,
)


@pytest.fixture
def mock_tracks():
    """Mock Tracks object without segmentation."""
    tracks = MagicMock()
    tracks.segmentation = None
    return tracks


@pytest.fixture
def mock_tracks_with_seg(mock_tracks):
    """Mock Tracks object with a segmentation array."""
    mock_tracks.segmentation = MagicMock()
    return mock_tracks


@pytest.fixture
def fake_parent(qtbot):
    from qtpy.QtWidgets import QWidget

    parent = QWidget()
    qtbot.addWidget(parent)
    return parent


@pytest.fixture
def mock_colormap():
    cmap = MagicMock()
    cmap.map.side_effect = lambda tid: [tid, tid, tid, 255]
    return cmap


# --- ExportTypeDialog unit tests ---


def test_checkbox_hidden_without_segmentation(qtbot):
    dialog = ExportTypeDialog(has_segmentation=False)
    qtbot.addWidget(dialog)
    assert not dialog.seg_checkbox.isVisibleTo(dialog)


def test_checkbox_visible_with_segmentation(qtbot):
    dialog = ExportTypeDialog(has_segmentation=True)
    qtbot.addWidget(dialog)
    assert dialog.seg_checkbox.isVisibleTo(dialog)


def test_seg_options_hidden_by_default(qtbot):
    """Format combo and relabel checkbox are hidden until seg_checkbox is ticked."""
    dialog = ExportTypeDialog(has_segmentation=True)
    qtbot.addWidget(dialog)
    assert not dialog.seg_format_combo.isVisibleTo(dialog)
    assert not dialog.relabel_checkbox.isVisibleTo(dialog)


def test_seg_options_shown_when_seg_checked(qtbot):
    dialog = ExportTypeDialog(has_segmentation=True)
    qtbot.addWidget(dialog)
    dialog.seg_checkbox.setChecked(True)
    assert dialog.seg_format_combo.isVisibleTo(dialog)
    assert dialog.relabel_checkbox.isVisibleTo(dialog)


def test_relabel_checked_by_default(qtbot):
    dialog = ExportTypeDialog(has_segmentation=True)
    qtbot.addWidget(dialog)
    assert dialog.relabel_checkbox.isChecked()
    assert dialog.seg_label_attr == "track_id"


def test_relabel_unchecked_gives_none_label_attr(qtbot):
    dialog = ExportTypeDialog(has_segmentation=True)
    qtbot.addWidget(dialog)
    dialog.relabel_checkbox.setChecked(False)
    assert dialog.seg_label_attr is None


def test_seg_format_defaults_to_zarr(qtbot):
    dialog = ExportTypeDialog(has_segmentation=True)
    qtbot.addWidget(dialog)
    assert dialog.seg_file_format == "zarr"


# --- ExportDialog integration tests ---


def test_export_dialog_cancel(mock_tracks, fake_parent, mock_colormap):
    """Returns False when user cancels."""
    mock_dialog = MagicMock()
    mock_dialog.exec_.return_value = 0
    with patch(
        "motile_tracker.import_export.menus.export_dialog.ExportTypeDialog",
        return_value=mock_dialog,
    ):
        result = ExportDialog.show_export_dialog(
            fake_parent, mock_tracks, name="TestGroup", colormap=mock_colormap
        )
    assert result is False


def test_export_dialog_passes_has_segmentation_false(
    mock_tracks, fake_parent, mock_colormap
):
    mock_dialog = MagicMock()
    mock_dialog.exec_.return_value = 0
    with patch(
        "motile_tracker.import_export.menus.export_dialog.ExportTypeDialog",
        return_value=mock_dialog,
    ) as mock_cls:
        ExportDialog.show_export_dialog(
            fake_parent, mock_tracks, name="x", colormap=mock_colormap
        )
    _, kwargs = mock_cls.call_args
    assert kwargs.get("has_segmentation") is False


def test_export_dialog_passes_has_segmentation_true(
    mock_tracks_with_seg, fake_parent, mock_colormap
):
    mock_dialog = MagicMock()
    mock_dialog.exec_.return_value = 0
    with patch(
        "motile_tracker.import_export.menus.export_dialog.ExportTypeDialog",
        return_value=mock_dialog,
    ) as mock_cls:
        ExportDialog.show_export_dialog(
            fake_parent, mock_tracks_with_seg, name="x", colormap=mock_colormap
        )
    _, kwargs = mock_cls.call_args
    assert kwargs.get("has_segmentation") is True


def test_export_csv_no_seg(mock_tracks, fake_parent, tmp_path, mock_colormap):
    """CSV export without segmentation."""
    csv_file = tmp_path / "tracks.csv"
    mock_tracks.graph = MagicMock()
    mock_tracks.graph.node_ids.return_value = [1, 2]
    mock_tracks.get_track_id.side_effect = lambda n: n

    mock_dialog = MagicMock()
    mock_dialog.exec_.return_value = 1
    mock_dialog.export_type = "CSV"
    mock_dialog.save_segmentation = False
    mock_dialog.seg_file_format = "zarr"
    mock_dialog.seg_label_attr = "track_id"

    mock_file_dialog = MagicMock()
    mock_file_dialog.exec_.return_value = True
    mock_file_dialog.selectedFiles.return_value = [str(csv_file)]

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
        ) as mock_export,
    ):
        result = ExportDialog.show_export_dialog(
            fake_parent,
            mock_tracks,
            name="G",
            nodes_to_keep={1, 2},
            colormap=mock_colormap,
        )

    assert result is True
    mock_export.assert_called_once_with(
        tracks=mock_tracks,
        outfile=csv_file,
        color_dict={1: [1, 1, 1, 255], 2: [2, 2, 2, 255], None: [0, 0, 0, 0]},
        node_ids={1, 2},
        use_display_names=True,
        export_seg=False,
        seg_path=None,
        seg_label_attr="track_id",
        seg_file_format="zarr",
    )


def test_export_csv_with_seg_zarr(
    mock_tracks_with_seg, fake_parent, tmp_path, mock_colormap
):
    """CSV export with segmentation as zarr."""
    csv_file = tmp_path / "tracks.csv"
    zarr_file = tmp_path / "tracks_seg.zarr"
    mock_tracks_with_seg.graph = MagicMock()
    mock_tracks_with_seg.graph.node_ids.return_value = [1, 2]
    mock_tracks_with_seg.get_track_id.side_effect = lambda n: n

    mock_dialog = MagicMock()
    mock_dialog.exec_.return_value = 1
    mock_dialog.export_type = "CSV"
    mock_dialog.save_segmentation = True
    mock_dialog.seg_file_format = "zarr"
    mock_dialog.seg_label_attr = "track_id"

    mock_csv_fd = MagicMock()
    mock_csv_fd.exec_.return_value = True
    mock_csv_fd.selectedFiles.return_value = [str(csv_file)]
    mock_seg_fd = MagicMock()
    mock_seg_fd.exec_.return_value = True
    mock_seg_fd.selectedFiles.return_value = [str(zarr_file)]

    with (
        patch(
            "motile_tracker.import_export.menus.export_dialog.ExportTypeDialog",
            return_value=mock_dialog,
        ),
        patch(
            "motile_tracker.import_export.menus.export_dialog.QFileDialog",
            side_effect=[mock_csv_fd, mock_seg_fd],
        ),
        patch(
            "motile_tracker.import_export.menus.export_dialog.export_to_csv"
        ) as mock_export,
    ):
        result = ExportDialog.show_export_dialog(
            fake_parent,
            mock_tracks_with_seg,
            name="G",
            nodes_to_keep={1, 2},
            colormap=mock_colormap,
        )

    assert result is True
    mock_export.assert_called_once_with(
        tracks=mock_tracks_with_seg,
        outfile=csv_file,
        color_dict={1: [1, 1, 1, 255], 2: [2, 2, 2, 255], None: [0, 0, 0, 0]},
        node_ids={1, 2},
        use_display_names=True,
        export_seg=True,
        seg_path=zarr_file,
        seg_label_attr="track_id",
        seg_file_format="zarr",
    )


def test_export_csv_with_seg_tiff(
    mock_tracks_with_seg, fake_parent, tmp_path, mock_colormap
):
    """CSV export with segmentation as tiff, no relabeling."""
    csv_file = tmp_path / "tracks.csv"
    tif_file = tmp_path / "tracks.tif"
    mock_tracks_with_seg.graph = MagicMock()
    mock_tracks_with_seg.graph.node_ids.return_value = [1]
    mock_tracks_with_seg.get_track_id.side_effect = lambda n: n

    mock_dialog = MagicMock()
    mock_dialog.exec_.return_value = 1
    mock_dialog.export_type = "CSV"
    mock_dialog.save_segmentation = True
    mock_dialog.seg_file_format = "tiff"
    mock_dialog.seg_label_attr = None  # no relabeling

    mock_csv_fd = MagicMock()
    mock_csv_fd.exec_.return_value = True
    mock_csv_fd.selectedFiles.return_value = [str(csv_file)]
    mock_seg_fd = MagicMock()
    mock_seg_fd.exec_.return_value = True
    mock_seg_fd.selectedFiles.return_value = [str(tif_file)]

    with (
        patch(
            "motile_tracker.import_export.menus.export_dialog.ExportTypeDialog",
            return_value=mock_dialog,
        ),
        patch(
            "motile_tracker.import_export.menus.export_dialog.QFileDialog",
            side_effect=[mock_csv_fd, mock_seg_fd],
        ),
        patch(
            "motile_tracker.import_export.menus.export_dialog.export_to_csv"
        ) as mock_export,
    ):
        result = ExportDialog.show_export_dialog(
            fake_parent,
            mock_tracks_with_seg,
            name="G",
            colormap=mock_colormap,
        )

    assert result is True
    mock_export.assert_called_once_with(
        tracks=mock_tracks_with_seg,
        outfile=csv_file,
        color_dict={1: [1, 1, 1, 255], None: [0, 0, 0, 0]},
        node_ids=None,
        use_display_names=True,
        export_seg=True,
        seg_path=tif_file,
        seg_label_attr=None,
        seg_file_format="tiff",
    )


def test_export_geff_no_seg(mock_tracks, fake_parent, tmp_path, mock_colormap):
    """GEFF export without segmentation."""
    geff_file = tmp_path / "tracks.zarr"

    mock_dialog = MagicMock()
    mock_dialog.exec_.return_value = 1
    mock_dialog.export_type = "geff"
    mock_dialog.save_segmentation = False
    mock_dialog.seg_file_format = "zarr"
    mock_dialog.seg_label_attr = "track_id"

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
        ) as mock_export,
    ):
        result = ExportDialog.show_export_dialog(
            fake_parent,
            mock_tracks,
            name="G",
            nodes_to_keep={1, 2},
            colormap=mock_colormap,
        )

    assert result is True
    mock_export.assert_called_once_with(
        mock_tracks,
        geff_file,
        overwrite=True,
        node_ids={1, 2},
        save_segmentation=False,
        seg_label_attr="track_id",
        seg_file_format="zarr",
    )


def test_export_geff_with_seg_zarr(
    mock_tracks_with_seg, fake_parent, tmp_path, mock_colormap
):
    """GEFF export with segmentation as zarr."""
    geff_file = tmp_path / "tracks.zarr"

    mock_dialog = MagicMock()
    mock_dialog.exec_.return_value = 1
    mock_dialog.export_type = "geff"
    mock_dialog.save_segmentation = True
    mock_dialog.seg_file_format = "zarr"
    mock_dialog.seg_label_attr = "track_id"

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
        ) as mock_export,
    ):
        result = ExportDialog.show_export_dialog(
            fake_parent,
            mock_tracks_with_seg,
            name="G",
            colormap=mock_colormap,
        )

    assert result is True
    mock_export.assert_called_once_with(
        mock_tracks_with_seg,
        geff_file,
        overwrite=True,
        node_ids=None,
        save_segmentation=True,
        seg_label_attr="track_id",
        seg_file_format="zarr",
    )


def test_export_geff_with_seg_tiff(
    mock_tracks_with_seg, fake_parent, tmp_path, mock_colormap
):
    """GEFF export with segmentation as tiff, no relabeling."""
    geff_file = tmp_path / "tracks.zarr"

    mock_dialog = MagicMock()
    mock_dialog.exec_.return_value = 1
    mock_dialog.export_type = "geff"
    mock_dialog.save_segmentation = True
    mock_dialog.seg_file_format = "tiff"
    mock_dialog.seg_label_attr = None

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
        ) as mock_export,
    ):
        result = ExportDialog.show_export_dialog(
            fake_parent,
            mock_tracks_with_seg,
            name="G",
            colormap=mock_colormap,
        )

    assert result is True
    mock_export.assert_called_once_with(
        mock_tracks_with_seg,
        geff_file,
        overwrite=True,
        node_ids=None,
        save_segmentation=True,
        seg_label_attr=None,
        seg_file_format="tiff",
    )


def test_export_geff_error(mock_tracks, fake_parent, tmp_path, mock_colormap):
    """Shows QMessageBox when export_to_geff raises ValueError."""
    geff_file = tmp_path / "error.zarr"

    mock_dialog = MagicMock()
    mock_dialog.exec_.return_value = 1
    mock_dialog.export_type = "geff"
    mock_dialog.save_segmentation = False
    mock_dialog.seg_file_format = "zarr"
    mock_dialog.seg_label_attr = "track_id"

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
            "motile_tracker.import_export.menus.export_dialog.export_to_geff",
            side_effect=ValueError("Export failed"),
        ),
        patch(
            "motile_tracker.import_export.menus.export_dialog.QMessageBox.warning"
        ) as mock_warning,
    ):
        result = ExportDialog.show_export_dialog(
            fake_parent, mock_tracks, name="G", colormap=mock_colormap
        )

    assert result is False
    mock_warning.assert_called_once()
