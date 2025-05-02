import os

import tifffile
import zarr
from psygnal import Signal
from qtpy.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class IntensityImageWidget(QWidget):
    """QWidget to select intensity image file"""

    update_buttons = Signal()

    def __init__(self):
        super().__init__()

        self.intensity_image = None

        layout = QVBoxLayout()
        self.image_path_line = QLineEdit(self)
        self.image_path_line.editingFinished.connect(self.update_buttons.emit)
        self.image_browse_button = QPushButton("Browse Intensity Image", self)
        self.image_browse_button.setAutoDefault(0)
        self.image_browse_button.clicked.connect(self._browse_intensity_image)

        image_widget = QWidget()
        image_layout = QVBoxLayout()
        image_sublayout = QHBoxLayout()
        image_sublayout.addWidget(QLabel("Intensity Image File Path:"))
        image_sublayout.addWidget(self.image_path_line)
        image_sublayout.addWidget(self.image_browse_button)

        label = QLabel(
            "Intensity image files can either be a single tiff stack, or a directory inside a zarr folder."
        )
        font = label.font()
        font.setItalic(True)
        label.setFont(font)

        label.setWordWrap(True)
        image_layout.addWidget(label)

        image_layout.addLayout(image_sublayout)
        image_widget.setLayout(image_layout)
        image_widget.setMaximumHeight(100)

        layout.addWidget(image_widget)

        self.setLayout(layout)

    def _browse_intensity_image(self) -> None:
        """Open custom dialog to select either a file or a folder"""

        dialog = FileFolderDialog(self)
        if dialog.exec_():
            selected_path = dialog.get_selected_path()
            if selected_path:
                self.image_path_line.setText(selected_path)
                self.update_buttons.emit()

    def load_intensity_image(self) -> None:
        """Load the intensity image file"""

        # Check if a valid path to a intensity image file is provided and if so load it
        if os.path.exists(self.image_path_line.text()):
            if self.image_path_line.text().endswith(".tif"):
                self.intensity_image = tifffile.imread(
                    self.image_path_line.text()
                )  # Assuming no intensity is needed at this step
            elif ".zarr" in self.image_path_line.text():
                self.intensity_image = zarr.open(self.image_path_line.text())
            else:
                QMessageBox.warning(
                    self,
                    "Invalid file type",
                    "Please provide a tiff or zarr file for the intensity image stack",
                )
                return
        else:
            self.intensity_image = None


class FileFolderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Tif File or Zarr Folder")

        self.layout = QVBoxLayout(self)

        self.path_line_edit = QLineEdit(self)
        self.layout.addWidget(self.path_line_edit)

        button_layout = QHBoxLayout()

        self.file_button = QPushButton("Select tiff file", self)
        self.file_button.clicked.connect(self.select_file)
        self.file_button.setAutoDefault(False)
        self.file_button.setDefault(False)

        button_layout.addWidget(self.file_button)

        self.folder_button = QPushButton("Select zarr folder", self)
        self.folder_button.clicked.connect(self.select_folder)
        self.folder_button.setAutoDefault(False)
        self.folder_button.setDefault(False)
        button_layout.addWidget(self.folder_button)

        self.layout.addLayout(button_layout)

        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Select intensity image file",
            "",
            "intensity image files (*.tiff *.zarr *.tif)",
        )
        if file:
            self.path_line_edit.setText(file)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if folder:
            self.path_line_edit.setText(folder)

    def get_selected_path(self):
        return self.path_line_edit.text()
