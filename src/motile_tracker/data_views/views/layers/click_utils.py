import time
from collections.abc import Generator

from napari.layers import Labels, Points
from napari.utils.events import Event


def detect_click(event: Event) -> Generator[None, None, bool]:
    """Yield during drag, then return True if this was a click."""

    mouse_press_time = time.time()
    dragged = False
    yield  # initial press
    while event.type == "mouse_move":
        dragged = True
        yield
    if dragged and time.time() - mouse_press_time < 0.5:
        dragged = False  # micro drag: treat as click
    return not dragged


def get_click_value(layer: Labels | Points, event: Event) -> int:
    """Return the value (label, point index) at the click location"""

    return layer.get_value(
        event.position,
        view_direction=event.view_direction,
        dims_displayed=event.dims_displayed,
        world=True,
    )
