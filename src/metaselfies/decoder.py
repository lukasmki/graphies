from metaselfies.dictionary import Dictionary
from typing import Pattern, Match
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


class Decoder:
    """Decode metaselfies to networkx.Graph"""

    TOKEN_RE: Pattern[str] = re.compile(r"\[[^\]]*\]|[^\[\]\s]")

    def __init__(self, dictionary: Dictionary | None = None):
        pass

    def classify_token(self, token: Match[str]) -> TokenType:
        tok = token.group()

        print(tok)

        return TokenType.STOP

    def run(self, data: str) -> Graph:
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
