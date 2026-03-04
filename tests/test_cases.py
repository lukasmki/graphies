import selfies as sf

from graphies import decode, encode


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

    NOTE: It's the inital link overshoot ([Ring2][N][O]) that is not passed that creates
    the ring between [O] and index 0 [C], see test_case 7
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
    After the [#N], the remaining degree is maxed out and the rest of the
    tokens are passed.
    """
    selfies = "[C][C][O][C][C][O][C][C][O][C][#N][C][O][C][=Branch2]"
    reference = "[C][C][O][C][C][O][C][C][O][C][#N]"
    graph = decode(selfies, grammar="tests/selfies.json")
    graphies = encode(graph, grammar="tests/selfies.json")
    assert graphies == reference


def test_case5():
    """Link resolution
    In selfies and graphies links are handled after the whole sequence is parsed,
    however graphies prioritizes the explicit C=N bond [=N] over the link
    reassignment of the C#C bond
    In graphies, this is parsed [C][=C][=N] with a passed pending link between 0 and 1
    In selfies, this is parsed [C][#C][-N] with N being reassigned.
    """
    # selfies = "[O][C][C][=C][Ring1][C][=N][C][Ring1][Branch1][O][Branch1][#N]"
    # reference = "[O][C][C][#C][N][C][Ring1][Branch1][O][N]"
    selfies = "[C][=C][Ring1][C][=N]"
    # reference = "[C][#C][N]"
    graph = decode(selfies, grammar="tests/selfies.json")
    graphies = encode(graph, grammar="tests/selfies.json")
    assert graphies == "[C][=C][=N]"


def test_case6():
    """Link resolution
    Example expanding upon test case 5,
    here the structure is [C][=S] and branches into [=O] and [=N]
    When the link between [C][=S] is applied, which branch bond order
    should be decremented to make room for the CS triple bond?
    The decision is arbitrary. While it makes sense that
    [=S][Ring1][C] should compile to [#S] (and similarly
    [-S][Ring1][C] should compile to [=S]) and resolve that way,
    it is simpler to treat all ring closures the same. This also prevents the
    expectation that [#C][Ring1][C] is a valid pattern with no quadruple bond.
    """
    selfies = "[C][=S][Ring1][C][=Branch1][C][=O][=N]"
    graph = decode(selfies, grammar="tests/selfies.json")
    graphies = encode(graph, grammar="tests/selfies.json")
    reference = sf.encoder(sf.decoder(selfies))
    assert reference == "[C][#S][=Branch1][C][=O][N]"
    assert graphies == "[C][=S][=Branch1][C][=O][=N]"

def test_case7():
    """Link resolution again, explaining test case 1
    The first link [Ring2][O][C] results in an overshoot that selfies 
    resolves as a link to node 0. Fixing this would confict with test case 1,
    which passes the improperly indexed link. I see this most often like in this
    case where there would never be a valid [Ring2] token in a small molecule (<255 nodes).
    It only appears as an artifact since [Ring2] tokens are also used to index the number 3
    and defining a set of dedicated index tokens would prevent these conficts. So, it
    should just be passed as a malformed link and ignored rather than creating an implied
    link to node 0. Same for the second link which indexes [O] 9 atoms before the [Ring1] token
    """
    selfies = "[C][O][C][Ring2][O][C][C][Ring1][O][C][F][C]"
    reference = "[C][O][C][Ring1][Ring1][C][Ring1][Ring2][C][F]"
    graph = decode(selfies, grammar="tests/selfies.json")
    graphies = encode(graph, grammar="tests/selfies.json")
    assert graphies == "[C][O][C][C][C][F]"