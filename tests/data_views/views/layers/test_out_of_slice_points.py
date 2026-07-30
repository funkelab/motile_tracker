import numpy as np
from napari.components import ViewerModel
from napari.layers import Points

from motile_tracker.data_views.views.layers.out_of_slice_points import ZOnlyPoints


def get_visible_indices(layer):
    """
    visible points are those in the current view_data,
    but we recover indices via comparison to full data.
    """
    visible = layer._view_data

    # match rows back to original data
    idx = []
    for row in visible:
        matches = np.where((layer.data[:, -2:] == row).all(axis=1))[0]
        idx.extend(matches.tolist())

    return sorted(set(idx))


def add_points(viewer, data):
    """Add a ZOnlyPoints and a plain Points layer for the same data.

    Returns the (zonly, normal) pair, both with out of slice display on.
    """
    zonly = ZOnlyPoints(data, size=20)
    normal = Points(data, size=20)

    viewer.add_layer(zonly)
    viewer.add_layer(normal)

    zonly.out_of_slice_display = True
    normal.out_of_slice_display = True

    return zonly, normal


# Uses ViewerModel rather than napari's ``make_napari_viewer`` fixture: these
# tests only need viewer dims and layer slicing, no Qt window, and
# ``make_napari_viewer`` cannot be mixed with the module scoped ``viewer``
# fixture in tests/data_views/conftest.py (see the note there).


def test_zonly_vs_normal_points():
    viewer = ViewerModel()
    viewer.add_labels(np.zeros((20, 20, 20, 20), dtype=np.uint8))  # to set viewer dims

    data = np.array(
        [
            [1, 4, 20, 20],  # idx 0
            [2, 5, 34, 22],  # idx 1
        ]
    )

    zonly, normal = add_points(viewer, data)

    viewer.dims.current_step = (1, 5, 20, 20)

    zonly.refresh()
    normal.refresh()

    n_idx = get_visible_indices(normal)
    z_idx = get_visible_indices(zonly)

    assert set(n_idx) == {0, 1}
    assert z_idx == [0]


def test_zonly_vs_normal_points_5d():
    viewer = ViewerModel()
    viewer.add_labels(
        np.zeros((20, 20, 20, 20, 20), dtype=np.uint8)
    )  # to set viewer dims

    data = np.array(
        [
            [1, 1, 4, 20, 20],  # idx 0
            [3, 2, 5, 34, 22],  # idx 1
            [3, 1, 5, 34, 22],  # idx 2
        ]
    )

    zonly, normal = add_points(viewer, data)

    viewer.dims.current_step = (1, 1, 5, 20, 20)

    zonly.refresh()
    normal.refresh()

    n_idx = get_visible_indices(normal)
    z_idx = get_visible_indices(zonly)

    assert set(n_idx) == {0, 1, 2}
    assert z_idx == [0]
