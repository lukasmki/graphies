from pathlib import Path

import polars as pl
from encode import format_colored_graph
from fourcolor import four_color_graph, random_planar_graph

from graphies import encode

root = Path(__file__).parent.resolve()


def generate_fourcolored_graph(num_nodes=10) -> str:
    planar = random_planar_graph(n=num_nodes)
    colored = four_color_graph(planar)
    graph = format_colored_graph(colored)
    graphies = encode(graph, root / "fourcolor.json")
    return graphies


if __name__ == "__main__":
    N = 10_000
    n = 10
    graphies = [generate_fourcolored_graph(num_nodes=n) for i in range(N)]

    df = pl.DataFrame({"graphies": graphies})
    df.write_csv(root / "fourcolor.csv")
