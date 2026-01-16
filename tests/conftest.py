import networkx as nx
import numpy as np
import pytest
from motile_toolbox.candidate_graph.graph_attributes import EdgeAttr, NodeAttr
from skimage.draw import disk

from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


@pytest.fixture
def segmentation_2d():
    frame_shape = (100, 100)
    total_shape = (5, *frame_shape)
    segmentation = np.zeros(total_shape, dtype="int32")
    # make frame with one cell in center with label 1
    rr, cc = disk(center=(50, 50), radius=20, shape=(100, 100))
    segmentation[0][rr, cc] = 1

    # make frame with two cells
    # first cell centered at (20, 80) with label 2
    # second cell centered at (60, 45) with label 3
    rr, cc = disk(center=(20, 80), radius=10, shape=frame_shape)
    segmentation[1][rr, cc] = 2
    rr, cc = disk(center=(60, 45), radius=15, shape=frame_shape)
    segmentation[1][rr, cc] = 3

    # continue track 3 with squares from 0 to 4 in x and y with label 3
    segmentation[2, 0:4, 0:4] = 4
    segmentation[4, 0:4, 0:4] = 5

    # unconnected node
    segmentation[4, 96:100, 96:100] = 6

    return segmentation


@pytest.fixture
def graph_2d():
    graph = nx.DiGraph()
    nodes = [
        (
            1,
            {
                NodeAttr.POS.value: [50, 50],
                NodeAttr.TIME.value: 0,
                NodeAttr.AREA.value: 1245,
                NodeAttr.TRACK_ID.value: 1,
            },
        ),
        (
            2,
            {
                NodeAttr.POS.value: [20, 80],
                NodeAttr.TIME.value: 1,
                NodeAttr.TRACK_ID.value: 2,
                NodeAttr.AREA.value: 305,
            },
        ),
        (
            3,
            {
                NodeAttr.POS.value: [60, 45],
                NodeAttr.TIME.value: 1,
                NodeAttr.AREA.value: 697,
                NodeAttr.TRACK_ID.value: 3,
            },
        ),
        (
            4,
            {
                NodeAttr.POS.value: [1.5, 1.5],
                NodeAttr.TIME.value: 2,
                NodeAttr.AREA.value: 16,
                NodeAttr.TRACK_ID.value: 3,
            },
        ),
        (
            5,
            {
                NodeAttr.POS.value: [1.5, 1.5],
                NodeAttr.TIME.value: 4,
                NodeAttr.AREA.value: 16,
                NodeAttr.TRACK_ID.value: 3,
            },
        ),
        # unconnected node
        (
            6,
            {
                NodeAttr.POS.value: [97.5, 97.5],
                NodeAttr.TIME.value: 4,
                NodeAttr.AREA.value: 16,
                NodeAttr.TRACK_ID.value: 5,
            },
        ),
    ]
    edges = [
        (1, 2, {EdgeAttr.IOU.value: 0.0}),
        (1, 3, {EdgeAttr.IOU.value: 0.395}),
        (
            3,
            4,
            {EdgeAttr.IOU.value: 0.0},
        ),
        (
            4,
            5,
            {EdgeAttr.IOU.value: 1.0},
        ),
    ]
    graph.add_nodes_from(nodes)
    graph.add_edges_from(edges)
    return graph


def sphere(center, radius, shape):
    assert len(center) == len(shape)
    indices = np.moveaxis(np.indices(shape), 0, -1)  # last dim is the index
    distance = np.linalg.norm(np.subtract(indices, np.asarray(center)), axis=-1)
    mask = distance <= radius
    return mask


@pytest.fixture
def segmentation_3d():
    frame_shape = (100, 100, 100)
    total_shape = (2, *frame_shape)
    segmentation = np.zeros(total_shape, dtype="int32")
    # make frame with one cell in center with label 1
    mask = sphere(center=(50, 50, 50), radius=20, shape=frame_shape)
    segmentation[0][mask] = 1

    # make frame with two cells
    # first cell centered at (20, 50, 80) with label 2
    # second cell centered at (60, 50, 45) with label 3
    mask = sphere(center=(20, 50, 80), radius=10, shape=frame_shape)
    segmentation[1][mask] = 2
    mask = sphere(center=(60, 50, 45), radius=15, shape=frame_shape)
    segmentation[1][mask] = 3

    return segmentation


@pytest.fixture
def graph_3d():
    graph = nx.DiGraph()
    nodes = [
        (
            1,
            {
                NodeAttr.POS.value: [50, 50, 50],
                NodeAttr.TIME.value: 0,
            },
        ),
        (
            2,
            {
                NodeAttr.POS.value: [20, 50, 80],
                NodeAttr.TIME.value: 1,
            },
        ),
        (
            3,
            {
                NodeAttr.POS.value: [60, 50, 45],
                NodeAttr.TIME.value: 1,
            },
        ),
    ]
    edges = [
        (1, 2),
        (1, 3),
    ]
    graph.add_nodes_from(nodes)
    graph.add_edges_from(edges)
    return graph


# Data views specific fixtures


@pytest.fixture(autouse=True)
def reset_tracks_viewer():
    """Reset TracksViewer singleton before and after each test.

    This autouse fixture ensures the TracksViewer singleton is cleared
    before and after each test to avoid state leakage between tests.
    """
    # clear the singleton before test
    if hasattr(TracksViewer, "_instance"):
        del TracksViewer._instance

    # after test, close all viewers and clear again
    yield
    if hasattr(TracksViewer, "_instance"):
        del TracksViewer._instance


@pytest.fixture
def graph_3d_with_division():
    """3D graph with 4 nodes and a division event (node 2 splits into 3 and 4).

    All nodes have AREA attribute set to 1000. This fixture is used for testing
    division-specific behavior in the data_views tests.
    """
    graph = nx.DiGraph()
    nodes = [
        (
            1,
            {
                NodeAttr.POS.value: [50, 50, 50],
                NodeAttr.TIME.value: 0,
                NodeAttr.AREA.value: 1000,
            },
        ),
        (
            2,
            {
                NodeAttr.POS.value: [20, 50, 80],
                NodeAttr.TIME.value: 1,
                NodeAttr.AREA.value: 1000,
            },
        ),
        (
            3,
            {
                NodeAttr.POS.value: [60, 50, 45],
                NodeAttr.TIME.value: 2,
                NodeAttr.AREA.value: 1000,
            },
        ),
        (
            4,
            {
                NodeAttr.POS.value: [40, 70, 60],
                NodeAttr.TIME.value: 2,
                NodeAttr.AREA.value: 1000,
            },
        ),
    ]
    edges = [(1, 2), (2, 3), (2, 4)]
    graph.add_nodes_from(nodes)
    graph.add_edges_from(edges)
    return graph


@pytest.fixture
def segmentation_3d_boxes():
    """3D segmentation with 5 timepoints using box regions (not spheres).

    Contains 4 labeled regions across different timepoints. This differs from
    segmentation_3d which uses sphere shapes and only has 2 timepoints.
    """
    frame_shape = (100, 100, 100)
    total_shape = (5, *frame_shape)
    segmentation = np.zeros(total_shape, dtype="int32")
    segmentation[0, 45:55, 45:55, 45:55] = 1
    segmentation[1, 15:25, 45:55, 75:85] = 2
    segmentation[2, 55:65, 45:55, 40:50] = 3
    segmentation[2, 35:45, 65:75, 55:65] = 4
    return segmentation
