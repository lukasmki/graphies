import re
from collections import defaultdict
from collections.abc import Iterator
from functools import cached_property
from itertools import product
from pathlib import Path
from re import Pattern
from typing import Union

from pydantic import BaseModel, PrivateAttr

from graphies.instances import (
    BranchInstance,
    Edge,
    EdgeInstance,
    LinkInstance,
    Modifier,
    Node,
    NodeInstance,
    Structure,
    TokenInstance,
    TokenType,
)
from graphies.utils import TokenTrie, base16


class Grammar(BaseModel):
    """GRAPHIES Grammar

    This subclasses the Pydantic BaseModel and can be constructed in many ways.
    See the `Pydantic Docs <https://docs.pydantic.dev/latest/concepts/models/#model-methods-and-properties>`_ for more information.
    """

    nodes: list[Node]
    edges: list[Edge]
    index: list[Structure]
    links: list[Structure]
    branches: list[Structure]
    modifiers: list[Modifier]

    _trie: TokenTrie = PrivateAttr()
    _edge_lookup: dict[str, Edge] = PrivateAttr()
    _edgeval_lookup: dict[float, list[Edge]] = PrivateAttr()
    _node_lookup: dict[str, Node] = PrivateAttr()
    _link_lookup: dict[int, list[Structure]] = PrivateAttr()
    _index_lookup: dict[int, list[Structure]] = PrivateAttr()
    _branch_lookup: dict[int, list[Structure]] = PrivateAttr()

    def model_post_init(self, ctx: object):
        """Post-init method for building lookups

        :meta private:
        """
        # symbol-based lookups
        self._edge_lookup = {e.symbol: e for e in self.edges}
        self._node_lookup = {n.symbol: n for n in self.nodes}

        # value-based lookups
        self._link_lookup = {}
        self._index_lookup = {}
        self._branch_lookup = {}
        self._edgeval_lookup = {}
        for link in self.links:
            self._link_lookup.setdefault(link.value, []).append(link)
        for index in self.index:
            self._index_lookup.setdefault(index.value, []).append(index)
        for branch in self.branches:
            self._branch_lookup.setdefault(branch.value, []).append(branch)
        for edge in self.edges:
            self._edgeval_lookup.setdefault(edge.weight, []).append(edge)

        # token prefix tree
        self._trie = TokenTrie(
            unknown=TokenInstance(
                type=TokenType.UNKNOWN, node=None, edge=None, modifiers=[]
            )
        )
        for token in self.all_tokens():
            self._trie.insert(token)

    def tokenize(self, text: str) -> Iterator[list[TokenInstance]]:
        """Tokenize a GRAPHIES sequence

        :param text: _description_
        :type text: str
        :yield: _description_
        :rtype: Iterator[list[TokenInstance]]
        """
        TOKEN_RE: Pattern[str] = re.compile(pattern=r"\[[^\]]*\]|[^\[\]\s]")
        for symbol in TOKEN_RE.findall(text):
            yield self._trie.search(symbol)

    def all_tokens(self) -> Iterator[TokenInstance]:
        for index in sorted(self.index, key=(lambda x: x.value)):
            yield TokenInstance(type=TokenType.INDEX, node=index)

        for edge in self.edges:
            for branch in sorted(self.branches, key=(lambda x: x.value)):
                yield TokenInstance(type=TokenType.BRANCH, node=branch, edge=edge)

            for link in sorted(self.links, key=(lambda x: x.value)):
                yield TokenInstance(type=TokenType.LINK, node=link, edge=edge)

            for node in self.nodes:
                if node.symbol == "*":
                    continue
                yield TokenInstance(
                    type=TokenType.NODE, node=node, edge=edge, modifiers=[]
                )
                for mods in self.modifier_combinations(node.symbol):
                    token = TokenInstance(
                        type=TokenType.NODE, node=node, edge=edge, modifiers=mods
                    )
                    yield token

    @classmethod
    def from_file(cls, path: Union[str, Path, "Grammar"]) -> "Grammar":
        if isinstance(path, Grammar):
            return path
        elif isinstance(path, str | Path):
            return cls.model_validate_json(Path(path).read_text())
        else:
            raise TypeError(f"Expected Grammar, str, or Path; got {type(path)!r}")

    @cached_property
    def default_edge(self) -> Edge | None:
        return self._edge_lookup.get("*")

    @cached_property
    def default_node(self) -> Node | None:
        return self._node_lookup.get("*")

    def get_node(self, symbol: str) -> NodeInstance:
        "Get NodeInstance from symbol not including edge/modifier symbols"
        node = self._node_lookup.get(symbol, self.default_node)
        if node is None:
            raise ValueError(f"Could not find node with symbol {symbol}")
        return NodeInstance(
            symbol=node.symbol, degree=node.degree, data=node.data, modifiers=[]
        )

    def get_edge(self, weight: float, symbol: str) -> EdgeInstance:
        "Get EdgeInstance from symbol and weight of edge"
        if (
            (self.default_edge is not None)
            and (weight == self.default_edge.weight)
            and (symbol == self.default_edge.symbol)
        ):
            return EdgeInstance(
                symbol=self.default_edge.symbol,
                weight=self.default_edge.weight,
                data=self.default_edge.data,
            )

        # lookup by symbol first
        edge = self._edge_lookup.get(symbol, None)
        if edge is not None and edge.weight == weight:
            return EdgeInstance(symbol=edge.symbol, weight=edge.weight, data=edge.data)

        # if not found or weight is wrong get edge by weight
        edges = self._edgeval_lookup.get(weight, None)
        if edges is None:
            raise ValueError(f"Could not find edge token with weight {weight}")

        # attempt to match symbol again
        for edge in edges:
            if edge.symbol == symbol:
                return EdgeInstance(
                    symbol=edge.symbol, weight=edge.weight, data=edge.data
                )
        else:  # return first match
            edge = edges[0]
        return EdgeInstance(symbol=edge.symbol, weight=edge.weight, data=edge.data)

    def get_branch(self, size: int) -> BranchInstance:
        "Get a BranchInstance from size of branch"
        indices = self.get_indices(size - 1)

        branches = self._branch_lookup.get(len(indices), None)
        if branches is None:
            raise ValueError(f"Could not find branch token with length {len(indices)}")
        branch = branches[0]

        return BranchInstance(symbol=branch.symbol, value=branch.value, indices=indices)

    def get_link(self, distance: int) -> LinkInstance:
        "Get a LinkInstance from the node distance between the source and the target"
        indices = self.get_indices(distance - 1)

        links = self._link_lookup.get(len(indices), None)
        if links is None:
            raise ValueError(f"Could not find branch token with length {len(indices)}")
        link = links[0]

        return LinkInstance(symbol=link.symbol, value=link.value, indices=indices)

    def get_indices(self, value: int) -> list[Structure]:
        "Convert a base10 value to a base16 sequence of index tokens"
        digits = base16(value)
        indices: list[Structure] = []
        for digit in digits:
            index = self._index_lookup.get(digit, None)
            if index is None:
                raise ValueError(f"Could not find index token for digit {digit}")
            indices.append(index[0])
        return indices

    def modifier_combinations(self, node_symbol: str) -> Iterator[list[Modifier]]:
        by_type: dict[str, list[Modifier]] = defaultdict(list)

        for m in self.modifiers:
            # check if explicitly not allowed
            if m.disallowed_nodes is not None and node_symbol in m.disallowed_nodes:
                continue

            # then check if allowed
            if m.allowed_nodes is None or node_symbol in m.allowed_nodes:
                by_type[m.category].append(m)

        # allow "no modifier" per type
        groups: list[list[Modifier | None]] = [
            [None] + mods for mods in by_type.values()
        ]

        for combo in product(*groups):
            mods: list[Modifier] = [m for m in combo if m is not None]
            if len(mods) > 0:
                yield mods

    def to_vocab(self) -> dict[str, int]:
        vocab: dict[str, int] = {}
        i = 0
        for token in self.all_tokens():
            symbol = token.serialize()
            if symbol not in vocab:
                vocab[symbol] = i
                i += 1
        return vocab
