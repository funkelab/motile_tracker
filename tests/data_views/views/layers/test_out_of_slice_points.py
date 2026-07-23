import numpy as np
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


def test_zonly_vs_normal_points(make_napari_viewer):

    viewer = make_napari_viewer()
    viewer.add_labels(np.zeros((20, 20, 20, 20), dtype=np.uint8))  # to set viewer dims

    data = np.array(
        [
            [1, 4, 20, 20],  # idx 0
            [2, 5, 34, 22],  # idx 1
        ]
    )

    zonly = ZOnlyPoints(data, size=20)
    normal = Points(data, size=20)

    viewer.add_layer(zonly)
    viewer.add_layer(normal)

    zonly.out_of_slice_display = True
    normal.out_of_slice_display = True

    viewer.dims.current_step = (1, 5, 20, 20)

    zonly.refresh()
    normal.refresh()

    n_idx = get_visible_indices(normal)
    z_idx = get_visible_indices(zonly)

    assert set(n_idx) == {0, 1}
    assert z_idx == [0]

    # Also check for 5 dims
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

    zonly = ZOnlyPoints(data, size=20)
    normal = Points(data, size=20)

    viewer.add_layer(zonly)
    viewer.add_layer(normal)

    zonly.out_of_slice_display = True
    normal.out_of_slice_display = True

    viewer.dims.current_step = (1, 1, 5, 20, 20)

    zonly.refresh()
    normal.refresh()

    n_idx = get_visible_indices(normal)
    z_idx = get_visible_indices(zonly)

    assert set(n_idx) == {0, 1, 2}
    assert z_idx == [0]
