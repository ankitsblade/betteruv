from __future__ import annotations

from betteruv.knowledge.alias_map import map_import_to_package


def map_imports_to_packages(imports: list[str]) -> tuple[list[str], list[str], dict[str, str]]:
    packages: list[str] = []
    unresolved: list[str] = []
    reasons: dict[str, str] = {}

    for import_name in imports:
        mapped = map_import_to_package(import_name)
        if mapped:
            packages.append(mapped)
            reasons[mapped] = f"Alias map for import '{import_name}'"
        else:
            # Fallback heuristic: assume package name matches top-level import.
            packages.append(import_name)
            reasons[import_name] = f"Direct-name fallback for import '{import_name}'"

    return packages, unresolved, reasons