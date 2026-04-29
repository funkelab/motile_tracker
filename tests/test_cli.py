from unittest.mock import patch


def test_main_entrypoint(make_napari_viewer, qtbot):
    """CLI entry point (motile_tracker.__main__:main) launches without errors."""
    viewer = make_napari_viewer()
    with (
        patch("motile_tracker.__main__.napari.Viewer", return_value=viewer),
        patch("motile_tracker.__main__.napari.run"),
        patch("motile_tracker.application_menus.main_app.initialize_ortho_views"),
    ):
        from motile_tracker.__main__ import main

        main()

    for widget in viewer.window.dock_widgets.values():
        qtbot.addWidget(widget)
