from graphies import encode
from pathlib import Path

import networkx as nx
from fourcolor import four_color_graph, random_planar_graph, draw_colored_graph

from graphies.instances import EdgeInstance, NodeInstance

root = Path(__file__).parent.resolve()


def format_colored_graph(G: nx.Graph):
    graph = G.copy()
    nodes_by_color = {
        0: NodeInstance(symbol="R", degree=24).model_dump(),
        1: NodeInstance(symbol="B", degree=24).model_dump(),
        2: NodeInstance(symbol="G", degree=24).model_dump(),
        3: NodeInstance(symbol="O", degree=24).model_dump(),
    }

    # set node data
    node_attrs = {}
    colors = nx.get_node_attributes(graph, name="color")
    for node_id, color in colors.items():
        node_attrs[node_id] = nodes_by_color[color]
    nx.set_node_attributes(graph, node_attrs)

    # set edge data
    edge_attrs = {}
    for edge in graph.edges:
        edge_attrs[edge] = EdgeInstance(symbol="*", weight=1)
    nx.set_edge_attributes(graph, edge_attrs)
    return graph


# generate a random four-colored graph
planar = random_planar_graph(n=10)
colored = four_color_graph(planar)
graph = format_colored_graph(colored)

graphies = encode(graph, root / "fourcolor.json")
draw_colored_graph(graph, title=f"'{graphies}'")

print("GRAPHIES", graphies)
