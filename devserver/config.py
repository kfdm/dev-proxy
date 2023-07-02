import tomllib
from pathlib import Path

DEFAULT = Path.home() / ".config" / "dev-server.toml"


def load(path: Path):
    with path.open("rb") as fp:
        return tomllib.load(fp)
