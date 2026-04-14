# Encoding

The `Encoder` takes a NetworkX graph and produces a GRAPHIES token sequence as a string. Encoding is performed by walking the graph in depth-first order and emitting a token for each node, branch, and non-tree edge encountered along the way.

```python
encoder = Encoder(grammar)
sequence = encoder.encode(graph, source=None)
```

## DFS Spanning Tree

Encoding begins by computing a depth-first search spanning tree of the graph rooted at the source node.

```python
tree = nx.dfs_tree(graph, source=source, sort_neighbors=sorted)
```

This spanning tree decomposes the graph's edges into two categories:

- **Tree edges** - edges that appear in the DFS spanning tree, connecting a parent node to its children.
- **Non-tree edges** — edges present in the original graph but absent from the spanning tree, connecting nodes that are non-adjacent in the tree (e.g. ring closures in molecules).

The encoder then walks this tree recursively, emitting tokens that reconstruct the full graph including both categories of edges. Branches of the tree are sorted by length to ensure that the main sequence is the longest branch of the spanning tree.

## Token Sequence Construction

The core of the encoder is the `walk` method, which visits each node and returns a list of `TokenInstance` objects.

```python
def walk(self, graph, tree, node_id, parent=None) -> list[TokenInstance]:
    ...
```

For each node visited, the walk proceeds in four steps.

### 1. Emit the Node Token

A `NODE` token is emitted for the current node. If the node has a parent in the tree, its incoming edge is included in the token.

```python
node = NodeInstance(**graph.nodes[node_id])
edge = EdgeInstance(**graph.get_edge_data(node_id, parent))  # None if root
token = TokenInstance(type=TokenType.NODE, node=node, edge=edge, modifiers=node.modifiers)
```

The serialized form of a node token is `[{edge_symbol}{node_symbol}{modifier_symbols}]`. For the root node, the edge symbol is omitted.

### 2. Classify Neighbors

The node's neighbors are partitioned into three groups:

- **Children** — successors in the DFS tree (`tree.successors(node_id)`). These are nodes reached for the first time via this node.
- **Ancestors** — predecessors in the DFS tree (`tree.predecessors(node_id)`). The parent node of the current node.
- **Links** — all remaining neighbors: nodes present in the original graph but not connected to the current node by a tree edge.

```python
children = list(tree.successors(node_id))
ancestors = list(tree.predecessors(node_id))
links = set(neighbors) - set(children) - set(ancestors)
```

### 3. Emit Branch Tokens

For each child except the last, the encoder recurses into that subtree and wraps the resulting tokens in a branch structure. The last child is handled by simple tail recursion without a branch wrapper, keeping it in the main sequence.

```python
for child in children[:-1]:
    branch_tokens = self.walk(graph, tree, child, node_id)
    branch_instance = self.grammar.get_branch(size=len(branch_tokens))
    branch_prefix = [TokenInstance(type=TokenType.BRANCH, node=branch_instance, edge=edge)]
    for index in branch_instance.indices:
        branch_prefix.append(TokenInstance(type=TokenType.INDEX, node=index))
    tokens.extend(branch_prefix + branch_tokens)

# last child continues the main chain
tokens.extend(self.walk(graph, tree, children[-1], parent=node_id))
```

The branch length (number of tokens in the subtree) is encoded into a sequence of index tokens via `grammar.get_branch`. The full branch structure in the token sequence is:

```text
[BRANCH_TOKEN][INDEX_TOKEN...][subtree tokens...]
```

Branch and index tokens are serialized in the same `[symbol]` format. The index tokens encode the branch length in base 16, with the number of index tokens determined by the branch token's value (i.e. the number of hex digits required).

### 4. Emit Link Tokens

After handling branches, link tokens are emitted for any non-tree edges connecting the current node to already-visited nodes.

```python
distance = self.visited.index(node_id) - self.visited.index(link_id)
link = self.grammar.get_link(distance)
tokens.append(TokenInstance(type=TokenType.LINK, node=link, edge=edge))
for index in link.indices:
    tokens.append(TokenInstance(type=TokenType.INDEX, node=index))
```

The distance is the number of steps back along the visited node sequence from the current node to the target node. Links to nodes that have not yet been visited (negative distance) are skipped, as those edges will be handled when the target node is visited later. The full link structure in the token sequence is:

```text
[LINK_TOKEN][INDEX_TOKEN...]
```

The index tokens encode `distance - 1` in base 16, analogous to branch encoding.

## Serialization

Once the full token list is assembled, `encode` joins the symbol of each token into a single string.

```python
return "".join([t.symbol for t in tokens])
```

Each `TokenInstance` serializes itself according to its type:

```python
def serialize(self) -> str:
    if self.type == TokenType.INDEX:
        return f"[{self.node.symbol}]"
    edge_symbol = "" if (self.edge is None) or (self.edge.symbol == "*") else self.edge.symbol
    mods_symbol = "".join(m.symbol for m in self.modifiers)
    return f"[{edge_symbol}{self.node.symbol}{mods_symbol}]"
```

Node, branch, and link tokens all follow the `[{edge}{node}{modifiers}]` pattern. Index tokens use only `[{symbol}]` with no edge or modifier components.
