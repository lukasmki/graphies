import networkx as nx


graph = nx.Graph()
graph.add_nodes_from([
    (0, {"symbol": "CH1"}),
    (1, {"symbol": "C@"}),
    (2, {"symbol": "C@@"}),
    (3, {"symbol": "C@H1"}),
    (4, {"symbol": "C@@H1"}),
    (5, {"symbol": "C", "modifiers": ["@", "H1", "+1"]}),
])
graph.add_edges_from([
    (0, 1, {'symbol': '='}),
    (1, 2, {'symbol': '-'}),
    (2, 3, {'symbol': '-'}),
    (3, 4, {'symbol': '-'}),
    (4, 5, {'symbol': '-'}),
    (5, 0, {'symbol': '-'}),
])