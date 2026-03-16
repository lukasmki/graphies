import pytest
import selfies as sf

SELFIES = "[C][N][C][C][C][O][C][Ring1][#Branch1][Ring1][Branch1][C][Ring1][#Branch1][C][Ring1][=Branch1][Ring1][Branch1]"
SMILES = sf.decoder(SELFIES)


@pytest.mark.benchmark(group="decode")
def test_decode_selfies(benchmark):
    benchmark(sf.decoder, SELFIES)


@pytest.mark.benchmark(group="encode")
def test_encode_selfies(benchmark):
    benchmark(sf.encoder, SMILES)


@pytest.mark.benchmark(group="recode")
def test_recode_selfies(benchmark):
    def recode(selfies: str):
        smiles = sf.decoder(selfies)
        selfies = sf.encoder(smiles)
        return selfies

    benchmark(recode, SELFIES)
