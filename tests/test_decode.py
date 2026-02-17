import selfies as sf

from metaselfies import decode


def test_ring():
    smiles = "c1ccccc1"
    selfies = sf.encoder(smiles)
    graph = decode(selfies, grammar="examples/selfies.json")
    bonds = [
        (0, 1, {"weight": 2}),
        (0, 5, {"weight": 1}),
        (1, 2, {"weight": 1}),
        (2, 3, {"weight": 2}),
        (3, 4, {"weight": 1}),
        (4, 5, {"weight": 2}),
    ]
    for u, v, d in bonds:
        assert d["weight"] == graph.edges[u, v]["weight"]


def test_branch():
    smiles = "C(C(C)C)C"
    selfies = sf.encoder(smiles)
    graph = decode(selfies, grammar="examples/selfies.json")
    bonds = [
        (0, 1, {"weight": 1}),
        (0, 4, {"weight": 1}),
        (1, 2, {"weight": 1}),
        (1, 3, {"weight": 1}),
    ]
    for u, v, d in bonds:
        assert d["weight"] == graph.edges[u, v]["weight"]


def test_ring_in_branch():
    smiles = "C1(CCC1)C"
    selfies = sf.encoder(smiles)
    graph = decode(selfies, grammar="examples/selfies.json")
    bonds = [
        (0, 1, {"weight": 1}),
        (1, 2, {"weight": 1}),
        (2, 3, {"weight": 1}),
        (0, 3, {"weight": 1}),
        (0, 4, {"weight": 1}),
    ]
    for u, v, d in bonds:
        assert d["weight"] == graph.edges[u, v]["weight"]


def test_ring_in_nestedbranch():
    smiles = "C1(CC(CC1))C"
    selfies = sf.encoder(smiles)
    graph = decode(selfies, grammar="examples/selfies.json")
    bonds = [
        (0, 1, {"weight": 1}),
        (1, 2, {"weight": 1}),
        (2, 3, {"weight": 1}),
        (3, 4, {"weight": 1}),
        (0, 4, {"weight": 1}),
        (0, 5, {"weight": 1}),
    ]
    for u, v, d in bonds:
        assert d["weight"] == graph.edges[u, v]["weight"]
