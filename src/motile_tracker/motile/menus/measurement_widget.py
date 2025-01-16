import logging

from napari import Viewer
from napari.layers import Image, Layer
from qtpy.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QWidget,
)

from .features_checkbox_widget import FeatureWidget
from .layer_dropdown import LayerDropdown
from .scale_widget import ScaleWidget

logger = logging.getLogger(__name__)


class MeasurementSetupWidget(QWidget):
    def __init__(self, viewer: Viewer, input_layer):
        super().__init__()
        self.viewer: Viewer = viewer
        self.input_layer = input_layer

        layout = QVBoxLayout()

        # create a dropdown menu to select an Image layer for optional intensity measurements
        self.intensity_box = QGroupBox("Intensity image")
        self.image_dropdown = LayerDropdown(self.viewer, (Image))
        self.image_dropdown.layer_changed.connect(self._update_intensity_image)
        if self.image_dropdown.get_current_layer() in self.viewer.layers:
            self.intensity_image = self.viewer.layers[
                self.image_dropdown.get_current_layer()
            ]
        else:
            self.intensity_image = None
        self.intensity_box_layout = QVBoxLayout()
        self.intensity_box_layout.addWidget(self.image_dropdown)
        self.intensity_box.setLayout(self.intensity_box_layout)
        layout.addWidget(self.intensity_box)

        # add a widget for choosing the different features to measure
        self.feature_widget = FeatureWidget(self.viewer, ndims=3)
        layout.addWidget(self.feature_widget)

        # add a widget for specifying the scaling information
        self.scale_widget = ScaleWidget(scaling=(1, 1, 1))
        layout.addWidget(self.scale_widget)

        self.setLayout(layout)

    def update_input_layer(self, layer: Layer) -> None:
        self.input_layer = layer

        if self.scale_widget is not None:
            self.layout().removeWidget(self.scale_widget)
            self.scale_widget.deleteLater()
        if self.feature_widget is not None:
            self.layout().removeWidget(self.feature_widget)
            self.feature_widget.deleteLater()

        self.feature_widget = FeatureWidget(
            self.viewer,
            ndims=self.input_layer.data.ndim if self.input_layer is not None else 3,
        )
        self.scale_widget = ScaleWidget(
            scaling=self.input_layer.scale
            if self.input_layer is not None
            else (1, 1, 1)
        )

        self.layout().addWidget(self.feature_widget)
        self.layout().addWidget(self.scale_widget)

    def _update_intensity_image(self, selected_layer: str) -> None:
        """Update the intensity image layer"""

        if selected_layer == "":
            self.intensity_image = None
            self.feature_widget.update_checkbox_availability(False)
        else:
            self.intensity_image = self.viewer.layers[selected_layer]
            self.image_dropdown.setCurrentText(selected_layer)
            self.feature_widget.update_checkbox_availability(True)

    def get_scaling(self):
        """Return the scaling information from the scaling widget"""

        return self.scale_widget.get_scaling()

    def get_features(self):
        """Return the features to be measured from the feature_widget"""

        return self.feature_widget.get_selected_features()

    def get_intensity_image(self):
        """Return the selected intensity image as np.ndarray, if available"""

        return self.intensity_image.data if self.intensity_image is not None else None
