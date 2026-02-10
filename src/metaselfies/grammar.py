from collections import defaultdict
from itertools import product
from typing import Any, Self, Iterable
from pydantic import BaseModel
import json
from pathlib import Path


class Node(BaseModel):
    symbol: str
    max_degree: int | float


class Edge(BaseModel):
    symbol: str
    weight: int | float


class BranchLink(BaseModel):
    symbol: str
    max_length_tokens: int


class Index(BaseModel):
    symbol: str
    value: int


class Modifier(BaseModel):
    type: str
    symbol: str
    weight: int | float
    allowed_nodes: list[str] | None = None
    data: dict[str, Any] | None = None
    exceptions: dict[str, Any] | None = None


class Grammar(BaseModel):
    index: list[Index]
    nodes: list[Node]
    edges: list[Edge]
    branch: BranchLink
    link: BranchLink
    modifiers: list[Modifier]

    @classmethod
    def from_file(cls, path: str | Path) -> Self:
        path = Path(path) if isinstance(path, str) else path
        data = json.loads(path.resolve().read_text())
        return cls.model_validate(data)

    def modifier_combinations(self, node_symbol: str) -> Iterable[list[Modifier]]:
        by_type: dict[str, list[Modifier]] = defaultdict(list)

        for m in self.modifiers:
            if m.allowed_nodes is None:
                by_type[m.type].append(m)
            elif node_symbol in m.allowed_nodes:
                by_type[m.type].append(m)

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
            if edge.symbol == "*":
                continue
            for ibranch in range(1, self.branch.max_length_tokens + 1):
                alphabet[f"{edge.symbol}{self.branch.symbol}{ibranch}"] = i
                i += 1

        # link symbols
        for edge in self.edges:
            if edge.symbol == "*":
                continue
            for ilink in range(1, self.link.max_length_tokens + 1):
                alphabet[f"{edge.symbol}{self.link.symbol}{ilink}"] = i
                i += 1

        # node symbols
        for edge in self.edges:
            if edge.symbol == "*":
                continue
            for node in self.nodes:
                if node.symbol == "*":
                    continue
                base = f"{edge.symbol}{node.symbol}"
                alphabet[base] = i
                i += 1
                for mods in self.modifier_combinations(node.symbol):
                    suffix = "".join(m.symbol for m in mods)
                    alphabet[f"{base}{suffix}"] = i
                    i += 1
        return alphabet
