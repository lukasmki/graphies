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
