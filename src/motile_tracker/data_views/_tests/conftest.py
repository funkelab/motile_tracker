import networkx as nx
import numpy as np
import pytest
from funtracks.data_model import NodeAttr


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
                NodeAttr.TIME.value: 1,
                NodeAttr.AREA.value: 1000,
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


@pytest.fixture
def segmentation_3d():
    frame_shape = (100, 100, 100)
    total_shape = (5, *frame_shape)
    segmentation = np.zeros(total_shape, dtype="int32")
    segmentation[0, 45:55, 45:55, 45:55] = 1
    segmentation[1, 15:25, 45:55, 75:85] = 2
    segmentation[1, 55:65, 45:55, 40:50] = 3
    return segmentation
