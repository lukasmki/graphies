import csv
from collections.abc import Callable
from pathlib import Path
from typing import Any

import torch
from torch.nn.utils import clip_grad_norm_
from torch.optim import Optimizer
from torch.optim.lr_scheduler import LRScheduler, ReduceLROnPlateau
from torch.utils.data import DataLoader
from tqdm import tqdm

from graphies.predict.models import GRU

type SupportedModel = GRU


class GraphiesTrainer:
    def __init__(
        self,
        model: SupportedModel,
        optimizer: Optimizer,
        scheduler: LRScheduler | None = None,
        device: torch.device | str | None = None,
        checkpoint: dict[str, Any] | None = None,
    ):
        """Training loop wrapper

        Args:
            model (nn.Module): initialized model to train
            optimizer (Optimizer): initialized optimizer
            scheduler (LRScheduler | None, optional):
            initialized learning rate
            scheduler. Defaults to None.
            device (torch.device | str | None, optional):
            device to train on. Defaults to None.
            checkpoint (dict[str, Any] | None, optional):
                Set `model_kwargs`, `optimizer_kwargs`, and `scheduler_kwargs`
                to enable full restore from checkpoint.
                Any state_dicts will be overwritten and not loaded.
                Use `from_checkpoint()` to load from a checkpoint.
                Defaults to None.

        """
        self.model: SupportedModel = model
        self.optimizer: Optimizer = optimizer
        self.scheduler: LRScheduler | None = scheduler
        self.device: torch.device | str | None = device
        if device:
            self.model.to(device)

        # checkpoint
        self.ckpt: dict[str, Any] = {
            "model_kwargs": {},
            "optimizer_kwargs": {},
            "scheduler_kwargs": {},
        }
        self.epoch = 0
        if checkpoint is not None:
            self.ckpt.update(checkpoint)
            self.epoch = checkpoint.get("epoch", 0)

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint: str | Path | dict,
        model_cls: type[SupportedModel],
        optimizer_cls: type[Optimizer],
        scheduler_cls: type[LRScheduler] | None = None,
        model_kwargs: dict[str, Any] | None = None,
        optimizer_kwargs: dict[str, Any] | None = None,
        scheduler_kwargs: dict[str, Any] | None = None,
        device: torch.device | str | None = None,
    ) -> "GraphiesTrainer":
        if isinstance(checkpoint, str):
            path = Path(checkpoint).resolve()
            ckpt = torch.load(path, map_location=device)
        elif isinstance(checkpoint, Path):
            ckpt = torch.load(checkpoint, map_location=device)
        else:
            ckpt = checkpoint

        # model
        if model_kwargs:
            ckpt["model_kwargs"].update(model_kwargs)
        model = model_cls(**ckpt["model_kwargs"])
        model.load_state_dict(ckpt["model_state_dict"])
        model.to(device)

        # optimizer
        if optimizer_kwargs:
            ckpt["optimizer_kwargs"].update(optimizer_kwargs)
        optimizer = optimizer_cls(params=model.parameters(), **ckpt["optimizer_kwargs"])
        optimizer.load_state_dict(ckpt["optimizer_state_dict"])

        # scheduler
        if scheduler_cls:
            if scheduler_kwargs:
                ckpt["scheduler_kwargs"].update(scheduler_kwargs)
            scheduler = scheduler_cls(optimizer, **ckpt["scheduler_kwargs"])
            scheduler.load_state_dict(ckpt["scheduler_state_dict"])
        else:
            scheduler = None

        return cls(
            model=model,
            optimizer=optimizer,
            scheduler=scheduler,
            device=device,
            checkpoint=ckpt,
        )

    def save_checkpoint(self, path: str | Path) -> None:
        # update checkpoint dict
        self.ckpt.update(
            {
                "epoch": self.epoch,
                "model_state_dict": self.model.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
            }
        )
        if self.scheduler:
            self.ckpt.update({"scheduler_state_dict": self.scheduler.state_dict()})

        # save to path
        path = Path(path) if isinstance(path, str) else path
        path.resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(self.ckpt, path.with_suffix(".pt"))

    def train(
        self,
        train: DataLoader,
        epochs: int,
        loss_fn: Callable[
            [SupportedModel, tuple[torch.Tensor, torch.Tensor]], torch.Tensor
        ]
        | None = None,
        log: str | Path | None = None,
        log_interval: int = 1,
        checkpoint: str | Path | None = None,
        checkpoint_interval: int = 1,
        val: DataLoader | None = None,
        val_interval: int = 1,
        test: DataLoader | None = None,
        test_interval: int = 1,
    ) -> None:
        writer = None  # init for csv logging
        if loss_fn is None:
            try:
                loss_fn = self.model.loss_fn
            except AttributeError as e:
                raise ValueError(
                    "Either provide an eval/loss function or implement in model class"
                ) from e

        for epoch in range(self.epoch, self.epoch + epochs):
            # train
            self.model.train()
            pbar = tqdm(train, desc=f"Epoch {epoch + 1}")
            train_loss = 0.0
            for i, batch in enumerate(pbar):
                self.optimizer.zero_grad()

                sequences, lengths = batch
                sequences = sequences.to(self.device)
                lengths = lengths.to(self.device)
                loss = loss_fn(self.model, (sequences, lengths))

                loss.backward()
                clip_grad_norm_(self.model.parameters(), 1.0)
                self.optimizer.step()

                train_loss += loss.item()
                avg_train_loss = train_loss / (i + 1)
                pbar.set_postfix(loss=f"{avg_train_loss:0.4f}")

            # validation
            val_loss = avg_val_loss = None
            if val is not None and ((epoch + 1) % val_interval == 0):
                self.model.eval()
                pbar = tqdm(val, desc=f"Validation {epoch + 1}")
                val_loss = 0.0
                for i, batch in enumerate(pbar):
                    sequences, lengths = batch
                    sequences = sequences.to(self.device)
                    lengths = lengths.to(self.device)
                    loss = loss_fn(self.model, (sequences, lengths))
                    val_loss += loss.item()
                    avg_val_loss = val_loss / (i + 1)
                    pbar.set_postfix(loss=f"{avg_val_loss:0.4f}")

            # test
            test_loss = avg_test_loss = None
            if test is not None and ((epoch + 1) % test_interval == 0):
                self.model.eval()
                pbar = tqdm(test, desc=f"Test {epoch + 1}")
                test_loss = 0.0
                for i, batch in enumerate(pbar):
                    sequences, lengths = batch
                    sequences = sequences.to(self.device)
                    lengths = lengths.to(self.device)
                    loss = loss_fn(self.model, (sequences, lengths))
                    test_loss += loss.item()
                    avg_test_loss = test_loss / (i + 1)
                    pbar.set_postfix(loss=f"{avg_test_loss:0.4f}")

            # update lr scheduler
            self.epoch = epoch + 1
            if self.scheduler:
                if isinstance(self.scheduler, ReduceLROnPlateau):
                    self.scheduler.step(metrics=avg_train_loss)
                else:
                    self.scheduler.step()

            # checkpoint
            if checkpoint is not None and ((epoch + 1) % checkpoint_interval == 0):
                checkpoint = Path(checkpoint)
                self.save_checkpoint(
                    checkpoint.with_stem(f"{epoch}-" + checkpoint.stem)
                )

            # logging
            if log is not None:
                log = Path(log) if isinstance(log, str) else log
                log.parent.mkdir(parents=True, exist_ok=True)

                output = {
                    "epoch": epoch,
                    "avg_train_loss": avg_train_loss,
                    "avg_val_loss": avg_val_loss,
                    "avg_test_loss": avg_test_loss,
                }
                if writer is None:
                    file = log.open("a", newline="")
                    writer = csv.DictWriter(file, fieldnames=output.keys())

                if epoch == 0:
                    writer.writeheader()
                writer.writerow(output)
                file.flush()

        file.close()
