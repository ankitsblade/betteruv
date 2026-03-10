from __future__ import annotations

from pathlib import Path

from betteruv.core.models import ImportClassification, ResolvePlan
from betteruv.parsing.pyproject_parser import parse_pyproject_dependencies
from betteruv.parsing.requirements_parser import parse_requirements_txt
from betteruv.resolution.candidate_mapper import map_imports_to_packages


def build_plan_from_metadata(repo_root: Path) -> ResolvePlan:
    packages: list[str] = []

    requirements_path = repo_root / "requirements.txt"
    pyproject_path = repo_root / "pyproject.toml"

    if requirements_path.exists():
        packages.extend(parse_requirements_txt(requirements_path))

    if pyproject_path.exists():
        packages.extend(parse_pyproject_dependencies(pyproject_path))

    deduped = sorted(set(packages))
    reasons = {pkg: "Declared in project metadata" for pkg in deduped}
    return ResolvePlan(
        packages=deduped,
        unresolved_imports=[],
        mapping_reasons=reasons,
    )


def build_plan_from_scan(classification: ImportClassification) -> ResolvePlan:
    packages, unresolved, reasons = map_imports_to_packages(
        sorted(classification.third_party_imports)
    )
    unresolved_combined = sorted(set(unresolved) | set(classification.ambiguous_imports))
    return ResolvePlan(
        packages=sorted(set(packages)),
        unresolved_imports=unresolved_combined,
        mapping_reasons=reasons,
    )