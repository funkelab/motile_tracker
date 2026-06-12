"""Tests for MenuManager: initialization, tab management, and widget visibility."""

from unittest.mock import MagicMock

from qtpy.QtWidgets import QDockWidget, QScrollArea, QTabBar, QWidget

from motile_tracker.application_menus.main_app import StartupWidget
from motile_tracker.application_menus.menu_manager import MenuManager


class DummyWidget(QWidget):
    def __init__(self, viewer):
        super().__init__()


def test_basic_menu_operations(make_napari_viewer):
    """Test initialize_menu, find_dock_widget, toggle, and tabbar location."""
    viewer = make_napari_viewer()
    manager = MenuManager(viewer)

    menu = {"TestWidget": {"widget": DummyWidget, "location": "right"}}
    manager.initialize_menu(menu)

    # initialize_menu adds widget wrapped in QScrollArea
    assert "TestWidget" in viewer.window.dock_widgets
    assert isinstance(viewer.window.dock_widgets["TestWidget"], QScrollArea)

    # _find_dock_widget_by_name finds the widget
    found = manager._find_dock_widget_by_name("TestWidget")
    assert found is not None

    # toggle_menu_panel_visibility doesn't raise
    manager.toggle_menu_panel_visibility()
    manager.toggle_menu_panel_visibility()

    # set_tabbar_location and set_foreground_tabs don't raise
    manager.set_tabbar_location("North")
    manager.set_foreground_tabs(["TestWidget"])


def test_recreate_hidden_widget_and_hide_restore_cycle(make_napari_viewer):
    """Test widget reuse when hidden and full hide/restore cycle."""
    viewer = make_napari_viewer()
    manager = MenuManager(viewer)

    menu = {"TestWidget": {"widget": DummyWidget, "location": "right"}}
    manager.initialize_menu(menu)

    dock = manager._find_dock_widget_by_name("TestWidget")
    assert dock is not None

    # Simulate hidden state for recreate path
    dock.isVisible = MagicMock(return_value=False)
    fake_parent = MagicMock()
    dock.parent = MagicMock(return_value=fake_parent)

    manager.initialize_menu(menu)
    assert "TestWidget" in manager.visible_menus
    fake_parent.show.assert_called_once()

    # Now test full hide/restore cycle with a fresh widget
    menu2 = {"A": {"widget": DummyWidget, "location": "right"}}
    manager.initialize_menu(menu2)
    dock2 = manager._find_dock_widget_by_name("A")
    dock2.isVisible = MagicMock(return_value=True)
    parent2 = MagicMock()
    dock2.parent = MagicMock(return_value=parent2)

    manager.toggle_menu_panel_visibility()
    parent2.close.assert_called_once()
    assert manager.hidden is True

    manager.toggle_menu_panel_visibility()
    parent2.show.assert_called_once()
    assert manager.hidden is False


def test_error_fallback_and_visible_tabs(make_napari_viewer):
    """Test RuntimeError fallback and _get_visible_tabs filtering."""
    viewer = make_napari_viewer()
    manager = MenuManager(viewer)

    # RuntimeError during isVisible causes safe fallback
    bad_widget = MagicMock()
    bad_widget.isVisible.side_effect = RuntimeError("deleted")
    viewer.window.__dict__["dock_widgets"] = {"BrokenWidget": bad_widget}
    result = manager._find_dock_widget_by_name("BrokenWidget")
    assert result is None

    # Restore dock_widgets for visible tabs test
    menu = {"Visible": {"widget": DummyWidget, "location": "right"}}
    manager.initialize_menu(menu)
    dock = manager._find_dock_widget_by_name("Visible")
    dock.isVisible = MagicMock(return_value=True)

    manager.initialized_menu_widgets.add("Hidden")

    def fake_find(name):
        if name == "Visible":
            return dock
        return None

    manager._find_dock_widget_by_name = fake_find

    visible = manager._get_visible_tabs()
    assert "Visible" in visible
    assert "Hidden" not in visible


def test_foreground_tabs_and_tabbar_fallback(make_napari_viewer):
    """Test set_foreground_tabs raises correct widget and tabbar fallback."""
    viewer = make_napari_viewer()
    manager = MenuManager(viewer)

    StartupWidget(viewer)

    qt_window = viewer.window._qt_window
    dock_widgets = qt_window.findChildren(QDockWidget)
    assert len(dock_widgets) > 0

    # set_foreground_tabs raises the correct widget
    target = dock_widgets[3]
    target_title = target.windowTitle()
    target.raise_ = MagicMock()
    manager.set_foreground_tabs([target_title])

    for dw in dock_widgets:
        if dw is target:
            dw.raise_.assert_called_once()
        else:
            assert not getattr(dw.raise_, "called", False)

    # Invalid tabbar location falls back safely
    tabbars = qt_window.findChildren(QTabBar)
    if not tabbars:
        tabbar = QTabBar()
        tabbar.setParent(qt_window)
        tabbars = [tabbar]

    for tb in tabbars:
        tb.setStyleSheet = MagicMock()
        tb.setElideMode = MagicMock()

    manager.set_tabbar_location("INVALID")

    for tb in tabbars:
        tb.setStyleSheet.assert_called()
        tb.setElideMode.assert_called()
