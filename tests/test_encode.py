import networkx as nx

from graphies import encode


def test_process():
    graph = nx.Graph()
    graph.add_nodes_from(
        [
            (0, {"symbol": "C", "degree": 4, "modifiers": []}),
            (1, {"symbol": "C", "degree": 4, "modifiers": []}),
            (2, {"symbol": "C", "degree": 4, "modifiers": []}),
            (3, {"symbol": "C", "degree": 4, "modifiers": []}),
            (4, {"symbol": "C", "degree": 4, "modifiers": []}),
            (5, {"symbol": "C", "degree": 4, "modifiers": []}),
        ]
    )
    graph.add_edges_from(
        [
            (0, 1, {"symbol": "=", "weight": 2}),
            (1, 2, {"symbol": "-", "weight": 1}),
            (2, 3, {"symbol": "=", "weight": 2}),
            (3, 4, {"symbol": "-", "weight": 1}),
            (4, 5, {"symbol": "=", "weight": 2}),
            (5, 0, {"symbol": "-", "weight": 1}),
        ]
    )
    _ = encode(graph, grammar="tests/selfies.json")


def test_process_edges():
    graph = nx.Graph()
    graph.add_nodes_from(
        [
            (0, {"symbol": "C", "degree": 4, "modifiers": []}),
            (1, {"symbol": "C", "degree": 4, "modifiers": []}),
            (2, {"symbol": "C", "degree": 4, "modifiers": []}),
            (3, {"symbol": "C", "degree": 4, "modifiers": []}),
            (4, {"symbol": "C", "degree": 4, "modifiers": []}),
            (5, {"symbol": "C", "degree": 4, "modifiers": []}),
        ]
    )
    graph.add_edges_from(
        [
            # both symbol and weight (symbol prioritized)
            (0, 1, {"symbol": "=", "weight": 2}),
            (1, 2, {"symbol": "-", "weight": 2}),
            # only symbol
            (2, 3, {"symbol": "="}),
            (3, 4, {"symbol": "-"}),
            # only weight
            (4, 5, {"weight": 2}),
            (5, 0, {"weight": 1}),
        ]
    )
    _ = encode(graph, grammar="tests/selfies.json")


def test_process_nodes():
    graph = nx.Graph()
    graph.add_nodes_from(
        [
            (0, {"symbol": "C", "degree": 4}),
            (1, {"symbol": "C", "degree": 4, "modifiers": []}),
            (2, {"symbol": "C", "degree": 4, "modifiers": []}),
            (3, {"symbol": "C", "degree": 4, "modifiers": []}),
            (4, {"symbol": "C", "degree": 4, "modifiers": []}),
            (5, {"symbol": "C", "degree": 4, "modifiers": []}),
        ]
    )
    graph.add_edges_from(
        [
            (0, 1, {"symbol": "=", "weight": 2}),
            (1, 2, {"symbol": "-", "weight": 1}),
            (2, 3, {"symbol": "=", "weight": 2}),
            (3, 4, {"symbol": "-", "weight": 1}),
            (4, 5, {"symbol": "=", "weight": 2}),
            (5, 0, {"symbol": "-", "weight": 1}),
        ]
    )
    _ = encode(graph, grammar="tests/selfies.json")
