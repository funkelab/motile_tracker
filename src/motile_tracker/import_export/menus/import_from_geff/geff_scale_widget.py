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

    def _prefill_from_metadata(self, metadata: dict, ndim: int | None = None) -> None:
        """Update the scale widget, prefilling with metadata information if possible.
        Args:
            metadata (dict): geff metadata dictionary containing 'axes' key with scaling
                information.
            ndim (int | None): The actual dimensionality of the segmentation data (3 or 4).
                If provided, this overrides any inference from metadata. Either ndim or
                axes in metadata must be provided.
        """
        axes = metadata.get("axes")

        # We need either ndim or axes to determine dimensionality
        if ndim is None and not axes:
            raise ValueError(
                "Cannot determine dimensionality: either ndim or metadata['axes'] must be provided"
            )

        self.setVisible(True)
        clear_layout(self.scale_layout)
        self.scale_form_layout = QFormLayout()

        # Determine dimensionality: use actual segmentation ndim if provided, otherwise axes
        target_ndim = ndim if ndim is not None else len(axes)

        # Initialize scale based on target dimensionality
        self.scale = [1.0] * target_ndim

        # Get scale values from axes metadata if available
        if axes:
            lookup = {a["name"].lower(): a.get("scale", 1) or 1 for a in axes}
            self.scale[-1], self.scale[-2] = lookup.get("x", 1), lookup.get("y", 1)
            if len(self.scale) == 4:
                self.scale[-3] = lookup.get("z", 1)

        # Create spinboxes
        self.y_spin_box = self._scale_spin_box(self.scale[-2])
        self.x_spin_box = self._scale_spin_box(self.scale[-1])

        # Only create z spinbox if we have 4D data
        if len(self.scale) == 4:
            self.z_spin_box = self._scale_spin_box(self.scale[-3])
            self.z_label = QLabel("z")
            self.scale_form_layout.addRow(self.z_label, self.z_spin_box)

        # Add y and x rows to form layout
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

    def get_scale(self) -> list[float] | None:
        """Return the scaling values in the spinboxes as a list of floats.

        Returns 1 for the time dimension, and then the spatial scales based on
        whether the data is 3D (time, y, x) or 4D (time, z, y, x).

        Returns None if the scale widget hasn't been initialized (no segmentation).
        """
        if self.scale is None:
            return None

        if len(self.scale) == 4:
            # 4D data
            scale = [
                1,
                self.z_spin_box.value(),
                self.y_spin_box.value(),
                self.x_spin_box.value(),
            ]
        else:
            # 3D data
            scale = [
                1,
                self.y_spin_box.value(),
                self.x_spin_box.value(),
            ]

        return scale
