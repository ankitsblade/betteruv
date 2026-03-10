from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files


@lru_cache(maxsize=1)
def load_alias_map() -> dict[str, str]:
    data_path = files("betteruv.knowledge.data").joinpath("import_to_package.json")
    return json.loads(data_path.read_text(encoding="utf-8"))


def map_import_to_package(import_name: str) -> str | None:
    aliases = load_alias_map()
    if import_name in aliases:
        return aliases[import_name]
    return None