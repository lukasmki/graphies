from graphies.grammar import Grammar


def test_load_from_file():
    grammar = Grammar.from_file("examples/selfies.json")
