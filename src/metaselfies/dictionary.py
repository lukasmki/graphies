from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class Dictionary:
    nodes: list[dict]
    edges: list[dict]
    branch: list[dict]
    link: list[dict]
    index: list[dict]
    alias: list[dict]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # create alphabet
        # get symbol ranges

    @classmethod
    def from_file(cls, path: str | Path):
        path = Path(path) if isinstance(path, str) else path
        data = json.loads(path.resolve().read_text())
        return cls(**data)

    def classify_token(self):
        pass

    def to_alphabet(self):
        i = 0

        pass
