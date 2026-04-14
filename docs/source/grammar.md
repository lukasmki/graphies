# Grammar

The `Grammar` is the central object in the graphies package and defines the tokenization, degree constraints, node and edge types, and available modifiers.
It also can set node or edge level data on decoded graphs for compatibility with downstream processing.
The Grammar dataclass is also a subclass of the Pydantic `BaseModel` allowing Grammar objects to be constructed in a variety of ways. [cite-pydantic]
I also provide a `.from_file` class method to instantiate a grammar instance directly from a JSON file.

## Node and Edge Tokens

In order to represent a simple, undirected graph as a string (or a sequence of tokens), we must first define the string (token) representations of the basic units of the graph: nodes and edges.

```python
class Node(BaseModel):
    symbol: str
    degree: int | float
    data: dict[str, Any] = Field(default_factory=dict)
```

```python
class Edge(BaseModel):
    symbol: str
    weight: int | float
    data: dict[str, Any] = Field(default_factory=dict)
```

The particular node and edge symbol representations will be different depending on the graph that you are trying to tokenize.
For molecules, the nodes are atom types (H, C, N, O, Na, Cl, etc.) and the edges are bond types (single [-], double [=], or triple [#]). Other types of connectivity can also be included such as a hydrogen bond [--] or left and right directional bonds [<-] [->].
For protein sequence generation, the nodes are residues (ALA, CYS, etc.) and edges are determined by the sequence or generic inter-residue contacts [-].

The core idea here is that if you can express your graph as a discrete set of node and edge types, it can be represented by a GRAPHIES string.
The node and edge definitions for SELFIES is shown below.

```json
{
    "nodes"    : [
        {"symbol": "H",  "degree": 1}, {"symbol": "F",  "degree": 1}, {"symbol": "Cl", "degree": 1},
        {"symbol": "Br", "degree": 1}, {"symbol": "I",  "degree": 1}, {"symbol": "B",  "degree": 3},
        {"symbol": "C",  "degree": 4}, {"symbol": "N",  "degree": 3}, {"symbol": "O",  "degree": 2},
        {"symbol": "P",  "degree": 5}, {"symbol": "S",  "degree": 6}, {"symbol": "*",  "degree": 8}
    ],
    "edges"    : [
        {"symbol": "-",  "weight": 1}, {"symbol": "=",  "weight": 2}, {"symbol": "#",  "weight": 3},
        {"symbol": "/",  "weight": 1}, {"symbol": "\\", "weight": 1}, {"symbol": "*",  "weight": 1}
    ]
}
```

A common restriction that is particularly critical in molecule generation is maximum degree limitations.
A standard carbon atom cannot make more than 4 covalent bonds, a nitrogen atom cannot make more than 3, and so on.
Therefore, we require that each node type must have a defined maximum degree and each edge type must have a defined weight. In practice, node degrees could be set very large and edge weights set to zero to allow any number of these edges to connect to a node.

## Node Modifiers

In molecular systems, atoms can be in one of many internal states. Any atom can possess a negative (-1) or positive (+1) charge or possess some number of explicit hydrogens (CH3, NH2, OH1, etc). They can also be chiral (typically denoted @ or @@).
Some of these internal states modify the degree of the node; therefore I refer to these as modifiers. A simple solution for dealing with these modifiers is to enumerate every combination of modifier as its own node type; however, this is a bit redundant. Rather, modifiers can be defined and applied to nodes.
Modifiers can be given a category to apply them mutually excusively with other modifiers in that category. This prevents the grammar from considering runaway sequences like [C+1-1+1-1+1-1...] which (while logical) should not exist.

```python
class Modifier(BaseModel):
    category: str
    symbol: str
    weight: int | float
    data: dict[str, Any] = Field(default_factory=dict)
    allowed_nodes: list[str] | None = None
    exceptions: dict[str, Any] | None = None
    disallowed_nodes: list[str] | None = None
```

Modifiers are specified by their symbol and weight (modification of the max degree). They can also be restricted to a list of allowed nodes or explicitly disallowed on particular nodes.
Modifiers also contain exceptions. For example, any charge on a carbon atom will decrease its maximum degree by 1, but oxygen gains additional bonding capacity with a +1 charge and loses capacity with a -1 charge. Boron is the opposite of oxygen, losing capacity with a +1 charge and gaining with a -1 charge. Therefore, modifiers need exceptions and can be expressed as a dictionary of node symbols.
The modifier scheme for SELFIES modifiers is shown below.

```json
"modifiers": [
    {
        "symbol"       : "@",
        "weight"       : 0,
        "allowed_nodes": ["C", "P", "S"],
        "data"         : {"chiral_order": 1},
        "category"     : "chirality"
    },
    {
        "symbol"       : "@@",
        "weight"       : 0,
        "allowed_nodes": ["C", "P", "S"],
        "data"         : {"chiral_order": 2},
        "category"     : "chirality"
    },
    { "symbol": "H1", "weight": 1, "allowed_nodes": ["C", "N", "O", "P", "S"], "category": "hydrogen" },
    { "symbol": "H2", "weight": 2, "allowed_nodes": ["C", "N", "P"], "category": "hydrogen" },
    { "symbol": "H3", "weight": 3, "allowed_nodes": ["N"], "category": "hydrogen" },
    {
        "symbol"       : "+1",
        "weight"       : -1,
        "allowed_nodes": ["B", "C", "N", "O", "P", "S"],
        "exceptions"   : { "B": {"weight": 1}, "C": {"weight": 1}, "S": {"weight": 1}, "P": {"weight": 1} },
        "category"     : "charge"
    },
    {
        "symbol"       : "-1",
        "weight"       : 1,
        "allowed_nodes": ["C", "N", "O", "P", "S"],
        "exceptions"   : { "B": {"weight": -1}, "C": {"weight": 1}, "S": {"weight": 1}, "P": {"weight": -1} },
        "category"     : "charge"
    }
]
```

## Structure Tokens

At this point, we have a robust description of the types of nodes and edges that compose the graph.
Nodes in the graph can be represented in the form `[{edge_symbol}{node_symbol}{modifier_symbols}]`.
A sequence of these nodes instances is a sufficient representation of a chain of nodes with varying internal state and edge types.

However in order to express graphs that contain edges that are not simply chains, we need tokens to indicate edges that connect non-adjacent node tokens. There are two kinds of non-chainlike structures: branches and links.

Starting with branches, we could introduce a SMILES-like syntax for branching by enclosing some part of the token sequence with parentheses to indicate a new chain to attach to the previous node.
However, this would break our ability to parse sequences with unterminated branches and, more importantly, it would introduce a severe fragility to the string representation.
A single token modification would drastically alter the structure. The solution developed by SELFIES is to pair the branch token with a set of numerical tokens that indicate the length of the branch.

Links are edges that bridge two nodes that are not sequential. SELFIES calls these ring-closure tokens. Similar to branches, they consist of a link (Ring) token and a set of numerical tokens. The numerical tokens indicate the node distance between the current node and the target node to link.

For representing the node distance or branch size, we define a set of index tokens that have an associated value. In order to represent larger numbers with fewer digits, the index tokens are hexidecimal (base 16). Unlike SELFIES, these index tokens can be assigned unique numerical symbols or overload node/branch/link token symbols. The branch, link, and index section for the SELFIES grammar is shown below.

```json
{
    "branches" : [
        {"symbol": "Branch1", "value": 1}, {"symbol": "Branch2", "value": 2}, {"symbol": "Branch3", "value": 3},
        {"symbol": "Branch4", "value": 4}
    ],
    "links"    : [
        {"symbol": "Ring1", "value": 1}, {"symbol": "Ring2", "value": 2}, {"symbol": "Ring3", "value": 3},
        {"symbol": "Ring4", "value": 4}
    ],
    "index"    : [
        {"symbol": "C",        "value":  0}, {"symbol": "Ring1",    "value":  1}, {"symbol": "Ring2",    "value":  2},
        {"symbol": "Branch1",  "value":  3}, {"symbol": "=Branch1", "value":  4}, {"symbol": "#Branch1", "value":  5},
        {"symbol": "Branch2",  "value":  6}, {"symbol": "=Branch2", "value":  7}, {"symbol": "#Branch2", "value":  8},
        {"symbol": "O",        "value":  9}, {"symbol": "N",        "value": 10}, {"symbol": "=N",       "value": 11},
        {"symbol": "=C",       "value": 12}, {"symbol": "#C",       "value": 13}, {"symbol": "S",        "value": 14},
        {"symbol": "P",        "value": 15}
    ]
}
```

Branch, link, and index tokens are defined by their symbol and some associated value. For branches and link tokens, the value corresponds to the number of expected index tokens proceeding the branch or link token. For index tokens, it is its base-10 value. All three types of stucture tokens thus fit the following schema:

```python
class Structure(BaseModel):
    symbol: str
    value: int
```

That's it! The grammar is then defined as a structured collection of node and edge types, node modifiers, and structure tokens.

```python
class Grammar(BaseModel):
    nodes: list[Node]
    edges: list[Edge]
    modifiers: list[Modifier]
    index: list[Structure]
    links: list[Structure]
    branches: list[Structure]
```

The grammar can then be used to encode and decode graphs into string representations.
