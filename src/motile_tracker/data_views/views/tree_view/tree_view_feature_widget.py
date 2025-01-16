from psygnal import Signal
from qtpy.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)


class TreeViewFeatureWidget(QWidget):
    """Widget to switch between viewing all nodes versus nodes of one or more lineages in the tree widget"""

    change_plot_type = Signal(str)

    def __init__(self, features):
        super().__init__()

        self.plot_type = "tree"
        self.current_feature = "area"

        display_box = QGroupBox("Feature [W]")
        display_layout = QHBoxLayout()
        button_group = QButtonGroup()
        self.show_tree_radio = QRadioButton("Lineage Tree")
        self.show_tree_radio.setChecked(True)
        self.show_tree_radio.clicked.connect(lambda: self._set_plot_type("tree"))
        self.show_area_radio = QRadioButton("Object feature")
        self.show_area_radio.clicked.connect(lambda: self._set_plot_type("feature"))
        button_group.addButton(self.show_tree_radio)
        button_group.addButton(self.show_area_radio)
        display_layout.addWidget(self.show_tree_radio)
        display_layout.addWidget(self.show_area_radio)

        self.feature_dropdown = QComboBox()
        for feature in features:
            self.feature_dropdown.addItem(feature)
        self.feature_dropdown.currentIndexChanged.connect(self._update_feature)
        display_layout.addWidget(self.feature_dropdown)

        display_box.setLayout(display_layout)
        display_box.setMaximumWidth(400)
        display_box.setMaximumHeight(60)

        layout = QVBoxLayout()
        layout.addWidget(display_box)

        self.setLayout(layout)

    def _toggle_plot_type(self, event=None) -> None:
        """Toggle display mode"""

        if (
            self.show_area_radio.isEnabled
        ):  # if button is disabled, toggle is not allowed
            if self.plot_type == "feature":
                self._set_plot_type("tree")
                self.show_tree_radio.setChecked(True)
            else:
                self._set_plot_type("feature")
                self.show_area_radio.setChecked(True)

    def _set_plot_type(self, plot_type: str):
        """Emit signal to change the display mode"""

        self.plot_type = plot_type
        self.change_plot_type.emit(plot_type)

    def _update_feature(self) -> None:
        """Update the feature to be plotted if the plot_type == 'feature'"""

        self.current_feature = self.feature_dropdown.currentText()
        self.change_plot_type.emit(self.plot_type)

    def get_current_feature(self):
        """Return the current feature that is being plotted"""

        return self.current_feature

    def update_feature_dropdown(self, feature_list: list[str]) -> None:
        """Update the list of features in the dropdown"""

        self.feature_dropdown.clear()
        for feature in feature_list:
            self.feature_dropdown.addItem(feature)

        if self.current_feature not in feature_list:
            self.current_feature = None
