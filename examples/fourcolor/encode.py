from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
from fourcolor import draw_colored_graph, four_color_graph, random_planar_graph

from graphies import decode, encode
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


if __name__ == "__main__":
    # generate a random four-colored graph
    planar = random_planar_graph(n=26)
    colored = four_color_graph(planar)
    graph = format_colored_graph(colored)
    graphies = encode(graph, root / "fourcolor.json")
    print("GRAPHIES", graphies)

    # re-encoded graph
    regraph = decode(graphies, root / "fourcolor.json")
    regraphies = encode(regraph, root / "fourcolor.json")
    print("ISOMORPHIC", nx.is_isomorphic(graph, regraph))

    # plot
    fig, ax = plt.subplots(1, 2, figsize=(16, 8))
    draw_colored_graph(graph, ax[0], title="Original")
    draw_colored_graph(regraph, ax[1], title="Encoded")
    fig.tight_layout()
    plt.show()
