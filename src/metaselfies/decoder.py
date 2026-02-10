from typing import Pattern, Match
from dataclasses import dataclass
from networkx import Graph
import re
from enum import Enum


class TokenType(Enum):
    START = 0
    STOP = 1
    NODE = 2
    EDGE = 3
    BRANCH = 4
    LINK = 5
    INDEX = 6


@dataclass
class State:
    pass


class Decoder:
    TOKEN_RE: Pattern[str] = re.compile(r"\[[^\]]*\]|[^\[\]\s]")

    def classify_token(self, token: Match[str]) -> TokenType:
        print(token.group())
        return TokenType.STOP

    def run(self, data: str) -> Graph:
        state = State()

        tokens = self.TOKEN_RE.finditer(data)
        for token in tokens:
            token_type = self.classify_token(token)
            match token_type:
                case TokenType.START:
                    pass
                case TokenType.NODE:
                    pass
                case TokenType.BRANCH:
                    pass
                case TokenType.LINK:
                    pass
                case TokenType.INDEX:
                    pass
                case TokenType.STOP:
                    pass
