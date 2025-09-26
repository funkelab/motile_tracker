import os

import tifffile
import zarr
from psygnal import Signal
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SegmentationWidget(QWidget):
    """QWidget for specifying pixel calibration"""

    update_buttons = Signal()

    def __init__(self, incl_z=True):
        super().__init__()

        self.incl_z = incl_z

        layout = QVBoxLayout()
        self.image_path_line = QLineEdit(self)
        self.image_path_line.editingFinished.connect(self.update_buttons.emit)
        self.image_browse_button = QPushButton("Browse Segmentation", self)
        self.image_browse_button.setAutoDefault(0)
        self.image_browse_button.clicked.connect(self._browse_segmentation)

        image_widget = QWidget()
        image_layout = QVBoxLayout()
        image_sublayout = QHBoxLayout()
        image_sublayout.addWidget(QLabel("Segmentation File Path:"))
        image_sublayout.addWidget(self.image_path_line)
        image_sublayout.addWidget(self.image_browse_button)

        label = QLabel(
            "Segmentation files can either be a single tiff stack, or a directory inside"
            " a zarr folder."
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

        # Spinboxes for scaling in x, y, and z (optional)
        layout.addWidget(QLabel("Specify scaling"))
        scale_form_layout = QFormLayout()
        self.z_spin_box = self._scale_spin_box()
        self.y_spin_box = self._scale_spin_box()
        self.x_spin_box = self._scale_spin_box()

        if self.incl_z:
            scale_form_layout.addRow(QLabel("z"), self.z_spin_box)
        scale_form_layout.addRow(QLabel("y"), self.y_spin_box)
        scale_form_layout.addRow(QLabel("x"), self.x_spin_box)

        layout.addLayout(scale_form_layout)
        layout.setAlignment(Qt.AlignTop)

        self.setLayout(layout)

    def _scale_spin_box(self) -> QDoubleSpinBox:
        """Return a QDoubleSpinBox for scaling values"""

        spin_box = QDoubleSpinBox()
        spin_box.setValue(1.0)
        spin_box.setSingleStep(0.1)
        spin_box.setMinimum(0)
        spin_box.setDecimals(3)
        return spin_box

    def get_scale(self) -> list[float]:
        """Return the scaling values in the spinboxes as a list of floats.
        Since we currently require a dummy 1 value for the time dimension, add it here.
        """

        if self.incl_z:
            scale = [
                1,
                self.z_spin_box.value(),
                self.y_spin_box.value(),
                self.x_spin_box.value(),
            ]
        else:
            scale = [
                1,
                self.y_spin_box.value(),
                self.x_spin_box.value(),
            ]

        return scale

    def _browse_segmentation(self) -> None:
        """Open custom dialog to select either a file or a folder"""

        dialog = FileFolderDialog(self)
        if dialog.exec_():
            selected_path = dialog.get_selected_path()
            if selected_path:
                self.image_path_line.setText(selected_path)

    def _load_segmentation(self) -> None:
        """Load the segmentation image file"""

        # Check if a valid path to a segmentation image file is provided and load it
        if os.path.exists(self.image_path_line.text()):
            if self.image_path_line.text().endswith(".tif"):
                segmentation = tifffile.imread(
                    self.image_path_line.text()
                )  # Assuming no segmentation is needed at this step
            elif ".zarr" in self.image_path_line.text():
                segmentation = zarr.open(self.image_path_line.text())
            else:
                QMessageBox.warning(
                    self,
                    "Invalid file type",
                    "Please provide a tiff or zarr file for the segmentation image stack",
                )
                return
        else:
            segmentation = None
        self.segmentation = segmentation


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
            "Select Segmentation File",
            "",
            "Segmentation Files (*.tiff *.zarr *.tif)",
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
