import re
from pathlib import Path

import torch
from torch import Tensor
from torch.nn.utils.rnn import pad_sequence

from graphies.grammar import Grammar


class GraphiesTokenizer:
    def __init__(self, grammar: Grammar | str | Path):
        self.grammar: Grammar = Grammar.from_file(grammar)
        self.control: dict[str, int] = {
            "[NULL]": 0,
            "[BEGIN]": 1,
            "[ENDBEGIN]": 2,
            "[END]": 3,
        }
        self.inv_control: dict[int, str] = {v: k for k, v in self.control.items()}
        self.vocab: dict[str, int] = self.grammar.to_vocab()
        self.inv_vocab: dict[int, str] = {v: k for k, v in self.vocab.items()}

        self.ncontrol: int = len(self.control)
        self.nvocab: int = len(self.vocab)

    @property
    def vocab_size(self) -> int:
        return self.ncontrol + self.nvocab

    @property
    def null_index(self) -> int:
        return self.control["[NULL]"]

    @property
    def begin_index(self) -> int:
        return self.control["[BEGIN]"]

    @property
    def end_index(self) -> int:
        return self.control["[END]"]

    def get_token_int(self, token: str) -> int:
        """Get the vocabulary index of a token string
        Returns the null token if not found
        """
        if (ctrl := self.control.get(token)) is not None:
            return ctrl
        if (idx := self.vocab.get(token)) is not None:
            return self.ncontrol + idx
        return self.null_index

    def get_token_str(self, index: int) -> str:
        """Get token string from its vocabulary index"""
        if (ctrl := self.inv_control.get(index)) is not None:
            return ctrl
        if (idx := self.inv_vocab.get(index - self.ncontrol)) is not None:
            return idx
        return "[NULL]"

    def encode(self, string: str) -> list[int]:
        """Encode a graphies string to a list of token indices"""
        TOKEN_RE: re.Pattern[str] = re.compile(pattern=r"\[[^\]]*\]|[^\[\]\s]")
        tokens: list[int] = [
            self.get_token_int(token) for token in TOKEN_RE.findall(string)
        ]
        return tokens

    def decode(self, sequence: list[int]) -> str:
        """Decode a list of token indices to a graphies string"""
        tokens: list[str] = [self.get_token_str(index) for index in sequence]
        return "".join(tokens)

    def collate(self, batch: list[Tensor]) -> tuple[Tensor, Tensor]:
        """Pads the sequences to match the longest length sequence in the batch
        Returns the padded token sequences and sequence lengths
        """
        lengths = torch.tensor([len(x) for x in batch])
        padded = pad_sequence(batch, batch_first=True, padding_value=self.null_index)
        return padded, lengths

    def collate_dpo(self, batch: list[tuple[Tensor, Tensor]]) -> tuple[Tensor, Tensor]:
        selected, rejected = map(list, zip(*batch, strict=True))
        return self.collate(selected + rejected)

    def strip(self, string: str) -> str:
        "Strips the graphies string of start and end tokens"
        if string.startswith("[BEGIN]"):
            string = string[7:]
        if string.endswith("[END]"):
            string = string[:-5]
        return string

    def wrap(self, string: str, partial: bool = False) -> str:
        """Wraps the graphies string with start and end tokens
        if partial, ends with [ENDBEGIN] rather than [END]
        """
        if partial:
            return f"[BEGIN]{string}[ENDBEGIN]"
        return f"[BEGIN]{string}[END]"

    def join(self, strings: list[str]) -> str:
        "Concatenate prompt/response strings and wrap with control tokens"
        assert len(strings) >= 2, "join requires at least a prompt and a response"
        return f"[BEGIN]{'[ENDBEGIN]'.join(strings)}[END]"
