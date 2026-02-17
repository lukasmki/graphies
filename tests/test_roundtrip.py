from pathlib import Path

import pytest
import selfies as sf
from rdkit import Chem
from tqdm import tqdm

from metaselfies import Decoder, Encoder, Grammar

TESTDIR = Path(__file__).parent.resolve()
SAMPLES = TESTDIR / "samples"
GRAMMAR = TESTDIR / "selfies.json"

datasets = list(SAMPLES.glob("*.txt"))


@pytest.mark.parametrize("path", datasets)
def test_roundtrip(path: Path):
    # selfies
    constraints = sf.get_preset_constraints("hypervalent")
    constraints.update({"P": 7, "P-1": 8, "P+1": 6, "?": 12})
    sf.set_semantic_constraints(constraints)

    # metaselfies
    grammar = Grammar.from_file(GRAMMAR)
    decoder = Decoder(grammar)
    encoder = Encoder(grammar)

    with open(path) as fp:
        lines = fp.readlines()

    for line in tqdm(lines[1:]):
        # run test case
        in_smiles = line.strip()
        in_selfies = sf.encoder(in_smiles)

        # selfies -> graph -> metaselfies
        graph = decoder.decode(in_selfies)
        metaselfies = encoder.encode(graph)

        out_selfies = metaselfies
        out_smiles = sf.decoder(out_selfies)
        passed = check_mol(in_smiles, out_smiles)
        assert passed, f"{in_smiles=}, {out_smiles=}"


def check_mol(sma, smb):
    csma = Chem.CanonSmiles(sma)
    csmb = Chem.CanonSmiles(smb)
    return csma == csmb
