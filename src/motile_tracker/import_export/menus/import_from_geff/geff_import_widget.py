import os
from pathlib import Path

import zarr
from psygnal import Signal
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from zarr.storage import FSStore

from motile_tracker.import_export.menus.import_from_geff.geff_import_utils import (
    find_geff_group,
)


class ImportGeffWidget(QWidget):
    """QWidget for selecting geff directory"""

    update_buttons = Signal()

    def __init__(self):
        super().__init__()

        self.root = None
        self.dir_name = None

        # QlineEdit for geff file path and browse button
        self.geff_path_line = QLineEdit(self)
        self.geff_path_line.setFocus()
        self.geff_path_line.setFocusPolicy(Qt.StrongFocus)
        self.geff_path_line.returnPressed.connect(self._on_line_editing_finished)
        self.geff_browse_button = QPushButton("Browse", self)
        self.geff_browse_button.setAutoDefault(0)
        self.geff_browse_button.clicked.connect(self._browse_geff)

        browse_layout = QHBoxLayout()
        browse_layout.addWidget(self.geff_path_line)
        browse_layout.addWidget(self.geff_browse_button)

        box = QGroupBox("Path to geff zarr directory")
        box_layout = QVBoxLayout()
        box_layout.addLayout(browse_layout)
        box.setLayout(box_layout)
        main_layout = QVBoxLayout()
        main_layout.addWidget(box)
        self.setLayout(main_layout)

    def _on_line_editing_finished(self) -> None:
        """Load the geff group when the user presses Enter in the path line"""

        folder_path = self.geff_path_line.text().strip()
        if not folder_path:
            self.root = None
            self.update_buttons.emit()  # to remove any widgets and disable finish button
        else:
            # try to load, will raise an error if no zarr group can be found
            self._load_geff(Path(folder_path))

    def _browse_geff(self) -> None:
        """Open File dialog to select geff folder"""

        folder = QFileDialog.getExistingDirectory(self, "Select Geff Zarr directory")
        if folder:
            folder_path = Path(folder)
            self.geff_path_line.setText(str(folder_path))
            self._load_geff(folder_path)

    def _load_geff(self, folder_path: Path) -> None:
        """Load the graph and display the geffFieldMapWidget"""

        self.root = None
        if not os.path.exists(folder_path):
            QMessageBox.critical(self, "Error", f"Path does not exist: {folder_path}")
            self.update_buttons.emit()
            return
        try:
            store = FSStore(folder_path)
            root = zarr.group(store=store)
        except (KeyError, ValueError, OSError) as e:
            QMessageBox.critical(self, "Error", f"Could not open zarr store: {e}")
            self.update_buttons.emit()
            return

        geff_group = find_geff_group(root)
        if geff_group is None:
            QMessageBox.critical(
                self, "Error", "No geff group found in the selected directory."
            )
            self.update_buttons.emit()
            return

        self.root = geff_group
        self.dir_name = os.path.basename(folder_path)
        self.update_buttons.emit()
