from qtpy.QtWidgets import QDoubleSpinBox, QGroupBox, QLabel, QVBoxLayout, QWidget


class ScaleWidget(QWidget):
    """Voxel dimension widget

    Lets the user specify voxel dimensions using double spin boxes
    """

    def __init__(self, scaling: tuple):
        super().__init__()

        self.scaling = scaling

        if len(self.scaling) not in (3, 4):
            raise ValueError("Dimensions must be 3 (tyx) or 4 (tzyx)")

        main_layout = QVBoxLayout()
        voxel_dimension_box = QGroupBox("Voxel dimensions")
        voxel_dimension_layout = QVBoxLayout()

        self.x_spin = QDoubleSpinBox()
        self.y_spin = QDoubleSpinBox()

        self.x_spin.setValue(self.scaling[2])
        self.y_spin.setValue(self.scaling[1])

        voxel_dimension_layout.addWidget(QLabel("Y (µm):"))
        voxel_dimension_layout.addWidget(self.y_spin)
        voxel_dimension_layout.addWidget(QLabel("X (µm):"))
        voxel_dimension_layout.addWidget(self.x_spin)

        if len(self.scaling) == 4:
            self.z_spin = QDoubleSpinBox()
            self.z_spin.setValue(self.scaling[3])
            voxel_dimension_layout.addWidget(QLabel("Z (µm):"))
            voxel_dimension_layout.addWidget(self.z_spin)

        voxel_dimension_box.setLayout(voxel_dimension_layout)
        main_layout.addWidget(voxel_dimension_box)
        self.setLayout(main_layout)

    def get_scaling(self):
        """Return the scaling information in the spinboxes"""

        if len(self.scaling) == 3:
            self.scaling = (1, self.y_spin.value(), self.x_spin.value())

        if len(self.scaling) == 4:
            self.scaling = (
                1,
                self.z_spin.value(),
                self.y_spin.value(),
                self.x_spin.value(),
            )

        return self.scaling
