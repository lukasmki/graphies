import torch.nn as nn
from torch import Tensor
from torch.nn.functional import cross_entropy
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence


class GRU(nn.Module):
    def __init__(
        self,
        vocab_size: int,
        hidden_dim: int = 512,
        n_layers: int = 3,
        dropout: float = 0.1,
    ):
        super().__init__()

        # Embedding layer
        self.embedding = nn.Embedding(
            num_embeddings=vocab_size,
            embedding_dim=hidden_dim,
        )

        # GRU layers
        self.gru = nn.GRU(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=n_layers,
            dropout=dropout if n_layers > 1 else 0.0,
            batch_first=True,
        )

        # Linear projection to vocab
        self.output = nn.Linear(
            in_features=hidden_dim,
            out_features=vocab_size,
        )

    def forward(
        self, sequences: Tensor, lengths: Tensor, hidden: Tensor | None = None
    ) -> tuple[Tensor, Tensor]:
        """Args:
            sequence: Tensor with shape (B, T)
            lengths: Tensor with shape (B,)
            hidden: Initial hidden state tensor with shape (L*D, B, H)

        Returns:
            logits: (B, T, vocab_size)
            hidden: last hidden state (L*D, B, H)

        """
        embedding = self.embedding(sequences)

        packed_in = pack_padded_sequence(
            input=embedding,
            lengths=lengths.cpu(),
            batch_first=True,
            enforce_sorted=False,
        )
        packed_out, hidden = self.gru(packed_in, hidden)
        unpacked_out, _ = pad_packed_sequence(sequence=packed_out, batch_first=True)

        logits = self.output(unpacked_out)
        return logits, hidden

    @staticmethod
    def loss_fn(self: "GRU", batch: tuple[Tensor, Tensor]) -> Tensor:
        sequences, lengths = batch
        logits, hidden = self(sequences, lengths)
        targets = sequences[:, 1:]  # (B, T-1)
        preds = logits[:, :-1, :]  # (B, T-1, V)
        loss = cross_entropy(
            input=preds.reshape(-1, preds.size(-1)),  # (N, V)
            target=targets.reshape(-1),  # (N,)
            ignore_index=0,
        )
        return loss


class LSTM(nn.Module):
    def __init__(
        self,
        vocab_size: int,
        hidden_dim: int = 512,
        n_layers: int = 3,
        dropout: float = 0.1,
    ):
        super().__init__()

        # Embedding layer
        self.embedding = nn.Embedding(
            num_embeddings=vocab_size,
            embedding_dim=hidden_dim,
        )

        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=n_layers,
            dropout=dropout if n_layers > 1 else 0.0,
            batch_first=True,
        )

        # Linear projection to vocab
        self.output = nn.Linear(
            in_features=hidden_dim,
            out_features=vocab_size,
        )

    def forward(
        self,
        sequences: Tensor,
        lengths: Tensor,
        hidden: tuple[Tensor, Tensor] | None = None,
    ) -> tuple[Tensor, tuple[Tensor, Tensor]]:
        """
        Args:
            sequences: (B, T)
            lengths:   (B,)
            hidden:    Optional (h_0, c_0) each of shape (L, B, H)

        Returns:
            logits: (B, T, vocab_size)
            hidden: (h_n, c_n)
        """

        embedding = self.embedding(sequences)

        packed_in = pack_padded_sequence(
            input=embedding,
            lengths=lengths.cpu(),
            batch_first=True,
            enforce_sorted=False,
        )
        packed_out, hidden = self.lstm(packed_in, hidden)
        unpacked_out, _ = pad_packed_sequence(
            sequence=packed_out,
            batch_first=True,
        )

        logits = self.output(unpacked_out)
        return logits, hidden

    @staticmethod
    def loss_fn(self: "LSTM", batch: tuple[Tensor, Tensor]) -> Tensor:
        sequences, lengths = batch
        logits, _ = self(sequences, lengths)
        targets = sequences[:, 1:]  # (B, T-1)
        preds = logits[:, :-1, :]  # (B, T-1, V)
        loss = cross_entropy(
            input=preds.reshape(-1, preds.size(-1)),
            target=targets.reshape(-1),
            ignore_index=0,
        )
        return loss
