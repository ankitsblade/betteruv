from __future__ import annotations

from pathlib import Path

from betteruv.core.models import RepoProfile

IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "build",
    "dist",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
}


def _should_skip(path: Path, include_tests: bool) -> bool:
    parts = set(path.parts)
    if parts & IGNORE_DIRS:
        return True
    if not include_tests and any(part in {"tests", "test"} for part in path.parts):
        return True
    return False


def inspect_repo(path: Path, include_tests: bool = True) -> RepoProfile:
    root = path.resolve()
    if not root.exists():
        raise FileNotFoundError(f"Path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {root}")

    python_files: list[Path] = []
    for file_path in root.rglob("*.py"):
        if _should_skip(file_path, include_tests=include_tests):
            continue
        python_files.append(file_path)

    return RepoProfile(
        root=root,
        has_requirements_txt=(root / "requirements.txt").exists(),
        has_pyproject_toml=(root / "pyproject.toml").exists(),
        has_uv_lock=(root / "uv.lock").exists(),
        has_setup_py=(root / "setup.py").exists(),
        has_setup_cfg=(root / "setup.cfg").exists(),
        python_files=sorted(python_files),
    )