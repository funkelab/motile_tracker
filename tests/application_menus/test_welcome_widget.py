"""Tests for WelcomeWidget: initialization and content."""

from qtpy.QtWidgets import QLabel, QTextBrowser

from motile_tracker.application_menus.welcome_widget import WelcomeWidget


def test_welcome_widget_initializes(qtbot):
    class DummyViewer:
        pass

    widget = WelcomeWidget(DummyViewer())
    assert widget is not None
    # Should have a layout
    assert widget.layout() is not None
    # Should contain a QLabel with 'Motile Tracker'
    found_label = False
    for i in range(widget.layout().count()):
        item = widget.layout().itemAt(i).widget()
        if isinstance(item, QLabel) and "Motile Tracker" in item.text():
            found_label = True
    assert found_label
    # Should contain at least one QTextBrowser
    found_browser = False
    for i in range(widget.layout().count()):
        item = widget.layout().itemAt(i).widget()
        if isinstance(item, QTextBrowser):
            found_browser = True
    assert found_browser
