import logging
from typing import List, Literal

from networkx import Graph
from pydantic import BaseModel, Field

from metaselfies.grammar import Grammar, TokenInstance, TokenType, Structure, Node
from metaselfies.tokenizer import tokenize

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class PendingLink(BaseModel):
    source: int
    target: int
    weight: int | float


class BranchState(BaseModel):
    source: int
    remaining: int


class IndexState(BaseModel):
    kind: Literal["branch", "link"]
    source: int
    remaining: int
    value: int = 0
    weight: int | float

    def consume(self, token: TokenInstance):
        assert isinstance(token.node, Structure)
        digit = token.node.value
        self.value = (self.value << 4) + digit
        self.remaining -= 1


class State(BaseModel):
    current_node: int | None = None
    remaining_degree: int | float = 0

    pending_links: list[PendingLink] = Field(default_factory=list)
    branch_stack: list[BranchState] = Field(default_factory=list)
    index_stack: list[IndexState] = Field(default_factory=list)

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
        index = 0  # token index
        logger.debug("STATE INITIALIZED")

        for candidates in tokenize(data, self.grammar):
            candidates: List[TokenInstance]
            token: TokenInstance = self.resolve_token(candidates, state)
            logger.debug(f"Resolved {token.symbol} to type {token.type}")

            # decrement all open branches
            for i in range(len(state.branch_stack)):
                state.branch_stack[i].remaining -= 1

            # handle token
            if token.type == TokenType.NODE:
                self.handle_node(token, state, graph, index)
            elif token.type == TokenType.BRANCH:
                self.handle_branch(token, state, index)
            elif token.type == TokenType.LINK:
                self.handle_link(token, state, index)
            elif token.type == TokenType.INDEX:
                self.handle_index(token, state, index)
            elif token.type == TokenType.UNKNOWN:
                pass
            else:
                raise ValueError("Unknown token type")

            index += 1

        logger.debug("Resolving pending links")
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
                raise ValueError("Expected index token")

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

    def handle_node(self, token: TokenInstance, state: State, graph: Graph, index: int):
        assert isinstance(token.node, Node)
        assert token.edge is not None

        # apply node modifiers
        degree = token.node.max_degree
        for mod in token.modifiers:
            degree -= mod.weight

        # if first node
        if state.current_node is None:
            graph.add_node(index, degree=degree, **token.model_dump())
            state.current_node = index
            state.remaining_degree = degree
            logger.debug(f"Added node {index} with degree {degree}")
            return

        edge_weight = min(token.edge.weight, degree, state.remaining_degree)

        # update state
        graph.add_node(index, degree=degree - edge_weight, **token.model_dump())
        logger.debug(f"Added node {index} with degree {degree - edge_weight}")

        graph.add_edge(state.current_node, index, weight=edge_weight)
        logger.debug(
            f"Added edge from {index} to {state.current_node} with weight {edge_weight}"
        )

        graph.nodes[state.current_node]["degree"] -= edge_weight
        logger.debug(
            f"Updated node {index} to degree {graph.nodes[state.current_node]['degree']}"
        )

        # check if exiting branch
        if state.inside_branch:
            branch = state.branch_stack[-1]
            if branch.remaining == 0:
                logger.debug(f"Exiting branch with new root {branch.source}")
                state.current_node = branch.source
                state.remaining_degree = graph.nodes[branch.source]["degree"]
                state.branch_stack.pop()
                return

        state.current_node = index
        state.remaining_degree = degree - edge_weight

    def handle_branch(self, token: TokenInstance, state: State, index: int):
        assert isinstance(token.node, Structure)
        assert state.current_node is not None
        assert token.edge is not None

        logger.debug(f"Expecting {token.node.value} index token(s) for branch")
        state.index_stack.append(
            IndexState(
                kind="branch",
                source=state.current_node,
                remaining=token.node.value,
                weight=token.edge.weight,
            )
        )

    def handle_link(self, token: TokenInstance, state: State, index: int):
        assert isinstance(token.node, Structure)
        assert state.current_node is not None
        assert token.edge is not None

        logger.debug(f"Expecting {token.node.value} index token(s) for link")
        state.index_stack.append(
            IndexState(
                kind="link",
                source=state.current_node,
                remaining=token.node.value,
                weight=token.edge.weight,
            )
        )

    def handle_index(self, token: TokenInstance, state: State, index: int):
        if len(state.index_stack) == 0:
            return

        # process index token
        current: IndexState = state.index_stack[-1]
        current.consume(token)
        if current.remaining == 0:
            logger.debug(f"All index tokens consumed for {current.kind}")
            if current.kind == "branch":
                logger.debug(f"Expecting {current.value + 1} tokens for branch")
                state.branch_stack.append(
                    BranchState(
                        source=current.source,
                        remaining=current.value + 1,
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
                        weight=current.weight,
                    )
                )
            state.index_stack.pop()

    def resolve_links(self, state: State, graph: Graph):
        for link in state.pending_links:
            print(graph.nodes)
            source_degree = graph.nodes[link.source]["degree"]
            target_degree = graph.nodes[link.target]["degree"]
            link_weight = min(source_degree, target_degree, link.weight)

            graph.add_edge(link.source, link.target, weight=link_weight)
            logger.debug(f"Added edge from {link.source} to {link.target}")

            graph.nodes[link.source]["degree"] -= link_weight
            logger.debug(
                f"Updated node {link.source} to degree {graph.nodes[link.source]['degree']}"
            )

            graph.nodes[link.target]["degree"] -= link_weight
            logger.debug(
                f"Updated node {link.target} to degree {graph.nodes[link.target]['degree']}"
            )
