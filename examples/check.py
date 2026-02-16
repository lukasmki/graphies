import json
from pathlib import Path

chempleter_vocab: dict = json.loads(Path("examples/chempleter_vocab.json").read_text())
selfies_vocab: dict = json.loads(Path("examples/selfies_vocab.json").read_text())

for k, v in chempleter_vocab.items():
    if k.strip("[]") in selfies_vocab:
        # print(k.strip("[]"), "Good")
        pass
    else:
        print(k.strip("[]"), "Not present")
