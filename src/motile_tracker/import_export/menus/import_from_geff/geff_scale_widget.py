import numpy as np
from geff.affine import Affine
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from motile_tracker.import_export.menus.import_from_geff.geff_import_utils import (
    clear_layout,
)


class ScaleWidget(QWidget):
    """Widget to specify the spatial scaling of the graph in relation to its segmentation
    data."""

    def __init__(self):
        super().__init__()

        self.scale = None

        # wrap content layout in a QGroupBox
        self.scale_layout = QVBoxLayout()
        box = QGroupBox("Scaling")
        box.setLayout(self.scale_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(box)
        main_layout.setAlignment(Qt.AlignTop)

        self.setLayout(main_layout)
        self.setToolTip(
            "<html><body><p style='white-space:pre-wrap; width: 300px;'>"
            "Specify the spatial scaling (pixel to world coordinate) in relation to "
            "the segmentation data, if provided."
        )
        self.setVisible(False)

    def _prefill_from_metadata(self, metadata: dict) -> None:
        """Update the scale widget, prefilling with metadata information if possible.
        Args:
            metadata (dict): geff metadata dictionary containing 'affine' and 'axes' keys.
        """

        if len(metadata) > 0:
            self.setVisible(True)
            clear_layout(self.scale_layout)
            self.scale_form_layout = QFormLayout()

            affine = metadata.get("affine")
            if affine is not None:
                affine = affine.get("matrix", None)
                affine = Affine(matrix=affine)
                linear = affine.linear_matrix
                self.scale = tuple(np.diag(linear))
            else:
                self.scale = [1] * len(metadata.get("axes"))

            # Spinboxes for scaling in (z), y, x.
            self.z_label = QLabel("z")
            self.z_spin_box = self._scale_spin_box(self.scale[-3])
            self.z_label.setVisible(len(self.scale) == 4)
            self.z_spin_box.setVisible(len(self.scale) == 4)
            self.y_spin_box = self._scale_spin_box(self.scale[-2])
            self.x_spin_box = self._scale_spin_box(self.scale[-1])

            self.scale_form_layout.addRow(self.z_label, self.z_spin_box)
            self.scale_form_layout.addRow(QLabel("y"), self.y_spin_box)
            self.scale_form_layout.addRow(QLabel("x"), self.x_spin_box)

            self.scale_layout.addLayout(self.scale_form_layout)

    def _scale_spin_box(self, value: float) -> QDoubleSpinBox:
        """Return a QDoubleSpinBox for scaling values"""

        spin_box = QDoubleSpinBox()
        spin_box.setValue(value)
        spin_box.setSingleStep(0.1)
        spin_box.setMinimum(0)
        spin_box.setDecimals(3)
        return spin_box

    def get_scale(self) -> list[float]:
        """Return the scaling values in the spinboxes as a list of floats. Also return 1
        for the time dimension.
        """

        if len(self.scale) == 4:
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
