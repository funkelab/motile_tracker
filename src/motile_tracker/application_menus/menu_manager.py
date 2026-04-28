from __future__ import annotations

import napari
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDockWidget, QScrollArea, QTabBar, QTabWidget, QWidget

from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


class MenuManager:
    """Initializes and manages the menu widgets, including show/hide functionality and
    tracking active widgets."""

    def __init__(self, viewer: napari.Viewer):
        super().__init__()

        self.viewer = viewer
        self.tracks_viewer = TracksViewer.get_instance(viewer)
        self.tracks_viewer.menu_manager = self

        # Track the active menu widgets for show/hide operations
        self.hidden = False
        self.initialized_menu_widgets: set[str] = (
            set()
        )  # names of widgets ever initialized
        self.visible_menus: set[str] = set()  # names of widgets currently visible
        self.active_tabs: list[str] = []  # names of foreground tabs

    def initialize_menu(self, menu: dict[str, dict[str, any]]) -> None:
        """Initialize the menu by creating and adding the specified widgets, with robust
        handling for closed/deleted dock widgets."""

        for name, config in menu.items():
            widget_exists = False
            dock_widget = self._find_dock_widget_by_name(name)
            if dock_widget is not None:
                # Check if the widget is visible
                if dock_widget.isVisible():
                    widget_exists = True
                else:
                    # Widget exists but is hidden, show it
                    parent = dock_widget.parent()
                    if parent is not None:
                        parent.show()
                    self.visible_menus.add(name)
                    widget_exists = True
            # If widget does not exist (was closed/deleted), or never initialized, create it
            if not widget_exists:
                widget_cls = config["widget"]
                location = config["location"]
                widget = widget_cls(self.viewer)
                scroll_wrapper = self._create_scroll_wrapper(widget)
                self.viewer.window.add_dock_widget(
                    scroll_wrapper, area=location, name=name, tabify=True
                )
                self.initialized_menu_widgets.add(name)
                self.visible_menus.add(name)

        for tb in self.viewer.window._qt_window.findChildren(QTabBar):
            tb.setUsesScrollButtons(True)
            tb.setExpanding(False)
            tb.setStyleSheet("""
                QTabBar::tab {
                    min-width: 50px;
                }
            """)

    def _find_dock_widget_by_name(self, name: str) -> QScrollArea | None:
        """Find a widget in the dock dock by name, or return None if not found or
        deleted."""

        # Try napari's dock_widgets dict first
        dock_widgets = getattr(self.viewer.window, "dock_widgets", {})
        dock_widget = dock_widgets.get(name, None)
        # Check if the widget is still alive
        if dock_widget is not None:
            try:
                _ = dock_widget.isVisible()
                return dock_widget
            except RuntimeError:
                return None
        # Fallback: search Qt window for a QDockWidget with the right title
        qt_window = self.viewer.window._qt_window
        for dw in qt_window.findChildren(QDockWidget):
            if dw.windowTitle() == name:
                try:
                    _ = dw.isVisible()
                    return dw
                except RuntimeError:
                    continue
        return None

    def _set_right_tabs_vertical(self) -> None:
        """Set the tab bar vertically"""

        qt_window = self.viewer.window._qt_window

        qt_window.setTabPosition(
            Qt.DockWidgetArea.RightDockWidgetArea, QTabWidget.TabPosition.East
        )

        for tb in self.viewer.window._qt_window.findChildren(QTabBar):
            if tb.height() > tb.width():
                tb.setUsesScrollButtons(True)
                tb.setExpanding(False)
                tb.setStyleSheet("""
                    QTabBar::tab {
                        min-width: 15px;
                        min-height: 50px;
                    }
                """)

    def _create_scroll_wrapper(self, widget: QWidget) -> QScrollArea:
        """Wrap a widget in a QScrollArea to make it scrollable."""
        scroll_area = QScrollArea()
        scroll_area.setWidget(widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        return scroll_area

    def _get_foreground_tabs(self) -> list[str]:
        """Get the names of the currently active tabs (dock widgets that are both
        initialized and currently present in a dock)."""
        tabs = []
        tabbars = self.viewer.window._qt_window.findChildren(QTabBar)
        for tabbar in tabbars:
            active = tabbar.tabText(tabbar.currentIndex())
            if self._find_dock_widget_by_name(active) is not None:
                tabs.append(active)
        return tabs

    def _set_foreground_tabs(self, tab_names: list[str]) -> None:
        """Set the specified tab to the foreground."""

        qt_window = self.viewer.window._qt_window
        dock_widgets = qt_window.findChildren(QDockWidget)

        for tab_name in tab_names:
            dock_widget = [dw for dw in dock_widgets if dw.windowTitle() == tab_name]

            if len(dock_widget) > 0:
                dock_widget[0].raise_()

    def _get_visible_tabs(self) -> set[str]:
        """Get the names of the current foreground tabs"""
        return {
            name
            for name in self.initialized_menu_widgets
            if self._find_dock_widget_by_name(name) is not None
            and self._find_dock_widget_by_name(name).isVisible()
        }

    def toggle_menu_panel_visibility(self) -> None:
        """Toggle visibility of all active menu widgets."""
        if not self.hidden:
            # Save the currently visible and active widgets
            self.visible_menus = self._get_visible_tabs()
            self.active_tabs = list(self._get_foreground_tabs())

            # hide all menus
            for name in self.initialized_menu_widgets:
                dock_widget = self._find_dock_widget_by_name(name)
                if dock_widget is not None:
                    parent = dock_widget.parent()
                    if parent is not None:
                        parent.close()
        else:
            # restore the previously visible widgets
            for name in self.visible_menus:
                dock_widget = self._find_dock_widget_by_name(name)
                if dock_widget is not None:
                    parent = dock_widget.parent()
                    if parent is not None:
                        parent.show()
            # restore the previously active tab
            self.active_tabs = [
                name
                for name in self.active_tabs
                if self._find_dock_widget_by_name(name) is not None
            ]
            if len(self.active_tabs) > 0:
                self._set_foreground_tabs(self.active_tabs)

        self.hidden = not self.hidden
