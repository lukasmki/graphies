import networkx as nx


graph = nx.Graph()
graph.add_nodes_from(
    [
        (0, {"symbol": "C"}),
        (1, {"symbol": "C"}),
        (2, {"symbol": "C"}),
        (3, {"symbol": "C"}),
        (4, {"symbol": "C", "modifiers": ["@@", "-1"]}),
        (5, {"symbol": "C", "modifiers": ["@", "H1", "+1"]}),
    ]
)
graph.add_edges_from(
    [
        (0, 1, {"symbol": "="}),
        (1, 2, {"symbol": "-"}),
        (2, 3, {"symbol": "-", "weight": 2}),
        (3, 4, {"symbol": "-"}),
        (4, 5, {"symbol": "-"}),
        (5, 0, {"weight": 1}),
    ]
)

for node in graph.nodes(data=True):
    print(node)

for edge in graph.edges(data=True):
    print(edge)
