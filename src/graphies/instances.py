from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class TokenType(StrEnum):
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
    disallowed_nodes: list[str] | None = None


class Structure(BaseModel):
    symbol: str
    value: int


@dataclass
class TokenInstance:
    type: TokenType = TokenType.UNKNOWN
    node: Node | Structure | None = None
    edge: Edge | None = None
    modifiers: list[Modifier] = field(default_factory=list)

    @property
    def symbol(self):
        return self.serialize()

    def serialize(self) -> str:
        if (self.node is None) or (self.node.symbol == "*"):
            raise ValueError(
                f"Cannot serialize TokenInstance without node attribute {self}"
            )

        if self.type == TokenType.INDEX:
            return f"[{self.node.symbol}]"

        if (self.edge is None) or (self.edge.symbol == "*"):
            edge_symbol = ""
        else:
            edge_symbol = self.edge.symbol

        mods_symbol = "".join(m.symbol for m in self.modifiers)

        return f"[{edge_symbol}{self.node.symbol}{mods_symbol}]"


class NodeInstance(Node):
    modifiers: list[Modifier] = field(default_factory=list)


class EdgeInstance(Edge): ...


class BranchInstance(Structure):
    indices: list[Structure]


class LinkInstance(Structure):
    indices: list[Structure]
