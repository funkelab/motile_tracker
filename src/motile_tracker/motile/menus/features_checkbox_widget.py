from napari import Viewer
from qtpy.QtWidgets import QCheckBox, QGroupBox, QVBoxLayout, QWidget

from motile_tracker.motile.backend.features import feature_properties


class FeatureWidget(QWidget):
    def __init__(self, viewer: Viewer, ndims: int):
        super().__init__()

        self.viewer = viewer
        self.ndims = ndims
        self.enable_intensity = False

        main_layout = QVBoxLayout()

        # create a dictionary to store the checkbox state for each property
        self.properties = [f for f in feature_properties if not f.required]

        self.checkbox_state = {
            prop.node_attr: prop.selected for prop in self.properties
        }
        self.group_box = QGroupBox("Features to measure")
        self.checkbox_layout = QVBoxLayout()
        self.checkboxes = []

        # create checkbox for each feature
        for prop in self.properties:
            if prop.dims == self.ndims:
                checkbox = QCheckBox(prop.display_name)
                checkbox.setEnabled(prop.enabled)
                checkbox.setStyleSheet("QCheckBox:disabled { color: grey }")
                checkbox.setChecked(self.checkbox_state[prop.node_attr])
                checkbox.stateChanged.connect(
                    lambda state, prop=prop: self.checkbox_state.update(
                        {prop.node_attr: state == 2}
                    )
                )
                self.checkboxes.append(
                    {"prop_name": prop.node_attr, "checkbox": checkbox}
                )
                self.checkbox_layout.addWidget(checkbox)

        self.group_box.setLayout(self.checkbox_layout)
        main_layout.addWidget(self.group_box)
        self.setLayout(main_layout)

    def get_selected_features(self) -> list[str]:
        """Return a list of the features that have been selected"""

        selected_features = [
            key for key in self.checkbox_state if self.checkbox_state[key]
        ]
        if self.enable_intensity is None and "intensity_mean" in selected_features:
            selected_features.remove("intensity_mean")
        return selected_features

    def set_selected_features(self, features: list[str]) -> None:
        """Set the selected features based on the input list"""

        for checkbox in self.checkboxes:
            checkbox["checkbox"].setChecked(checkbox["prop_name"] in features)

    def update_checkbox_availability(self, enable: bool = False):
        self.enable_intensity = enable
        for checkbox in self.checkboxes:
            if checkbox["prop_name"] == "intensity_mean":
                if self.enable_intensity:
                    checkbox["checkbox"].setEnabled(True)
                else:
                    checkbox["checkbox"].setEnabled(False)
