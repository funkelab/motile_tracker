from pathlib import Path

from funtracks.data_model import Tracks
from funtracks.import_export.export_to_geff import export_to_geff
from qtpy.QtWidgets import (
    QFileDialog,
    QInputDialog,
    QMessageBox,
)


class ExportDialog:
    """Handles exporting tracks to CSV or Geff."""

    @staticmethod
    def show_export_dialog(parent, tracks: Tracks, name: str):
        """
        Export tracks to CSV or Geff.

        Args:
            tracks (Tracks): to be exported Tracks object.
            name (str): filename for exporting
        """

        label = "Choose export format:"

        export_type, ok = QInputDialog.getItem(
            parent,
            "Select Export Type",
            label,
            ["CSV", "geff"],
            0,
            False,
        )

        if not ok:
            return False

        if export_type == "CSV":
            file_dialog = QFileDialog(parent)
            file_dialog.setFileMode(QFileDialog.AnyFile)
            file_dialog.setAcceptMode(QFileDialog.AcceptSave)
            file_dialog.setNameFilter("CSV files (*.csv)")
            file_dialog.setDefaultSuffix("csv")
            default_file = f"{name}_tracks.csv"
            file_dialog.selectFile(str(Path.home() / default_file))

            if file_dialog.exec_():
                file_path = Path(file_dialog.selectedFiles()[0])
                tracks.export_tracks(file_path)
                return True

        elif export_type == "geff":
            file_dialog = QFileDialog(parent, "Save as geff file")
            file_dialog.setFileMode(QFileDialog.AnyFile)
            file_dialog.setAcceptMode(QFileDialog.AcceptSave)
            file_dialog.setNameFilter("Zarr folder (*.zarr)")
            file_dialog.setDefaultSuffix("zarr")
            default_file = f"{name}_geff.zarr"
            file_dialog.selectFile(str(Path.home() / default_file))

            if file_dialog.exec_():
                file_path = Path(file_dialog.selectedFiles()[0])
                try:
                    export_to_geff(tracks, file_path, overwrite=True)
                    return True
                except ValueError as e:
                    QMessageBox.warning(parent, "Export Error", str(e))
        return False
