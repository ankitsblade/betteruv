from __future__ import annotations

import re

from betteruv.ai.groq_client import GroqClient

_PACKAGE_NAME_SPLIT_RE = re.compile(r"[\s\[<>=!~]")


def _package_key(package: str) -> str:
    name = _PACKAGE_NAME_SPLIT_RE.split(package, maxsplit=1)[0]
    return name.strip().lower().replace("_", "-")


def _looks_versioned(package: str) -> bool:
    return _package_key(package) != package.strip().lower().replace("_", "-")


class VersionSuggester:
    """Suggest versioned package specifiers from code usage context."""

    def __init__(self) -> None:
        self.groq = GroqClient()

    def suggest_specifiers(
        self,
        import_to_package: dict[str, str],
        snippets_by_import: dict[str, list[str]],
        declared_packages: list[str] | None = None,
    ) -> dict[str, str]:
        if not import_to_package:
            return {}
        if not self.groq.enabled:
            return {}

        inferred = {
            import_name: package
            for import_name, package in import_to_package.items()
            if not _looks_versioned(package)
        }
        if not inferred:
            return {}

        snippet_lines: list[str] = []
        for import_name, package in sorted(inferred.items()):
            snippet_lines.append(f"[{import_name} -> {package}]")
            snippets = snippets_by_import.get(import_name, [])
            if snippets:
                snippet_lines.extend(snippets[:3])
            else:
                snippet_lines.append("(no snippet available)")

        response = self.groq.chat_json(
            system_prompt=(
                "You infer conservative Python package version specifiers from code usage. "
                "Use only the provided import names, package candidates, declared packages, "
                "and code snippets. Return strict JSON only."
            ),
            user_prompt=(
                "Given these inferred import-to-package mappings and code snippets, suggest "
                "versioned package specifiers only when usage strongly implies an API generation "
                "or minimum version. Prefer conservative lower bounds like 'package>=x.y'. "
                "Do not invent tight upper bounds unless strongly justified. "
                "If confidence is low, omit the package.\n\n"
                f"declared_packages: {declared_packages or []}\n"
                f"import_to_package: {inferred}\n"
                "code_snippets:\n"
                + "\n".join(snippet_lines)
                + "\n\nReturn JSON object with key 'specifiers' where value is "
                "{import_name: versioned_package_specifier}."
            ),
            max_tokens=900,
        )
        if not response:
            return {}

        specifiers = response.get("specifiers", response)
        if not isinstance(specifiers, dict):
            return {}

        parsed: dict[str, str] = {}
        for raw_import, raw_specifier in specifiers.items():
            if not isinstance(raw_import, str) or not isinstance(raw_specifier, str):
                continue
            import_name = raw_import.strip()
            specifier = raw_specifier.strip()
            if import_name not in inferred or not specifier:
                continue
            if _package_key(specifier) != _package_key(inferred[import_name]):
                continue
            if not _looks_versioned(specifier):
                continue
            parsed[import_name] = specifier

        return parsed
