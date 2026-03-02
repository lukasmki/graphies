# GRAPHIES

**GRAPH Indexed Embedded Strings**

> [!WARNING]
> Documentation under construction...

A Python library for tokenizing arbitrary graph structures. `graphies` is a graph embedding language that can encode and decode any graph representation using a configurable grammar.

## Overview

`graphies` provides bidirectional conversion between:
- **Graphs** (networkx `Graph` objects)
- **Strings** (graphies tokens)

The encoding/decoding is governed by a **Grammar** that defines:
- Node types and their maximum degree
- Edge types and weights
- Branch and link structures
- Node modifiers

## Installation

> [!NOTE]
> This package will be published to PyPI once it's stable.

```bash
pip install git+https://github.com/lukasmki/graphies.git
```

<!-- ```bash
pip install graphies
``` -->

### Predict Module

To use the predict module install with the `predict` optional dependencies.

```bash
pip install 'graphies[predict] @ git+https://github.com/lukasmki/graphies.git'
```

or with `uv`

```bash
uv pip install --extra predict git+https://github.com/lukasmki/graphies.git
```

## Quick Start

```python
import networkx as nx
from graphies import Grammar, encode, decode

# Load a grammar
grammar = Grammar.from_file("path/to/grammar.json")

# Encode a graph to graphies
graph = nx.Graph()
graph.add_node(0, symbol="C", degree=4)
graph.add_node(1, symbol="C", degree=4)
graph.add_edge(0, 1, symbol="-", weight=1)

graphies = encode(graph, grammar)
print(graphies)  # Output: [C][C]

# Decode back to graph
decoded_graph = decode(graphies, grammar)
```

## Citation

```bibtex
@software{Kim_Graphies_2025,
  author = {Kim, Lukas},
  title = {Graphies},
  url = {https://github.com/lukasmki/graphies},
  year = {2025},
  version = {0.1},
}
```

## Documentation

Build the documentation.

```bash
cd docs/
make html
```

## Token Types

There are four types of tokens:

| Token Type | Description | Token Format |
|------------|-------------|--------|
| **Node** | Represents graph vertices | `{edge?}{node}{modifiers?}` |
| **Branch** | Starts a branch | `{edge?}{structure}` |
| **Link** | Creates back-references | `{edge?}{structure}` |
| **Index** | Specifies branch/link size | `{index}` |

## Grammar Format

A grammar is defined in JSON format. See `examples/selfies.json` for the SELFIES grammar.

### Grammar Fields

| Field | Description |
|-------|-------------|
| `nodes` | List of node types with their maximum degree |
| `edges` | List of edge types with their weights |
| `branches` | Branch structures for encoding child subtrees |
| `links` | Link structures for encoding back-references (rings) |
| `index` | Index symbols for specifying sizes |
| `modifiers` | Node modifiers (chirality, charge, etc.) |

## CLI Usage

```bash
graphies --help
```

```bash
python -m graphies --help
```

## Examples

See the `examples/` directory for usage examples.

## License

MIT
