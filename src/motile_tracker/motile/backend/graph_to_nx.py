import networkx as nx
from motile import TrackGraph


def graph_to_nx(graph: TrackGraph) -> nx.DiGraph:
    """Convert a motile TrackGraph into a networkx DiGraph.

    Args:
        graph (TrackGraph): TrackGraph to be converted to networkx

    Returns:
        nx.DiGraph: Directed networkx graph with same nodes, edges, and attributes.
    """
    nx_graph = nx.DiGraph()
    nodes_list = list(graph.nodes.items())
    nx_graph.add_nodes_from(nodes_list)
    edges_list = [
        (edge_id[0], edge_id[1], data) for edge_id, data in graph.edges.items()
    ]
    nx_graph.add_edges_from(edges_list)
    return nx_graph
