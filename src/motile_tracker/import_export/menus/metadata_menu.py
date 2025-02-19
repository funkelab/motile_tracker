from qtpy.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)


class MetadataMenu(QWidget):
    """Menu to choose tracks name, data dimensions, scaling, and optional segmentation"""

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # Name of the tracks
        name_layout = QVBoxLayout()
        name_box = QGroupBox("Tracks Name")
        self.name_widget = QLineEdit("External Tracks from CSV")
        name_layout.addWidget(self.name_widget)
        name_box.setLayout(name_layout)
        name_box.setMaximumHeight(100)
        layout.addWidget(name_box)

        # Dimensions of the tracks
        dimensions_layout = QVBoxLayout()
        dimension_box = QGroupBox("Data Dimensions")
        data_button_group = QButtonGroup()
        button_layout = QHBoxLayout()
        self.radio_2D = QRadioButton("2D + time")
        self.radio_2D.setChecked(True)
        self.radio_3D = QRadioButton("3D + time")
        data_button_group.addButton(self.radio_2D)
        data_button_group.addButton(self.radio_3D)
        button_layout.addWidget(self.radio_2D)
        button_layout.addWidget(self.radio_3D)
        dimensions_layout.addLayout(button_layout)
        dimension_box.setLayout(dimensions_layout)
        dimension_box.setMaximumHeight(80)
        layout.addWidget(dimension_box)

        # Whether or not a segmentation file exists
        segmentation_layout = QVBoxLayout()
        segmentation_box = QGroupBox("Segmentation Image")
        self.segmentation_checkbox = QCheckBox("I have a segmentation image")
        segmentation_layout.addWidget(self.segmentation_checkbox)
        segmentation_box.setLayout(segmentation_layout)
        segmentation_box.setMaximumHeight(80)
        layout.addWidget(segmentation_box)

        layout.setContentsMargins(0, 3, 0, 0)
        self.setLayout(layout)
        self.setMinimumHeight(400)
