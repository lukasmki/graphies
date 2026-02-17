from metaselfies.instances import NodeInstance, EdgeInstance
import logging
from typing import List, Literal

from networkx import Graph
from pydantic import BaseModel, Field

from metaselfies.grammar import Grammar, TokenType, Structure, Node
from metaselfies.tokenizer import tokenize, TokenInstance

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class PendingLink(BaseModel):
    source: int
    target: int
    edge: EdgeInstance


class BranchState(BaseModel):
    source: int
    remaining: int
    length: int
    edge: EdgeInstance


class IndexCounter(BaseModel):
    kind: Literal["branch", "link"]
    source: int
    edge: EdgeInstance

    remaining: int
    value: int = 0

    def consume(self, token: TokenInstance):
        assert isinstance(token.node, Structure)
        digit = token.node.value
        self.value = (self.value << 4) + digit
        self.remaining -= 1


class State(BaseModel):
    current_node: int | None = None
    previous_node: int | None = None
    current_token: int = 0
    remaining_degree: int | float = 0

    pending_links: list[PendingLink] = Field(default_factory=list)
    branch_stack: list[BranchState] = Field(default_factory=list)
    index_stack: list[IndexCounter] = Field(default_factory=list)

    @property
    def expecting_index(self) -> bool:
        return bool(self.index_stack)

    @property
    def inside_branch(self) -> bool:
        return bool(self.branch_stack)


class Decoder:
    """Decode metaselfies to networkx.Graph"""

    def __init__(self, grammar: Grammar):
        self.grammar: Grammar = grammar

    def decode(self, data: str) -> Graph:
        # initialize state
        state = State()
        graph = Graph()
        logger.debug("STATE INITIALIZED")

        for candidates in tokenize(data, self.grammar):
            token: TokenInstance = self.resolve_token(candidates, state)
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
                    logger.debug(f"Exiting branch with new root {branch.source}")
                    state.previous_node = branch.source
                    state.remaining_degree = graph.nodes[branch.source]["degree"]
                    state.branch_stack.pop()

            # increment token number
            state.current_token += 1

        logger.debug("Resolving pending links...")
        self.resolve_links(state, graph)

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
                raise ValueError(f"Expected index token instead got {candidates}")

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
            graph.add_node(state.current_node, **node.model_dump())
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
        degree -= edge_weight

        # add node
        node = NodeInstance(
            symbol=token.node.symbol,
            data=token.node.data,
            degree=degree,
            modifiers=token.modifiers,
        )
        graph.add_node(state.current_node, **node.model_dump())
        logger.debug(f"Added node {state.current_node} with degree {degree}")

        # add edge
        edge = EdgeInstance(
            symbol=token.edge.symbol, weight=edge_weight, data=token.edge.data
        )
        graph.add_edge(state.previous_node, state.current_node, **edge.model_dump())
        logger.debug(
            f"Added edge from {state.current_node} to {state.previous_node} with weight {edge_weight}"
        )

        # update node degree
        graph.nodes[state.previous_node]["degree"] -= edge_weight
        logger.debug(
            f"Updated node {state.previous_node} to degree {graph.nodes[state.previous_node]['degree']}"
        )

        # update state
        state.previous_node = state.current_node
        state.current_node = state.current_node + 1
        state.remaining_degree = degree

    def handle_branch(self, token: TokenInstance, state: State):
        assert isinstance(token.node, Structure)
        assert state.previous_node is not None
        assert token.edge is not None
        logger.debug(f"Expecting {token.node.value} index token(s) for branch")

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
        assert isinstance(token.node, Structure)
        assert state.previous_node is not None
        assert token.edge is not None
        logger.debug(f"Expecting {token.node.value} index token(s) for link")

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
            logger.debug(f"All index tokens consumed for {current.kind}")
            if current.kind == "branch":
                logger.debug(f"Expecting {current.value + 1} tokens for branch")
                state.branch_stack.append(
                    BranchState(
                        source=current.source,
                        remaining=current.value + 1,
                        length=0,
                        edge=current.edge,
                    )
                )
            if current.kind == "link":
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
            source_degree = graph.nodes[link.source]["degree"]
            target_degree = graph.nodes[link.target]["degree"]
            link_weight = min(source_degree, target_degree, link.edge.weight)

            edge_data = link.edge.model_dump()
            edge_data.update({"weight": link_weight})

            graph.add_edge(link.source, link.target, **edge_data)
            logger.debug(f"Added edge from {link.source} to {link.target}")

            graph.nodes[link.source]["degree"] -= link_weight
            logger.debug(
                f"Updated node {link.source} to degree {graph.nodes[link.source]['degree']}"
            )

            graph.nodes[link.target]["degree"] -= link_weight
            logger.debug(
                f"Updated node {link.target} to degree {graph.nodes[link.target]['degree']}"
            )
