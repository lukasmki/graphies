from pathlib import Path

import networkx as nx
import torch

import graphies as gf
from graphies.grammar import Grammar
from graphies.predict import GraphiesModel, GraphiesTokenizer
from graphies.predict.models import GRU

# logging.basicConfig(level=logging.DEBUG)

root = Path(__file__).parent.resolve()
chk = root / "chk"

grammar = Grammar.from_file(root / "fourcolor.json")
tokenizer = GraphiesTokenizer(grammar)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def get_latest_checkpoint():
    latest = max(
        [
            int(file.name.split("-")[0])
            for file in chk.iterdir()
            if file.name.endswith("chk.pt")
        ]
    )
    return str(latest)


model = GraphiesModel.from_checkpoint(
    checkpoint=chk / f"{get_latest_checkpoint()}-chk.pt",
    tokenizer=tokenizer,
    model_cls=GRU,
    device=device,
)
print("Loaded model", chk / f"{get_latest_checkpoint()}-chk.pt")


def is_four_colored(graph: nx.Graph):
    for u, v in graph.edges:
        if graph.nodes[u]["color"] == graph.nodes[v]["color"]:
            return False
    else:
        return True


sequences = model.generate(temperature=1.0, top_p=1.0)
for sequence in sequences:
    graphies = tokenizer.strip(sequence)
    print("GENERATED", graphies)
    graph = gf.decode(graphies, grammar)
    graph_selfies = gf.encode(graph, grammar)
    print("COLORED", is_four_colored(graph))
    print("PLANAR", nx.is_planar(graph))
    print("GRAPHIES", graph_selfies)
    print()
