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
from motile_tracker.data_views.views.tree_view.custom_table_widget import (
    ColoredTableWidget,
)
from motile_tracker.data_views.views.tree_view.tree_widget import TreeWidget
from motile_tracker.data_views.views_coordinator.groups import GroupWidget
from motile_tracker.data_views.views_coordinator.tracks_list import TrackListWidget
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer
from motile_tracker.motile.menus.motile_widget import MotileWidget

MENU_WIDGETS = {
    "Getting Started": {"widget": WelcomeWidget, "location": "right"},
    "Tracking": {"widget": MotileWidget, "location": "right"},
    "Tracks List": {"widget": TrackListWidget, "location": "right"},
    "Editing && Selection": {"widget": EditingSelectionWidget, "location": "right"},
    "Visualization": {"widget": LabelVisualizationWidget, "location": "right"},
    "Groups": {"widget": GroupWidget, "location": "right"},
    "Table": {"widget": ColoredTableWidget, "location": "right"},
    "Lineage View": {"widget": TreeWidget, "location": "bottom"},
}


# MainAppWidget: initialize all widgets
class MainAppWidget(QWidget):
    def __init__(self, napari_viewer: napari.Viewer):
        super().__init__()
        self.viewer = napari_viewer
        tracks_viewer = TracksViewer.get_instance(napari_viewer)
        if tracks_viewer.menu_manager is not None:
            self.menu_manager = tracks_viewer.menu_manager
        else:
            self.menu_manager = MenuManager(napari_viewer)
        for name, config in MENU_WIDGETS.items():
            self.menu_manager.initialize_menu({name: config})
        # make sure the 'Getting started' tab is the active foreground tab.
        QTimer.singleShot(
            0,
            lambda: tracks_viewer.menu_manager.set_foreground_tabs(["Getting Started"]),
        )
        QTimer.singleShot(0, self._remove_self)

    def _remove_self(self):
        self.viewer.window.remove_dock_widget(self)


# --- One widget class per menu item ---
def _make_single_menu_widget_class(widget_name):
    class _SingleMenuWidget(QWidget):
        def __init__(self, napari_viewer: napari.Viewer):
            super().__init__()
            self.viewer = napari_viewer
            tracks_viewer = TracksViewer.get_instance(napari_viewer)
            if tracks_viewer.menu_manager is not None:
                self.menu_manager = tracks_viewer.menu_manager
            else:
                self.menu_manager = MenuManager(napari_viewer)
            self.menu_manager.initialize_menu({widget_name: MENU_WIDGETS[widget_name]})
            QTimer.singleShot(0, self._remove_self)

        def _remove_self(self):
            self.viewer.window.remove_dock_widget(self)

    _SingleMenuWidget.__name__ = widget_name.replace(" ", "") + "Widget"
    return _SingleMenuWidget


# Export one class per menu item (except MainAppWidget)
GettingStartedWidget = _make_single_menu_widget_class("Getting Started")
TrackingWidget = _make_single_menu_widget_class("Tracking")
TracksListWidget = _make_single_menu_widget_class("Tracks List")
EditingSelectionWidget = _make_single_menu_widget_class("Editing && Selection")
VisualizationWidget = _make_single_menu_widget_class("Visualization")
GroupsWidget = _make_single_menu_widget_class("Groups")
TableWidget = _make_single_menu_widget_class("Table")
LineageViewWidget = _make_single_menu_widget_class("Lineage View")
