import logging
from pathlib import Path

import selfies as sf
from rdkit import Chem

import graphies as gf


def compare_mol(sma, smb):
    csma = Chem.CanonSmiles(sma)
    csmb = Chem.CanonSmiles(smb)
    return csma == csmb


logging.basicConfig(level=logging.DEBUG)

grammar = Path(__file__).parent.resolve() / "selfies.json"

# smiles = "c12cc1ccc2"
smiles = "C(C(C)C)C"
smiles = "CC(=O)C#C"
smiles = "CC1CC1C"
selfies = sf.encoder(smiles=smiles)
print("SELFIES", selfies)
graph = gf.decode(graphies=selfies, grammar=grammar)

for edge in graph.edges(data=True):
    print(edge)
# nids = list(graph.nodes())
# shuffled = nids.copy()
# random.shuffle(shuffled)
# mapping = dict(zip(nids, shuffled))
# graph = nx.relabel_nodes(graph, mapping, copy=True)

graphies = gf.encode(graph=graph, grammar=grammar)
print("GRAPHIES", graphies)
new_smiles = sf.decoder(graphies)

print("SMILES2SMILES", smiles, new_smiles, compare_mol(smiles, new_smiles))
