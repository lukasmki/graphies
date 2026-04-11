import random
from pathlib import Path

import polars as pl
import torch
from datasets import Dataset as HFDataset
from datasets import DatasetDict as HFDatasetDict
from polars import DataFrame
from polars.series.series import Series
from torch.utils.data import Dataset

from graphies import Decoder, Encoder
from graphies.predict.tokenizer import GraphiesTokenizer


class HFGraphiesDataset(Dataset):
    def __init__(
        self,
        dataset: HFDataset | HFDatasetDict,
        column: str,
        tokenizer: GraphiesTokenizer,
        split: str | None = "train",
        max_length: int | None = None,
    ):
        self.dataset: HFDataset | HFDatasetDict = dataset
        self.column: str = column

        if isinstance(dataset, HFDataset):
            self.graphies = dataset
        elif split is not None:
            self.graphies = dataset[split]
        else:
            raise TypeError(
                "dataset must be one of datasets.Dataset or datasets.DatasetDict with split"
            )

        self.tokenizer: GraphiesTokenizer = tokenizer
        self.max_length: int | None = max_length

    def __len__(self):
        return len(self.graphies)

    def __getitem__(self, index: int):
        graphies = self.graphies[index][self.column]
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
        return len(self.graphies)

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
        return len(self.graphies)

    def __getitem__(self, index: int):
        in_graphies = self.graphies[index]
        graph = self.decoder.decode(in_graphies)
        source = random.choice(list(graph.nodes))
        graphies = self.encoder.encode(graph, source)
        tokens = self.tokenizer.encode("[BEGIN]" + graphies + "[END]")
        if self.max_length:
            tokens = tokens[: self.max_length]
        return torch.as_tensor(tokens, dtype=torch.long)


class CSVGraphiesDPODataset(Dataset):
    def __init__(
        self,
        path: str | Path,
        selected_column: str,
        rejected_column: str,
        tokenizer: GraphiesTokenizer,
        max_length: int | None = None,
    ):
        if isinstance(path, str):
            path = Path(path)
        path = path.resolve()
        self.dataset: DataFrame = pl.read_csv(
            path,
            columns=[
                selected_column,
                rejected_column,
            ],
        )
        self.selected_column: str = selected_column
        self.rejected_column: str = rejected_column
        self.selected_graphies: Series = self.dataset[selected_column]
        self.rejected_graphies: Series = self.dataset[rejected_column]
        self.tokenizer: GraphiesTokenizer = tokenizer
        self.max_length: int | None = max_length

    def __len__(self):
        return min(len(self.selected_graphies), len(self.rejected_graphies))

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        selected_graphies = self.selected_graphies[index]
        rejected_graphies = self.rejected_graphies[index]
        selected = self.tokenizer.encode("[BEGIN]" + selected_graphies + "[END]")
        rejected = self.tokenizer.encode("[BEGIN]" + rejected_graphies + "[END]")
        if self.max_length:
            selected = selected[: self.max_length]
            rejected = rejected[: self.max_length]
        return (
            torch.as_tensor(selected, dtype=torch.long),
            torch.as_tensor(rejected, dtype=torch.long),
        )


class HFGraphiesDPODataset(Dataset):
    def __init__(
        self,
        tokenizer: GraphiesTokenizer,
        dataset: HFDataset | HFDatasetDict,
        selected_column: str,
        rejected_column: str,
        # prompt_column: str | None = None,
        split: str | None = "train",
        max_length: int | None = None,
    ):
        self.dataset: HFDataset | HFDatasetDict = dataset
        self.selected_column: str = selected_column
        self.rejected_column: str = rejected_column
        # self.prompt_column: str | None = prompt_column

        if isinstance(dataset, HFDataset):
            self.graphies = dataset
        elif split is not None:
            self.graphies = dataset[split]
        else:
            raise TypeError(
                "dataset must be one of datasets.Dataset or datasets.DatasetDict with split"
            )

        self.tokenizer: GraphiesTokenizer = tokenizer
        self.max_length: int | None = max_length

    def __len__(self):
        return len(self.graphies)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        selected_graphies = self.graphies[index][self.selected_column]
        rejected_graphies = self.graphies[index][self.rejected_column]
        selected = self.tokenizer.encode("[BEGIN]" + selected_graphies + "[END]")
        rejected = self.tokenizer.encode("[BEGIN]" + rejected_graphies + "[END]")
        if self.max_length:
            selected = selected[: self.max_length]
            rejected = rejected[: self.max_length]
        return (
            torch.as_tensor(selected, dtype=torch.long),
            torch.as_tensor(rejected, dtype=torch.long),
        )
