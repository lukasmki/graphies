from importlib.util import find_spec

if find_spec("torch") is None:
    raise ImportError("Install torch to use the graphies.predict module")

import numpy as np

from graphies.predict import GraphiesModel, GraphiesTokenizer
from graphies.predict.models import GRU

TOKENIZER = GraphiesTokenizer.from_file("tests/selfies.json")
MODEL = GraphiesModel.from_checkpoint(
    "tests/chembl-pretrained.pt",
    TOKENIZER,
    GRU,
    "cuda",
)


def test_generate(max_len=20):
    graphies = MODEL.generate(
        num=16,
        temperature=1,
        top_p=1,
        max_len=max_len,
    )

    print()
    for gf in graphies:
        seq = TOKENIZER.encode(gf)
        print(len(seq), gf)
        assert len(seq) - 2 <= max_len


def test_extend(max_len=10):
    prefixes = MODEL.generate(
        num=4,
        temperature=1,
        top_p=1,
        max_len=10,
    )
    prefixes = [TOKENIZER.strip(seq) for seq in prefixes]

    graphies = MODEL.extend(
        prefixes,
        num=4,
        temperature=1,
        top_p=1,
        max_len=max_len,
    )

    print()
    for gf in graphies:
        seq = TOKENIZER.encode(gf)
        print(len(seq), gf)
        assert len(seq) - 2 <= max_len + 10


def test_embed(max_len=10):
    graphies = MODEL.generate(
        num=16,
        temperature=1,
        top_p=1,
        max_len=max_len,
    )

    embeddings = MODEL.embed(graphies)
    embeddings = np.array(embeddings)
    assert embeddings.shape == (16, 512)

    graphies = [
        "[C][C][=C][C][=C][C][=Ring1][=Branch1]",
        "[C][=C][C][=C][C][=C][Ring1][=Branch1]",
    ]
    embeddings = MODEL.embed(graphies)
    embeddings = np.array(embeddings)

    cossim = np.dot(embeddings[0], embeddings[1]) / (
        np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
    )
    print(cossim)
