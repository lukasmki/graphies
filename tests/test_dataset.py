from datasets.load import load_dataset
from torch.utils.data import DataLoader

from graphies.predict import GraphiesTokenizer, HFGraphiesDataset
from graphies.predict.dataset import CSVGraphiesDPODataset


def test_dpo_batching():
    tokenizer = GraphiesTokenizer("tests/fourcolor.json")
    dataset = CSVGraphiesDPODataset(
        "tests/fourcolor-planar-dpo.csv",
        selected_column="selected",
        rejected_column="rejected",
        tokenizer=tokenizer,
    )

    loader = DataLoader(
        dataset,
        batch_size=2,
        shuffle=False,
        collate_fn=tokenizer.collate_dpo,
    )

    print()
    for batch in loader:
        print(batch)
        break


def test_dataset_slicing():
    tokenizer = GraphiesTokenizer("tests/selfies.json")
    dataset = load_dataset("lukaskim/ChEMBL-36", "molecules", split="train")
    dset = HFGraphiesDataset(
        dataset, column="canonical_smiles", tokenizer=tokenizer, split=None
    )
    dset = dset[1]
    print(dset)
