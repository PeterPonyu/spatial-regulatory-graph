from __future__ import annotations

from pathlib import Path


def find_repo_root(anchor: str | Path | None = None) -> Path:
    here = Path(anchor or __file__).resolve()
    if here.is_file():
        here = here.parent
    for candidate in (here, *here.parents):
        if (candidate / "data" / "processed").is_dir():
            return candidate
    raise FileNotFoundError("could not find repository root containing data/processed")


def processed_data_path(*parts: str, anchor: str | Path | None = None) -> Path:
    return find_repo_root(anchor) / "data" / "processed" / Path(*parts)
