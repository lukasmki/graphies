from pathlib import Path

from networkx.classes.graph import Graph

from graphies.decoder import Decoder
from graphies.encoder import Encoder
from graphies.grammar import Grammar


def decode(graphies: str, grammar: Grammar | str | Path) -> Graph:
    if isinstance(grammar, str):
        grammar_path = Path(grammar).resolve()
        grammar = Grammar.model_validate_json(grammar_path.read_text())
    elif isinstance(grammar, Path):
        grammar = Grammar.model_validate_json(grammar.read_text())

    decoder = Decoder(grammar)
    graph = decoder.decode(graphies)
    return graph


def encode(graph: Graph, grammar: Grammar | str | Path) -> str:
    if isinstance(grammar, str):
        grammar_path = Path(grammar).resolve()
        grammar = Grammar.model_validate_json(grammar_path.read_text())
    elif isinstance(grammar, Path):
        grammar = Grammar.model_validate_json(grammar.read_text())

    encoder = Encoder(grammar)
    graphies = encoder.encode(graph)
    return graphies
