import networkx as nx
import numpy as np
import pytest
from funtracks.data_model import SolutionTracks
from funtracks.import_export import export_to_csv
from skimage.draw import disk


@pytest.fixture
def graph_3d():
    graph = nx.DiGraph()
    nodes = [
        (
            1,
            {
                "pos": [50, 50, 50],
                "time": 0,
            },
        ),
        (
            2,
            {
                "pos": [20, 50, 80],
                "time": 1,
            },
        ),
        (
            3,
            {
                "pos": [60, 50, 45],
                "time": 1,
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
                "pos": [50, 50],
                "time": 0,
                "area": 1245,
                "track_id": 1,
            },
        ),
        (
            2,
            {
                "pos": [20, 80],
                "time": 1,
                "track_id": 2,
                "area": 305,
            },
        ),
        (
            3,
            {
                "pos": [60, 45],
                "time": 1,
                "area": 697,
                "track_id": 3,
            },
        ),
        (
            4,
            {
                "pos": [1.5, 1.5],
                "time": 2,
                "area": 16,
                "track_id": 3,
            },
        ),
        (
            5,
            {
                "pos": [1.5, 1.5],
                "time": 4,
                "area": 16,
                "track_id": 3,
            },
        ),
        # unconnected node
        (
            6,
            {
                "pos": [97.5, 97.5],
                "time": 4,
                "area": 16,
                "track_id": 5,
            },
        ),
    ]
    edges = [
        (1, 2, {"iou": 0.0}),
        (1, 3, {"iou": 0.395}),
        (
            3,
            4,
            {"iou": 0.0},
        ),
        (
            4,
            5,
            {"iou": 1.0},
        ),
    ]
    graph.add_nodes_from(nodes)
    graph.add_edges_from(edges)
    return graph


def test_export_solution_to_csv(graph_2d, graph_3d, tmp_path):
    tracks = SolutionTracks(graph_2d, ndim=3)
    temp_file = tmp_path / "test_export_2d.csv"
    export_to_csv(tracks, temp_file)
    with open(temp_file) as f:
        lines = f.readlines()

    assert len(lines) == tracks.graph.number_of_nodes() + 1  # add header

    # funtracks exports standard column names by default
    header = ["t", "y", "x", "id", "parent_id", "track_id"]
    assert lines[0].strip().split(",") == header
    # Row format: t, y, x, id, parent_id, track_id
    line1 = ["0", "50", "50", "1", "", "1"]
    assert lines[1].strip().split(",") == line1

    tracks = SolutionTracks(graph_3d, ndim=4)
    temp_file = tmp_path / "test_export_3d.csv"
    export_to_csv(tracks, temp_file)
    with open(temp_file) as f:
        lines = f.readlines()

    assert len(lines) == tracks.graph.number_of_nodes() + 1  # add header

    # funtracks exports standard column names by default
    header = ["t", "z", "y", "x", "id", "parent_id", "track_id"]
    assert lines[0].strip().split(",") == header
