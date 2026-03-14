from graphies.instances import TokenInstance


def base16(n: int) -> list[int]:
    if n == 0:
        return [0]
    elif n > 0:
        digits: list[int] = []
        while n > 0:
            digits.insert(0, n % 16)
            n //= 16
        return digits
    else:
        raise ValueError("n cannot be negative")


class _TrieNode:
    __slots__ = ("children", "values")

    def __init__(self):
        self.children: dict[str, _TrieNode] = {}
        self.values: list[TokenInstance] = []


class TokenTrie:
    def __init__(self, unknown: TokenInstance):
        self._root = _TrieNode()
        self._unknown = unknown

    def insert(self, token: TokenInstance) -> None:
        """
        Insert a TokenInstance into the trie using its serialized symbol.
        """
        symbol = token.serialize()

        # Expect bracketed format: "[...]" → strip brackets
        if not (symbol.startswith("[") and symbol.endswith("]")):
            raise ValueError(f"Invalid token symbol: {symbol}")
        content = symbol[1:-1]

        node = self._root
        for char in content:
            node = node.children.setdefault(char, _TrieNode())

        node.values.append(token)

    def search(self, symbol: str) -> list[TokenInstance]:
        """
        Search for exact content match using its serialized symbol
        Returns list of TokenInstance or [unknown].
        """
        if not (symbol.startswith("[") and symbol.endswith("]")):
            raise ValueError(f"Invalid token symbol: {symbol}")
        content = symbol[1:-1]

        node = self._root

        for char in content:
            if char not in node.children:
                return [self._unknown]
            node = node.children[char]

        return node.values if node.values else [self._unknown]
