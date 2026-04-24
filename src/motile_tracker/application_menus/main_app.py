import napari
from qtpy.QtCore import QTimer
from qtpy.QtWidgets import (
    QWidget,
)

from motile_tracker.application_menus.editing_selection_menu import (
    EditingSelectionWidget,
)
from motile_tracker.application_menus.menu_manager import MenuManager
from motile_tracker.application_menus.visualization_widget import (
    LabelVisualizationWidget,
)
from motile_tracker.application_menus.welcome_widget import WelcomeWidget
from motile_tracker.data_views.views.tree_view.tree_widget import TreeWidget
from motile_tracker.data_views.views_coordinator.groups import GroupWidget
from motile_tracker.data_views.views_coordinator.tracks_list import TrackListWidget
from motile_tracker.motile.menus.motile_widget import MotileWidget

MENU_WIDGETS = {
    "Getting started": {"widget": WelcomeWidget, "location": "right"},
    "Tracking": {"widget": MotileWidget, "location": "right"},
    "Tracks List": {"widget": TrackListWidget, "location": "right"},
    "Editing && Selection": {"widget": EditingSelectionWidget, "location": "right"},
    "Visualization": {"widget": LabelVisualizationWidget, "location": "right"},
    "Groups": {"widget": GroupWidget, "location": "right"},
    "Lineage View": {"widget": TreeWidget, "location": "bottom"},
}


class MainApp(QWidget):
    def __init__(self, viewer: napari.Viewer):
        super().__init__()

        self.viewer = viewer

        self.viewer.mouse_double_click_callbacks.clear()  # no double click to zoom
        self.menu_manager = MenuManager(viewer)

        for name, config in MENU_WIDGETS.items():
            self.menu_manager.initialize_menu(menu={name: config})

        QTimer.singleShot(0, self._remove_self)

    def _remove_self(self):
        # This removes the *napari-created dock wrapper* around MainApp
        self.viewer.window.remove_dock_widget(self)
