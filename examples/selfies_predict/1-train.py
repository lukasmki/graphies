from pathlib import Path

import torch
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader, random_split

from graphies.predict import (
    CSVRandomizedGraphiesDataset,
    GraphiesTokenizer,
    GraphiesTrainer,
)
from graphies.predict.models import GRU

root = Path(__file__).parent.resolve()
chk = root / "chk"
chk.mkdir(parents=True, exist_ok=True)


tokenizer = GraphiesTokenizer.from_file(root / "selfies.json")
dataset = CSVRandomizedGraphiesDataset(root / "qm9.selfies.csv", "selfies", tokenizer)


trn, tst = random_split(dataset, [0.9, 0.1])
torch.save({"trn_indices": trn.indices, "tst_indices": tst.indices}, chk / "split.pt")
trn_loader = DataLoader(
    dataset=trn,
    batch_size=16,
    shuffle=True,
    collate_fn=tokenizer.collate,
)
tst_loader = DataLoader(
    dataset=tst,
    batch_size=16,
    shuffle=True,
    collate_fn=tokenizer.collate,
)


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = GRU(vocab_size=tokenizer.vocab_size)
optimizer = Adam(params=model.parameters(), lr=1e-3)
scheduler = ReduceLROnPlateau(optimizer, mode="min", patience=3, factor=0.1)
checkpoint = {
    "model_kwargs": {"vocab_size": tokenizer.vocab_size},
    "optimizer_kwargs": {"lr": 1e-3},
    "scheduler_kwargs": {"mode": "min", "patience": 3, "factor": 0.1},
}


trainer = GraphiesTrainer(model, optimizer, scheduler, device, checkpoint)
trainer.train(
    train=trn_loader,
    epochs=10,
    log=chk / "log.csv",
    checkpoint=chk / "ckpt.pt",
    test=tst_loader,
    test_interval=1,
)
