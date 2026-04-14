# Overview

- [Grammar](grammar.md)
- [Decoding](decoder.md)
- [Encoding](encoder.md)

## Quickstart

Start a graphies session by loading a grammar using the `Graphies` interface. You can run this example in `examples/selfies/quickstart.py`

```python
import networkx as nx
from graphies import Graphies

# Load a grammar
g = Graphies("selfies.json")

# Create a graph
graph = nx.Graph()
graph.add_node(0, symbol="C", degree=4)
graph.add_node(1, symbol="C", degree=4)
graph.add_node(2, symbol="C", degree=4)
graph.add_node(3, symbol="C", degree=4)
graph.add_edge(0, 1, symbol="*", weight=1)
graph.add_edge(1, 2, symbol="-", weight=1)
graph.add_edge(2, 3, symbol="=", weight=2)

# Encode the graph to graphies
graphies = g.encode(graph)
print(graphies)  # Output: [C][C][-C][=C]

# Decode back to graph
decoded_graph = g.decode(graphies)
print(decoded_graph)  # Output: Graph with 4 nodes and 3 edges
```

## Differences with SELFIES

For any valid molecule, GRAPHIES and SELFIES encoded graphs are identical (100% agreement tested on QM9 SMILES in `tests/test_roundtrip.py`). However, I have identified a few different ways in which GRAPHIES decoding differs from SELFIES decoding for invalid graphs where differences in implementation and error handling produce different graphs from the same SELFIES/GRAPHIES token sequence.

### 1. Inconsistent Edge Weight Reduction with Branches

When decoding a GRAPHIES or SELFIES string that does not obey degree constraints, edge weight reduction is used when creating edges to prevent the overloading of node degrees. Reduction is performed if the attempted edge weight exceeds the source or target node degree and is reduced to the smaller of the two so that neither max degree is violated. Therefore, the final edges are subject to the order in which they are processed as well as when the edge reduction is applied. Consider the following example sequence representing the SMILES `O=N=O`.

```
[O][=N][=Branch1][C][=O]
```

At the branch token, the valence of the nitrogen is exceeded (2 + 2 = 4 > 3). SELFIES does not apply edge reduction in this case. Rather, the branch is cancelled and the next two tokens are resolved as a carbon atom and bound to a double bonded oxygen. Giving the sequence, `[O][=N][C][=O]`.

GRAPHIES applies edge reduction at the first node of the branch. At the branch token, one index node is expected, and the `[=Branch1][C]` is resolved to a branch length of 1. The first node of the branch is then resolved as `[=O]`, then edge reduction is applied to form `[O][=N][-O]`.

This method is preferable to SELFIES especially when using overloaded index tokens since the failure to create the branch introduced an unintended carbon atom. In longer branches, parsing well-formatted index tokens as standard tokens can introduce unintended sequence terminating symbols, rings and sub-branches, or sulfur and phosphorous atoms that the original molecule did not possess.

### 2. Handling the Sequential Link (`[Ring1][C]`)

When resolving a link edge, it is possible that an edge already exists between the source and target node. Since links can only connect the current node to previous nodes, this means that at decode-time only the sequence `[Ring1][C]` can create a link between two nodes that already share an edge. This sequence targets the first (`[C]` = 0 + 1 = 1) previous node. Both SELFIES and GRAPHIES handle this case by attempting to add the weight of the link edge with the weight of existing edge. Since, in both SELFIES and GRAPHIES, all links are resolved after the full sequence has been parsed, changes in the source node's remaining degree introduce a new problem with edge reweighting. Consider the following example sequence.

```
[C][=C][Ring1][C][=N]
```

Since the `[Ring1][C]` tokens essentially increment the carbon double bond `[=C]` to a triple bond `[#C]`, the sequence could be interpreted as `[C][#C][-N]` with the CN edge reweighted after resolving the link. This is the SELFIES result and is acheived by reweighting the outgoing edge (C-N) of the source node in order to apply the edge addition onto (C=C). While it is logical that `[=C][Ring1][C]` should compile to `[#C]`, this process is confusing because it inverts the order of edge resolution and can introduce ambiguity. Consider this next example where the carbon has been replaced by a sulfur atom and the nitrogen by two branches of oxygen and nitrogen.

```
[C][=S][Ring1][C][=Branch1][C][=O][=N]
```

Following the SELFIES decoding, the `[=S][Ring1][C]` should compile to a triple bond `[#S]`. Since sulfur has a max degree of 5, the following node bond order should be decremented. Which bond should be decremented, the oxygen or nitrogen? Herein lies the problem; the decision is arbitrary. SELFIES chooses to decrement the last atom in the sequence (in this case, the nitrogen): `[C][#S][=Branch1][C][=O][N]`.

However, if the link instead attempted to form a double bond (i.e. `[=Ring1][C]`), the sulfur would be incremented to a triple bond, (`[#S]`) since there is no symbol for a quadruple bond, and both the sulfur-oxygen and the sulfur-nitrogen bonds are decremented: `[C][#S][=Branch1][C][O][N]`.

GRAPHIES avoids this link reweighting problem altogether by applying normal edge reweighting rules to existing edges. If an edge already exists, the link edge weight and the existing edge weight are added. If the new total edge weight exceeds the degree, then the edge is reweighted to fit the maximum allowable degree; otherwise, do nothing. The resulting GRAPHIES result is `[C][=S][=Branch1][C][=O][=N]` where the sequential link is ignored due to maximum degree violation.

### 3. Link Resolution for Unindexable Target Nodes

Non-sequential links in the graph are formed by a starting link token (`[Ring1]`) followed by a set of index tokens that encode the node-distance to the edge target from the edge source. In SELFIES, links that overshoot the target (i.e. target node index is negative) are resolved by redirecting the target to the first node in the sequence. In GRAPHIES, links with an invalid target are ignored.
Ignoring these malformed links is preferable to redirection to prevent erroneous tokens at the end of the sequence from drastically changing the graph topology. A branch of length 3, `[=Branch1][Ring2][N][C][C]` for example, that was cancelled in the manner described in part 1 would attempt to create a link targeting the 161st previous node. A single misused link token (`[Ring2]` vs `[Ring1]`) would corrupt the entire structure of the graph.
This issue appears frequently when tokens that were intended for indexing end up being resolved as normal tokens leading to spurious ring closures that were not intended.
