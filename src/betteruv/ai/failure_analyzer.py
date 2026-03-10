from __future__ import annotations


class FailureAnalyzer:
    """
    Placeholder failure analyzer for future AI-driven repair loops.
    """

    def analyze(self, stderr: str, failed_imports: list[str]) -> dict[str, str]:
        joined = stderr.lower()

        if "no module named" in joined and failed_imports:
            return {
                "type": "missing-package",
                "message": f"Likely missing package(s) for imports: {', '.join(failed_imports)}",
            }

        if "cannot import name" in joined:
            return {
                "type": "api-version-mismatch",
                "message": "Possible wrong package version or incompatible API.",
            }

        return {
            "type": "unknown",
            "message": "Could not confidently diagnose failure.",
        }