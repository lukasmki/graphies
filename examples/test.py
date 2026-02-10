import json
from molify import rdkit2networkx, networkx2rdkit
import networkx as nx
import selfies as sf
from metaselfies.decoder import Decoder
import random
from rdkit import Chem

# Decoder().run(
#     "[C][C][Branch1][C][C][C][=C][C][=Branch2][Branch1][Ring1][=N][Branch1][=N][C][=Branch1][C][=O][C][=C][C][=C][C][=C][Ring1][=Branch1][Pt+2][Branch1][C][Cl-1][Branch1][C][Cl-1][N][Branch1][=N][C][=Branch1][C][=O][C][=C][C][=C][C][=C][Ring1][=Branch1][=C][C][=C][C][Branch1][C][C][Branch1][C][C][N][Ring1][#Branch1][N][Ring2][Ring2][C]"
# )

smiles = "c1ccccc1"
selfies = sf.encoder(smiles)
print(smiles, selfies)

alphabet = sf.get_semantic_robust_alphabet()  # Gets the alphabet of robust symbols
rnd_selfies = "".join(random.sample(list(alphabet), 16))
print("SELFIES\n", rnd_selfies)
Decoder().run(rnd_selfies)
rnd_smiles = sf.decoder(rnd_selfies)
print("SMILES\n", rnd_smiles)
mol = Chem.MolFromSmiles(rnd_smiles)
print("STRUCTURE\n", json.dumps(nx.node_link_data(rdkit2networkx(mol)), indent=2))
