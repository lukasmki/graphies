from pathlib import Path

import torch
from torch.optim import AdamW
from torch.utils.data import DataLoader

from graphies.predict import (
    CSVGraphiesDPODataset,
    GraphiesTokenizer,
    GraphiesTrainer,
)
from graphies.predict.models import GRU

root = Path(__file__).parent.resolve()
chk = root / "chk"
chk.mkdir(parents=True, exist_ok=True)
dpo = root / "dpo"
dpo.mkdir(parents=True, exist_ok=True)


tokenizer = GraphiesTokenizer.from_file(root / "fourcolor.json")
dataset = CSVGraphiesDPODataset(
    root / "fourcolor-planar-dpo.csv",
    selected_column="selected",
    rejected_column="rejected",
    tokenizer=tokenizer,
)

trn_loader = DataLoader(
    dataset=dataset,
    batch_size=16,
    shuffle=True,
    collate_fn=tokenizer.collate_dpo,
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# reinitialize from checkpoint
def get_latest_checkpoint():
    files = [f for f in chk.glob("*-chk.pt")]
    latest = max(int(f.name.split("-")[0]) for f in files)
    return latest


ckpt = torch.load(chk / f"{get_latest_checkpoint()}-chk.pt", map_location=device)
model = GRU(**ckpt["model_kwargs"])
model.load_state_dict(ckpt["model_state_dict"])
optimizer = AdamW(model.parameters(), lr=1e-5)
checkpoint = {
    "model_kwargs": ckpt["model_kwargs"],
    "optimizer_kwargs": {"lr": 1e-5},
}

# create new trainer
trainer = GraphiesTrainer(
    model=model,
    optimizer=optimizer,
    device=device,
    checkpoint=checkpoint,
)
trainer.train(
    train=trn_loader,
    epochs=5,
    log=dpo / "log.csv",
    checkpoint=dpo / "chk.pt",
)
