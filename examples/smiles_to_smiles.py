from pathlib import Path
import selfies as sf
import metaselfies as msf

import logging

logging.basicConfig(level=logging.DEBUG)

grammar = Path(__file__).parent.resolve() / "selfies.json"

smiles = "c1ccccc1"
smiles = "C1(=O)CCCC1"
selfies = sf.encoder(smiles=smiles)
print("SELFIES", selfies)
graph = msf.decode(metaselfies=selfies, grammar=grammar)
metaselfies = msf.encode(graph=graph, grammar=grammar)
print("METASELFIES", metaselfies)
new_smiles = sf.decoder(metaselfies)
