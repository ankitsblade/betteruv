from __future__ import annotations

import re

from betteruv.knowledge.alias_map import map_import_to_package

_EXACT_PACKAGE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _can_use_exact_match(import_name: str) -> bool:
    return bool(_EXACT_PACKAGE_RE.fullmatch(import_name))


def map_imports_to_package_map(imports: list[str]) -> tuple[dict[str, str], list[str], dict[str, str]]:
    mappings: dict[str, str] = {}
    unresolved: list[str] = []
    reasons: dict[str, str] = {}

    for import_name in imports:
        mapped = map_import_to_package(import_name)
        if mapped:
            mappings[import_name] = mapped
            reasons[mapped] = f"Alias map for import '{import_name}'"
        elif _can_use_exact_match(import_name):
            mappings[import_name] = import_name
            reasons[import_name] = f"Exact match fallback for import '{import_name}'"
        else:
            unresolved.append(import_name)

    return mappings, unresolved, reasons


def map_imports_to_packages(imports: list[str]) -> tuple[list[str], list[str], dict[str, str]]:
    mappings, unresolved, reasons = map_imports_to_package_map(imports)
    return list(mappings.values()), unresolved, reasons
