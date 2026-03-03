import random

import networkx as nx

from graphies import Encoder, Grammar, encode

GRAMMAR = Grammar.from_file("tests/selfies.json")


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
    graphies = encode(graph, grammar="tests/selfies.json")
    assert graphies == "[C][=C][-C][=C][-C][=C][-Ring1][=Branch1]"


def test_source():
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
    encoder = Encoder(GRAMMAR)
    graphies = encoder.encode(graph, source=1)
    assert graphies == "[C][=C][-C][=C][-C][=C][-Ring1][=Branch1]"


def test_randomized():
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
    nodeids = list(graph.nodes)
    random.shuffle(nodeids)
    graph = nx.relabel_nodes(graph, {n: nodeids[i] for i, n in enumerate(graph.nodes)})

    encoder = Encoder(GRAMMAR)
    graphies = encoder.encode(graph, source=0)
    assert (graphies == "[C][=C][-C][=C][-C][=C][-Ring1][=Branch1]") or (
        graphies == "[C][-C][=C][-C][=C][-C][=Ring1][=Branch1]"
    )


def test_named():
    graph = nx.Graph()
    graph.add_nodes_from(
        [
            ("A", {"symbol": "C", "degree": 4, "modifiers": []}),
            ("B", {"symbol": "C", "degree": 4, "modifiers": []}),
            ("C", {"symbol": "C", "degree": 4, "modifiers": []}),
            ("D", {"symbol": "C", "degree": 4, "modifiers": []}),
            ("E", {"symbol": "C", "degree": 4, "modifiers": []}),
            ("F", {"symbol": "C", "degree": 4, "modifiers": []}),
        ]
    )
    graph.add_edges_from(
        [
            ("A", "B", {"symbol": "=", "weight": 2}),
            ("B", "C", {"symbol": "-", "weight": 1}),
            ("C", "D", {"symbol": "=", "weight": 2}),
            ("D", "E", {"symbol": "-", "weight": 1}),
            ("E", "F", {"symbol": "=", "weight": 2}),
            ("F", "A", {"symbol": "-", "weight": 1}),
        ]
    )
    encoder = Encoder(GRAMMAR)
    graphies = encoder.encode(graph, source="A")
    assert (graphies == "[C][=C][-C][=C][-C][=C][-Ring1][=Branch1]") or (
        graphies == "[C][-C][=C][-C][=C][-C][=Ring1][=Branch1]"
    )


# def test_process_edges():
#     graph = nx.Graph()
#     graph.add_nodes_from(
#         [
#             (0, {"symbol": "C", "degree": 4, "modifiers": []}),
#             (1, {"symbol": "C", "degree": 4, "modifiers": []}),
#             (2, {"symbol": "C", "degree": 4, "modifiers": []}),
#             (3, {"symbol": "C", "degree": 4, "modifiers": []}),
#             (4, {"symbol": "C", "degree": 4, "modifiers": []}),
#             (5, {"symbol": "C", "degree": 4, "modifiers": []}),
#         ]
#     )
#     graph.add_edges_from(
#         [
#             # both symbol and weight (symbol prioritized)
#             (0, 1, {"symbol": "=", "weight": 2}),
#             (1, 2, {"symbol": "-", "weight": 2}),
#             # only symbol
#             (2, 3, {"symbol": "="}),
#             (3, 4, {"symbol": "-"}),
#             # only weight
#             (4, 5, {"weight": 2}),
#             (5, 0, {"weight": 1}),
#         ]
#     )
#     _ = encode(graph, grammar="tests/selfies.json")


def test_process_nodes():
    graph = nx.Graph()
    graph.add_nodes_from(
        [
            (0, {"symbol": "C", "degree": 4}),
            (1, {"symbol": "C", "degree": 4}),
            (2, {"symbol": "C", "degree": 4}),
            (3, {"symbol": "C", "degree": 4}),
            (4, {"symbol": "C", "degree": 4}),
            (5, {"symbol": "C", "degree": 4}),
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
