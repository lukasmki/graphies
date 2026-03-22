import cProfile
import pstats

from graphies import Graphies

profiler = cProfile.Profile()

SESSION = Graphies("tests/selfies.json")
SELFIES = "[C][N][C][C][C][O][C][Ring1][#Branch1][Ring1][Branch1][C][Ring1][#Branch1][C][Ring1][=Branch1][Ring1][Branch1]"

profiler.enable()
GRAPH = SESSION.decode(SELFIES)
GRAPHIES = SESSION.encode(GRAPH)
profiler.disable()

stats = pstats.Stats(profiler)
stats = stats.strip_dirs().sort_stats("cumtime")
stats.print_stats(20)
stats.print_stats("decode")
stats.print_stats("encode")
