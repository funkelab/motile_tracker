"""Tests for MenuManager: initialization, tab management, and widget visibility."""

from unittest.mock import MagicMock

from qtpy.QtWidgets import QDockWidget, QScrollArea, QTabBar, QWidget

from motile_tracker.application_menus.menu_manager import MenuManager


def test_initialize_menu_adds_widget(make_napari_viewer):
    viewer = make_napari_viewer()
    manager = MenuManager(viewer)

    class DummyWidget(QWidget):
        def __init__(self, viewer):
            super().__init__()

    menu = {"TestWidget": {"widget": DummyWidget, "location": "right"}}
    manager.initialize_menu(menu)
    assert "TestWidget" in viewer.window.dock_widgets
    # Should wrap in QScrollArea
    assert isinstance(viewer.window.dock_widgets["TestWidget"], QScrollArea)


def test_find_dock_widget_by_name(make_napari_viewer):
    viewer = make_napari_viewer()
    manager = MenuManager(viewer)

    class DummyWidget(QWidget):
        def __init__(self, viewer):
            super().__init__()

    menu = {"TestWidget": {"widget": DummyWidget, "location": "right"}}
    manager.initialize_menu(menu)
    found = manager._find_dock_widget_by_name("TestWidget")
    assert found is not None


def test_toggle_menu_panel_visibility(make_napari_viewer):
    viewer = make_napari_viewer()
    manager = MenuManager(viewer)

    class DummyWidget(QWidget):
        def __init__(self, viewer):
            super().__init__()

    menu = {"TestWidget": {"widget": DummyWidget, "location": "right"}}
    manager.initialize_menu(menu)
    # Should not raise
    manager.toggle_menu_panel_visibility()
    manager.toggle_menu_panel_visibility()


def test_set_tabbar_location_and_foreground_tabs(make_napari_viewer):
    viewer = make_napari_viewer()
    manager = MenuManager(viewer)
    # Should not raise
    manager.set_tabbar_location("North")
    manager.set_foreground_tabs(["TestWidget"])


def test_initialize_menu_recreates_missing_widget(make_napari_viewer):
    """If a widget exists but is hidden, it should be reused and shown."""
    viewer = make_napari_viewer()
    manager = MenuManager(viewer)

    class DummyWidget(QWidget):
        def __init__(self, viewer):
            super().__init__()

    # create real widget via system
    menu = {"TestWidget": {"widget": DummyWidget, "location": "right"}}
    manager.initialize_menu(menu)

    # get dock widget
    dock = manager._find_dock_widget_by_name("TestWidget")
    assert dock is not None

    # simulate hidden state
    dock.isVisible = MagicMock(return_value=False)

    fake_parent = MagicMock()
    dock.parent = MagicMock(return_value=fake_parent)

    # re-run initialization (triggers reuse path)
    manager.initialize_menu(menu)

    assert "TestWidget" in manager.visible_menus
    fake_parent.show.assert_called_once()


def test_find_dock_widget_runtime_error_fallback(make_napari_viewer):
    """Ensure RuntimeError during isVisible causes fallback search to continue safely."""
    viewer = make_napari_viewer()
    manager = MenuManager(viewer)

    bad_widget = MagicMock()
    bad_widget.isVisible.side_effect = RuntimeError("deleted")

    viewer.window.__dict__["dock_widgets"] = {"BrokenWidget": bad_widget}

    result = manager._find_dock_widget_by_name("BrokenWidget")
    assert result is None


def test_get_visible_tabs(make_napari_viewer):
    """Visible tabs should only include initialized + visible widgets."""
    viewer = make_napari_viewer()
    manager = MenuManager(viewer)

    class DummyWidget(QWidget):
        def __init__(self, viewer):
            super().__init__()

    # Create one visible widget
    menu = {"Visible": {"widget": DummyWidget, "location": "right"}}
    manager.initialize_menu(menu)

    dock = manager._find_dock_widget_by_name("Visible")
    dock.isVisible = MagicMock(return_value=True)

    # Add fake initialized-but-not-visible widget
    manager.initialized_menu_widgets.add("Hidden")

    def fake_find(name):
        if name == "Visible":
            return dock
        return None

    manager._find_dock_widget_by_name = fake_find

    visible = manager._get_visible_tabs()
    assert "Visible" in visible
    assert "Hidden" not in visible


def test_toggle_menu_hide_and_restore(make_napari_viewer):
    """Test full hide → restore cycle for menu visibility."""
    viewer = make_napari_viewer()
    manager = MenuManager(viewer)

    class DummyWidget(QWidget):
        def __init__(self, viewer):
            super().__init__()

    menu = {"A": {"widget": DummyWidget, "location": "right"}}
    manager.initialize_menu(menu)

    dock = manager._find_dock_widget_by_name("A")

    # Make isVisible controllable
    dock.isVisible = MagicMock(return_value=True)

    parent = MagicMock()
    dock.parent = MagicMock(return_value=parent)

    # --- hide ---
    manager.toggle_menu_panel_visibility()
    parent.close.assert_called_once()

    assert manager.hidden is True

    # --- restore ---
    manager.toggle_menu_panel_visibility()
    parent.show.assert_called_once()

    assert manager.hidden is False


def test_set_foreground_tabs_raises_correct_widget(make_napari_viewer):
    viewer = make_napari_viewer()
    manager = MenuManager(viewer)

    qt_window = viewer.window._qt_window
    dock_widgets = qt_window.findChildren(QDockWidget)

    assert len(dock_widgets) > 0

    # Pick one real widget to test
    target = dock_widgets[3]
    target_title = target.windowTitle()

    target.raise_ = MagicMock()

    manager.set_foreground_tabs([target_title])

    for dw in dock_widgets:
        if dw is target:
            dw.raise_.assert_called_once()
        else:
            assert not getattr(dw.raise_, "called", False)


def test_set_tabbar_location_default_fallback(make_napari_viewer):
    """Invalid location should fall back to North safely using real Qt objects."""
    viewer = make_napari_viewer()
    manager = MenuManager(viewer)

    qt_window = viewer.window._qt_window

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
