from napari import Viewer
from qtpy.QtWidgets import QCheckBox, QGroupBox, QVBoxLayout, QWidget


class FeatureWidget(QWidget):
    def __init__(self, viewer: Viewer, ndims: int):
        super().__init__()

        self.viewer = viewer
        self.ndims = ndims
        self.enable_intensity = False

        main_layout = QVBoxLayout()

        # create a dictionary to store the checkbox state for each property
        self.properties = [
            {
                "prop_name": "pixel_count",
                "display_name": "Pixel count",
                "selected": False,
                "enabled": True,
                "dims": 3,
            },
            {
                "prop_name": "area",
                "display_name": "Area",
                "selected": False,
                "enabled": True,
                "dims": 3,
            },
            {
                "prop_name": "perimeter",
                "display_name": "Perimeter",
                "selected": False,
                "enabled": True,
                "dims": 3,
            },
            {
                "prop_name": "circularity",
                "display_name": "Circularity",
                "selected": False,
                "enabled": True,
                "dims": 3,
            },
            {
                "prop_name": "axes",
                "display_name": "Axes radii",
                "selected": False,
                "enabled": True,
                "dims": 3,
            },
            {
                "prop_name": "intensity_mean",
                "display_name": "Mean intensity",
                "selected": False,
                "enabled": self.enable_intensity,
                "dims": 3,
            },
            {
                "prop_name": "voxel_count",
                "display_name": "Voxel count",
                "selected": False,
                "enabled": True,
                "dims": 4,
            },
            {
                "prop_name": "volume",
                "display_name": "Volume",
                "selected": False,
                "enabled": True,
                "dims": 4,
            },
            {
                "prop_name": "surface_area",
                "display_name": "Surface area",
                "selected": False,
                "enabled": True,
                "dims": 4,
            },
            {
                "prop_name": "sphericity",
                "display_name": "Sphericity",
                "selected": False,
                "enabled": True,
                "dims": 4,
            },
            {
                "prop_name": "axes",
                "display_name": "Axes radii",
                "selected": False,
                "enabled": True,
                "dims": 4,
            },
            {
                "prop_name": "intensity_mean",
                "display_name": "Mean intensity",
                "selected": False,
                "enabled": self.enable_intensity,
                "dims": 4,
            },
        ]

        self.checkbox_state = {
            prop["prop_name"]: prop["selected"] for prop in self.properties
        }
        self.group_box = QGroupBox("Features to measure")
        self.checkbox_layout = QVBoxLayout()
        self.checkboxes = []

        # create checkbox for each feature
        for prop in self.properties:
            if prop["dims"] == self.ndims:
                checkbox = QCheckBox(prop["display_name"])
                checkbox.setEnabled(prop["enabled"])
                checkbox.setStyleSheet("QCheckBox:disabled { color: grey }")
                checkbox.setChecked(self.checkbox_state[prop["prop_name"]])
                checkbox.stateChanged.connect(
                    lambda state, prop=prop: self.checkbox_state.update(
                        {prop["prop_name"]: state == 2}
                    )
                )
                self.checkboxes.append(
                    {"prop_name": prop["prop_name"], "checkbox": checkbox}
                )
                self.checkbox_layout.addWidget(checkbox)

        self.group_box.setLayout(self.checkbox_layout)
        main_layout.addWidget(self.group_box)
        self.setLayout(main_layout)

    def get_selected_features(self):
        """Return a list of the features that have been selected"""

        selected_features = [
            key for key in self.checkbox_state if self.checkbox_state[key]
        ]
        if self.enable_intensity is None and "intensity_mean" in selected_features:
            selected_features.remove("intensity_mean")
        return selected_features

    def update_checkbox_availability(self, enable: bool = False):
        self.enable_intensity = enable
        for checkbox in self.checkboxes:
            if checkbox["prop_name"] == "intensity_mean":
                if self.enable_intensity:
                    checkbox["checkbox"].setEnabled(True)
                else:
                    checkbox["checkbox"].setEnabled(False)
