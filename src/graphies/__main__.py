import json
import logging
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

import networkx as nx

from graphies.graphies import decode, encode


class Args(Namespace):
    graphies_or_graph: str
    grammar: Path
    encode: bool
    decode: bool


def main():
    parser = ArgumentParser()
    parser.add_argument("-g", "--grammar", type=Path, required=True)
    parser.add_argument("--encode", action="store_true")
    parser.add_argument("--decode", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("graphies_or_graph", nargs="?", type=str)
    args = parser.parse_args(namespace=Args())

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if args.encode and args.decode:
        raise ValueError("Mutually exclusive arguments `--encode` and `--decode`")
    if not (args.encode or args.decode):
        args.decode = True

    if (args.graphies_or_graph is None) and (not sys.stdin.isatty()):
        args.graphies_or_graph = sys.stdin.read()
    elif args.graphies_or_graph is None:
        print("No input provided")
        sys.exit(1)

    if args.decode:
        input = args.graphies_or_graph.splitlines()
        for graphies in input:
            graphies = args.graphies_or_graph
            graph = decode(graphies, grammar=args.grammar)
            output = json.dumps(nx.node_link_data(graph))
            sys.stdout.write(output + "\n")

    if args.encode:
        input = args.graphies_or_graph.splitlines()
        for graph in input:
            graph = nx.node_link_graph(json.loads(args.graphies_or_graph))
            graphies = encode(graph, grammar=args.grammar)
            sys.stdout.write(graphies + "\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
