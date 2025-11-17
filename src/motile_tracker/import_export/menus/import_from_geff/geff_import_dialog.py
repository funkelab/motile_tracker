from pathlib import Path

from funtracks.import_export.import_from_geff import import_from_geff
from funtracks.import_export.magic_imread import magic_imread
from geff_spec.utils import axes_from_lists
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
        self.segmentation_widget.button_group.buttonClicked.connect(
            self._update_scale_widget
        )
        self.segmentation_widget.segmentation_widget.seg_path_updated.connect(
            self._update_scale_widget
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
            self._update_scale_widget()
        else:
            self.prop_map_widget.setVisible(False)
            self.scale_widget.setVisible(False)

        self._update_finish_button()
        self._resize_dialog()

    def _update_scale_widget(self) -> None:
        """Update the scale widget based on segmentation selection.

        Only shows the scale widget when:
        1. A segmentation option is selected (not "None")
        2. A valid segmentation path exists
        3. The segmentation can be loaded successfully

        Loads the segmentation to determine its dimensionality (3D or 4D).
        """
        # Check if user has selected to include segmentation
        include_seg = self.segmentation_widget.include_seg()

        if not include_seg:
            # "None" is selected, hide scale widget
            self.scale_widget.setVisible(False)
            self._resize_dialog()
            return

        seg_path = self.segmentation_widget.get_segmentation()

        if seg_path is not None and seg_path.exists():
            try:
                # Load segmentation to determine ndim
                seg = magic_imread(seg_path, use_dask=True)
                ndim = seg.ndim

                # Prefill scale widget with metadata and actual ndim
                metadata = (
                    dict(self.geff_widget.root.attrs.get("geff", {}))
                    if self.geff_widget.root
                    else {}
                )
                self.scale_widget._prefill_from_metadata(metadata, ndim=ndim)
                self.scale_widget.setVisible(True)

                # Update z field visibility based on segmentation dimensionality
                self.prop_map_widget.update_z_visibility(ndim)
            except (OSError, ValueError, RuntimeError, KeyError) as e:
                # If loading fails, hide the scale widget and show error
                QMessageBox.warning(
                    self,
                    "Invalid Segmentation",
                    f"Could not load segmentation file:\n{seg_path}\n\nError: {e}",
                )
                self.scale_widget.setVisible(False)
        else:
            # Path doesn't exist yet (user hasn't selected a file)
            self.scale_widget.setVisible(False)

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

        # Update scale widget visibility based on whether segmentation is included
        # and whether a valid path exists
        self._update_scale_widget()

        # Also remove the seg_id from the fields widget
        if len(self.prop_map_widget.mapping_widgets) > 0:
            self.prop_map_widget.mapping_widgets["seg_id"].setVisible(not checked)
            self.prop_map_widget.mapping_labels["seg_id"].setVisible(not checked)
            self.prop_map_widget.optional_features["area"]["recompute"].setEnabled(
                not checked
            )

            # If "None" is selected (no segmentation), show z field since we don't know ndim
            if checked:
                self.prop_map_widget.update_z_visibility(None)

        self._update_finish_button()
        self._resize_dialog()

    def _cancel(self) -> None:
        """Close the dialog without loading tracks."""
        self.reject()

    def _generate_axes_metadata(
        self,
        name_map: dict[str, str | None],
        scale: list[float] | None,
        segmentation_path: Path,
    ) -> None:
        """Generate axes metadata when missing from geff file.

        Uses the user-provided name_map and scale information to construct
        axes metadata that matches the segmentation dimensionality.

        Args:
            name_map: Mapping from standard fields (t, z, y, x) to node property names
            scale: Scale values from scale widget [t, (z), y, x]
            segmentation_path: Path to segmentation file to determine ndim
        """
        # Load segmentation to get ndim
        seg = magic_imread(segmentation_path, use_dask=True)
        ndim = seg.ndim

        # Build axis names and types based on dimensionality
        # Use "time" to match NodeAttr.TIME.value used in standard_fields
        if ndim == 3:  # 2D+time
            axis_keys = ["time", "y", "x"]
            axis_types = ["time", "space", "space"]
        else:  # 3D+time (ndim == 4)
            axis_keys = ["time", "z", "y", "x"]
            axis_types = ["time", "space", "space", "space"]

        # Get actual node property names from name_map
        axis_names = []
        for key in axis_keys:
            prop_name = name_map.get(key)
            if prop_name is None:
                # Fall back to standard name if not in name_map
                prop_name = key
            axis_names.append(prop_name)

        # Use provided scale or default to 1.0
        axis_scales = [1.0] * ndim if scale is None else scale

        # Generate axes using geff_spec utility
        axes = axes_from_lists(
            axis_names=axis_names,
            axis_types=axis_types,
            axis_scales=axis_scales,
        )

        # Inject into geff root attrs
        geff_metadata = dict(self.geff_widget.root.attrs.get("geff", {}))
        geff_metadata["axes"] = [ax.model_dump(exclude_none=True) for ax in axes]
        self.geff_widget.root.attrs["geff"] = geff_metadata

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

            # Generate axes metadata if missing (required for funtracks validation)
            geff_metadata = dict(self.geff_widget.root.attrs.get("geff", {}))
            if "axes" not in geff_metadata and segmentation is not None:
                self._generate_axes_metadata(name_map, scale, segmentation)

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
