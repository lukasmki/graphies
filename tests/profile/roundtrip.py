import cProfile
import pstats

from graphies import decode, encode
from graphies.grammar import Grammar

profiler = cProfile.Profile()



SELFIES = "[C][N][C][C][C][O][C][Ring1][#Branch1][Ring1][Branch1][C][Ring1][#Branch1][C][Ring1][=Branch1][Ring1][Branch1]"

profiler.enable()
GRAMMAR = Grammar.from_file("tests/selfies.json")
for _ in range(1000):
    GRAPH = decode(SELFIES, GRAMMAR)
    GRAPHIES = encode(GRAPH, GRAMMAR)
profiler.disable()

stats = pstats.Stats(profiler)
stats.strip_dirs().sort_stats("cumtime").print_stats(20)
