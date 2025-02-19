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


class MeasurementWidget(QWidget):
    """QWidget to choose which measurements should be calculated"""

    update_features = Signal()

    def __init__(self, columns_left: list[str], ndim: int):
        super().__init__()

        self.columns_left = columns_left
        self.layout = QVBoxLayout()

        # Checkboxes for measurements
        self.measurements = []
        self.layout.addWidget(QLabel("Choose measurements to calculate"))

        if ndim == 2:
            self.measurements.append("Area")
        elif ndim == 3:
            self.measurements.append("Volume")

        self.measurement_checkboxes = {}
        self.radio_buttons = {}
        self.select_column_radio_buttons = {}
        self.column_dropdowns = {}

        for measurement in self.measurements:
            row_layout = QHBoxLayout()

            checkbox = QCheckBox(measurement)
            checkbox.setChecked(False)
            checkbox.stateChanged.connect(self.emit_update_features)
            self.measurement_checkboxes[measurement] = checkbox
            row_layout.addWidget(checkbox)

            recompute_radio = QRadioButton("Recompute")
            recompute_radio.setChecked(True)
            select_column_radio = QRadioButton("Select from column")
            button_group = QButtonGroup()
            button_group.addButton(recompute_radio)
            button_group.addButton(select_column_radio)
            self.radio_buttons[measurement] = button_group
            row_layout.addWidget(recompute_radio)
            row_layout.addWidget(select_column_radio)

            column_dropdown = QComboBox()
            column_dropdown.addItems(self.columns_left)
            column_dropdown.setEnabled(False)
            column_dropdown.currentIndexChanged.connect(self.emit_update_features)
            self.column_dropdowns[measurement] = column_dropdown
            row_layout.addWidget(column_dropdown)

            select_column_radio.toggled.connect(
                lambda checked, dropdown=column_dropdown: dropdown.setEnabled(checked)
            )
            select_column_radio.toggled.connect(self.emit_update_features)

            self.layout.addLayout(row_layout)

        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)

    def emit_update_features(self):
        self.update_features.emit()

    def get_measurements(self) -> list[str]:
        """Return the selected measurements as a list of strings"""

        selected_measurements = []
        for prop_name, checkbox in self.measurement_checkboxes.items():
            if checkbox.isChecked():
                selected_measurements.append(prop_name)

        measurements = {}
        for measurement in selected_measurements:
            button_group = self.radio_buttons[measurement]
            checked_button = button_group.checkedButton()
            if checked_button is not None:
                if checked_button.text() == "Recompute":
                    measurements[measurement] = "Recompute"
                elif checked_button.text() == "Select from column":
                    # retrieve the column name that was chosen
                    measurements[measurement] = self.column_dropdowns[
                        measurement
                    ].currentText()

        return measurements
