from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from betteruv.ai.failure_analyzer import FailureAnalyzer
from betteruv.ai.resolver_assistant import ResolverAssistant
from betteruv.ai.version_suggester import VersionSuggester
from betteruv.classification.import_classifier import classify_imports
from betteruv.core.models import (
    ImportOccurrence,
    ResolveResult,
    ScanResult,
    ScanStats,
)
from betteruv.install.uv_backend import UVBackend
from betteruv.outputs.requirements_writer import write_requirements_file
from betteruv.parsing.python_imports import extract_imports
from betteruv.repo.inspector import inspect_repo
from betteruv.knowledge.alias_map import map_import_to_package
from betteruv.resolution.plan_builder import (
    build_plan_from_metadata,
    build_plan_from_scan,
    consolidate_plan,
    merge_plans,
)
from betteruv.resolution.candidate_mapper import map_imports_to_package_map
from betteruv.resolution.torch_family import harmonize_torch_family
from betteruv.verify.import_check import verify_imports


def _package_key(package: str) -> str:
    for marker in ("[", "<", ">", "=", "!", "~", " "):
        if marker in package:
            package = package.split(marker, maxsplit=1)[0]
    return package.strip().lower().replace("_", "-")


class BetterUVOrchestrator:
    def __init__(self) -> None:
        self.installer = UVBackend()
        self.ai_resolver = ResolverAssistant()
        self.version_suggester = VersionSuggester()
        self.failure_analyzer = FailureAnalyzer()

    def _build_import_locations(
        self,
        imports: list[ImportOccurrence],
        repo_root: Path,
        target_imports: list[str],
    ) -> dict[str, list[str]]:
        target_set = set(target_imports)
        locations_by_import: dict[str, list[str]] = {}
        for occurrence in imports:
            if occurrence.top_level not in target_set:
                continue
            locations = locations_by_import.setdefault(occurrence.top_level, [])
            location = f"{occurrence.file_path.relative_to(repo_root)}:{occurrence.lineno}"
            if location not in locations:
                locations.append(location)
        return locations_by_import

    def _build_usage_snippets(
        self,
        imports: list[ImportOccurrence],
        repo_root: Path,
        target_imports: list[str],
    ) -> dict[str, list[str]]:
        target_set = set(target_imports)
        snippets_by_import: dict[str, list[str]] = {item: [] for item in target_imports}
        seen_locations: set[tuple[str, str]] = set()

        for occurrence in imports:
            if occurrence.top_level not in target_set:
                continue
            key = (occurrence.top_level, str(occurrence.file_path))
            if key in seen_locations:
                continue
            seen_locations.add(key)
            try:
                lines = occurrence.file_path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                lines = occurrence.file_path.read_text(encoding="utf-8", errors="ignore").splitlines()

            start = max(0, occurrence.lineno - 1)
            end = min(len(lines), start + 14)
            numbered = [
                f"{occurrence.file_path.relative_to(repo_root)}:{idx + 1}: {lines[idx]}"
                for idx in range(start, end)
            ]
            snippets_by_import.setdefault(occurrence.top_level, []).append("\n".join(numbered))

        return snippets_by_import

    def scan(self, path: Path, include_tests: bool = True) -> ScanResult:
        repo_profile = inspect_repo(path, include_tests=include_tests)
        imports = extract_imports(repo_profile.python_files)
        classification = classify_imports(
            imports=imports,
            repo_root=repo_profile.root,
            python_files=repo_profile.python_files,
        )
        stats = ScanStats(
            python_files_scanned=len(repo_profile.python_files),
            raw_imports_found=len(imports),
        )
        return ScanResult(
            repo_profile=repo_profile,
            imports=imports,
            classification=classification,
            stats=stats,
        )

    def resolve(
        self,
        path: Path,
        include_tests: bool = True,
        install: bool = True,
        write_requirements: bool = True,
        init_project: bool = True,
        sync: bool = False,
        frozen_sync: bool = False,
        progress_callback: Callable[[str], None] | None = None,
    ) -> ResolveResult:
        scan_result = self.scan(path, include_tests=include_tests)
        third_party_imports = sorted(scan_result.classification.third_party_imports)
        direct_mappings, unresolved_imports, _ = map_imports_to_package_map(third_party_imports)
        scan_plan = build_plan_from_scan(scan_result.classification)
        metadata_plan = None
        metadata_package_keys: set[str] = set()

        if (
            scan_result.repo_profile.has_requirements_txt
            or scan_result.repo_profile.has_pyproject_toml
        ):
            mode = "metadata+scan"
            metadata_plan = build_plan_from_metadata(scan_result.repo_profile.root)
            metadata_package_keys = {_package_key(item) for item in metadata_plan.packages}
            plan = merge_plans(metadata_plan, scan_plan)
        else:
            mode = "inference"
            plan = scan_plan

        exact_match_candidates = sorted(
            import_name
            for import_name, package in direct_mappings.items()
            if package == import_name and map_import_to_package(import_name) is None
        )

        ai_candidates = sorted(set(plan.unresolved_imports) | set(exact_match_candidates))
        if ai_candidates:
            import_context = self._build_import_locations(
                scan_result.imports,
                scan_result.repo_profile.root,
                ai_candidates,
            )
            suggestions = self.ai_resolver.suggest_packages(
                ai_candidates,
                declared_packages=plan.packages,
                import_context=import_context,
            )
            for import_name, suggested_package in suggestions.items():
                previous_package = direct_mappings.get(import_name)
                if previous_package:
                    updated_packages: list[str] = []
                    replaced = False
                    for package in plan.packages:
                        if _package_key(package) == _package_key(previous_package):
                            updated_packages.append(suggested_package)
                            replaced = True
                        else:
                            updated_packages.append(package)
                    if not replaced:
                        updated_packages.append(suggested_package)
                    plan.packages = updated_packages
                    plan.mapping_reasons.pop(previous_package, None)
                    plan.mapping_reasons[suggested_package] = (
                        f"AI suggestion for import '{import_name}'"
                    )
                else:
                    if suggested_package not in plan.packages:
                        plan.packages.append(suggested_package)
                    plan.mapping_reasons[suggested_package] = (
                        f"AI suggestion for import '{import_name}'"
                    )
                direct_mappings[import_name] = suggested_package

            plan.unresolved_imports = [
                item for item in plan.unresolved_imports if item not in suggestions
            ]
            unresolved_imports = [item for item in unresolved_imports if item not in suggestions]

        inferred_import_map = {
            import_name: package
            for import_name, package in direct_mappings.items()
            if _package_key(package) not in metadata_package_keys
        }
        version_suggestions = self.version_suggester.suggest_specifiers(
            inferred_import_map,
            snippets_by_import=self._build_usage_snippets(
                scan_result.imports,
                scan_result.repo_profile.root,
                list(inferred_import_map.keys()),
            ),
            declared_packages=metadata_plan.packages if metadata_plan is not None else [],
        )
        if version_suggestions:
            package_replacements = {
                _package_key(inferred_import_map[import_name]): suggested
                for import_name, suggested in version_suggestions.items()
            }
            updated_packages: list[str] = []
            for package in plan.packages:
                replacement = package_replacements.get(_package_key(package))
                updated_packages.append(replacement or package)
            plan.packages = updated_packages
            for import_name, suggested in version_suggestions.items():
                previous = inferred_import_map[import_name]
                plan.mapping_reasons.pop(previous, None)
                plan.mapping_reasons[suggested] = (
                    f"AI version inference for import '{import_name}'"
                )

        plan = harmonize_torch_family(plan)
        plan = consolidate_plan(plan)

        install_result = None
        verify_result = None
        requirements_path = None
        failure_analysis = None

        if write_requirements:
            requirements_path = write_requirements_file(scan_result.repo_profile.root, plan)

        if install and plan.packages:
            install_result = self.installer.install_packages(
                repo_root=scan_result.repo_profile.root,
                packages=plan.packages,
                ensure_project=init_project,
                sync=sync,
                frozen_sync=frozen_sync,
                progress_callback=progress_callback,
            )
            if install_result.success:
                verify_result = verify_imports(
                    imports=sorted(scan_result.classification.third_party_imports),
                    python_executable=None,
                    cwd=scan_result.repo_profile.root,
                    use_uv_run=True,
                    uv_executable=self.installer.uv_executable,
                )
        elif install and not plan.packages:
            verify_result = verify_imports(
                imports=sorted(scan_result.classification.third_party_imports),
                python_executable=None,
                cwd=scan_result.repo_profile.root,
                use_uv_run=True,
                uv_executable=self.installer.uv_executable,
            )

        if verify_result and not verify_result.success:
            failure_analysis = self.failure_analyzer.analyze(
                verify_result.stderr,
                verify_result.failed_imports,
                installed_packages=plan.packages,
            )

        return ResolveResult(
            mode=mode,
            scan_result=scan_result,
            plan=plan,
            install_result=install_result,
            verify_result=verify_result,
            requirements_path=requirements_path,
            failure_analysis=failure_analysis,
        )

    def verify(
        self,
        path: Path,
        include_tests: bool = True,
        python_executable: Optional[str] = None,
        use_uv_run: bool = False,
    ):
        scan_result = self.scan(path, include_tests=include_tests)
        return verify_imports(
            imports=sorted(scan_result.classification.third_party_imports),
            python_executable=python_executable,
            cwd=scan_result.repo_profile.root,
            use_uv_run=use_uv_run,
            uv_executable=self.installer.uv_executable,
        )
