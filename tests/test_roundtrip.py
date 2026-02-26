from pathlib import Path

import pytest
import selfies as sf
from rdkit import Chem
from tqdm import tqdm

from graphies import Decoder, Encoder, Grammar

TESTDIR = Path(__file__).parent.resolve()
GRAMMAR = TESTDIR / "selfies.json"

datasets = list(TESTDIR.glob("*.smi"))


@pytest.mark.parametrize("path", datasets)
def test_roundtrip(path: Path):
    # selfies
    constraints = sf.get_preset_constraints("hypervalent")
    constraints.update({"P": 7, "P-1": 8, "P+1": 6, "?": 12})
    sf.set_semantic_constraints(constraints)

    # graphies
    grammar = Grammar.from_file(GRAMMAR)
    decoder = Decoder(grammar)
    encoder = Encoder(grammar)

    with open(path) as fp:
        lines = fp.readlines()

    for line in tqdm(lines[1:]):
        # run test case
        in_smiles = line.strip()
        in_selfies = sf.encoder(in_smiles)

        # selfies -> graph -> graphies
        graph = decoder.decode(in_selfies)
        graphies = encoder.encode(graph)

        out_selfies = graphies
        out_smiles = sf.decoder(out_selfies)
        passed = check_mol(in_smiles, out_smiles)
        assert passed, f"{in_smiles=}, {out_smiles=}"


def check_mol(sma, smb):
    csma = Chem.CanonSmiles(sma)
    csmb = Chem.CanonSmiles(smb)
    return csma == csmb
