from __future__ import annotations

from pathlib import Path


def parse_requirements_txt(path: Path) -> list[str]:
    if not path.exists():
        return []

    packages: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        cleaned = line.strip()
        if not cleaned or cleaned.startswith("#"):
            continue
        if cleaned.startswith(("-r ", "--requirement ")):
            continue
        packages.append(cleaned)
    return packages