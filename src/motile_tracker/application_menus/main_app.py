import napari
from qtpy.QtWidgets import (
    QVBoxLayout,
    QWidget,
)

from motile_tracker.application_menus.menu_widget import MenuWidget
from motile_tracker.data_views.views.tree_view.tree_widget import TreeWidget


class MainApp(QWidget):
    """Combines the different tracker widgets for faster dock arrangement"""

    def __init__(self, viewer: napari.Viewer):
        super().__init__()

        self.menu_widget = MenuWidget(viewer)
        tree_widget = TreeWidget(viewer)

        viewer.window.add_dock_widget(tree_widget, area="bottom", name="Tree View")

        layout = QVBoxLayout()
        layout.addWidget(self.menu_widget)

        self.setLayout(layout)
