import json
from pathlib import Path

import graphies as msf

root = Path(__file__).parent.resolve()

grammar = msf.Grammar.from_file(path=root / "selfies.json")
vocab = grammar.to_vocab()

output_path = root / "selfies_vocab.json"
output_path.write_text(json.dumps(vocab, indent=4))
