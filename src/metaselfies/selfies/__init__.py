from networkx.classes.graph import Graph
from pathlib import Path
from metaselfies.utils import decode, encode

SELFIES_GRAMMAR = Path(__file__).parent.resolve() / "selfies.json"


def decoder(selfies: str):
    graph = decode(selfies, SELFIES_GRAMMAR)


def encoder(graph: Graph):
    selfies = encode(graph, SELFIES_GRAMMAR)
