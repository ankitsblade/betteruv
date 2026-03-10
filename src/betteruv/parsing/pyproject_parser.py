from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore


def parse_pyproject_dependencies(path: Path) -> list[str]:
    if not path.exists() or tomllib is None:
        return []

    data = tomllib.loads(path.read_text(encoding="utf-8"))

    project = data.get("project", {})
    deps = project.get("dependencies", [])
    if isinstance(deps, list):
        return [str(item) for item in deps]

    return []