from __future__ import annotations

from pathlib import Path
from typing import Optional

from betteruv.ai.failure_analyzer import FailureAnalyzer
from betteruv.ai.resolver_assistant import ResolverAssistant
from betteruv.classification.import_classifier import classify_imports
from betteruv.core.models import (
    ResolveResult,
    ScanResult,
    ScanStats,
)
from betteruv.install.uv_backend import UVBackend
from betteruv.outputs.requirements_writer import write_requirements_file
from betteruv.parsing.python_imports import extract_imports
from betteruv.repo.inspector import inspect_repo
from betteruv.resolution.plan_builder import build_plan_from_metadata, build_plan_from_scan
from betteruv.verify.import_check import verify_imports


class BetterUVOrchestrator:
    def __init__(self) -> None:
        self.installer = UVBackend()
        self.ai_resolver = ResolverAssistant()
        self.failure_analyzer = FailureAnalyzer()

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
        use_ai: bool = False,
        init_project: bool = True,
        sync: bool = True,
        frozen_sync: bool = False,
    ) -> ResolveResult:
        scan_result = self.scan(path, include_tests=include_tests)

        if (
            scan_result.repo_profile.has_requirements_txt
            or scan_result.repo_profile.has_pyproject_toml
        ):
            mode = "metadata-first"
            plan = build_plan_from_metadata(scan_result.repo_profile.root)
        else:
            mode = "inference"
            plan = build_plan_from_scan(scan_result.classification)

        if use_ai and plan.unresolved_imports:
            suggestions = self.ai_resolver.suggest_packages(plan.unresolved_imports)
            for unresolved, package in suggestions.items():
                if package not in plan.packages:
                    plan.packages.append(package)
                    plan.mapping_reasons[package] = f"AI suggestion for import '{unresolved}'"
            plan.unresolved_imports = [
                item for item in plan.unresolved_imports if item not in suggestions
            ]

        plan.packages = sorted(set(plan.packages))

        install_result = None
        verify_result = None
        requirements_path = None

        if write_requirements:
            requirements_path = write_requirements_file(scan_result.repo_profile.root, plan)

        if install and plan.packages:
            install_result = self.installer.install_packages(
                repo_root=scan_result.repo_profile.root,
                packages=plan.packages,
                ensure_project=init_project,
                sync=sync,
                frozen_sync=frozen_sync,
            )
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
            _ = self.failure_analyzer.analyze(verify_result.stderr, verify_result.failed_imports)

        return ResolveResult(
            mode=mode,
            scan_result=scan_result,
            plan=plan,
            install_result=install_result,
            verify_result=verify_result,
            requirements_path=requirements_path,
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