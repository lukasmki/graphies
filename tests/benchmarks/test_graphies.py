import pytest
from graphies import Graphies
from graphies.grammar import Grammar

GRAMMAR = Grammar.from_file("tests/selfies.json")
SELFIES = "[C][N][C][C][C][O][C][Ring1][#Branch1][Ring1][Branch1][C][Ring1][#Branch1][C][Ring1][=Branch1][Ring1][Branch1]"


@pytest.mark.benchmark(group="decode")
def test_decode_graphies(benchmark):
    session = Graphies(GRAMMAR)
    benchmark(session.decode, SELFIES)


@pytest.mark.benchmark(group="encode")
def test_encode_graphies(benchmark):
    session = Graphies(GRAMMAR)
    graph = session.decode(SELFIES)
    benchmark(session.encode, graph)


@pytest.mark.benchmark(group="recode")
def test_recode_graphies(benchmark):
    session = Graphies(GRAMMAR)
    benchmark(session.recode, SELFIES)
