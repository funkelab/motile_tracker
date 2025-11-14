import difflib
import inspect

import pandas as pd
import zarr
from funtracks.data_model.graph_attributes import NodeAttr
from funtracks.features import _regionprops_features
from funtracks.import_export.feature_import import ImportedNodeFeature
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from motile_tracker.import_export.menus.geff_import_utils import (
    clear_layout,
)


class StandardFieldMapWidget(QWidget):
    """QWidget to map motile attributes to geff node properties."""

    def __init__(self) -> None:
        super().__init__()

        self.node_attrs: list[str] = []
        self.metadata = None
        self.mapping_labels = {}
        self.mapping_widgets = {}

        # Group box for property field mapping
        box = QGroupBox("Property mapping")
        box_layout = QHBoxLayout()
        box.setLayout(box_layout)
        main_layout = QVBoxLayout()

        main_layout.addWidget(box)
        self.setLayout(main_layout)

        # Graph data mapping Layout
        mapping_box = QGroupBox("Graph data")
        mapping_box.setToolTip(
            "<html><body><p style='white-space:pre-wrap; width: 300px;'>"
            "Map spatiotemporal attributes and optional track and lineage attributes to "
            "node properties."
        )
        self.mapping_layout = QFormLayout()
        mapping_box.setLayout(self.mapping_layout)
        box_layout.addWidget(mapping_box, alignment=Qt.AlignTop)

        # Optional features
        optional_box = QGroupBox("Optional features")
        optional_box.setToolTip(
            "<html><body><p style='white-space:pre-wrap; width: 300px;'>"
            "Optionally select additional features to be imported. If the 'Recompute' "
            "checkbox is checked, the feature will be recomputed, otherwise it will "
            "directly be imported from the data."
        )

        self.optional_mapping_layout = QGridLayout()
        optional_box.setLayout(self.optional_mapping_layout)
        box_layout.addWidget(optional_box, alignment=Qt.AlignTop)
        self.optional_features = {}

        self.setVisible(False)

    def _get_attr_dtype_kind(self, root: zarr.Group, attr: str) -> str:
        """
        Determine the data type for a property stored under
        root['nodes']['props'][attr].

        Returns:
            One of: 'bool', 'int', 'float', 'str', or 'object'
        """
        node = root["nodes"]["props"][attr]

        # Try to find a child array and inspect its dtype
        for name in getattr(node, "keys", list)():
            child = node[name]
            if hasattr(child, "dtype"):
                kind = child.dtype.kind
                # Convert numpy kind to readable type
                if kind == "b":
                    return "bool"
                elif kind in ("i", "u"):
                    return "int"
                elif kind == "f":
                    return "float"
                elif kind in ("S", "U"):
                    return "str"
                else:
                    return "object"

    def extract_csv_property_fields(
        self, df: pd.DataFrame, incl_z: bool = False, seg: bool = False
    ) -> None:
        """Update the mapping widget with the provided root group and segmentation flag."""

        self.incl_z = incl_z
        self.df = df
        if self.df is not None:
            self.setVisible(True)
            self.node_attrs = list(self.df.columns)

            # Retrieve attribute types
            self.attr_types = {
                attr: str(self.df[attr].dtype) for attr in self.node_attrs
            }
            self.props_left = []
            self.standard_fields = [
                "id",
                "parent_id",
                NodeAttr.TIME.value,
                "y",
                "x",
                "tracklet_id",
                "lineage_id",
                "seg_id",
            ]

            if self.incl_z:
                self.standard_fields.insert(3, "z")

            self.update_mapping(seg)
        else:
            self.setVisible(False)

    def extract_geff_property_fields(
        self, root: zarr.Group | None = None, seg: bool = False
    ) -> None:
        """Update the mapping widget with the provided root group and segmentation flag."""

        if root is not None:
            self.setVisible(True)
            self.node_attrs = list(root["nodes"]["props"].group_keys())
            self.metadata = dict(root.attrs.get("geff", {}))

            # Retrieve attribute types from the zarr group
            self.attr_types = {
                attr: self._get_attr_dtype_kind(root, attr) for attr in self.node_attrs
            }
            self.props_left = []
            self.standard_fields = [
                NodeAttr.TIME.value,
                "y",
                "x",
                "seg_id",
                NodeAttr.TRACK_ID.value,
                "lineage_id",
            ]

            axes = self.metadata.get("axes", None)
            if axes is not None:
                axes_types = [
                    ax.get("type") for ax in axes if ax.get("type") == "space"
                ]
                if len(axes_types) == 3:
                    self.standard_fields.insert(1, "z")
            else:
                # allow z option if axes info missing
                self.standard_fields.insert(1, "z")

            self.update_mapping(seg)
        else:
            self.setVisible(False)

    def update_mapping(self, seg: bool = False) -> None:
        """Map graph spatiotemporal data and optionally the track and lineage attributes
        Arg:
            seg (bool = False): whether a segmentation is associated with this data
        """

        self.mapping_labels = {}
        self.mapping_widgets = {}
        clear_layout(self.mapping_layout)  # clear layout first
        initial_mapping = self._get_initial_mapping()
        # for attribute, geff_attr in initial_mapping.items():
        for attribute in self.standard_fields:
            combo = QComboBox()
            combo.addItems(self.node_attrs + ["None"])  # also add None
            combo.setCurrentText(initial_mapping.get(attribute, "None"))
            combo.currentIndexChanged.connect(self._update_props_left)
            label = QLabel(attribute)
            label.setToolTip(self._get_tooltip(attribute))
            self.mapping_widgets[attribute] = combo
            self.mapping_labels[attribute] = label
            self.mapping_layout.addRow(label, combo)
            if attribute == "seg_id" and not seg:
                combo.setVisible(False)
                label.setVisible(False)

        # Optional extra features
        self.feature_options = []
        for name, func in inspect.getmembers(_regionprops_features, inspect.isfunction):
            if func.__module__ == "funtracks.features._regionprops_features":
                sig = inspect.signature(func)
                if "ndim" in sig.parameters:
                    ndim = 4 if "z" in self.standard_fields else 3
                    feature = func(ndim)  # call with ndim
                else:
                    feature = func()  # Call without ndim
                display_name = feature.get("display_name", name)
                self.feature_options.append(display_name)

        # Clear existing optional layout and widgets
        clear_layout(self.optional_mapping_layout)
        self.optional_features = {}

        # Add header
        header_prop = QLabel("Name")
        header_assign = QLabel("Assign as Feature")
        header_recompute = QLabel("Recompute")
        header_prop.setAlignment(Qt.AlignLeft)
        header_assign.setAlignment(Qt.AlignLeft)
        header_recompute.setAlignment(Qt.AlignLeft)
        self.optional_mapping_layout.addWidget(header_prop, 0, 0)
        self.optional_mapping_layout.addWidget(header_assign, 0, 1)
        self.optional_mapping_layout.addWidget(header_recompute, 0, 2)
        self._update_props_left()
        self.setMinimumHeight(350)

    def _add_optional_prop(self, attribute) -> None:
        # Add a row per remaining property
        row_idx = 1
        for attribute in self.props_left:
            # Prop checkbox
            attr_checkbox = QCheckBox(attribute)
            # Feature option combobox
            feature_option = QComboBox()
            # Numerical types => list regionprops features
            if self.attr_types.get(attribute) in {
                "int",
                "int32",
                "int64",
                "float",
                "float32",
                "float64",
            }:
                feature_option.addItems(self.feature_options)
            elif self.attr_types.get(attribute) in {"bool", "object", "0"}:
                # Boolean or unknown/object types => grouping option
                feature_option.addItem("Group")

            # Always have "Custom" as last option
            feature_option.addItem("Custom")

            # Recompute checkbox - initially disabled
            recompute_checkbox = QCheckBox()
            recompute_checkbox.setEnabled(False)

            # When the combobox selection changes, update recompute checkbox enable
            def make_on_change(checkbox, combo):
                def on_change(index):
                    selected_feature = combo.currentText()
                    # Enable recompute only if the selected feature corresponds to a regionprops feature
                    if selected_feature in self.feature_options:
                        checkbox.setEnabled(True)
                    else:
                        checkbox.setEnabled(False)
                        checkbox.setChecked(False)

                return on_change

            feature_option.currentIndexChanged.connect(
                make_on_change(recompute_checkbox, feature_option)
            )

            # initialize recompute enabled state based on current selection
            make_on_change(recompute_checkbox, feature_option)(
                feature_option.currentIndex()
            )

            # Place widgets into the grid
            self.optional_mapping_layout.addWidget(attr_checkbox, row_idx, 0)
            self.optional_mapping_layout.addWidget(feature_option, row_idx, 1)
            self.optional_mapping_layout.addWidget(recompute_checkbox, row_idx, 2)

            # Save references for later retrieval
            self.optional_features[attribute] = {
                "attr_checkbox": attr_checkbox,
                "feature_option": feature_option,
                "recompute": recompute_checkbox,
            }

            row_idx += 1

    def _remove_optional_prop(self, attribute: str) -> None:
        """Remove an attribute from the dictionary of optional features and remove the
        associated widgets from the 'extra features' layout."""

        self.optional_features[attribute]["attr_checkbox"].setParent(None)
        self.optional_features[attribute]["attr_checkbox"].deleteLater()
        self.optional_features[attribute]["feature_option"].setParent(None)
        self.optional_features[attribute]["feature_option"].deleteLater()
        self.optional_features[attribute]["recompute"].setParent(None)
        self.optional_features[attribute]["recompute"].deleteLater()

        del self.optional_features[attribute]
        self.row_idx = len(self.optional_features)

    def get_optional_props(self) -> list[dict]:
        """Get all the extra features that are requested and their settings. Only entries
        whose checkbox in the prop_name column is checked are returned.

        Returns a list of dicts like:
        {
            "prop_name": "area",
            "feature": <Display name for regionprops feature> or 'Group' or 'Custom',
            "recompute": True/False
            "dtype": str/int/float/bool
        }
        """
        optional_features = []
        for attr, widgets in self.optional_features.items():
            if widgets["attr_checkbox"].isChecked():
                selected = widgets["feature_option"].currentText()
                optional_features.append(
                    ImportedNodeFeature(
                        prop_name=attr,
                        feature=selected,
                        recompute=bool(widgets["recompute"].isChecked()),
                        dtype=self.attr_types.get(attr, "str"),
                    )
                )

        return optional_features

    def _get_tooltip(self, attribute: str) -> str:
        """Return the tooltip for the given attribute"""

        tooltips = {
            NodeAttr.TIME.value: "The time point of the node. Must be an integer",
            "z": "The world z-coordinate of the node.",
            "y": "The world y-coordinate of the node.",
            "x": "The world x-coordinate of the node.",
            "seg_id": "The integer label value in the segmentation file.",
            NodeAttr.TRACK_ID.value: "<html><body><p style='white-space:pre-wrap; width: "
            "300px;'>"
            "(Optional) The tracklet id that this node belongs "
            "to, defined as a single chain with at most one incoming and one outgoing "
            "edge.",
            "lineage_id": "<html><body><p style='white-space:pre-wrap; width: "
            "(Optional) Lineage id that this node belongs to, defined as "
            "weakly connected component in the graph.",
        }

        return tooltips.get(attribute, "")

    def _update_props_left(self) -> None:
        """Update the list of columns that have not been mapped yet"""
        self.props_left = [
            attr for attr in self.node_attrs if attr not in self.get_name_map().values()
        ]

        optional_features = list(self.optional_features.keys())
        for attribute in optional_features:
            if attribute not in self.props_left:
                self._remove_optional_prop(attribute)

        for attribute in self.props_left:
            if attribute not in self.optional_features:
                self._add_optional_prop(attribute)

    def _get_initial_mapping(self) -> dict[str, str]:
        """Make an initial guess for mapping of geff columns to fields"""

        mapping: dict[str, str] = {}
        self.props_left = self.node_attrs.copy()

        # check if the axes information is in the metadata, if so, use it for initial
        # mapping
        if hasattr(self.metadata, "axes"):
            axes_names = [ax.name for ax in self.metadata.axes]
            for attribute in self.standard_fields:
                if attribute in axes_names:
                    mapping[attribute] = attribute
                    self.props_left.remove(attribute)

        # if fields could not be assigned via the metadata, try find exact matches for
        # standard fields
        for attribute in self.standard_fields:
            if attribute in mapping:
                continue
            if attribute in self.props_left:
                mapping[attribute] = attribute
                self.props_left.remove(attribute)

        # assign closest remaining column as best guess for remaining standard fields
        for attribute in self.standard_fields:
            if attribute in mapping:
                continue
            if len(self.props_left) > 0:
                lower_map = {p.lower(): p for p in self.props_left}
                closest = difflib.get_close_matches(
                    attribute.lower(), lower_map.keys(), n=1, cutoff=0.5
                )
                if closest:
                    # map back to the original case
                    best_match = lower_map[closest[0]]
                    mapping[attribute] = best_match
                    self.props_left.remove(best_match)
                else:
                    mapping[attribute] = "None"
            else:
                mapping[attribute] = "None"

        return mapping

    def get_name_map(self) -> dict[str, str]:
        """Return a mapping from feature name to geff field name"""

        return {
            attribute: combo.currentText()
            for attribute, combo in self.mapping_widgets.items()
        }
