from __future__ import annotations

from betteruv.ai.groq_client import GroqClient


class ResolverAssistant:
    """Resolve unresolved imports to package names, with Groq as the primary source."""

    def __init__(self) -> None:
        self.groq = GroqClient()

    def suggest_packages(
        self,
        unresolved_imports: list[str],
        declared_packages: list[str] | None = None,
        import_context: dict[str, list[str]] | None = None,
    ) -> dict[str, str]:
        imports = sorted(set(item.strip() for item in unresolved_imports if item.strip()))
        if not imports:
            return {}

        suggestions = self._from_groq(
            imports,
            declared_packages=declared_packages or [],
            import_context=import_context or {},
        )

        return suggestions

    def _from_groq(
        self,
        unresolved_imports: list[str],
        declared_packages: list[str],
        import_context: dict[str, list[str]],
    ) -> dict[str, str]:
        context_lines: list[str] = []
        for item in unresolved_imports:
            locations = import_context.get(item, [])
            if locations:
                context_lines.append(f"{item}: {', '.join(locations[:3])}")

        response = self.groq.chat_json(
            system_prompt=(
                "You map Python import module names to installable PyPI package names. "
                "Return strict JSON only."
            ),
            user_prompt=(
                "For each unresolved Python import below, suggest the most likely PyPI package. "
                "Only include high-confidence mappings. "
                "Return JSON object with a single key 'mappings', where value is an object "
                "{import_name: package_name}.\n\n"
                f"imports: {unresolved_imports}\n"
                f"declared_packages: {declared_packages}\n"
                "import_locations:\n"
                + ("\n".join(context_lines) if context_lines else "(none)")
            ),
        )
        if not response:
            return {}

        mappings = response.get("mappings", response)
        if not isinstance(mappings, dict):
            return {}

        valid_imports = set(unresolved_imports)
        parsed: dict[str, str] = {}
        for raw_import, raw_package in mappings.items():
            if not isinstance(raw_import, str) or not isinstance(raw_package, str):
                continue
            imp = raw_import.strip()
            pkg = raw_package.strip()
            if not imp or not pkg or imp not in valid_imports:
                continue
            parsed[imp] = pkg

        return parsed
