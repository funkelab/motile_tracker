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


def test_export_dialog_cancel(monkeypatch, mock_tracks, fake_parent):
    """Should return False if user cancels export type selection."""
    # Simulate QInputDialog returning 'ok=False'
    monkeypatch.setattr(
        "qtpy.QtWidgets.QInputDialog.getItem", lambda *a, **kw: ("CSV", False)
    )

    result = ExportDialog.show_export_dialog(fake_parent, mock_tracks, name="TestGroup")
    assert result is False
    mock_tracks.export_tracks.assert_not_called()


def test_export_dialog_csv(monkeypatch, mock_tracks, fake_parent, tmp_path):
    """Should call export_tracks when CSV is selected and confirmed."""
    test_file = tmp_path / "test_export.csv"

    # Mock the QInputDialog to simulate choosing CSV and clicking OK
    monkeypatch.setattr(
        "motile_tracker.import_export.menus.export_dialog.QInputDialog.getItem",
        lambda *a, **kw: ("CSV", True),
    )

    # Create a fake QFileDialog instance
    mock_file_dialog_instance = MagicMock()
    mock_file_dialog_instance.exec_.return_value = True
    mock_file_dialog_instance.selectedFiles.return_value = [str(test_file)]

    # Create a fake class that returns that instance when constructed
    mock_file_dialog_class = MagicMock(return_value=mock_file_dialog_instance)

    # Patch QFileDialog *in the same module where ExportDialog is defined
    monkeypatch.setattr(
        "motile_tracker.import_export.menus.export_dialog.QFileDialog",
        mock_file_dialog_class,
    )

    # Run the dialog method
    result = ExportDialog.show_export_dialog(fake_parent, mock_tracks, name="MyGroup")

    # Assertions
    assert result is True
    mock_tracks.export_tracks.assert_called_once_with(test_file)

    # Verify QFileDialog was instantiated once
    mock_file_dialog_class.assert_called_once()


def test_export_dialog_geff(monkeypatch, mock_tracks, fake_parent, tmp_path):
    """Should call export_to_geff when geff is selected and confirmed."""
    test_file = tmp_path / "test_export.zarr"

    # Mock user selecting 'geff' and confirming
    monkeypatch.setattr(
        "motile_tracker.import_export.menus.export_dialog.QInputDialog.getItem",
        lambda *a, **kw: ("geff", True),
    )

    # Mock QFileDialog instance + class
    mock_file_dialog_instance = MagicMock()
    mock_file_dialog_instance.exec_.return_value = True
    mock_file_dialog_instance.selectedFiles.return_value = [str(test_file)]
    mock_file_dialog_class = MagicMock(return_value=mock_file_dialog_instance)

    monkeypatch.setattr(
        "motile_tracker.import_export.menus.export_dialog.QFileDialog",
        mock_file_dialog_class,
    )

    with patch(
        "motile_tracker.import_export.menus.export_dialog.export_to_geff"
    ) as mock_export_geff:
        result = ExportDialog.show_export_dialog(
            fake_parent, mock_tracks, name="MyGroup"
        )

    assert result is True
    mock_export_geff.assert_called_once_with(mock_tracks, test_file, overwrite=True)
    mock_file_dialog_class.assert_called_once()


def test_export_dialog_geff_error(monkeypatch, mock_tracks, fake_parent, tmp_path):
    """Should show a QMessageBox if export_to_geff raises ValueError."""
    test_file = tmp_path / "error_case.zarr"

    # Mock user choosing 'geff' and confirming
    monkeypatch.setattr(
        "motile_tracker.import_export.menus.export_dialog.QInputDialog.getItem",
        lambda *a, **kw: ("geff", True),
    )

    # Mock QFileDialog instance + class
    mock_file_dialog_instance = MagicMock()
    mock_file_dialog_instance.exec_.return_value = True
    mock_file_dialog_instance.selectedFiles.return_value = [str(test_file)]
    mock_file_dialog_class = MagicMock(return_value=mock_file_dialog_instance)

    monkeypatch.setattr(
        "motile_tracker.import_export.menus.export_dialog.QFileDialog",
        mock_file_dialog_class,
    )

    # Patch export_to_geff to raise ValueError and QMessageBox.warning to intercept UI
    with (
        patch(
            "motile_tracker.import_export.menus.export_dialog.export_to_geff",
            side_effect=ValueError("Export Error"),
        ),
        patch(
            "motile_tracker.import_export.menus.export_dialog.QMessageBox.warning"
        ) as mock_warning,
    ):
        result = ExportDialog.show_export_dialog(
            fake_parent, mock_tracks, name="ErrGroup"
        )

    assert result is False
    mock_warning.assert_called_once()
    mock_file_dialog_class.assert_called_once()
