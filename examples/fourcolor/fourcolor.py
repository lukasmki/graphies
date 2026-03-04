import random

import matplotlib.pyplot as plt
import networkx as nx


def random_planar_graph(n: int = 10, seed: int | None = None) -> nx.Graph:
    if seed is not None:
        random.seed(seed)

    G = nx.Graph()
    G.add_nodes_from(range(n))

    # Random spanning tree
    nodes = list(range(n))
    random.shuffle(nodes)
    for i in range(1, n):
        G.add_edge(nodes[i - 1], nodes[i])

    # Add random planarity preserving edges
    all_edges = [
        (u, v) for u in range(n) for v in range(u + 1, n) if not G.has_edge(u, v)
    ]
    for u, v in all_edges:
        G.add_edge(u, v)
        if not nx.is_planar(G):
            G.remove_edge(u, v)

    return G


def four_color_graph(G: nx.Graph) -> nx.Graph:
    n = G.number_of_nodes()
    nodes = list(G.nodes())
    coloring = {}

    def is_valid(node, color):
        return all(coloring.get(neighbor) != color for neighbor in G.neighbors(node))

    def backtrack(idx):
        if idx == n:
            return True
        node = nodes[idx]
        for color in range(4):
            if is_valid(node, color):
                coloring[node] = color
                if backtrack(idx + 1):
                    return True
                del coloring[node]
        return False

    if not backtrack(0):
        raise ValueError("Graph could not be 4-colored — ensure it is planar.")

    nx.set_node_attributes(G, coloring, "color")
    return G


def draw_colored_graph(G: nx.Graph, title="") -> None:
    color_map = {0: "#E74C3C", 1: "#3498DB", 2: "#2ECC71", 3: "#F39C12"}

    node_colors = [color_map[G.nodes[n]["color"]] for n in G.nodes()]

    try:
        pos = nx.planar_layout(G)
    except nx.NetworkXException:
        pos = nx.spring_layout(G, seed=42)

    fig, ax = plt.subplots(1, 1, figsize=(10, 7))
    nx.draw_networkx(
        G,
        pos,
        node_color=node_colors,
        with_labels=True,
        node_size=800,
        font_color="white",
        font_weight="bold",
        font_size=12,
        edge_color="#95A5A6",
        width=1.5,
        ax=ax,
    )

    # Legend
    handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=hex_color,
            markersize=12,
            label=f"Color {i}",
        )
        for i, hex_color in color_map.items()
        if i in set(nx.get_node_attributes(G, "color").values())
    ]
    ax.legend(handles=handles, loc="upper left", framealpha=0.9)
    ax.set_title(f"Four-Colored Planar Graph\n{title}", fontsize=14, fontweight="bold")
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    graph = random_planar_graph()
    colored = four_color_graph(graph)
    draw_colored_graph(colored)
