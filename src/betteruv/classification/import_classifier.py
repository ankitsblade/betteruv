from __future__ import annotations

import sys
from pathlib import Path

from betteruv.core.models import ImportClassification, ImportOccurrence


def _build_local_module_names(repo_root: Path, python_files: list[Path]) -> set[str]:
    names: set[str] = set()

    for file_path in python_files:
        rel = file_path.relative_to(repo_root)
        package_rel = Path(*rel.parts[1:]) if rel.parts[:1] == ("src",) and len(rel.parts) > 1 else rel

        if file_path.name == "__init__.py":
            if package_rel.parent != Path("."):
                names.add(package_rel.parent.parts[0])
            continue

        names.add(file_path.stem)
        if package_rel.parts:
            names.add(package_rel.parts[0])

    return names


def classify_imports(
    imports: list[ImportOccurrence],
    repo_root: Path,
    python_files: list[Path],
) -> ImportClassification:
    stdlib_modules = set(sys.stdlib_module_names)
    local_modules = _build_local_module_names(repo_root, python_files)

    all_top_level = {item.top_level for item in imports if item.top_level}

    stdlib_imports: set[str] = set()
    local_imports: set[str] = set()
    third_party_imports: set[str] = set()
    ambiguous_imports: set[str] = set()

    for name in all_top_level:
        if name in stdlib_modules:
            stdlib_imports.add(name)
        elif name in local_modules:
            local_imports.add(name)
        else:
            third_party_imports.add(name)

    for name in set(local_imports) & set(third_party_imports):
        ambiguous_imports.add(name)

    third_party_imports -= ambiguous_imports
    local_imports -= ambiguous_imports

    return ImportClassification(
        all_top_level_imports=all_top_level,
        stdlib_imports=stdlib_imports,
        local_imports=local_imports,
        third_party_imports=third_party_imports,
        ambiguous_imports=ambiguous_imports,
    )
