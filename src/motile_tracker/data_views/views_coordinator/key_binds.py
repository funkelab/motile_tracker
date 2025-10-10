from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from napari.layers import Labels, Points

    from motile_tracker.data_views.views.layers.track_labels import TrackLabels
    from motile_tracker.data_views.views.layers.track_points import TrackPoints
    from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer

KEYMAP = {
    "toggle_display_mode": ["q"],
    "create_edge": ["a"],
    "delete_node": ["d", "Delete"],
    "delete_edge": ["b"],
    "undo": ["z"],
    "redo": ["r"],
}


def bind_keymap(
    target: TrackPoints | Points | TrackLabels | Labels,
    keymap: dict[str, str],
    tracks_viewer: TracksViewer,
):
    """Bind all keys in `keymap` to the corresponding methods on `tracks_viewer` to the
    target layer. This should be an instance of (Track)Labels or (Track)Points"""

    for method_name, keys in keymap.items():
        handler = getattr(tracks_viewer, method_name, None)
        if handler is not None:
            for key in keys:
                target.bind_key(key)(handler)
