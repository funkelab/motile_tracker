"""Tests for main_app.py: StartupWidget, MainAppWidget, and single menu widget classes."""

from qtpy.QtWidgets import QWidget

from motile_tracker.application_menus.main_app import (
    MENU_WIDGETS,
    EditingGroupWidget,
    EditingSelection_LauncherWidget,
    GettingStarted_LauncherWidget,
    Groups_LauncherWidget,
    LineageView_LauncherWidget,
    MainAppWidget,
    StartupWidget,
    Table_LauncherWidget,
    Tracking_LauncherWidget,
    TrackingGroupWidget,
    TrackList_LauncherWidget,
    Visualization_LauncherWidget,
)


def test_startup_main_and_group_widgets(make_napari_viewer):
    """Test StartupWidget, MainAppWidget, and group widget initialization."""
    viewer = make_napari_viewer()

    # StartupWidget initializes all tabs
    widget = StartupWidget(viewer)
    assert isinstance(widget, QWidget)
    assert len(viewer.window.dock_widgets) == len(MENU_WIDGETS)

    # MainAppWidget is a StartupWidget and also initializes all tabs
    viewer2 = make_napari_viewer()
    widget2 = MainAppWidget(viewer2)
    assert isinstance(widget2, StartupWidget)
    assert len(viewer2.window.dock_widgets) == len(MENU_WIDGETS)

    # TrackingGroupWidget and EditingGroupWidget initialize subset of widgets
    viewer3 = make_napari_viewer()
    tracking = TrackingGroupWidget(viewer3)
    editing = EditingGroupWidget(viewer3)
    assert isinstance(tracking, StartupWidget)
    assert isinstance(editing, StartupWidget)
    assert len(viewer3.window.dock_widgets) == 6


def test_single_menu_widgets(qtbot, make_napari_viewer):
    """Each single menu widget should only initialize one docked widget."""
    for WidgetClass in [
        GettingStarted_LauncherWidget,
        Tracking_LauncherWidget,
        TrackList_LauncherWidget,
        EditingSelection_LauncherWidget,
        Visualization_LauncherWidget,
        Groups_LauncherWidget,
        Table_LauncherWidget,
        LineageView_LauncherWidget,
    ]:
        n_docked_widgets = 0
        viewer = make_napari_viewer()
        widget = WidgetClass(viewer)
        n_docked_widgets += 1
        assert isinstance(widget, StartupWidget)
        assert len(viewer.window.dock_widgets) == n_docked_widgets
