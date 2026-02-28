from pathlib import Path

import torch

import graphies as gf
from graphies.grammar import Grammar
from graphies.predict import GraphiesModel, GraphiesTokenizer
from graphies.predict.models import GRU

root = Path(__file__).parent.resolve()
chk = root / "chk"

grammar = Grammar.from_file(root / "selfies.json")
tokenizer = GraphiesTokenizer(grammar)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = GraphiesModel.from_checkpoint(
    checkpoint=chk / "9-ckpt.pt", tokenizer=tokenizer, model_cls=GRU, device=device
)


sequences = model.generate(temperature=1.1)
for sequence in sequences:
    graphies = tokenizer.strip(sequence)
    print(graphies)
    try:
        _ = gf.decode(graphies, grammar)
    except ValueError as e:
        print(e)
    except KeyError as e:
        print(e)
