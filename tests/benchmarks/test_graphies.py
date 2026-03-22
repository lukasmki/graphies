import pytest

from graphies import Graphies

SESSION = Graphies("tests/selfies.json")
SELFIES = "[C][N][C][C][C][O][C][Ring1][#Branch1][Ring1][Branch1][C][Ring1][#Branch1][C][Ring1][=Branch1][Ring1][Branch1]"


@pytest.mark.benchmark(group="decode")
def test_decode_graphies(benchmark):
    benchmark(SESSION.decode, SELFIES)


@pytest.mark.benchmark(group="encode")
def test_encode_graphies(benchmark):
    graph = SESSION.decode(SELFIES)
    benchmark(SESSION.encode, graph)


@pytest.mark.benchmark(group="recode")
def test_recode_graphies(benchmark):
    benchmark(SESSION.recode, SELFIES)
