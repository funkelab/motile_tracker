from pathlib import Path

from funtracks.import_export.import_from_geff import import_from_geff
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from motile_tracker.import_export.load_tracks import tracks_from_df
from motile_tracker.import_export.menus.csv_dimension_widget import (
    DimensionWidget,
)
from motile_tracker.import_export.menus.csv_import_widget import (
    ImportCSVWidget,
)
from motile_tracker.import_export.menus.geff_import_widget import (
    ImportGeffWidget,
)
from motile_tracker.import_export.menus.prop_map_widget import StandardFieldMapWidget
from motile_tracker.import_export.menus.scale_widget import ScaleWidget
from motile_tracker.import_export.menus.segmentation_widgets import (
    CSVSegmentationWidget,
    GeffSegmentationWidget,
)


class ImportDialog(QDialog):
    """Dialog for importing external tracks from a csv or geff file"""

    def __init__(self, import_type: str = "csv"):
        """
        Construct import dialog depending on the data type.
        Args:
            import_type (str): either 'geff' or 'csv'
        """

        super().__init__()
        self.import_type = import_type
        self.seg = None
        self.df = None
        self.incl_z = False
        self.setWindowTitle(f"Import external tracks from {import_type}")
        self.name = f"Tracks from {import_type}"

        # cancel and finish buttons
        self.button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.finish_button = QPushButton("Finish")
        self.finish_button.setEnabled(False)
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.finish_button)

        # Connect button signals
        self.cancel_button.clicked.connect(self._cancel)
        self.finish_button.clicked.connect(self._finish)
        self.cancel_button.setDefault(False)
        self.cancel_button.setAutoDefault(False)
        self.finish_button.setDefault(False)
        self.finish_button.setAutoDefault(False)

        # Initialize widgets and connect to update signals
        self.prop_map_widget = StandardFieldMapWidget()
        self.scale_widget = ScaleWidget()

        if import_type == "geff":
            self.import_widget = ImportGeffWidget()
            self.import_widget.update_buttons.connect(self._update_segmentation_widget)
            self.import_widget.update_buttons.connect(
                self._update_geff_field_map_widget
            )
            self.segmentation_widget = GeffSegmentationWidget(
                root=self.import_widget.root
            )
        else:
            self.import_widget = ImportCSVWidget()
            self.segmentation_widget = CSVSegmentationWidget()
            self.import_widget.update_buttons.connect(self._update_finish_button)
            self.import_widget.update_buttons.connect(self._update_csv_field_map_widget)
            self.dimension_widget = DimensionWidget()
            self.dimension_widget.update_dims.connect(self._update_csv_field_map_widget)

        self.segmentation_widget.none_radio.toggled.connect(
            self._toggle_scale_widget_and_seg_id
        )
        self.segmentation_widget.segmentation_widget.seg_path_updated.connect(
            self._update_finish_button
        )

        self.content_widget = QWidget()
        main_layout = QVBoxLayout(self.content_widget)
        main_layout.addWidget(self.import_widget)
        if import_type == "csv":
            main_layout.addWidget(self.dimension_widget)
        main_layout.addWidget(self.segmentation_widget)
        main_layout.addWidget(self.prop_map_widget)
        main_layout.addWidget(self.scale_widget)
        main_layout.addLayout(self.button_layout)
        self.content_widget.setLayout(main_layout)

        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.content_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setMinimumWidth(500)
        self.scroll_area.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.MinimumExpanding
        )

        dialog_layout = QVBoxLayout()
        dialog_layout.addWidget(self.scroll_area)
        self.setLayout(dialog_layout)

    def _resize_dialog(self) -> None:
        """Dynamic widget resizing depending on the visible contents"""

        self.content_widget.layout().activate()
        self.content_widget.adjustSize()
        self.content_widget.updateGeometry()
        content_hint = self.content_widget.sizeHint()

        # Determine the screen the dialog is currently on
        current_screen = QApplication.screenAt(self.frameGeometry().center())
        if current_screen is None:
            current_screen = QApplication.primaryScreen()
        screen_geometry = current_screen.availableGeometry()

        max_height = int(screen_geometry.height() * 0.85)
        new_height = min(content_hint.height(), max_height)
        new_width = max(content_hint.width(), 700)

        self.resize(new_width, new_height)

        # Center horizontally, but upwards if too tall
        screen_center = screen_geometry.center()
        x = screen_center.x() - self.width() // 2

        if new_height < screen_geometry.height():
            y = screen_center.y() - new_height // 2
        else:
            y = screen_geometry.top() + 50

        self.move(x, y)

    def _update_segmentation_widget(self) -> None:
        """Refresh the segmentation widget based on the geff root group."""

        if self.import_widget.root is not None:
            self.segmentation_widget.update_root(self.import_widget.root)
        else:
            self.segmentation_widget.setVisible(False)
        self._update_finish_button()
        self._resize_dialog()

    def _update_csv_field_map_widget(self) -> None:
        """Prefill the field map widget with the csv metadata and graph attributes."""

        self.incl_z = self.dimension_widget.incl_z
        self.df = self.import_widget.df
        if self.df is not None:
            self.prop_map_widget.extract_csv_property_fields(
                self.df, self.incl_z, self.seg
            )
            if self.seg:
                self.scale_widget.update(incl_z=self.incl_z)
        else:
            self.prop_map_widget.setVisible(False)
            self.scale_widget.setVisible(False)

        self._update_finish_button()
        self._resize_dialog()

    def _update_geff_field_map_widget(self) -> None:
        """Prefill the field map widget with the geff metadata and graph attributes."""

        if self.import_widget.root is not None:
            self.prop_map_widget.extract_geff_property_fields(
                self.import_widget.root, self.segmentation_widget.include_seg()
            )

            self.scale_widget.update(
                dict(self.import_widget.root.attrs.get("geff", {}))
            )
            self.scale_widget.setVisible(self.segmentation_widget.include_seg())
        else:
            self.prop_map_widget.setVisible(False)
            self.scale_widget.setVisible(False)

        self._update_finish_button()
        self._resize_dialog()

    def _update_finish_button(self):
        """Update the finish button status depending on whether a segmentation is required
        and whether a valid geff root is present."""

        include_seg = self.segmentation_widget.include_seg()
        has_seg = self.segmentation_widget.get_segmentation() is not None
        valid_seg = not (include_seg and not has_seg)
        if self.import_type == "geff":
            self.finish_button.setEnabled(
                self.import_widget.root is not None and valid_seg
            )
        else:
            self.finish_button.setEnabled(
                self.import_widget.df is not None and valid_seg
            )

    def _toggle_scale_widget_and_seg_id(self, checked: bool) -> None:
        """Toggle visibility of the scale widget based on the 'None' radio button state,
        and update the visibility of the 'seg_id' combobox in the prop map widget."""

        self.seg = not checked
        self.scale_widget.setVisible(self.seg)
        if self.seg and self.import_type == "csv":
            self.scale_widget.update(incl_z=self.incl_z)

        # Also remove the seg_id from the fields widget
        if len(self.prop_map_widget.mapping_widgets) > 0:
            self.prop_map_widget.mapping_widgets["seg_id"].setVisible(not checked)
            self.prop_map_widget.mapping_labels["seg_id"].setVisible(not checked)

        self._update_finish_button()
        self._resize_dialog()

    def _cancel(self) -> None:
        """Close the dialog without loading tracks."""
        self.reject()

    def _finish(self) -> None:
        """Tries to read the csv/geff file and optional segmentation image and apply the
        attribute to column mapping to construct a Tracks object"""

        if self.import_type == "geff":
            if self.import_widget.root is not None:
                store_path = Path(
                    self.import_widget.root.store.path
                )  # e.g. /.../my_store.zarr
                group_path = Path(self.import_widget.root.path)  # e.g. 'tracks'
                geff_dir = store_path / group_path

                self.name = self.import_widget.dir_name
                scale = self.scale_widget.get_scale()

                segmentation = self.segmentation_widget.get_segmentation()
                name_map = self.prop_map_widget.get_name_map()
                name_map = {
                    k: (None if v == "None" else v) for k, v in name_map.items()
                }
                extra_features = self.prop_map_widget.get_optional_props()

                try:
                    self.tracks = import_from_geff(
                        geff_dir,
                        name_map,
                        segmentation_path=segmentation,
                        node_features=extra_features,
                        scale=scale,
                    )
                except (ValueError, OSError, FileNotFoundError, AssertionError) as e:
                    QMessageBox.critical(self, "Error", f"Failed to load tracks: {e}")
                    return
                self.accept()
        else:
            if self.df is not None:
                scale = self.scale_widget.get_scale()

                segmentation = self.segmentation_widget.load_segmentation()
                name_map = self.prop_map_widget.get_name_map()
                name_map = {
                    k: (None if v == "None" else v) for k, v in name_map.items()
                }
                extra_features = self.prop_map_widget.get_optional_props()

                try:
                    self.tracks = tracks_from_df(
                        self.df, name_map, segmentation, scale, extra_features
                    )
                except (ValueError, OSError, FileNotFoundError, AssertionError) as e:
                    QMessageBox.critical(self, "Error", f"Failed to load tracks: {e}")
                    return
                self.accept()
