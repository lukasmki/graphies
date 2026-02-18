import json
from pathlib import Path

import graphies as msf

root = Path(__file__).parent.resolve()

grammar = msf.Grammar.from_file(path=root / "selfies.json")
alphabet = grammar.to_alphabet()

output_path = root / "selfies_alphabet.json"
output_path.write_text(json.dumps(alphabet, indent=4))
