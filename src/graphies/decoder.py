import logging
from dataclasses import dataclass, field
from typing import Literal

from networkx import Graph

from graphies.grammar import Grammar
from graphies.instances import (
    EdgeInstance,
    Node,
    NodeInstance,
    Structure,
    TokenInstance,
    TokenType,
)

logger = logging.getLogger(__name__)


@dataclass
class PendingLink:
    source: int
    target: int
    edge: EdgeInstance


@dataclass
class BranchState:
    source: int
    remaining: int
    length: int
    edge: EdgeInstance


@dataclass
class IndexCounter:
    kind: Literal["branch", "link"]
    source: int
    edge: EdgeInstance

    remaining: int
    digits: list[int] = field(default_factory=list)

    @property
    def value(self):
        return sum(d * (16**i) for i, d in enumerate(self.digits))

    def consume(self, token: TokenInstance):
        if logger.isEnabledFor(logging.DEBUG):
            assert isinstance(token.node, Structure)
        digit = token.node.value
        self.digits.append(digit)
        self.remaining -= 1


@dataclass
class State:
    current_node: int | None = None
    previous_node: int | None = None
    current_token: int = 0
    remaining_degree: int | float = 0

    pending_links: list[PendingLink] = field(default_factory=list)
    branch_stack: list[BranchState] = field(default_factory=list)
    index_stack: list[IndexCounter] = field(default_factory=list)

    @property
    def expecting_index(self) -> bool:
        return bool(self.index_stack)

    @property
    def inside_branch(self) -> bool:
        return bool(self.branch_stack)


class Decoder:
    """Decode graphies to networkx.Graph"""

    def __init__(self, grammar: Grammar):
        self.grammar: Grammar = grammar

    def decode(self, text: str) -> Graph:
        # initialize state
        state = State()
        graph = Graph()
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("STARTING DECODE")

        for candidates in self.grammar.tokenize(text):
            token: TokenInstance = self.resolve_token(candidates, state)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Resolved {token.symbol} to type {token.type}")

            # decrement all open branches
            for branch in state.branch_stack:
                branch.remaining -= 1
                branch.length += 1

            # handle token
            if token.type == TokenType.NODE:
                self.handle_node(token, state, graph)
            elif token.type == TokenType.BRANCH:
                self.handle_branch(token, state)
            elif token.type == TokenType.LINK:
                self.handle_link(token, state)
            elif token.type == TokenType.INDEX:
                self.handle_index(token, state)
            elif token.type == TokenType.UNKNOWN:
                pass
            else:
                raise ValueError("Unknown token type")

            # check to exit branch
            if state.inside_branch:
                branch = state.branch_stack[-1]
                if branch.remaining == 0:
                    state.previous_node = branch.source
                    state.remaining_degree = graph.nodes[branch.source]["degree"]
                    state.branch_stack.pop()
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"Exiting branch with new root {branch.source}")

            # increment token number
            state.current_token += 1

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Resolving pending links...")
        self.resolve_links(state, graph)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("FINISHED DECODE")

        return graph

    def resolve_token(
        self, candidates: list[TokenInstance], state: State
    ) -> TokenInstance:
        if not candidates:
            raise ValueError("No valid token interpretations")

        # expecting index tokens
        if state.expecting_index:
            for token in candidates:
                if token.type == TokenType.INDEX:
                    return token
            else:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        f"Expected index token instead got types {[c.type for c in candidates]}"
                    )
                    logger.debug("Closing index counter and resolving normally")
                # raise ValueError(f"Expected index token instead got types {[c.type for c in candidates]})
                # remove index counter and resolve token normally
                state.index_stack.pop()

        # normal resolution
        nonindex = [t for t in candidates if t.type != TokenType.INDEX]
        if len(nonindex) == 1:
            chosen = nonindex[0]
        elif len(nonindex) > 1:
            priority = {
                TokenType.NODE: 0,
                TokenType.BRANCH: 1,
                TokenType.LINK: 2,
                TokenType.INDEX: 3,
                TokenType.UNKNOWN: 4,
            }
            chosen = sorted(nonindex, key=lambda t: priority[t.type])[0]
        else:
            chosen = candidates[0]
        return chosen

    def handle_node(self, token: TokenInstance, state: State, graph: Graph):
        if logger.isEnabledFor(logging.DEBUG):
            assert isinstance(token.node, Node)
            assert token.edge is not None

        # apply node modifiers
        degree = token.node.degree
        for mod in token.modifiers:
            degree -= mod.weight

        # if first node
        if state.current_node is None:
            state.current_node = 0

            # add node
            node = NodeInstance(
                symbol=token.node.symbol,
                data=token.node.data,
                degree=degree,
                modifiers=token.modifiers,
            )
            mod_data = {k: v for m in node.modifiers for k, v in m.data.items()}
            graph.add_node(
                state.current_node, **node.model_dump(), **node.data, **mod_data
            )
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Added node {state.current_node} with degree {degree}")

            # update state
            state.previous_node = 0
            state.current_node = 1
            state.remaining_degree = degree
            return

        # compute edge weight
        if state.inside_branch and state.branch_stack[-1].length == 0:
            # if first in branch, use branch edge
            edge_weight = state.branch_stack[-1].edge.weight
        else:
            edge_weight = token.edge.weight

        edge_weight = min(edge_weight, degree, state.remaining_degree)

        # if adding a node is not possible
        if edge_weight == 0:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Maxmum degree reached")
            return

        # add node
        degree -= edge_weight
        node = NodeInstance(
            symbol=token.node.symbol,
            data=token.node.data,
            degree=degree,
            modifiers=token.modifiers,
        )
        mod_data = {k: v for m in node.modifiers for k, v in m.data.items()}
        graph.add_node(state.current_node, **node.model_dump(), **node.data, **mod_data)

        # add edge
        edge = self.grammar.get_edge(edge_weight)
        graph.add_edge(
            state.previous_node, state.current_node, **edge.model_dump(), **edge.data
        )

        # update node degree
        graph.nodes[state.previous_node]["degree"] -= edge_weight

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Added node {state.current_node} with degree {degree}")
            logger.debug(
                f"Added edge from {state.current_node} to {state.previous_node} with weight {edge_weight}"
            )
            logger.debug(
                f"Updated node {state.previous_node} to degree {graph.nodes[state.previous_node]['degree']}"
            )

        # update state
        state.previous_node = state.current_node
        state.current_node = state.current_node + 1
        state.remaining_degree = degree

    def handle_branch(self, token: TokenInstance, state: State):
        if logger.isEnabledFor(logging.DEBUG):
            assert isinstance(token.node, Structure)
            assert state.previous_node is not None
            assert token.edge is not None
            logger.debug(f"Expecting {token.node.value} index token(s) for branch")

        # if branch is the first token
        if state.previous_node is None:
            # don't do anything
            return

        edge = EdgeInstance(
            symbol=token.edge.symbol,
            weight=token.edge.weight,
            data=token.edge.data,
        )
        state.index_stack.append(
            IndexCounter(
                kind="branch",
                source=state.previous_node,
                remaining=token.node.value,
                edge=edge,
            )
        )

    def handle_link(self, token: TokenInstance, state: State):
        if logger.isEnabledFor(logging.DEBUG):
            assert isinstance(token.node, Structure)
            assert state.previous_node is not None
            assert token.edge is not None
            logger.debug(f"Expecting {token.node.value} index token(s) for link")

        # if link is the first token
        if state.previous_node is None:
            # don't do anything
            return

        edge = EdgeInstance(
            symbol=token.edge.symbol,
            weight=token.edge.weight,
            data=token.edge.data,
        )
        state.index_stack.append(
            IndexCounter(
                kind="link",
                source=state.previous_node,
                remaining=token.node.value,
                edge=edge,
            )
        )

    def handle_index(self, token: TokenInstance, state: State):
        if len(state.index_stack) == 0:
            return

        # process index token
        current: IndexCounter = state.index_stack[-1]
        current.consume(token)
        if current.remaining == 0:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"All index tokens consumed for {current.kind}")

            # Create branch
            if current.kind == "branch":
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Expecting {current.value + 1} tokens for branch")
                state.branch_stack.append(
                    BranchState(
                        source=current.source,
                        remaining=current.value + 1,
                        length=0,
                        edge=current.edge,
                    )
                )

            # Queue link
            if current.kind == "link":
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        f"Queuing link between {current.source} and {current.source - current.value - 1}"
                    )
                state.pending_links.append(
                    PendingLink(
                        source=current.source,
                        target=current.source - current.value - 1,
                        edge=current.edge,
                    )
                )
            state.index_stack.pop()

    def resolve_links(self, state: State, graph: Graph):
        for link in state.pending_links:
            # catch invalid link source/destination
            if link.source < 0 or link.target < 0:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        f"Attempted to create link {link.source} {link.target}. Continuing."
                    )
                continue

            # get pending link weight
            source_degree = graph.nodes[link.source]["degree"]
            target_degree = graph.nodes[link.target]["degree"]
            link_weight = min(source_degree, target_degree, link.edge.weight)

            # check if it would violate maximum degree
            if link_weight == 0:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        f"Passing link {link.source} {link.target} that would exceed max degree {source_degree} {target_degree} {link.edge.weight}"
                    )
                continue

            # get edge instance for link_weight
            if graph.has_edge(link.source, link.target):
                # add weight if an edge already exists
                try:
                    edge = self.grammar.get_edge(
                        link_weight + graph.edges[link.source, link.target]["weight"]
                    )
                except ValueError as e:
                    # if can't find edge token with the updated weight, continue 
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(e.args)
                    continue
            else:
                edge = self.grammar.get_edge(link_weight)

            # Add edge and update node degrees
            graph.add_edge(link.source, link.target, **edge.model_dump(), **edge.data)
            graph.nodes[link.source]["degree"] -= link_weight  # update with link weight
            graph.nodes[link.target]["degree"] -= link_weight

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Added edge from {link.source} to {link.target}")
                logger.debug(
                    f"Updated node {link.source} to degree {graph.nodes[link.source]['degree']}"
                )
                logger.debug(
                    f"Updated node {link.target} to degree {graph.nodes[link.target]['degree']}"
                )
