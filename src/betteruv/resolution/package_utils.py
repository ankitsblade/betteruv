from __future__ import annotations

import re

_PACKAGE_NAME_SPLIT_RE = re.compile(r"[\s\[<>=!~]")


def package_key(package: str) -> str:
    name = _PACKAGE_NAME_SPLIT_RE.split(package, maxsplit=1)[0]
    return name.strip().lower().replace("_", "-")


def is_versioned_specifier(package: str) -> bool:
    normalized = package.strip().lower().replace("_", "-")
    return package_key(package) != normalized
