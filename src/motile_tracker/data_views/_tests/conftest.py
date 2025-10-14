import networkx as nx
import numpy as np
import pytest
from funtracks.data_model import NodeAttr

from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


@pytest.fixture(autouse=True)
def reset_tracks_viewer():
    # clear the singleton before test
    if hasattr(TracksViewer, "_instance"):
        del TracksViewer._instance

    # after test, close all viewers and clear again
    yield
    if hasattr(TracksViewer, "_instance"):
        del TracksViewer._instance


@pytest.fixture
def graph_3d():
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
def segmentation_3d():
    frame_shape = (100, 100, 100)
    total_shape = (5, *frame_shape)
    segmentation = np.zeros(total_shape, dtype="int32")
    segmentation[0, 45:55, 45:55, 45:55] = 1
    segmentation[1, 15:25, 45:55, 75:85] = 2
    segmentation[2, 55:65, 45:55, 40:50] = 3
    segmentation[2, 35:45, 65:75, 55:65] = 4
    return segmentation
