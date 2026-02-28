from pathlib import Path

import polars as pl
import torch
from datasets import Dataset as HFDataset
from polars import DataFrame
from torch.utils.data import Dataset

from graphies.predict.tokenizer import GraphiesTokenizer


class HFGraphiesDataset(Dataset):
    def __init__(
        self,
        dataset: HFDataset,
        column: str,
        tokenizer: GraphiesTokenizer,
        max_length: int | None = None,
    ):
        self.dataset: HFDataset = dataset
        self.column: str = column
        self.tokenizer: GraphiesTokenizer = tokenizer
        self.max_length: int | None = max_length

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, index):
        graphies = self.dataset[index][self.column]
        tokens = self.tokenizer.encode("[BEGIN]" + graphies + "[END]")
        if self.max_length:
            tokens = tokens[: self.max_length]
        return torch.tensor(tokens, dtype=torch.long)


class CSVGraphiesDataset(Dataset):
    def __init__(
        self,
        path: str | Path,
        column: str,
        tokenizer: GraphiesTokenizer,
        max_length: int | None = None,
    ):
        if isinstance(path, str):
            path = Path(path)
        path = path.resolve()
        self.dataset: DataFrame = pl.read_csv(path, columns=[column])
        self.column: str = column
        self.tokenizer: GraphiesTokenizer = tokenizer
        self.max_length: int | None = max_length

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, index: int):
        graphies = self.dataset.row(index, named=True)[self.column]
        tokens = self.tokenizer.encode("[BEGIN]" + graphies + "[END]")
        if self.max_length:
            tokens = tokens[: self.max_length]

        return torch.tensor(tokens, dtype=torch.long)
