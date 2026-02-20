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
        # validate graph
        graph = self.validate(graph)

        # walk and build token sequence
        tree = nx.dfs_tree(graph, source=0, sort_neighbors=sorted)
        tokens = self.walk(graph, tree, node_id=0)
        return "".join([t.symbol for t in tokens])

    def validate(self, graph: Graph):
        # copy the graph and relabel nodes to node order
        mapping = dict(zip(graph.nodes(), range(graph.order())))
        graph = nx.relabel_nodes(graph, mapping, copy=True)

        self.grammar.default_node.model_dump()
        # for node, data in graph.nodes.items():
        #     print(node, data)
        #     graph.nodes[node].clear()
        #     graph.nodes[node]['node'] = NodeInstance(**data)

        # for edge, data in graph.edges.items():
        #     print(edge, data)
        #     graph.edges[edge].clear()
        #     graph.edges[edge]['edge'] = EdgeInstance(**data)
        return graph

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
            for link_id in links:
                if link_id < node_id:
                    edge = EdgeInstance(**graph.get_edge_data(node_id, link_id))
                    link: LinkInstance = self.grammar.get_link(
                        distance=node_id - link_id
                    )

                    link_tokens = [
                        TokenInstance(type=TokenType.LINK, node=link, edge=edge)
                    ]
                    for index in link.indices:
                        link_tokens.append(
                            TokenInstance(type=TokenType.INDEX, node=index)
                        )
                    tokens.extend(link_tokens)

            return tokens

        for child in children[:-1]:
            # branch
            edge = EdgeInstance(**graph.get_edge_data(node_id, child))

            branch_tokens: list[TokenInstance] = self.walk(
                graph, tree, child, parent=node_id
            )
            branch: BranchInstance = self.grammar.get_branch(size=len(branch_tokens))

            branch_prefix = [
                TokenInstance(type=TokenType.BRANCH, node=branch, edge=edge)
            ]
            for index in branch.indices:
                branch_prefix.append(TokenInstance(type=TokenType.INDEX, node=index))

            tokens.extend(branch_prefix + branch_tokens)

        # create links
        for link_id in links:
            if link_id < node_id:
                edge = EdgeInstance(**graph.get_edge_data(node_id, link_id))
                link: LinkInstance = self.grammar.get_link(distance=node_id - link_id)
                link_tokens = [TokenInstance(type=TokenType.LINK, node=link, edge=edge)]
                for index in link.indices:
                    link_tokens.append(TokenInstance(type=TokenType.INDEX, node=index))
                tokens.extend(link_tokens)

        # last child
        tokens.extend(self.walk(graph, tree, children[-1], parent=node_id))

        return tokens

    def create_link(self, graph, links):
        tokens = []

        for link_id in links:
            if link_id < node_id:
                edge = EdgeInstance(**graph.get_edge_data(node_id, link_id))
                link: LinkInstance = self.grammar.get_link(distance=node_id - link_id)
                link_tokens = [
                    TokenInstance(type=TokenType.LINK, node=link, edge=edge)
                ] + [
                    TokenInstance(type=TokenType.INDEX, node=index)
                    for index in link.indices
                ]
                tokens.extend(link_tokens)
        return tokens
