from pathlib import Path

from networkx.classes.graph import Graph

from metaselfies.decoder import Decoder
from metaselfies.encoder import Encoder
from metaselfies.grammar import Grammar


def decode(metaselfies: str, grammar: Grammar | str | Path) -> Graph:
    if isinstance(grammar, str):
        grammar_path = Path(grammar).resolve()
        grammar = Grammar.model_validate_json(grammar_path.read_text())
    elif isinstance(grammar, Path):
        grammar = Grammar.model_validate_json(grammar.read_text())

    decoder = Decoder(grammar)
    graph = decoder.decode(metaselfies)
    return graph


def encode(graph: Graph, grammar: Grammar | str | Path) -> str:
    if isinstance(grammar, str):
        grammar_path = Path(grammar).resolve()
        grammar = Grammar.model_validate_json(grammar_path.read_text())
    elif isinstance(grammar, Path):
        grammar = Grammar.model_validate_json(grammar.read_text())

    encoder = Encoder(grammar)
    metaselfies = encoder.encode(graph)
    return metaselfies
