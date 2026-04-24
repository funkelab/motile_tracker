from __future__ import annotations

import napari
from qtpy.QtWidgets import QDockWidget, QScrollArea, QTabBar

from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


class MenuManager:
    """Initializes and manages the menu widgets, including show/hide functionality and tracking active widgets."""

    def __init__(self, viewer: napari.Viewer):
        super().__init__()

        self.viewer = viewer
        self.tracks_viewer = TracksViewer.get_instance(viewer)
        self.tracks_viewer.menu_manager = self

        # Track the active menu widgets for show/hide operations
        self.hidden = False
        self._active_menu_widgets: set[str] = (
            set()
        )  # track which menu widgets have been initialized and added to the viewer
        self.visible_menus: set[str] = (
            set()
        )  # track which menu widgets are currently visible (subset of active_menu_widgets)
        self.active_tabs: list[str] = []
        self.dw_map: dict[
            str, QDockWidget
        ] = {}  # map of menu widget names to their dock widgets

    def initialize_menu(self, menu: dict[str, dict[str, any]]) -> None:
        """Initialize the menu by creating and adding the specified widgets."""

        for name, config in menu.items():
            if name not in self._active_menu_widgets:
                widget_cls = config["widget"]
                location = config["location"]

                widget = widget_cls(self.viewer)
                # Wrap the widget in a scroll area
                scroll_wrapper = self._create_scroll_wrapper(widget)

                # Add the scroll wrapper as a dock widget in the specified location
                self.viewer.window.add_dock_widget(
                    scroll_wrapper, area=location, name=name, tabify=True
                )

                # Track this menu widget as active and visible
                self._active_menu_widgets.add(name)
                self.visible_menus.add(name)

                # immediately find the dock widget to map a reference
                qt_window = self.viewer.window._qt_window
                dock_widgets = qt_window.findChildren(QDockWidget)

                # find the one we just added
                for dw in dock_widgets:
                    if dw.windowTitle() == name:
                        self.dw_map[name] = dw
                        break

    def _create_scroll_wrapper(self, widget) -> QScrollArea:
        """Wrap a widget in a QScrollArea to make it scrollable."""
        scroll_area = QScrollArea()
        scroll_area.setWidget(widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        return scroll_area

    def _get_current_active_tabs(self) -> list[str]:
        """Get the names of the currently active tabs."""

        tabs = []
        tabbars = self.viewer.window._qt_window.findChildren(QTabBar)
        for tabbar in tabbars:
            active = tabbar.tabText(tabbar.currentIndex())
            if active in self.dw_map:
                tabs.append(active)
        return tabs

    def set_active_tabs(self, tab_names: list[str]) -> None:
        """Set the specified tab as active."""

        tab_names = [name for name in tab_names if name in self.dw_map]
        for tab_name in tab_names:
            self.dw_map[tab_name].raise_()
        self.active_tabs = tab_names

    def _get_visible_menu_widgets(self) -> set[str]:
        """Get the set of currently visible menu widgets."""

        return {name for name in self.dw_map if self.dw_map[name].isVisible()}

    def toggle_menu_panel_visibility(self) -> None:
        """Toggle visibility of all active menu widgets."""

        if not self.hidden:
            # Save the currently visible and active widgets
            self.visible_menus = self._get_visible_menu_widgets()
            self.active_tabs = self._get_current_active_tabs()

            # hide all menus
            for name in self.dw_map:
                if name in self.viewer.window.dock_widgets:
                    dock_widget = self.viewer.window.dock_widgets[name]
                    parent = dock_widget.parent()
                    if parent is not None:
                        parent.close()

        else:
            # restore the previously visible widgets
            for name in self.visible_menus:
                if name in self.viewer.window.dock_widgets:
                    dock_widget = self.viewer.window.dock_widgets[name]
                    parent = dock_widget.parent()
                    if parent is not None:
                        parent.show()
            # restore the previously active tab
            if len(self.active_tabs) > 0:
                self.set_active_tabs(self.active_tabs)

        self.hidden = not self.hidden
