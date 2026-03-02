import selfies as sf

from graphies import decode, encode


def test_ring():
    smiles = "c1ccccc1"
    selfies = sf.encoder(smiles)
    graph = decode(selfies, grammar="tests/selfies.json")
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
    graph = decode(selfies, grammar="tests/selfies.json")
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
    graph = decode(selfies, grammar="tests/selfies.json")
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
    graph = decode(selfies, grammar="tests/selfies.json")
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


def test_case1():
    """Tests link resolution
    The first link creates an invalid link target
    The second link creates a link between C and O (index 0 and 3)
    The third link would exceed the degree of O and is passed.

    NOTE: selfies gives this: [C][C][C][O][Ring1][Ring2]
    I'm not sure why selfies decodes this into a ring between
    the [O] and index 0 [C]. A [Ring1][C] sequence should create a link
    between the previous atom and index = m - ([C] + 1) atom before it.
    Unless selfies has a special rule for this, it isn't consistent with
    the ring indexing.
    """

    selfies = "[C][C][C][O][Ring2][N][O][Ring1][C][Ring1][C]"
    graph = decode(selfies, grammar="tests/selfies.json")
    graphies = encode(graph, grammar="tests/selfies.json")
    reference = "[C][C][C][=O]"
    assert graphies == reference


def test_case2():
    """Link additivity
    The link [Ring2][C][C] creates a link between 5 and 4
    A single bond already exists so it should add the weight of the link
    and resolve to a weight=2 bond
    """
    selfies = "[O][C][C][C][C][C][Ring2][C][C][O][C]"
    reference = "[O][C][C][C][C][=C][O][C]"
    graph = decode(selfies, grammar="tests/selfies.json")
    graphies = encode(graph, grammar="tests/selfies.json")
    assert graphies == reference


def test_case3():
    """Node level edge weight reduction
    Each of the trailing [=O] tokens should get their edge weight reduced
    """
    selfies = "[C][C][C][C][C][C][O][O][=O][=O][=O]"
    reference = "[C][C][C][C][C][C][O][O][O][O][O]"
    graph = decode(selfies, grammar="tests/selfies.json")
    graphies = encode(graph, grammar="tests/selfies.json")
    assert graphies == reference

def test_case4():
    """Node level max degree reached
    After the [#N], the remaining degree is maxed out.
    """
    selfies = "[C][C][O][C][C][O][C][C][O][C][#N][C][O][C][=Branch2]"
    reference = "[C][C][O][C][C][O][C][C][O][C][#N]"
    graph = decode(selfies, grammar="tests/selfies.json")
    graphies = encode(graph, grammar="tests/selfies.json")
    assert graphies == reference
