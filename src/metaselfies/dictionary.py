from typing import Any, Self
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
    symbol: str
    weight: int | float
    data: dict[str, Any] | None
    exceptions: dict[str, Any] | None


class Dictionary(BaseModel):
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

    def to_alphabet(self):
        pass
