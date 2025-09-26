import difflib

import zarr
from funtracks.data_model.graph_attributes import NodeAttr
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from motile_tracker.import_export.menus.import_from_geff.geff_import_utils import (
    clear_layout,
)


class StandardFieldMapWidget(QWidget):
    """QWidget to map motile attributes to geff node properties."""

    def __init__(
        self,
    ):
        super().__init__()

        self.node_attrs = []
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
            "geff node properties."
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
        self.optional_mapping_layout = QVBoxLayout()
        optional_box.setLayout(self.optional_mapping_layout)
        box_layout.addWidget(optional_box, alignment=Qt.AlignTop)

        self.setVisible(False)

    def update_mapping(self, root: zarr.Group | None = None, seg: bool = False) -> None:
        """Update the mapping widget with the provided root group and segmentation
        flag."""

        if root is not None:
            self.setVisible(True)
            self.node_attrs = list(root["nodes"]["props"].group_keys())
            self.metadata = dict(root.attrs.get("geff", {}))

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
                self.standard_fields.insert(
                    1, "z"
                )  # also provide the option to choose z if
                # no axes information is available

            # Map graph spatiotemporal data and optionally the track and lineage
            # attributes
            self.mapping_labels = {}
            self.mapping_widgets = {}
            clear_layout(self.mapping_layout)  # clear layout first
            initial_mapping = self._get_initial_mapping()
            for attribute, geff_attr in initial_mapping.items():
                if attribute in self.standard_fields:
                    combo = QComboBox()
                    combo.addItems(self.node_attrs + ["None"])  # also add None
                    combo.setCurrentText(geff_attr)
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
            clear_layout(self.optional_mapping_layout)
            self.optional_features = {}
            for attribute in self.props_left:
                row_layout = QHBoxLayout()
                attr_checkbox = QCheckBox(attribute)
                recompute_checkbox = QCheckBox("Recompute")
                activate_checkbox = bool(attribute == NodeAttr.AREA.value and seg)
                recompute_checkbox.setEnabled(activate_checkbox)
                row_layout.addWidget(attr_checkbox)
                row_layout.addWidget(recompute_checkbox)
                self.optional_mapping_layout.addLayout(row_layout)
                self.optional_features[attribute] = {
                    "attr_checkbox": attr_checkbox,
                    "recompute": recompute_checkbox,
                }
        else:
            self.setVisible(False)

    def _get_tooltip(self, attribute: str) -> str:
        """Return the tooltip for the given attribute"""

        tooltips = {
            NodeAttr.TIME.value: "The time point of the node. Must be an integer",
            "z": "The world z-coordinate of the node.",
            "y": "The world y-coordinate of the node.",
            "x": "The world x-coordinate of the node.",
            NodeAttr.SEG_ID.value: "The integer label value in the segmentation file.",
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

    def _get_initial_mapping(
        self,
    ) -> dict[str:str]:
        """Make an initial guess for mapping of geff columns to fields"""

        mapping = {}
        self.props_left: list = self.node_attrs.copy()

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
                closest = difflib.get_close_matches(
                    attribute, self.props_left, n=1, cutoff=0.6
                )
                if closest:
                    mapping[attribute] = closest[0]
                    self.props_left.remove(closest[0])
                else:
                    mapping[attribute] = "None"
            else:
                mapping[attribute] = "None"

        return mapping

    def get_name_map(self) -> dict[str:str]:
        """Return a mapping from feature name to geff field name"""

        return {
            attribute: combo.currentText()
            for attribute, combo in self.mapping_widgets.items()
        }

    def get_optional_props(self) -> dict[str:bool]:
        """Get all the extra features that are requested and whether they should be
        recomputed"""

        optional_features = {}
        for attr, checkbox_dict in self.optional_features.items():
            if checkbox_dict["attr_checkbox"].isChecked():
                optional_features[attr] = checkbox_dict["recompute"].isChecked()

        return optional_features
