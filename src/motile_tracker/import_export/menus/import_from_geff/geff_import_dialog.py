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

from motile_tracker.import_export.menus.import_from_geff.geff_import_widget import (
    ImportGeffWidget,
)
from motile_tracker.import_export.menus.import_from_geff.geff_prop_map_widget import (
    StandardFieldMapWidget,
)
from motile_tracker.import_export.menus.import_from_geff.geff_scale_widget import (
    ScaleWidget,
)
from motile_tracker.import_export.menus.import_from_geff.geff_segmentation_widgets import (
    SegmentationWidget,
)


class ImportGeffDialog(QDialog):
    """Dialgo for importing external tracks from a geff file"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Import external tracks from geff")
        self.name = "Tracks from Geff"

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
        self.geff_widget = ImportGeffWidget()
        self.geff_widget.update_buttons.connect(self._update_segmentation_widget)
        self.segmentation_widget = SegmentationWidget(root=self.geff_widget.root)
        self.segmentation_widget.none_radio.toggled.connect(
            self._toggle_scale_widget_and_seg_id
        )
        self.segmentation_widget.segmentation_widget.seg_path_updated.connect(
            self._update_finish_button
        )
        self.prop_map_widget = StandardFieldMapWidget()
        self.geff_widget.update_buttons.connect(self._update_field_map_widget)
        self.scale_widget = ScaleWidget()

        self.content_widget = QWidget()
        main_layout = QVBoxLayout(self.content_widget)
        main_layout.addWidget(self.geff_widget)
        main_layout.addWidget(self.segmentation_widget)
        main_layout.addWidget(self.prop_map_widget)
        main_layout.addWidget(self.scale_widget)
        main_layout.addLayout(self.button_layout)
        self.content_widget.setLayout(main_layout)
        self.content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.content_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setMinimumWidth(500)
        self.scroll_area.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.MinimumExpanding
        )
        self.content_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        dialog_layout = QVBoxLayout()
        dialog_layout.addWidget(self.scroll_area)
        self.setLayout(dialog_layout)
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), QSizePolicy.Minimum)

    def _resize_dialog(self):
        """Dynamic widget resizing depending on the visible contents"""

        self.content_widget.adjustSize()
        self.content_widget.updateGeometry()

        content_hint = self.content_widget.sizeHint()
        screen_geometry = QApplication.primaryScreen().availableGeometry()

        max_height = int(screen_geometry.height() * 0.85)
        new_height = min(content_hint.height(), max_height)
        new_width = max(content_hint.width(), 500)

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

        if self.geff_widget.root is not None:
            self.segmentation_widget.update_root(self.geff_widget.root)
        else:
            self.segmentation_widget.setVisible(False)
        self._update_finish_button()
        self._resize_dialog()

    def _update_field_map_widget(self) -> None:
        """Prefill the field map widget with the geff metadata and graph attributes."""

        if self.geff_widget.root is not None:
            self.prop_map_widget.update_mapping(
                self.geff_widget.root, self.segmentation_widget.include_seg()
            )

            self.scale_widget._prefill_from_metadata(
                dict(self.geff_widget.root.attrs.get("geff", {}))
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
        self.finish_button.setEnabled(self.geff_widget.root is not None and valid_seg)

    def _toggle_scale_widget_and_seg_id(self, checked: bool) -> None:
        """Toggle visibility of the scale widget based on the 'None' radio button state,
        and update the visibility of the 'seg_id' combobox in the prop map widget."""

        self.scale_widget.setVisible(not checked)

        # Also remove the seg_id from the fields widget
        if len(self.prop_map_widget.mapping_widgets) > 0:
            self.prop_map_widget.mapping_widgets["seg_id"].setVisible(not checked)
            self.prop_map_widget.mapping_labels["seg_id"].setVisible(not checked)
            self.prop_map_widget.optional_features["area"]["recompute"].setEnabled(
                not checked
            )

        self._update_finish_button()
        self._resize_dialog()

    def _cancel(self) -> None:
        """Close the dialog without loading tracks."""
        self.reject()

    def _finish(self) -> None:
        """Tries to read the geff file and optional segmentation image and apply the
        attribute to column mapping to construct a Tracks object"""

        if self.geff_widget.root is not None:
            store_path = Path(
                self.geff_widget.root.store.path
            )  # e.g. /.../my_store.zarr
            group_path = Path(self.geff_widget.root.path)  # e.g. 'tracks'
            geff_dir = store_path / group_path

            self.name = self.geff_widget.dir_name
            scale = self.scale_widget.get_scale()

            segmentation = self.segmentation_widget.get_segmentation()
            name_map = self.prop_map_widget.get_name_map()
            name_map = {k: (None if v == "None" else v) for k, v in name_map.items()}
            extra_features = self.prop_map_widget.get_optional_props()

            try:
                self.tracks = import_from_geff(
                    geff_dir,
                    name_map,
                    segmentation_path=segmentation,
                    extra_features=extra_features,
                    scale=scale,
                )
            except (ValueError, OSError, FileNotFoundError, AssertionError) as e:
                QMessageBox.critical(self, "Error", f"Failed to load tracks: {e}")
                return
            self.accept()
