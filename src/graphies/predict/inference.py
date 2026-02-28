from pathlib import Path

import torch
from torch.nn import Module

from graphies.predict.tokenizer import GraphiesTokenizer


class GraphiesModel:
    def __init__(
        self,
        tokenizer: GraphiesTokenizer,
        model: Module,
        device: str | torch.device | int | None = None,
    ):
        self.tokenizer: GraphiesTokenizer = tokenizer
        self.model: Module = model
        self.device = device
        if device:
            self.model.to(device=device)

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint: str | Path | dict,
        tokenizer: GraphiesTokenizer,
        model_cls: type[Module],
        device: torch.device | str | None = None,
    ) -> "GraphiesModel":
        if isinstance(checkpoint, str):
            path = Path(checkpoint).resolve()
            ckpt = torch.load(path, map_location=device)
        elif isinstance(checkpoint, Path):
            ckpt = torch.load(checkpoint, map_location=device)
        else:
            ckpt = checkpoint
        model = model_cls(**ckpt["model_kwargs"])
        model.load_state_dict(ckpt["model_state_dict"])
        return cls(model=model, tokenizer=tokenizer, device=device)

    @torch.inference_mode()
    def _generate(
        self,
        sequences: torch.Tensor,
        lengths: torch.Tensor,
        hidden: torch.Tensor | None = None,
        temperature: float = 1,
        top_p: float = 1,
        max_len=200,
        end_all=True,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        self.model.eval()
        sequences = sequences.to(device=self.device)
        lengths = lengths.to(device=self.device)

        length_one = torch.ones_like(lengths)
        next_tokens = sequences[:, [-1]]
        seq_mask = torch.ones_like(lengths, dtype=torch.bool, device=self.device)

        if hidden is None:
            _, hidden = self.model(sequences, lengths)

        for _ in range(max_len):
            logits, hidden = self.model(next_tokens, length_one, hidden)
            last_logits = logits[:, -1, :]

            # temperature + top_p
            probs = torch.softmax(last_logits / temperature, dim=-1)
            sorted_probs, sorted_indices = torch.sort(probs, descending=True)
            cumulative_probs = torch.cumsum(sorted_probs, dim=-1)

            cutoff = cumulative_probs > top_p
            # extend the mask to include the token that crossed the threshold
            cutoff[:, 1:] = cutoff[:, :-1].clone()
            cutoff[:, 0] = False  # ensure at least the first choice is available
            sorted_probs[cutoff] = 0.0

            renormalized_probs = sorted_probs / torch.sum(
                sorted_probs, dim=-1, keepdim=True
            )

            samples = torch.multinomial(renormalized_probs, 1)
            next_tokens = torch.gather(sorted_indices, -1, samples)

            # set finished sequences to null
            next_tokens[~seq_mask] = self.tokenizer.null_index

            # add next tokens to all sequences
            sequences = torch.hstack((sequences, next_tokens))
            lengths[seq_mask] += 1

            # update sequence mask
            reached_end = next_tokens.squeeze(-1) == self.tokenizer.end_index
            seq_mask = seq_mask & ~reached_end

            if not torch.any(seq_mask):
                break
        else:  # handle unterminated sequences
            next_tokens[seq_mask] = (
                self.tokenizer.end_index if end_all else self.tokenizer.null_index
            )
            sequences = torch.hstack((sequences, next_tokens))
            lengths[seq_mask] += 1

        return sequences, lengths

    def generate(
        self,
        num: int = 16,
        temperature: float = 1,
        top_p: float = 1,
        max_len: int = 200,
    ) -> list[str]:
        self.model.eval()

        sequences = torch.ones((num, 1), dtype=torch.long, device=self.device)
        lengths = torch.ones((num,), dtype=torch.long, device=self.device)

        sequences, lengths = self._generate(
            sequences, lengths, temperature=temperature, top_p=top_p, max_len=max_len
        )

        seq_out: list[list[int]] = sequences.tolist()
        len_out: list[int] = lengths.tolist()
        str_out = [
            self.tokenizer.decode(seq_int[:length])
            for seq_int, length in zip(seq_out, len_out, strict=True)
        ]
        return str_out
