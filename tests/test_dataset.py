from torch.utils.data import DataLoader

from graphies.predict import GraphiesTokenizer
from graphies.predict.dataset import CSVGraphiesDPODataset


def test_dpo_batching():
    tokenizer = GraphiesTokenizer.from_file("tests/fourcolor.json")
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
