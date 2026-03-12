import random
from pathlib import Path

import polars as pl
import torch
from datasets import Dataset as HFDataset
from polars import DataFrame
from polars.series.series import Series
from torch.utils.data import Dataset

from graphies import Decoder, Encoder
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
        return torch.as_tensor(tokens, dtype=torch.long)


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
        self.graphies: Series = self.dataset[column]
        self.tokenizer: GraphiesTokenizer = tokenizer
        self.max_length: int | None = max_length

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, index: int):
        graphies = self.graphies[index]
        tokens = self.tokenizer.encode("[BEGIN]" + graphies + "[END]")
        if self.max_length:
            tokens = tokens[: self.max_length]

        return torch.as_tensor(tokens, dtype=torch.long)


class CSVRandomizedGraphiesDataset(Dataset):
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
        self.graphies: Series = self.dataset[column]
        self.tokenizer: GraphiesTokenizer = tokenizer
        self.max_length: int | None = max_length

        self.encoder = Encoder(self.tokenizer.grammar)
        self.decoder = Decoder(self.tokenizer.grammar)

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, index: int):
        in_graphies = self.graphies[index]
        graph = self.decoder.decode(in_graphies)
        source = random.choice(list(graph.nodes))
        graphies = self.encoder.encode(graph, source)
        tokens = self.tokenizer.encode("[BEGIN]" + graphies + "[END]")
        if self.max_length:
            tokens = tokens[: self.max_length]
        return torch.as_tensor(tokens, dtype=torch.long)
