# GRAPHIES

<div align="center" width='100%'>
<img src='assets/logo.png' width='50%' alt='GRAPHIES logo'/>
</div>

`graphies` is a Python library for encoding degree-limited graphs with discrete node and edge types as GRAPHIES strings.
Using a JSON configurable grammar, you can represent molecules, proteins, colored graphs, and more!

## Overview

`graphies` provides bidirectional conversion between GRAPHIES strings and `networkx` graphs.

Graph transcoding is governed by a Grammar that defines:

- A set of node types and their maximum degrees
- A set of edge types and their weights
- Node modifiers representing node internal state, containing data or altering node degree
- Structural token symbols including fork/branch symbols, link/ring-closure symbols, and optionally self-referencing numeric symbols.

GRAPHIES are more akin to computer programs than natural language. Given a particular grammar, a GRAPHIES token sequence provides an ordered set of instructions to deterministically reproduce the encoded graph.

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

The predict module provides simple models and high-level classes for inference and training of generative next-token prediction models on GRAPHIES.

To use the predict module, install with the `predict` optional dependencies.

```bash
pip install 'graphies[predict] @ git+https://github.com/lukasmki/graphies.git'
```

or with `uv`

```bash
uv pip install --extra predict git+https://github.com/lukasmki/graphies.git
```

The predict module depends on PyTorch and installation will vary by hardware.
Follow the [PyTorch installation instructions](https://pytorch.org/get-started/locally/) for your system.

## Quick Start

```python
import networkx as nx
from graphies import Graphies

# Load a grammar
g = Graphies("path/to/grammar.json")

# Encode a graph to graphies
graph = nx.Graph()
graph.add_node(0, symbol="C", degree=4)
graph.add_node(1, symbol="C", degree=4)
graph.add_edge(0, 1, symbol="-", weight=1)

graphies = g.encode(graph)
print(graphies)  # Output: [C][C]

# Decode back to graph
decoded_graph = g.decode(graphies)
```

## Examples

See the `examples/` directory for usage examples.

## Citation

```bibtex
@software{Kim_Graphies_2026,
  author = {Kim, Lukas},
  title = {Graphies},
  url = {https://github.com/lukasmki/graphies},
  year = {2026},
  version = {0.1},
}
```

## Documentation

> [!WARNING]
> Documentation under construction...

Build the documentation.

```bash
cd docs/
make html
```
