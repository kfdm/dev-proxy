from pathlib import Path

import tomllib

DEFAULT = Path.home() / ".config" / "dev-server.toml"


def load(path: Path):
    with path.open("rb") as fp:
        return tomllib.load(fp)
