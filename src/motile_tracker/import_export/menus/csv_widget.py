import os

import pandas as pd
from psygnal import Signal
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QComboBox,
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

from motile_tracker.data_views.graph_attributes import NodeAttr


class CSVFieldMapWidget(QWidget):
    """QWidget accepting a CSV file and displaying the different column names in
    QComboBoxes
    """

    columns_updated = Signal()

    def __init__(self, csv_columns: list[str], seg: bool = False, incl_z: bool = False):
        super().__init__()

        self.standard_fields = [
            NodeAttr.TIME.value,
            "y",
            "x",
            "id",
            "parent_id",
        ]

        self.csv_columns = csv_columns
        self.columns_left = []

        if incl_z:
            self.standard_fields.insert(1, "z")
        if seg:
            self.standard_fields.insert(-2, "seg_id")

        csv_column_layout = QVBoxLayout()
        csv_column_layout.addWidget(QLabel("Choose columns from CSV file"))

        # Field Mapping Layout
        self.mapping_layout = QFormLayout()
        self.mapping_widgets = {}
        layout = QVBoxLayout()

        initial_mapping = self._get_initial_mapping(csv_columns)
        for attribute, csv_column in initial_mapping.items():
            if attribute in self.standard_fields:
                combo = QComboBox()
                combo.addItems(csv_columns)
                combo.setCurrentText(csv_column)
                combo.currentIndexChanged.connect(self._update_columns_left)
                label = QLabel(attribute)
                label.setToolTip(self._get_tooltip(attribute))
                self.mapping_widgets[attribute] = combo
                self.mapping_layout.addRow(label, combo)

        # Assemble layouts
        csv_column_layout.addLayout(self.mapping_layout)
        layout.addLayout(csv_column_layout)
        self.setLayout(layout)

    def _update_columns_left(self) -> None:
        """Update the list of columns that have not been mapped yet"""

        self.columns_left = [
            column
            for column in self.csv_columns
            if column not in self.get_name_map().values()
        ]
        self.columns_updated.emit()

    def _get_tooltip(self, attribute: str) -> str:
        """Return the tooltip for the given attribute"""

        tooltips = {
            NodeAttr.TIME.value: "The time point of the track. Must be an integer",
            "y": "The world y-coordinate of the track.",
            "x": "The world x-coordinate of the track.",
            "id": "The unique identifier of the node (string or integer).",
            "parent_id": "The unique identifier of the parent node (string or integer).",
            "z": "The world z-coordinate of the track.",
            "seg_id": "The integer label value in the segmentation file.",
        }

        return tooltips.get(attribute, "")

    def _get_initial_mapping(self, csv_columns: list[str]) -> dict[str, str]:
        """Make an initial guess for mapping of csv columns to fields"""

        mapping = {}
        self.columns_left: list = csv_columns.copy()

        # find exact matches for standard fields
        for attribute in self.standard_fields:
            if attribute in self.columns_left:
                mapping[attribute] = attribute
                self.columns_left.remove(attribute)

        # assign first remaining column as best guess for remaining standard fields
        for attribute in self.standard_fields:
            if attribute in mapping:
                continue
            if len(self.columns_left) > 0:
                mapping[attribute] = self.columns_left.pop(0)
            else:
                # no good guesses left - just put something
                mapping[attribute] = csv_columns[-1]

        return mapping

    def get_name_map(self) -> dict[str, str]:
        """Return a mapping from feature name to csv field name"""

        return {
            attribute: combo.currentText()
            for attribute, combo in self.mapping_widgets.items()
        }


class CSVWidget(QWidget):
    """QWidget for selecting CSV file and optional segmentation image"""

    update_buttons = Signal()

    def __init__(self, add_segmentation: bool = False, incl_z: bool = False):
        super().__init__()

        self.add_segmentation = add_segmentation
        self.incl_z = incl_z
        self.df = None

        self.layout = QVBoxLayout(self)

        # QlineEdit for CSV file path and browse button
        self.csv_path_line = QLineEdit(self)
        self.csv_path_line.setFocusPolicy(Qt.StrongFocus)
        self.csv_path_line.returnPressed.connect(self._on_csv_editing_finished)
        self.csv_browse_button = QPushButton("Browse Tracks CSV file", self)
        self.csv_browse_button.setAutoDefault(0)
        self.csv_browse_button.clicked.connect(self._browse_csv)

        csv_layout = QHBoxLayout()
        csv_layout.addWidget(QLabel("CSV File Path:"))
        csv_layout.addWidget(self.csv_path_line)
        csv_layout.addWidget(self.csv_browse_button)
        csv_widget = QWidget()
        csv_widget.setLayout(csv_layout)

        self.layout.addWidget(csv_widget)

        # Initialize the CSVFieldMapWidget as None
        self.csv_field_widget = None

    def _on_csv_editing_finished(self) -> None:
        """Load the CSV file when the user presses Enter in the CSV path line"""

        csv_path = self.csv_path_line.text()
        self._load_csv(csv_path)

    def _browse_csv(self) -> None:
        """Open File dialog to select CSV file"""

        csv_file, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "", "CSV Files (*.csv)"
        )
        if csv_file:
            self._load_csv(csv_file)
        else:
            QMessageBox.warning(self, "Input Required", "Please select a CSV file.")

    def _load_csv(self, csv_file: str) -> None:
        """Load the csv file and display the CSVFieldMapWidget"""

        if csv_file == "":
            self.df = None
            return
        if not os.path.exists(csv_file):
            QMessageBox.critical(self, "Error", "The specified file was not found.")
            self.df = None
            return

        self.csv_path_line.setText(csv_file)

        # Ensure CSV path is valid
        try:
            self.df = pd.read_csv(csv_file)
            if self.csv_field_widget is not None:
                self.layout.removeWidget(self.csv_field_widget)
            self.csv_field_widget = CSVFieldMapWidget(
                list(self.df.columns), seg=self.add_segmentation, incl_z=self.incl_z
            )
            self.csv_field_widget.columns_updated.connect(self.update_buttons)
            self.layout.addWidget(self.csv_field_widget)
            self.update_buttons.emit()

        except pd.errors.EmptyDataError:
            QMessageBox.critical(self, "Error", "The file is empty or has no data.")
            self.df = None
            return
        except pd.errors.ParserError:
            self.df = None
            QMessageBox.critical(
                self, "Error", "The file could not be parsed as a valid CSV."
            )
            return
