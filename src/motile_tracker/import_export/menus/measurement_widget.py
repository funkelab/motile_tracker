import numpy as np
from motile_toolbox.candidate_graph.graph_attributes import NodeAttr
from psygnal import Signal
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from motile_tracker.import_export.menus.intensity_img_widget import IntensityImageWidget
from motile_tracker.motile.backend.features import feature_properties


class MeasurementWidget(QWidget):
    """QWidget to choose which measurements should be calculated"""

    update_features = Signal()

    def __init__(self, columns_left: list[str], ndim: int):
        super().__init__()

        self.columns_left = columns_left
        self.layout = QVBoxLayout()

        # Mapping between display_name and node_attr
        self.feature_mapping = {
            feature.display_name: feature.node_attr
            for feature in feature_properties
            if feature.dims == ndim + 1 and not feature.required
        }

        self.layout.addWidget(QLabel("Choose measurements to calculate"))

        self.measurement_checkboxes = {}
        self.radio_buttons = {}
        self.column_dropdowns = {}

        # Add IntensityImageWidget
        self.intensity_widget = IntensityImageWidget()
        self.intensity_widget.update_buttons.connect(self.emit_update_features)
        self.intensity_widget.setEnabled(False)  # Initially disabled
        self.layout.addWidget(self.intensity_widget)

        for display_name, node_attr in self.feature_mapping.items():
            row_layout = QHBoxLayout()

            # Use display_name for the checkbox label
            checkbox = QCheckBox(display_name)
            checkbox.setChecked(False)
            checkbox.stateChanged.connect(self.emit_update_features)
            self.measurement_checkboxes[display_name] = checkbox
            row_layout.addWidget(checkbox)

            recompute_radio = QRadioButton("Recompute")
            recompute_radio.setChecked(True)
            select_column_radio = QRadioButton("Select from column")
            button_group = QButtonGroup()
            button_group.addButton(recompute_radio)
            button_group.addButton(select_column_radio)
            self.radio_buttons[display_name] = button_group
            row_layout.addWidget(recompute_radio)
            row_layout.addWidget(select_column_radio)

            column_dropdown = QComboBox()
            column_dropdown.addItems(self.columns_left)
            column_dropdown.setEnabled(False)
            column_dropdown.currentIndexChanged.connect(self.emit_update_features)
            self.column_dropdowns[display_name] = column_dropdown
            row_layout.addWidget(column_dropdown)

            select_column_radio.toggled.connect(
                lambda checked, dropdown=column_dropdown: dropdown.setEnabled(checked)
            )
            select_column_radio.toggled.connect(self.emit_update_features)

            # Special handling for INTENSITY_MEAN
            if node_attr == NodeAttr.INTENSITY_MEAN.value:
                checkbox.stateChanged.connect(
                    lambda state: self._update_intensity_widget(state)
                )

            self.layout.addLayout(row_layout)

        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)

    def _update_intensity_widget(self, checkbox_state):
        """Enable or disable the IntensityImageWidget based on conditions."""
        if checkbox_state:
            self.intensity_widget.setEnabled(True)
        else:
            self.intensity_widget.setEnabled(False)

    def emit_update_features(self):
        self.update_features.emit()

    def get_measurements(self) -> dict:
        """Return the selected measurements as a dictionary with node_attr as keys"""

        selected_measurements = {}
        for display_name, checkbox in self.measurement_checkboxes.items():
            if checkbox.isChecked():
                button_group = self.radio_buttons[display_name]
                checked_button = button_group.checkedButton()
                if checked_button is not None:
                    if checked_button.text() == "Recompute":
                        selected_measurements[self.feature_mapping[display_name]] = (
                            "Recompute"
                        )
                    elif checked_button.text() == "Select from column":
                        # Retrieve the column name that was chosen
                        selected_measurements[self.feature_mapping[display_name]] = (
                            self.column_dropdowns[display_name].currentText()
                        )
        return selected_measurements

    def get_intensity_image(self) -> np.ndarray | None:
        """Loaded intensity image, if provided"""

        self.intensity_widget.load_intensity_image()
        return self.intensity_widget.intensity_image
