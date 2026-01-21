import networkx as nx
from motile import TrackGraph
from networkx.utils import graphs_equal

from motile_tracker.motile.backend.graph_to_nx import graph_to_nx


def test_graph_to_nx(graph_3d: nx.DiGraph):
    track_graph = TrackGraph(nx_graph=graph_3d, frame_attribute="time")
    nx_graph = graph_to_nx(track_graph)
    assert graphs_equal(graph_3d, nx_graph)
