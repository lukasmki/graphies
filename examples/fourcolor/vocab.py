import json
from pathlib import Path

import graphies as gf

root = Path(__file__).parent.resolve()

grammar_path = root / "fourcolor.json"
vocab_path = root / "fourcolor_vocab.json"

grammar = gf.Grammar.from_file(path=grammar_path)
vocab_path.write_text(json.dumps(grammar.to_vocab(), indent=4))
