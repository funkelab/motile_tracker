import sys
from unittest.mock import patch

import pytest


@pytest.mark.parametrize("mode", ["all", "tracking", "editing"])
def test_main_entrypoint(make_napari_viewer, qtbot, mode):
    """CLI entrypoint passes correct mode to StartupWidget."""

    viewer = make_napari_viewer()

    with (
        patch("motile_tracker.__main__.napari.Viewer", return_value=viewer),
        patch("motile_tracker.__main__.napari.run"),
        patch("motile_tracker.data_views.views.ortho_views.initialize_ortho_views"),
        patch("motile_tracker.__main__.StartupWidget") as mock_widget,
        patch.object(sys, "argv", ["prog", "--mode", mode]),
    ):
        from motile_tracker.__main__ import main

        main()

    mock_widget.assert_called_once()
    args, kwargs = mock_widget.call_args

    # First positional arg should be viewer
    assert args[0] == viewer

    # mode should match CLI flag
    assert kwargs["mode"] == mode
