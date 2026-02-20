from graphies import decode, encode
from graphies.grammar import Grammar

GRAMMAR = Grammar.from_file("tests/selfies.json")
SELFIES = "[C][N][C][C][C][O][C][Ring1][#Branch1][Ring1][Branch1][C][Ring1][#Branch1][C][Ring1][=Branch1][Ring1][Branch1]"
GRAPH = decode(SELFIES, GRAMMAR)


def test_roundtrip(benchmark):
    def decode_encode(selfies: str, grammar: Grammar):
        graph = decode(selfies, grammar)
        graphies = encode(graph, grammar)

    benchmark(decode_encode, SELFIES, GRAMMAR)


def test_decode(benchmark):
    benchmark(decode, SELFIES, GRAMMAR)


def test_encode(benchmark):
    benchmark(encode, GRAPH, GRAMMAR)
