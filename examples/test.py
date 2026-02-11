from pathlib import Path
from metaselfies.grammar import Grammar
import json
from molify import rdkit2networkx, networkx2rdkit
import networkx as nx
import selfies as sf
from metaselfies.decoder import Decoder
import random
from rdkit import Chem

# grammar = Grammar.from_file("examples/protein.json")
# Path("examples/protein_vocab.json").write_text(json.dumps(grammar.to_alphabet(), indent=4))

grammar = Grammar.from_file(path="examples/selfies.json")
Path("examples/selfies_vocab.json").write_text(
    json.dumps(grammar.to_alphabet(), indent=4)
)

decoder = Decoder(grammar)

smiles = "c1ccccc1"
# smiles = "C/C=C\\C"

selfies = sf.encoder(smiles)
print(smiles, selfies)
decoder.run(selfies)

# alphabet = sf.get_semantic_robust_alphabet()  # Gets the alphabet of robust symbols
# rnd_selfies = "".join(random.sample(list(alphabet), 16))
# print("SELFIES\n", rnd_selfies)
# Decoder().run(rnd_selfies)
# rnd_smiles = sf.decoder(rnd_selfies)
# print("SMILES\n", rnd_smiles)
# mol = Chem.MolFromSmiles(rnd_smiles)
# print("STRUCTURE\n", json.dumps(nx.node_link_data(rdkit2networkx(mol)), indent=2))
