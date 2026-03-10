from __future__ import annotations


class ResolverAssistant:
    """
    Placeholder AI resolver assistant.

    In v1 this is intentionally simple.
    Later you can wire it to OpenAI, Ollama, or another provider.
    """

    def suggest_packages(self, unresolved_imports: list[str]) -> dict[str, str]:
        suggestions: dict[str, str] = {}

        # Very small hand-coded fallback examples.
        fallback_map = {
            "yaml": "PyYAML",
            "cv2": "opencv-python",
            "PIL": "Pillow",
            "sklearn": "scikit-learn",
            "bs4": "beautifulsoup4",
        }

        for item in unresolved_imports:
            if item in fallback_map:
                suggestions[item] = fallback_map[item]

        return suggestions