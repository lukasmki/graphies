from pathlib import Path

import torch

from graphies.predict import GraphiesModel, GraphiesTokenizer
from graphies.predict.models import GRU

root = Path(__file__).parent.resolve()
chk = root / "chk"


tokenizer = GraphiesTokenizer.from_file(root / "fasta.json")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = GraphiesModel.from_checkpoint(
    checkpoint=chk / "9-ckpt.pt", tokenizer=tokenizer, model_cls=GRU, device=device
)


sequences = model.generate()
for sequence in sequences:
    print(sequence)
