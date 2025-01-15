import logging

from napari import Viewer
from napari.layers import Image
from qtpy.QtWidgets import (
    QVBoxLayout,
    QWidget,
)

from .features_checkbox_widget import featuresCheckboxWidget
from .layer_dropdown import LayerDropdown

logger = logging.getLogger(__name__)


class MeasurementSetupWidget(QWidget):
    def __init__(self, viewer: Viewer):
        super().__init__()
        self.viewer: Viewer = viewer
        self.input_layer = None
        self.image_layer = None

        layout = QVBoxLayout()

        self.image_dropdown = LayerDropdown(self.viewer, (Image))
        self.image_dropdown.layer_changed.connect(self._update_image)

        layout.addWidget(self.image_dropdown)

        self.feature_widget = featuresCheckboxWidget(ndims=3)
        layout.addWidget(self.feature_widget)

        self.setLayout(layout)

    def update_input_layer(self, layer_name: str) -> None:
        self.input_layer = self.viewer.layers[layer_name]

        if self.feature_widget is not None:
            self.layout().removeWidget(self.feature_widget)
            self.feature_widget.deleteLater()

        self.feature_widget = featuresCheckboxWidget(ndims=self.input_layer.data.ndim)
        self.layout().addWidget(self.feature_widget)

    def _update_image(self, selected_layer: str) -> None:
        """Update the layer that is set to be the 'source labels' layer for copying labels from."""

        if selected_layer == "":
            self.image_layer = None
        else:
            self.image_layer = self.viewer.layers[selected_layer]
            self.image_dropdown.setCurrentText(selected_layer)
