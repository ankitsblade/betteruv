from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class RepoProfile:
    root: Path
    has_requirements_txt: bool = False
    has_pyproject_toml: bool = False
    has_uv_lock: bool = False
    has_setup_py: bool = False
    has_setup_cfg: bool = False
    python_files: list[Path] = field(default_factory=list)


@dataclass(slots=True)
class ScanStats:
    python_files_scanned: int = 0
    raw_imports_found: int = 0


@dataclass(slots=True)
class ImportOccurrence:
    module: str
    top_level: str
    file_path: Path
    lineno: int
    is_from_import: bool


@dataclass(slots=True)
class ImportClassification:
    all_top_level_imports: set[str] = field(default_factory=set)
    stdlib_imports: set[str] = field(default_factory=set)
    local_imports: set[str] = field(default_factory=set)
    third_party_imports: set[str] = field(default_factory=set)
    ambiguous_imports: set[str] = field(default_factory=set)


@dataclass(slots=True)
class ScanResult:
    repo_profile: RepoProfile
    imports: list[ImportOccurrence]
    classification: ImportClassification
    stats: ScanStats


@dataclass(slots=True)
class ResolvePlan:
    packages: list[str] = field(default_factory=list)
    unresolved_imports: list[str] = field(default_factory=list)
    mapping_reasons: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class InstallResult:
    success: bool
    command: list[str]
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0


@dataclass(slots=True)
class VerifyResult:
    success: bool
    checked_imports: list[str] = field(default_factory=list)
    failed_imports: list[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""


@dataclass(slots=True)
class ResolveResult:
    mode: str
    scan_result: ScanResult
    plan: ResolvePlan
    install_result: Optional[InstallResult] = None
    verify_result: Optional[VerifyResult] = None
    requirements_path: Optional[Path] = None
    failure_analysis: Optional[dict[str, str]] = None
