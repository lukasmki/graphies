from metaselfies.utils import base16
import logging
from ase.atoms import default
from typing import Iterator
import networkx as nx
from networkx.classes.digraph import Graph, DiGraph
from metaselfies.grammar import Grammar, TokenInstance, TokenType

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Encoder:
    def __init__(self, grammar: Grammar):
        self.grammar = grammar

    def encode(self, graph: Graph) -> str:
        tree: DiGraph = nx.dfs_tree(graph, source=0, sort_neighbors=sorted)
        assert isinstance(tree, DiGraph)
        logger.debug("Created spanning tree")

        logger.debug("Starting graph walk...")
        tokens, tokens_map = self.walk(graph, tree, nid=0)
        logger.debug("Graph walk complete.")

        print(tokens_map)
        print([t.serialize() for t in tokens])
        print([t.idx for t in tokens])

        tree_edges = {tuple(sorted(e)) for e in tree.edges()}
        graph_edges = {tuple(sorted(e)) for e in graph.edges()}
        link_edges = graph_edges - tree_edges
        logger.debug(f"Identified link edges {link_edges=}")

        for src, dst in link_edges:
            link_weight = graph.edges[src, dst]["weight"]
            if tokens_map[src] > tokens_map[dst]:
                source, target = tokens_map[src], tokens_map[dst]
            else:
                source, target = tokens_map[dst], tokens_map[src]
            link_tokens = self.create_link(source, target, link_weight, src + 1)

            print(link_tokens)
            for i, token in enumerate(link_tokens):
                tokens.insert(source + i + 1, token)

        return "".join([t.serialize() for t in tokens])

    def walk(
        self, graph: Graph, tree: DiGraph, nid: int, parent=None, idx: int = 0
    ) -> tuple[list[TokenInstance], dict[int, int]]:
        tokens_map = {}  # graph nid to token idx
        tokens: list[TokenInstance] = []

        node_data: dict = graph.nodes[nid]
        node_data.update(idx=idx)
        token = TokenInstance.model_validate(node_data, extra="allow")
        tokens.append(token)
        tokens_map[nid] = idx
        logger.debug(f"Pushed token {token.serialize()} to {idx=} from {parent=}")
        idx += 1

        children = list(tree.successors(nid))
        if not children:
            logger.debug(f"Reached branch end at {nid=} {idx=}")
            return tokens, tokens_map

        for branch_child in children[:-1]:
            logger.debug(f"Opening branch at parent {nid} for child {branch_child}")
            branch_tokens, branch_map = self.walk(graph, tree, branch_child, nid, idx)
            branch_weight = graph.edges[nid, branch_child]["weight"]
            branch = self.create_branch(branch_tokens, branch_weight, idx)
            tokens.extend(branch)
            tokens_map.update(branch_map)
            idx += len(branch)

        last_child = children[-1]
        last_tokens, last_map = self.walk(graph, tree, last_child, nid, idx)
        tokens.extend(last_tokens)
        tokens_map.update(last_map)
        idx += len(last_tokens)

        return tokens, tokens_map

    def create_branch(
        self, tokens: list[TokenInstance], weight: int | float, idx: int
    ) -> list[TokenInstance]:
        size = len(tokens)
        digits = base16(size - 1)

        # create branch token
        # check if default edge applies
        default_edge = self.grammar.default_edge
        if default_edge is not None and weight == default_edge.weight:
            branch_edge = default_edge
        else:
            for edge in self.grammar.edges:
                if edge.weight == weight:
                    branch_edge = edge
                    break
            else:
                branch_edge = None

        for branch in self.grammar.branches:
            if branch.value == len(digits):
                branch_token = TokenInstance(
                    type=TokenType.BRANCH,
                    symbol=f"[{branch.symbol}]",
                    node=branch,
                    edge=branch_edge,
                    modifiers=[],
                    idx=idx,
                )
                idx += 1
                break
        else:
            raise ValueError(
                f"Can not encode branch of length {size}. Increase the number of branch tokens."
            )

        # create index tokens
        index_tokens = []
        for digit in digits:
            for indextoken in self.grammar.index:
                if indextoken.value == digit:
                    index_tokens.append(
                        TokenInstance(
                            type=TokenType.INDEX,
                            symbol=f"[{indextoken.symbol}]",
                            node=indextoken,
                            edge=None,
                            modifiers=[],
                            idx=idx,
                        )
                    )
                    idx += 1
                    break
            else:
                raise ValueError(
                    f"Could not encode index digit {digit}. Missing index token for this value."
                )

        # increment output token idx
        for token in tokens:
            token.idx = idx
            idx += 1

        return [branch_token] + index_tokens + tokens

    def create_link(
        self, source: int, target: int, weight: int | float, idx: int
    ) -> list[TokenInstance]:
        m = source - target - 1
        digits = base16(m)

        # create link token
        default_edge = self.grammar.default_edge
        if default_edge is not None and weight == default_edge.weight:
            link_edge = default_edge
        else:
            for edge in self.grammar.edges:
                if edge.weight == weight:
                    link_edge = edge
                    break
            else:
                link_edge = None

        for link in self.grammar.links:
            if link.value == len(digits):
                link_token = TokenInstance(
                    type=TokenType.LINK,
                    symbol=f"[{link.symbol}]",
                    node=link,
                    edge=link_edge,
                    modifiers=[],
                    idx=idx,
                )
                idx += 1
                break
        else:
            raise ValueError(
                f"Can not encode link with distance {m}. Increase the number of link tokens."
            )

        # create index tokens
        index_tokens = []
        for digit in digits:
            for indextoken in self.grammar.index:
                if indextoken.value == digit:
                    index_tokens.append(
                        TokenInstance(
                            type=TokenType.INDEX,
                            symbol=f"[{indextoken.symbol}]",
                            node=indextoken,
                            edge=None,
                            modifiers=[],
                            idx=idx,
                        )
                    )
                    idx += 1
                    break
            else:
                raise ValueError(
                    f"Could not encode index digit {digit}. Missing index token for this value."
                )

        return [link_token] + index_tokens
