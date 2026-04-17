from typing import Any

from networkx import DiGraph

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


def reverse_tree(T: DiGraph) -> DiGraph:
    """Reverses a DFS tree to end at its source

    Args:
        T (DiGraph): DFS tree

    Returns:
        DiGraph: Reversed DFS tree
    """
    # The root of a DFS tree is the unique node with no incoming edges.
    source = next(n for n, d in T.in_degree() if d == 0)

    def find_longest_path(node: Any) -> list[Any]:
        # Recursively pick the deepest child branch; base case is a leaf.
        children = list(T.successors(node))
        if not children:
            return [node]
        return [node] + max(
            [find_longest_path(c) for c in children], key=lambda x: len(x)
        )

    # longest_path = [source, p1, p2, ..., leaf]. The leaf becomes the new root
    # and source becomes the last node on the longest branch in the reversed tree.
    longest_path = find_longest_path(source)
    # Map each path node to its position so dfs_build can navigate the path by index.
    path_index = {node: i for i, node in enumerate(longest_path)}

    R = DiGraph()

    def add_subtree(node):
        # Copy an off-path subtree from T into R unchanged (preserves original structure).
        for child in T.successors(node):
            R.add_edge(node, child)
            add_subtree(child)

    def dfs_build(node):
        idx = path_index[node]
        if idx == 0:
            # source is a leaf in the new tree — stop recursion here so it is inserted last.
            return
        # The original path successor of this node points deeper into T; exclude it
        # so only true off-path branches are treated as side children in R.
        path_successor = longest_path[idx + 1] if idx + 1 < len(longest_path) else None
        off_path = [c for c in T.successors(node) if c != path_successor]
        if idx == 1:
            # p1 (the first path node after source) inherits source's own off-path children.
            # This keeps source childless in R, ensuring it is inserted last.
            off_path += [c for c in T.successors(source) if c != node]
        # Add off-path subtrees before continuing down the reversed path so that
        # DFS insertion order visits all side branches before reaching source.
        for child in off_path:
            R.add_edge(node, child)
            add_subtree(child)
        # Walk one step closer to source along the reversed main path.
        path_child = longest_path[idx - 1]
        R.add_edge(node, path_child)
        dfs_build(path_child)

    # Seed R with the new root (the original leaf) and build outward toward source.
    R.add_node(longest_path[-1])
    dfs_build(longest_path[-1])
    return R
