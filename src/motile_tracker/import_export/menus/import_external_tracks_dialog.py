import pandas as pd
from qtpy.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from motile_tracker.import_export.load_tracks import tracks_from_df
from motile_tracker.import_export.menus.csv_widget import CSVWidget
from motile_tracker.import_export.menus.measurement_widget import MeasurementWidget
from motile_tracker.import_export.menus.metadata_menu import MetadataMenu
from motile_tracker.import_export.menus.segmentation_widget import SegmentationWidget


class ImportTracksDialog(QDialog):
    """Multipage dialog for importing external tracks from a CSV file"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Import external tracks from CSV")

        self.csv = None
        self.segmentation = None

        self.layout = QVBoxLayout(self)
        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

        # navigation buttons
        self.button_layout = QHBoxLayout()
        self.previous_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.finish_button = QPushButton("Finish")
        self.button_layout.addWidget(self.previous_button)
        self.button_layout.addWidget(self.next_button)
        self.button_layout.addWidget(self.finish_button)
        self.layout.addLayout(self.button_layout)

        # Connect button signals
        self.previous_button.clicked.connect(self._go_to_previous_page)
        self.next_button.clicked.connect(self._go_to_next_page)
        self.finish_button.clicked.connect(self._finish)

        # Page 1 for metadata choices
        self.page1 = QWidget()
        page1_layout = QVBoxLayout()
        self.menu_widget = MetadataMenu()
        page1_layout.addWidget(self.menu_widget)
        self.page1.setLayout(page1_layout)
        self.stacked_widget.addWidget(self.page1)

        # Connect signals for updating pages
        self.menu_widget.segmentation_checkbox.stateChanged.connect(self._update_pages)
        self.menu_widget.radio_2D.clicked.connect(self._update_pages)
        self.menu_widget.radio_3D.clicked.connect(self._update_pages)

        # Page 2 for csv loading
        self.data_widget = CSVWidget(
            add_segmentation=self.menu_widget.segmentation_checkbox.isChecked()
        )
        self.data_widget.update_buttons.connect(self._update_buttons)
        self.data_widget.update_buttons.connect(self._update_measurement_widget)
        self.stacked_widget.addWidget(self.data_widget)

        # Optional Page 3 with segmentation information
        self.segmentation_page = None

        # Optional Page 4 with measurement attributes that should be calculated
        # (only if segmentation is provided)
        self.measurement_widget = None

        self._update_buttons()

    def _update_measurement_widget(self) -> None:
        """Update the measurement widget based on the data dimensions and on columns that
        have not been picked in the csv_field_widget
        """

        if (
            self.data_widget.df is not None
            and self.menu_widget.segmentation_checkbox.isChecked()
        ):
            if self.measurement_widget is not None:
                self.stacked_widget.removeWidget(self.measurement_widget)
            self.measurement_widget = MeasurementWidget(
                self.data_widget.csv_field_widget.columns_left,
                ndim=2 if self.menu_widget.radio_2D.isChecked() else 3,
            )
            self.stacked_widget.addWidget(self.measurement_widget)
            self._update_buttons()

    def _update_pages(self) -> None:
        """Recreate page3 and page4 when the user changes the options in the menu"""

        self.stacked_widget.removeWidget(self.data_widget)
        if self.segmentation_page is not None:
            self.stacked_widget.removeWidget(self.segmentation_page)
        if self.measurement_widget is not None:
            self.stacked_widget.removeWidget(self.measurement_widget)

        self.data_widget = CSVWidget(
            add_segmentation=self.menu_widget.segmentation_checkbox.isChecked(),
            incl_z=self.menu_widget.radio_3D.isChecked(),
        )
        self.data_widget.update_buttons.connect(self._update_buttons)
        self.data_widget.update_buttons.connect(self._update_measurement_widget)

        self.stacked_widget.addWidget(self.data_widget)

        if self.menu_widget.segmentation_checkbox.isChecked():
            self.segmentation_page = SegmentationWidget(
                self.menu_widget.radio_3D.isChecked()
            )
            self.stacked_widget.addWidget(self.segmentation_page)
            self.segmentation_page.update_buttons.connect(self._update_buttons)

        if (
            self.data_widget.df is not None
            and self.menu_widget.segmentation_checkbox.isChecked()
        ):
            self.measurement_widget = MeasurementWidget(
                self.data_widget.csv_field_widget.columns_left,
                ndim=2 if self.menu_widget.radio_2D.isChecked() else 3,
            )
            self.stacked_widget.addWidget(self.measurement_widget)

        self.stacked_widget.hide()
        self.stacked_widget.show()

    def _go_to_previous_page(self) -> None:
        """Go to the previous page."""

        current_index = self.stacked_widget.currentIndex()
        if current_index > 0:
            self.stacked_widget.setCurrentIndex(current_index - 1)
        self._update_buttons()

    def _go_to_next_page(self) -> None:
        """Go to the next page."""

        current_index = self.stacked_widget.currentIndex()
        if current_index < self.stacked_widget.count() - 1:
            self.stacked_widget.setCurrentIndex(current_index + 1)
        self._update_buttons()

    def _update_buttons(self) -> None:
        """Enable or disable buttons based on the current page."""

        # Do not allow to finish if no CSV file is loaded, or if the segmentation
        # checkbox was checked but no seg file path is given.
        if self.data_widget.df is None or (
            self.menu_widget.segmentation_checkbox.isChecked()
            and self.segmentation_page.image_path_line.text() == ""
        ):
            self.finish_button.setEnabled(False)
        else:
            self.finish_button.setEnabled(True)

        current_index = self.stacked_widget.currentIndex()
        if current_index + 1 == self.stacked_widget.count():
            self.next_button.hide()
            self.finish_button.show()
        else:
            self.next_button.show()
            self.finish_button.hide()
        self.previous_button.setEnabled(current_index > 0)
        self.next_button.setEnabled(current_index < self.stacked_widget.count() - 1)

        self.finish_button.setAutoDefault(0)
        self.next_button.setAutoDefault(0)
        self.previous_button.setAutoDefault(0)

    def _finish(self) -> None:
        """Tries to read the CSV file and optional segmentation image,
        and apply the attribute to column mapping to construct a Tracks object"""

        # Retrieve selected columns for each required field, and optional columns for
        # additional attributes
        name_map = self.data_widget.csv_field_widget.get_name_map()

        # Create new columns for each feature based on the original column values
        df = pd.DataFrame()
        for feature, column in name_map.items():
            df[feature] = self.data_widget.df[column]

        # Read scaling information from the spinboxes
        if self.segmentation_page is not None:
            scale = self.segmentation_page.get_scale()
        else:
            scale = [1, 1, 1] if self.data_widget.incl_z is False else [1, 1, 1, 1]

        if self.measurement_widget is not None:
            features = self.measurement_widget.get_measurements()
            for feature in features:
                if features[feature] != "Recompute" and (
                    feature == "Area" or feature == "Volume"
                ):
                    df["area"] = self.data_widget.df[features[feature]]
        else:
            features = []

        # Try to create a Tracks object with the provided CSV file, the attr:column
        # dictionaries, and the scaling information
        self.name = self.menu_widget.name_widget.text()

        if self.menu_widget.segmentation_checkbox.isChecked():
            self.segmentation_page._load_segmentation()
            segmentation = self.segmentation_page.segmentation
        else:
            segmentation = None

        try:
            self.tracks = tracks_from_df(df, segmentation, scale, features)

        except ValueError as e:
            QMessageBox.critical(self, "Error", f"Failed to load tracks: {e}")
            return
        self.accept()
