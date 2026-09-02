import sys
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.parametrize("mode", ["all", "tracking", "editing"])
def test_main_entrypoint(mode):
    """CLI entrypoint passes correct mode to StartupWidget."""

    viewer = MagicMock(name="viewer")

    with (
        patch("napari_track_edit.__main__.napari.Viewer", return_value=viewer),
        patch("napari_track_edit.__main__.napari.run"),
        patch("napari_track_edit.data_views.views.ortho_views.initialize_ortho_views"),
        patch("napari_track_edit.__main__.StartupWidget") as mock_widget,
        patch.object(sys, "argv", ["prog", "--mode", mode]),
    ):
        from napari_track_edit.__main__ import main

        main()

    mock_widget.assert_called_once()
    args, kwargs = mock_widget.call_args

    # First positional arg should be viewer
    assert args[0] is viewer

    # mode should match CLI flag
    assert kwargs["mode"] == mode
