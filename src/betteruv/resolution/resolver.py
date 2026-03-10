from __future__ import annotations

from pathlib import Path

from betteruv.core.models import ResolvePlan
from betteruv.parsing.pyproject_parser import parse_pyproject_dependencies
from betteruv.parsing.requirements_parser import parse_requirements_txt
from betteruv.resolution.candidate_mapper import map_imports_to_packages


def resolve_from_metadata(repo_root: Path) -> ResolvePlan:
    packages = []
    packages.extend(parse_requirements_txt(repo_root / "requirements.txt"))
    packages.extend(parse_pyproject_dependencies(repo_root / "pyproject.toml"))
    packages = sorted(set(packages))
    return ResolvePlan(
        packages=packages,
        unresolved_imports=[],
        mapping_reasons={pkg: "Declared in project metadata" for pkg in packages},
    )


def resolve_from_imports(imports: list[str]) -> ResolvePlan:
    packages, unresolved, reasons = map_imports_to_packages(imports)
    return ResolvePlan(
        packages=sorted(set(packages)),
        unresolved_imports=sorted(set(unresolved)),
        mapping_reasons=reasons,
    )