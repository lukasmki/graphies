# Decoding

The `Decoder` takes a string of GRAPHIES tokens and decodes the token sequence as a `networkx` graph.
Decoding is performed via a state-based grammar. Given an initial state, each token is parsed and produces an updated state. A simplified outline of the decoding process is shown below.

## Decoding Process

```python
state, graph = State(), Graph()

for candidate_tokens in graphies_sequence:
    token = resolve_token(candidate_tokens)
    if state.branches:
        state.branches.tokens_remaining -= 1

    state, graph = handle_token(token, state, graph)

    if state.inside_branch:
        state = check_exit_branch(state)
    
    state.current_token += 1

state, graph = resolve_pending_links(state, graph)
```

## Token Resolution

Decoding begins with spliting the GRAPHIES string into a list of tokens, decoding each token into its node and edge representation, and applying the token to the state/graph. Tokens can be decoded into different meanings depending on the current state of the decoder. In the SELFIES grammar using self-referencing index tokens, the carbon atom `[C]` token can be interpreted as either a carbon atom node or as a numerical 0 token. Rather than decoding the multiple meanings at decode-time, the Grammar initializes a prefix tree (also referred to as a trie) containing each token symbol and list of TokenInstance objects for each interpretation. This has the benefit of being linear time complexity for token symbol lookup and also has the potential for resolving unknown tokens using neighbor search.

```python
@dataclass
class TokenInstance:
    type: TokenType = TokenType.UNKNOWN
    node: Node | Structure | None = None
    edge: Edge | None = None
    modifiers: list[Modifier] = field(default_factory=list)
```

The TokenInstance represents a particular interpretation of an encoded GRAPHIES token. The token type is a string enum that is used in routing the token through decoding and serialization.

```python
class TokenType(StrEnum):
    NODE = "NODE"
    BRANCH = "BRANCH"
    LINK = "LINK"
    INDEX = "INDEX"
    UNKNOWN = "UNKNOWN"
```

## Decoder State

For basic sequences without branching or non-sequential links, the state simply needs to track IDs of the current and previous node and the remaining degree of the previous node in the sequence.

```python
@dataclass
class State:
    current_node: int | None = None
    previous_node: int | None = None
    remaining_degree: int | float = 0
```

If a new edge would fill or exceed this degree, then no new nodes can be added to the sequence without violating the degree constraints, and the decoding is halted and the graph is returned. In order to keep track of branching and nested sequences, two stacks of counters are added, the branch counter and the index counter.

```python
@dataclass
class State:
    ...
    pending_links: list[PendingLink] = field(default_factory=list)
    branch_stack: list[BranchState] = field(default_factory=list)
    index_stack: list[IndexCounter] = field(default_factory=list)

    @property
    def expecting_index(self) -> bool:
        return bool(self.index_stack)

    @property
    def inside_branch(self) -> bool:
        return bool(self.branch_stack)
```

## Branch and Link Handling

When entering a branch (or link), an index counter is created with the number of expected numerical tokens. Future tokens will try to resolve as index tokens. If it is unable to find an index representation for the token, the branch (or link) is cancelled and previously consumed index tokens are not re-interpreted as node tokens. Once the index tokens are consumed the index counter is resolved, the handling of branches and links diverge.

For branches, the index-encoded value corresponds to the number of following tokens that are contained within the branch, including other structure/index tokens. A new branch counter is initialized with the decoded value of the branch length. The following tokens are processed as normal.

For links, the encoded value is the number of previous nodes (not tokens) as they appeared in sequence from the current node. Then, the target and source nodes are computed and added to the pending link stack. Links are not resolved immediately, but are resolved after the tree has been constructed. If the target node is unindexable (i.e. id < 0), the link is cancelled. In SELFIES, unindexable target nodes are rerouted to link to node 0 rather than passing the link.
