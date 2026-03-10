from graphies import decode, encode
from graphies.decoder import IndexCounter
from graphies.grammar import Grammar
from graphies.instances import EdgeInstance, TokenInstance, TokenType
from graphies.utils import base16

GRAMMAR = Grammar.from_file("tests/fourcolor.json")


def test_digits():
    nums = [10, 15, 16 + 5, 255]
    for num in nums:
        digits = base16(num)
        print(num, digits)


def test_base10_to_base16():
    nums = [10, 15, 16 + 5, 255]
    for num in nums:
        indices = GRAMMAR.get_indices(num)
        print(num, indices)


def test_base16_to_base10(num=21):
    counter = IndexCounter(
        kind="link",
        source=0,
        edge=EdgeInstance(symbol="*", weight=1),
        remaining=2,
    )
    indices = GRAMMAR.get_indices(num)
    for index in indices:
        counter.consume(TokenInstance(TokenType.INDEX, node=index))
    assert counter.value == num


def test_ordering():
    """test the ordering of selfies vs graphies index tokens
    index token values should be in order
    19 = [3, 1] = 3*(16^0) + 1*(16^1)
    """
    print()
    graphies = (
        "[R][R][R][R][R][R][R][R][R][R][R][R][R][R][R][R][R][R][R][R][R][Link2][3][1]"
    )
    graph = decode(graphies, GRAMMAR)
    regraphies = encode(graph, GRAMMAR)
    assert graphies == regraphies
