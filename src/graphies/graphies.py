from collections.abc import Hashable
from pathlib import Path

from networkx.classes.graph import Graph

from graphies.decoder import Decoder
from graphies.encoder import Encoder
from graphies.grammar import Grammar


class Graphies:
    def __init__(self, grammar: Grammar | str | Path):
        self.grammar = grammar

    def __repr__(self) -> str:
        return f"Graphies(grammar={self.grammar!r})"

    @property
    def grammar(self) -> Grammar:
        """The grammar used for encoding and decoding.

        Can be set with a :class:`.Grammar` object, a path string, or a
        :class:`pathlib.Path` to a JSON file. Assigning a new value rebuilds
        the encoder and decoder automatically.

        :type: Grammar
        """
        return self._grammar

    @grammar.setter
    def grammar(self, value: Grammar | str | Path) -> None:
        self._grammar: Grammar = Grammar.from_file(value)
        self._encoder: Encoder = Encoder(grammar=self._grammar)
        self._decoder: Decoder = Decoder(grammar=self._grammar)

    def decode(self, graphies: str) -> Graph:
        """Decode GRAPHIES to a networkx Graph

        :param graphies: GRAPHIES string
        :type graphies: str
        :return: GRAPHIES decoded graph
        :rtype: Graph
        """
        return self._decoder.decode(graphies)

    def encode(self, graph: Graph, source: Hashable = None) -> str:
        """Encode a networkx graph to GRAPHIES

        :param graph: Networkx graph to encode
        :type graph: Graph
        :param source: Source node to start encoding, defaults to None
        :type source: Hashable, optional
        :return: GRAPHIES encoded graph
        :rtype: str
        """
        return self._encoder.encode(graph, source=source)

    def recode(self, graphies: str) -> str:
        """Decode and re-encode GRAPHIES

        :param graphies: GRAPHIES string
        :type graphies: str
        :return: Recoded GRAPHIES string
        :rtype: str
        """
        return self._encoder.encode(self._decoder.decode(graphies))


def decode(graphies: str, grammar: Grammar | str | Path) -> Graph:
    """Decode GRAPHIES to a networkx Graph

    See :meth:`Graphies.decode` for full documentation.
    """
    return Graphies(grammar).decode(graphies)


def encode(graph: Graph, grammar: Grammar | str | Path, source: Hashable = None) -> str:
    """Encode a networkx graph to GRAPHIES

    See :meth:`Graphies.encode` for full documentation.
    """
    return Graphies(grammar).encode(graph, source=source)


def recode(graphies: str, grammar: Grammar | str | Path) -> str:
    """Decode and re-encode GRAPHIES

    See :meth:`Graphies.recode` for full documentation.
    """
    return Graphies(grammar).recode(graphies)
