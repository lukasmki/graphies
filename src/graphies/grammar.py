import json
import re
from collections import defaultdict
from functools import cached_property
from itertools import product
from pathlib import Path
from typing import Iterable, Iterator, Pattern, Self

from pydantic import BaseModel, PrivateAttr

from graphies.instances import (
    BranchInstance,
    Edge,
    LinkInstance,
    Modifier,
    Node,
    Structure,
    TokenInstance,
    TokenType,
)
from graphies.utils import TokenTrie, base16


class Grammar(BaseModel):
    nodes: list[Node]
    edges: list[Edge]
    index: list[Structure]
    links: list[Structure]
    branches: list[Structure]
    modifiers: list[Modifier]

    _trie: TokenTrie = PrivateAttr()
    _edge_lookup: dict[str, Edge] = PrivateAttr()
    _node_lookup: dict[str, Node] = PrivateAttr()
    _link_lookup: dict[int, list[Structure]] = PrivateAttr()
    _index_lookup: dict[int, list[Structure]] = PrivateAttr()
    _branch_lookup: dict[int, list[Structure]] = PrivateAttr()

    def model_post_init(self, ctx: object):
        self._build_lookup()

    def _build_lookup(self):
        # symbol-based lookups
        self._edge_lookup = {e.symbol: e for e in self.edges}
        self._node_lookup = {n.symbol: n for n in self.nodes}

        # value-based lookups
        self._link_lookup = {}
        self._index_lookup = {}
        self._branch_lookup = {}
        for link in self.links:
            self._link_lookup.setdefault(link.value, []).append(link)
        for index in self.index:
            self._index_lookup.setdefault(index.value, []).append(index)
        for branch in self.branches:
            self._branch_lookup.setdefault(branch.value, []).append(branch)

        # token prefix tree
        self._trie = TokenTrie(
            unknown=TokenInstance(
                type=TokenType.UNKNOWN, node=None, edge=None, modifiers=[]
            )
        )
        for token in self.all_tokens():
            self._trie.insert(token)

    def tokenize(self, text: str) -> Iterator[list[TokenInstance]]:
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
    def from_file(cls, path: str | Path) -> Self:
        path = Path(path) if isinstance(path, str) else path
        data = json.loads(path.resolve().read_text())
        return cls.model_validate(data)

    @cached_property
    def default_edge(self) -> Edge | None:
        return self._edge_lookup.get("*")

    @cached_property
    def default_node(self) -> Node | None:
        return self._node_lookup.get("*")

    def get_branch(self, size: int) -> BranchInstance:
        "Get a BranchInstance from size of branch"
        digits = base16(size - 1)

        for branch in self.branches:
            if branch.value == len(digits):
                symbol = branch.symbol
                break
        else:
            raise ValueError(f"Could not find branch token with length {len(digits)}")

        indices = []
        for digit in digits:
            index = self._index_lookup.get(digit, None)
            if index is None:
                raise ValueError(f"Could not find index token for digit {digit}")
            indices.append(index[0])

        return BranchInstance(symbol=symbol, value=len(digits), indices=indices)

    def get_link(self, distance: int) -> LinkInstance:
        "Get a LinkInstance from the node distance between the source and the target"
        digits = base16(distance - 1)

        for link in self.links:
            if link.value == len(digits):
                symbol = link.symbol
                break
        else:
            raise ValueError(f"Could not find branch token with length {len(digits)}")

        indices = []
        for digit in digits:
            index = self._index_lookup.get(digit, None)
            if index is None:
                raise ValueError(f"Could not find index token for digit {digit}")
            indices.append(index[0])

        return LinkInstance(symbol=symbol, value=len(digits), indices=indices)

    def modifier_combinations(self, node_symbol: str) -> Iterable[list[Modifier]]:
        by_type: dict[str, list[Modifier]] = defaultdict(list)

        for m in self.modifiers:
            if m.allowed_nodes is None:
                by_type[m.category].append(m)
            elif node_symbol in m.allowed_nodes:
                by_type[m.category].append(m)

        # allow "no modifier" per type
        groups: list[list[Modifier | None]] = [
            [None] + mods for mods in by_type.values()
        ]

        for combo in product(*groups):
            mods: list[Modifier] = [m for m in combo if m is not None]
            if len(mods) > 0:
                yield mods

    def to_alphabet(self) -> dict[str, int]:
        alphabet: dict[str, int] = {}
        i = 0
        for token in self.all_tokens():
            symbol = token.serialize()
            if symbol not in alphabet:
                alphabet[symbol] = i
                i += 1
        return alphabet
