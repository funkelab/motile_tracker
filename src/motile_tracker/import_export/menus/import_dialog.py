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
        self.prop_map_widget.props_updated.connect(self._update_finish_button)
        self.scale_widget = ScaleWidget()

        if import_type == "geff":
            self.import_widget = ImportGeffWidget()
            self.import_widget.update_buttons.connect(self._update_segmentation_widget)
            self.segmentation_widget = GeffSegmentationWidget(
                root=self.import_widget.root
            )
        else:
            self.import_widget = ImportCSVWidget()
            self.segmentation_widget = CSVSegmentationWidget()
            self.dimension_widget = DimensionWidget()
            self.dimension_widget.update_dims.connect(self._update_field_map_and_scale)

        self.import_widget.update_buttons.connect(self._update_field_map_and_scale)
        self.segmentation_widget.seg_updated.connect(self._update_field_map_and_scale)

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

    def _update_field_map_and_scale(self, checked: bool | None = None) -> None:
        """Update field map and scale widget based on segmentation selection."""

        self.seg = (
            self.segmentation_widget.include_seg() if checked is None else not checked
        )
        self.scale_widget.setVisible(self.seg)

        if self.import_type == "csv":
            self.incl_z = self.dimension_widget.incl_z
            self.df = self.import_widget.df
            if self.df is not None:
                self.prop_map_widget.extract_csv_property_fields(
                    self.df, self.seg, self.incl_z
                )
                if self.seg:
                    self.scale_widget.update(incl_z=self.incl_z)
            else:
                self.prop_map_widget.setVisible(False)
                self.scale_widget.setVisible(False)

        elif self.import_type == "geff":
            if self.import_widget.root is not None:
                geff_metadata = dict(self.import_widget.root.attrs.get("geff", {}))
                if "axes" not in geff_metadata:
                    self.infer_dims_from_segmentation()  # read dims from segmentation if
                    # no axes are available in geff metadata
                if self.seg:
                    self.scale_widget.update(
                        dict(self.import_widget.root.attrs.get("geff", {})),
                        incl_z=self.incl_z,
                    )

                self.prop_map_widget.extract_geff_property_fields(
                    self.import_widget.root, self.seg, self.incl_z
                )

            else:
                self.prop_map_widget.setVisible(False)
                self.scale_widget.setVisible(False)

        # Check whether we should keep seg_id visible in the fields widget
        if len(self.prop_map_widget.mapping_widgets) > 0:
            self.prop_map_widget.mapping_widgets["seg_id"].setVisible(self.seg)
            self.prop_map_widget.mapping_labels["seg_id"].setVisible(self.seg)

        self._update_finish_button()
        self._resize_dialog()

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

    def infer_dims_from_segmentation(self) -> None:
        """Infer whether to include z dimension based on the selected segmentation file."""

        # Check if user has selected to include segmentation
        self.seg = self.segmentation_widget.include_seg()

        if not self.seg:
            self.incl_z = (
                True  # when no segmentation is selected, we cannot infer dims,
            )
            # so we keep z in case it is needed
            return

        seg_path = self.segmentation_widget.get_segmentation()
        if seg_path is not None and seg_path.exists():
            try:
                # Load segmentation to determine ndim
                seg = magic_imread(seg_path, use_dask=True)
                ndim = seg.ndim
                self.incl_z = ndim == 4

            except (OSError, ValueError, RuntimeError, KeyError) as e:
                # If loading fails, hide the scale widget and show error
                QMessageBox.warning(
                    self,
                    "Invalid Segmentation",
                    f"Could not load segmentation file:\n{seg_path}\n\nError: {e}",
                )
                return

    def _update_finish_button(self):
        """Update the finish button status depending on whether a segmentation is required
        and whether a valid geff root or pandas dataframe is present. Duplicate region
        properties are not allowed."""

        include_seg = self.segmentation_widget.include_seg()
        has_seg = self.segmentation_widget.get_segmentation() is not None
        valid_seg = not (include_seg and not has_seg)

        if self.import_type == "geff":
            self.finish_button.setEnabled(
                self.import_widget.root is not None
                and valid_seg
                and not self.prop_map_widget.has_duplicates
            )
        else:
            self.finish_button.setEnabled(
                self.import_widget.df is not None
                and valid_seg
                and not self.prop_map_widget.has_duplicates
            )

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
        geff_metadata = dict(self.import_widget.root.attrs.get("geff", {}))
        geff_metadata["axes"] = [ax.model_dump(exclude_none=True) for ax in axes]
        self.import_widget.root.attrs["geff"] = geff_metadata

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
                scale = self.scale_widget.get_scale() if self.seg else None

                segmentation = self.segmentation_widget.get_segmentation()
                name_map = self.prop_map_widget.get_name_map()
                name_map = {
                    k: (None if v == "None" else v) for k, v in name_map.items()
                }
                extra_features = self.prop_map_widget.get_optional_props()

                # Generate axes metadata if missing (required for funtracks validation)
                geff_metadata = dict(self.import_widget.root.attrs.get("geff", {}))
                if "axes" not in geff_metadata:
                    if segmentation is not None:
                        self._generate_axes_metadata(name_map, scale, segmentation)
                    else:
                        if name_map["z"] is None:
                            del name_map[
                                "z"
                            ]  # remove z from name_map if no segmentation is provided
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
