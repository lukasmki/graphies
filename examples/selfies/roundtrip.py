from pathlib import Path

import selfies as sf
from rdkit import Chem

import graphies as gf


def compare_mol(sma, smb):
    csma = Chem.CanonSmiles(sma)
    csmb = Chem.CanonSmiles(smb)
    return csma == csmb


grammar = gf.Grammar.from_file(path=Path(__file__).parent.resolve() / "selfies.json")

smiles = "c1ccccc1"
print("SMILES", smiles)

selfies = sf.encoder(smiles)
print("SELFIES", selfies)

graph = gf.decode(graphies=selfies, grammar=grammar)
print("GRAPH", graph)

graphies = gf.encode(graph=graph, grammar=grammar)
print("GRAPHIES", graphies)

new_smiles = sf.decoder(graphies)
print("SMILES", new_smiles, compare_mol(smiles, new_smiles))
