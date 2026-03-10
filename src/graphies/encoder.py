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
        self.visited: list[int] = list()

    def encode(self, graph: Graph, source=None) -> str:
        # walk and build token sequence
        source = list(graph)[0] if source is None else source
        tree = nx.dfs_tree(graph, source=source, sort_neighbors=sorted)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("STARTING WALK")
        self.visited = list()
        tokens = self.walk(graph, tree, node_id=source)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("FINISHED WALK")
        return "".join([t.symbol for t in tokens])

    def walk(
        self, graph: Graph, tree: DiGraph, node_id: int, parent: int | None = None
    ) -> list[TokenInstance]:
        tokens: list[TokenInstance] = []
        self.visited.append(node_id)  # add to visited nodes
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Reached node {node_id} from {parent}")

        # add node
        node = NodeInstance(**graph.nodes[node_id])
        if parent is not None:
            edge = EdgeInstance(**graph.get_edge_data(node_id, parent))
        else:
            edge = None
        token = TokenInstance(
            type=TokenType.NODE, node=node, edge=edge, modifiers=node.modifiers
        )
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Added node {token.serialize()}")
        tokens.append(token)

        # get non-tree edges to current node
        neighbors = list(graph.neighbors(node_id))
        children = list(tree.successors(node_id))
        ancestors = list(tree.predecessors(node_id))
        links = set(neighbors) - set(children) - set(ancestors)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Neighbors of {node_id}: {neighbors}")
            logger.debug(f"Children of {node_id}: {children}")
            logger.debug(f"Ancestors of {node_id}: {ancestors}")
            logger.debug(f"Links of {node_id}: {links}")

        if not children:
            # create links
            tokens.extend(self.create_link(graph, node_id, links))
            return tokens

        for child in children[:-1]:
            # branch
            branch_tokens: list[TokenInstance] = self.walk(graph, tree, child, node_id)

            # create branch prefix
            edge = EdgeInstance(**graph.get_edge_data(node_id, child))
            branch_instance: BranchInstance = self.grammar.get_branch(
                size=len(branch_tokens)
            )
            branch_prefix = [
                TokenInstance(type=TokenType.BRANCH, node=branch_instance, edge=edge)
            ]
            for index in branch_instance.indices:
                branch_prefix.append(TokenInstance(type=TokenType.INDEX, node=index))
            branch = branch_prefix + branch_tokens
            tokens.extend(branch)

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    f"Created branch {[token.serialize() for token in branch_prefix]}"
                )

        # create links
        tokens.extend(self.create_link(graph, node_id, links))

        # last child
        tokens.extend(self.walk(graph, tree, children[-1], parent=node_id))

        return tokens

    def create_link(self, graph: Graph, node_id, links):
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Resolving links for node {node_id}: {links}")
        tokens = []
        for link_id in links:
            if link_id in self.visited:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        f"Attempting to create link from node {node_id} to node {link_id}"
                    )

                edge = EdgeInstance(**graph.get_edge_data(node_id, link_id))
                distance = self.visited.index(node_id) - self.visited.index(link_id)
                if distance < 0:
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(
                            "Cannot create link with node distance < 0:"
                            f"{distance} = {self.visited.index(node_id)} - {self.visited.index(link_id)}"
                        )
                    continue

                link: LinkInstance = self.grammar.get_link(distance)
                tokens.append(TokenInstance(type=TokenType.LINK, node=link, edge=edge))
                tokens.extend(
                    [
                        TokenInstance(type=TokenType.INDEX, node=index)
                        for index in link.indices
                    ]
                )
        if logger.isEnabledFor(logging.DEBUG) and tokens:
            logger.debug(f"Added node {[token.serialize() for token in tokens]}")
        return tokens
