from __future__ import annotations

import ast
from pathlib import Path

from betteruv.core.models import ImportOccurrence


class ImportCollector(ast.NodeVisitor):
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.found: list[ImportOccurrence] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            module = alias.name
            top_level = module.split(".")[0]
            self.found.append(
                ImportOccurrence(
                    module=module,
                    top_level=top_level,
                    file_path=self.file_path,
                    lineno=node.lineno,
                    is_from_import=False,
                )
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            module = node.module
            top_level = module.split(".")[0]
            self.found.append(
                ImportOccurrence(
                    module=module,
                    top_level=top_level,
                    file_path=self.file_path,
                    lineno=node.lineno,
                    is_from_import=True,
                )
            )
        self.generic_visit(node)


def extract_imports(python_files: list[Path]) -> list[ImportOccurrence]:
    found: list[ImportOccurrence] = []

    for file_path in python_files:
        try:
            source = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            source = file_path.read_text(encoding="utf-8", errors="ignore")

        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError:
            continue

        collector = ImportCollector(file_path)
        collector.visit(tree)
        found.extend(collector.found)

    return found