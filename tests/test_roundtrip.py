import selfies as sf
from metaselfies import Encoder, Decoder, Grammar
from pathlib import Path
from rdkit import Chem
import pytest

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
        line = fp.readline()  # skip header
        while line:
            if line.strip().startswith("#"):
                line = fp.readline()
                continue

            # run test case
            in_smiles = line.strip()
            in_selfies = sf.encoder(in_smiles)

            graph = decoder.decode(in_selfies)
            metaselfies = encoder.encode(graph)

            out_selfies = metaselfies
            out_smiles = sf.decoder(out_selfies)
            passed = check_mol(in_smiles, out_smiles)
            assert passed, f"{in_smiles=}, {out_smiles=}"

            line = fp.readline()


def check_mol(sma, smb):
    csma = Chem.CanonSmiles(sma)
    csmb = Chem.CanonSmiles(smb)
    return csma == csmb
