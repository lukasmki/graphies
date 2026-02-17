from metaselfies.utils import base16
from pydantic import BaseModel
from metaselfies.grammar import Node, Edge, Structure, Modifier, TokenType, Grammar
from typing import Self


class NodeInstance(Node):
    modifiers: list[Modifier]


class EdgeInstance(Edge): ...


class BranchInstance(Structure):
    indices: list[Structure]

    @classmethod
    def from_size(cls, size: int, grammar: Grammar) -> Self:
        digits = base16(size - 1)

        for branch in grammar.branches:
            if branch.value == len(digits):
                symbol = branch.symbol
                break
        else:
            raise ValueError(f"Could not find branch token with length {len(digits)}")

        indices = []
        for digit in digits:
            for index in grammar.index:
                if index.value == digit:
                    indices.append(index)
                    break
            else:
                raise ValueError(f"Could not find index token for digit {digit}")

        return cls.model_construct(symbol=symbol, value=len(digits), indices=indices)


class LinkInstance(Structure):
    indices: list[Structure]

    @classmethod
    def from_distance(cls, distance: int, grammar: Grammar) -> Self:
        digits = base16(distance - 1)

        for link in grammar.links:
            if link.value == len(digits):
                symbol = link.symbol
                break
        else:
            raise ValueError(f"Could not find branch token with length {len(digits)}")

        indices = []
        for digit in digits:
            for index in grammar.index:
                if index.value == digit:
                    indices.append(index)
                    break
            else:
                raise ValueError(f"Could not find index token for digit {digit}")

        return cls.model_construct(symbol=symbol, value=len(digits), indices=indices)
