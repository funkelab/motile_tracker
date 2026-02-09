from pathlib import Path

import napari
from funtracks.data_model import Tracks
from funtracks.import_export import export_to_csv
from funtracks.import_export.export_to_geff import export_to_geff
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QMessageBox,
    QVBoxLayout,
)


class ExportTypeDialog(QDialog):
    def __init__(self, parent=None, label: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Select Export Type")

        layout = QVBoxLayout(self)

        if label:
            layout.addWidget(QLabel(label))

        self.export_type_combo = QComboBox()
        self.export_type_combo.addItems(["CSV", "geff"])
        layout.addWidget(self.export_type_combo)

        self.relabel_checkbox = QCheckBox(
            "Export segmentation relabeled by Tracklet ID"
        )
        layout.addWidget(self.relabel_checkbox)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        # Initial visibility
        self._update_checkbox_visibility(self.export_type_combo.currentText())

        # Update visibility when export type changes
        self.export_type_combo.currentTextChanged.connect(
            self._update_checkbox_visibility
        )

    def _update_checkbox_visibility(self, export_type: str):
        self.relabel_checkbox.setVisible(export_type == "CSV")

    @property
    def export_type(self) -> str:
        return self.export_type_combo.currentText()

    @property
    def relabel_by_tracklet_id(self) -> bool:
        return self.relabel_checkbox.isChecked()


class ExportDialog:
    """Handles exporting tracks to CSV or Geff."""

    @staticmethod
    def show_export_dialog(
        parent,
        tracks: Tracks,
        name: str,
        colormap: napari.utils.Colormap,
        nodes_to_keep: set[int] | None = None,
    ):
        """
        Export tracks to CSV or Geff, with the option to export a subset of nodes only.

        Args:
            tracks (Tracks): to be exported Tracks object.
            name (str): filename for exporting
            nodes_to_keep (set[int], optional): list of nodes to be exported. Ancestor
                nodes will automatically be included to make sure the graph has no missing
                  parent nodes.
        """

        if nodes_to_keep is None:
            label = "Choose export format:"
        else:
            label = (
                f"<p style='white-space: normal;'>"
                f"<i>Export all nodes in group </i>"
                f"<span style='color: green;'><b>{name}.</b></span><br>"
                f"<i>Note that ancestors will also be included to maintain a valid "
                f"graph.</i>"
                f"</p>"
                f"<p>Choose export format:</p>"
            )

        dialog = ExportTypeDialog(parent, label)

        if dialog.exec_() != QDialog.Accepted:
            return False

        export_type = dialog.export_type
        relabel_by_tracklet_id = dialog.relabel_by_tracklet_id

        if export_type == "CSV":
            # CSV file dialog
            csv_dialog = QFileDialog(parent, "Save to CSV")  # set title
            csv_dialog.setFileMode(QFileDialog.AnyFile)
            csv_dialog.setAcceptMode(QFileDialog.AcceptSave)
            csv_dialog.setNameFilter("CSV files (*.csv)")
            csv_dialog.setDefaultSuffix("csv")
            default_csv_file = f"{name}_tracks.csv"
            csv_dialog.selectFile(str(Path.home() / default_csv_file))

            if not csv_dialog.exec_():
                return False  # User canceled

            file_path = Path(csv_dialog.selectedFiles()[0])
            seg_path = None

            # Optional segmentation dialog
            if relabel_by_tracklet_id:
                default_seg_path = file_path.with_suffix(".tif")
                seg_dialog = QFileDialog(
                    parent, "Save segmentation to TIF"
                )  # set title
                seg_dialog.setFileMode(QFileDialog.AnyFile)
                seg_dialog.setAcceptMode(QFileDialog.AcceptSave)
                seg_dialog.setNameFilter("TIF files (*.tif)")
                seg_dialog.setDefaultSuffix("tif")
                seg_dialog.selectFile(str(default_seg_path))

                if not seg_dialog.exec_():
                    return False  # User canceled

                seg_path = Path(seg_dialog.selectedFiles()[0])

            # Construct color_dict from colormap
            nodes = list(tracks.graph.nodes())
            track_ids = [tracks.get_track_id(node) for node in nodes]
            colors = [colormap.map(tid) for tid in track_ids]
            color_dict = {
                **dict(zip(nodes, colors, strict=True)),
                None: [0, 0, 0, 0],
            }

            export_to_csv(
                tracks=tracks,
                outfile=file_path,
                color_dict=color_dict,
                node_ids=nodes_to_keep,
                use_display_names=True,
                export_seg=relabel_by_tracklet_id,
                seg_path=seg_path,
            )
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
                    export_to_geff(
                        tracks, file_path, overwrite=True, node_ids=nodes_to_keep
                    )
                    return True
                except ValueError as e:
                    QMessageBox.warning(parent, "Export Error", str(e))
        return False
