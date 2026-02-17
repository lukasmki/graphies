import json
from collections import defaultdict
from enum import Enum
from itertools import product
from pathlib import Path
from typing import Any, Iterable, Self

from pydantic import BaseModel


class TokenType(str, Enum):
    NODE = "NODE"
    BRANCH = "BRANCH"
    LINK = "LINK"
    INDEX = "INDEX"
    UNKNOWN = "UNKNOWN"


class Node(BaseModel):
    symbol: str
    degree: int | float
    data: dict[str, Any] | None = None


class Edge(BaseModel):
    symbol: str
    weight: int | float
    data: dict[str, Any] | None = None


class Modifier(BaseModel):
    category: str
    symbol: str
    weight: int | float
    data: dict[str, Any] | None = None
    allowed_nodes: list[str] | None = None
    exceptions: dict[str, Any] | None = None


class Structure(BaseModel):
    symbol: str
    value: int


class Grammar(BaseModel):
    nodes: list[Node]
    edges: list[Edge]
    index: list[Structure]
    links: list[Structure]
    branches: list[Structure]
    modifiers: list[Modifier]

    @classmethod
    def from_file(cls, path: str | Path) -> Self:
        path = Path(path) if isinstance(path, str) else path
        data = json.loads(path.resolve().read_text())
        return cls.model_validate(data)

    @property
    def default_edge(self):
        for edge in self.edges:
            if edge.symbol == "*":
                return edge
        return None

    @property
    def default_node(self):
        for node in self.nodes:
            if node.symbol == "*":
                return node
        return None

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
        # index symbols
        for index in sorted(self.index, key=(lambda x: x.value)):
            alphabet[index.symbol] = i
            i += 1

        # branch symbols
        for edge in self.edges:
            edge_symbol = edge.symbol if edge.symbol != "*" else ""
            for branch in self.branches:
                alphabet[f"{edge_symbol}{branch.symbol}"] = i
                i += 1

        # link symbols
        for edge in self.edges:
            edge_symbol = edge.symbol if edge.symbol != "*" else ""
            for link in self.links:
                alphabet[f"{edge_symbol}{link.symbol}"] = i
                i += 1

        # node symbols
        for edge in self.edges:
            edge_symbol = edge.symbol if edge.symbol != "*" else ""
            for node in self.nodes:
                if node.symbol == "*":
                    continue
                base = f"{edge_symbol}{node.symbol}"
                alphabet[base] = i
                i += 1
                for mods in self.modifier_combinations(node.symbol):
                    suffix = "".join(m.symbol for m in mods)
                    alphabet[f"{base}{suffix}"] = i
                    i += 1
        return alphabet
