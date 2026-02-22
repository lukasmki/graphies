import logging

import networkx as nx
from networkx import DiGraph, Graph

from graphies.grammar import Grammar
from graphies.instances import (
    BranchInstance,
    EdgeInstance,
    LinkInstance,
    NodeInstance,
    TokenInstance,
    TokenType,
)

logger = logging.getLogger(__name__)


class Encoder:
    def __init__(self, grammar: Grammar):
        self.grammar: Grammar = grammar

    def encode(self, graph: Graph) -> str:
        # walk and build token sequence
        tree = nx.dfs_tree(graph, source=0, sort_neighbors=sorted)
        tokens = self.walk(graph, tree, node_id=0)
        return "".join([t.symbol for t in tokens])

    def walk(
        self, graph: Graph, tree: DiGraph, node_id: int, parent: int | None = None
    ) -> list[TokenInstance]:
        tokens: list[TokenInstance] = []

        # add node
        node = NodeInstance(**graph.nodes[node_id])
        if parent is not None:
            edge = EdgeInstance(**graph.get_edge_data(node_id, parent))
        else:
            edge = None
        token = TokenInstance(
            type=TokenType.NODE, node=node, edge=edge, modifiers=node.modifiers
        )
        tokens.append(token)

        # get non-tree edges to current node
        neighbors = list(graph.neighbors(node_id))
        children = list(tree.successors(node_id))
        ancestors = list(tree.predecessors(node_id))
        links = set(neighbors) - set(children) - set(ancestors)

        if not children:
            # create links
            tokens.extend(self.create_link(graph, node_id, links))
            return tokens

        for child in children[:-1]:
            # branch
            branch_tokens: list[TokenInstance] = self.walk(graph, tree, child, node_id)
            edge = EdgeInstance(**graph.get_edge_data(node_id, child))
            branch: BranchInstance = self.grammar.get_branch(size=len(branch_tokens))
            branch_prefix = [
                TokenInstance(type=TokenType.BRANCH, node=branch, edge=edge)
            ]
            for index in branch.indices:
                branch_prefix.append(TokenInstance(type=TokenType.INDEX, node=index))

            tokens.extend(branch_prefix + branch_tokens)

        # create links
        tokens.extend(self.create_link(graph, node_id, links))

        # last child
        tokens.extend(self.walk(graph, tree, children[-1], parent=node_id))

        return tokens

    def create_link(self, graph, node_id, links):
        tokens = []
        for link_id in links:
            if link_id < node_id:
                edge = EdgeInstance(**graph.get_edge_data(node_id, link_id))
                link: LinkInstance = self.grammar.get_link(distance=node_id - link_id)
                tokens.append(TokenInstance(type=TokenType.LINK, node=link, edge=edge))
                tokens.extend(
                    [
                        TokenInstance(type=TokenType.INDEX, node=index)
                        for index in link.indices
                    ]
                )
        return tokens
