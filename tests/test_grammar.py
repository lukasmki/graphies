from graphies.grammar import Grammar
from graphies.instances import TokenType


def test_load_from_file():
    grammar = Grammar.from_file("tests/selfies.json")


def test_trie_search():
    grammar = Grammar.from_file("tests/selfies.json")
    interpretations = grammar._trie.search("[C]")
    assert set(i.type for i in interpretations) == set(
        [TokenType.INDEX, TokenType.NODE]
    )


def test_tokenize():
    grammar = Grammar.from_file("tests/selfies.json")

    all_tokens = grammar.all_tokens()
    for token in all_tokens:
        symbol = token.serialize()
        candidates = grammar._trie.search(symbol)
        for tok in candidates:
            assert tok.symbol == symbol
