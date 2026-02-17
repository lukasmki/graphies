from metaselfies.instances import (
    NodeInstance,
    EdgeInstance,
    BranchInstance,
    LinkInstance,
)
from metaselfies.utils import base16
import logging
from ase.atoms import default
from typing import Iterator
import networkx as nx
from networkx.classes.digraph import Graph, DiGraph
from metaselfies.grammar import Grammar, TokenType
from metaselfies.tokenizer import TokenInstance

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Encoder:
    def __init__(self, grammar: Grammar):
        self.grammar = grammar

    def encode(self, graph: Graph) -> str:
        # TODO: preprocess graph with grammar

        # relabel nodes to token order
        nodes = list(graph.nodes())
        mapping = dict(zip(nodes, range(len(nodes))))
        graph = nx.relabel_nodes(graph, mapping, copy=True)
        tree = nx.dfs_tree(graph, source=0, sort_neighbors=sorted)
        tokens = self.walk(graph, tree, node_id=0)
        return "".join([t.symbol for t in tokens])

    def walk(
        self, graph: Graph, tree: DiGraph, node_id: int, parent: int | None = None
    ):
        tokens = []

        # add node
        node = NodeInstance.model_validate(graph.nodes[node_id])
        if parent is not None:
            edge = EdgeInstance.model_validate(graph.get_edge_data(node_id, parent))
        else:
            edge = None
        token = TokenInstance(
            type=TokenType.NODE, node=node, edge=edge, modifiers=node.modifiers
        )
        tokens.append(token)

        neighbors = list(graph.neighbors(node_id))
        children = list(tree.successors(node_id))
        ancestors = list(tree.predecessors(node_id))
        links = set(neighbors) - set(children) - set(ancestors)

        if not children:
            # create links
            for link_id in links:
                if link_id < node_id:
                    edge = EdgeInstance.model_validate(
                        graph.get_edge_data(node_id, link_id)
                    )
                    link = LinkInstance.from_distance(
                        distance=node_id - link_id, grammar=self.grammar
                    )
                    link_tokens = [
                        TokenInstance(
                            type=TokenType.LINK, node=link, edge=edge, modifiers=[]
                        )
                    ]
                    for index in link.indices:
                        link_tokens.append(
                            TokenInstance(
                                type=TokenType.INDEX,
                                node=index,
                                edge=None,
                                modifiers=[],
                            )
                        )
                    tokens.extend(link_tokens)

            return tokens

        for child in children[:-1]:
            # branch
            edge = EdgeInstance.model_validate(graph.get_edge_data(node_id, child))

            branch_tokens = self.walk(graph, tree, child, parent=node_id)
            branch = BranchInstance.from_size(
                size=len(branch_tokens), grammar=self.grammar
            )
            branch_prefix = [
                TokenInstance(
                    type=TokenType.BRANCH, node=branch, edge=edge, modifiers=[]
                )
            ]
            for index in branch.indices:
                branch_prefix.append(
                    TokenInstance(
                        type=TokenType.INDEX, node=index, edge=None, modifiers=[]
                    )
                )

            tokens.extend(branch_prefix + branch_tokens)

        # create links
        for link_id in links:
            if link_id < node_id:
                edge = EdgeInstance.model_validate(
                    graph.get_edge_data(node_id, link_id)
                )
                link = LinkInstance.from_distance(
                    distance=node_id - link_id, grammar=self.grammar
                )
                link_tokens = [
                    TokenInstance(
                        type=TokenType.LINK, node=link, edge=edge, modifiers=[]
                    )
                ]
                for index in link.indices:
                    link_tokens.append(
                        TokenInstance(
                            type=TokenType.INDEX, node=index, edge=None, modifiers=[]
                        )
                    )
                tokens.extend(link_tokens)

        # last child
        tokens.extend(self.walk(graph, tree, children[-1], parent=node_id))

        return tokens
