from __future__ import annotations

from pathlib import Path

from betteruv.core.models import ImportClassification, ResolvePlan
from betteruv.parsing.pyproject_parser import parse_pyproject_dependencies
from betteruv.parsing.requirements_parser import parse_requirements_txt
from betteruv.resolution.candidate_mapper import map_imports_to_packages
from betteruv.resolution.package_utils import package_key


def _prefer_package(existing: str, candidate: str) -> str:
    if existing == candidate:
        return existing

    existing_key = package_key(existing)
    candidate_key = package_key(candidate)
    if existing_key != candidate_key:
        return existing

    existing_has_detail = existing != existing_key and len(existing) > len(existing_key)
    candidate_has_detail = candidate != candidate_key and len(candidate) > len(candidate_key)

    if candidate_has_detail and not existing_has_detail:
        return candidate
    return existing


def consolidate_plan(plan: ResolvePlan) -> ResolvePlan:
    selected_by_key: dict[str, str] = {}
    reasons_by_package = dict(plan.mapping_reasons)

    for package in plan.packages:
        key = package_key(package)
        selected = selected_by_key.get(key)
        if selected is None:
            selected_by_key[key] = package
            continue

        preferred = _prefer_package(selected, package)
        if preferred != selected:
            selected_by_key[key] = preferred

    packages = sorted(selected_by_key.values())
    mapping_reasons = {
        package: reasons_by_package.get(package, reasons_by_package.get(package_key(package), "-"))
        for package in packages
    }

    return ResolvePlan(
        packages=packages,
        unresolved_imports=sorted(set(plan.unresolved_imports)),
        mapping_reasons=mapping_reasons,
    )


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


def merge_plans(primary: ResolvePlan, secondary: ResolvePlan) -> ResolvePlan:
    unresolved_imports = sorted(set(primary.unresolved_imports) | set(secondary.unresolved_imports))
    mapping_reasons = dict(primary.mapping_reasons)

    for package, reason in secondary.mapping_reasons.items():
        if package not in mapping_reasons:
            mapping_reasons[package] = reason

    merged = ResolvePlan(
        packages=[*primary.packages, *secondary.packages],
        unresolved_imports=unresolved_imports,
        mapping_reasons=mapping_reasons,
    )
    return consolidate_plan(merged)
