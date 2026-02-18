# metaselfies

> [!WARNING]
> Documentation under construction...

A Python library for tokenizing arbitrary graph structures. Metaselfies extends [SELFIES](https://github.com/aspuru-guzik-group/selfies) to encode and decode any graph representation using a configurable grammar.

## Overview

Metaselfies provides bidirectional conversion between:
- **Graphs** (networkx `Graph` objects)
- **Strings** (metaselfies tokens)

The encoding/decoding is governed by a **Grammar** that defines:
- Node types and their maximum degree
- Edge types and weights
- Branch and link structures
- Node modifiers

## Installation

> [!NOTE]
> This package will be published to PyPI once it's stable.

```bash
pip install git+https://github.com/lukasmki/metaselfies.git
```

<!-- ```bash
pip install metaselfies
``` -->

## Quick Start

```python
import networkx as nx
from metaselfies import encode, decode
from metaselfies.grammar import Grammar

# Load a grammar
grammar = Grammar.from_file("path/to/grammar.json")

# Encode a graph to metaselfies
graph = nx.Graph()
graph.add_node(0, symbol="C", degree=4)
graph.add_node(1, symbol="C", degree=4)
graph.add_edge(0, 1, symbol="-", weight=1)

metaselfies = encode(graph, grammar)
print(metaselfies)  # Output: C-C

# Decode back to graph
decoded_graph = decode(metaselfies, grammar)
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
metaselfies --help
```

```bash
python -m metaselfies --help
```

## Examples

See the `examples/` directory for usage examples.

## License

MIT
