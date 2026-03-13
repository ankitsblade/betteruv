from __future__ import annotations

from betteruv.ai.groq_client import GroqClient


MAX_STDERR_CHARS_FOR_AI = 4000


class FailureAnalyzer:
    """Diagnose verification failures with Groq-backed analysis and local fallbacks."""

    def __init__(self) -> None:
        self.groq = GroqClient()

    def analyze(
        self,
        stderr: str,
        failed_imports: list[str],
        installed_packages: list[str] | None = None,
    ) -> dict[str, str]:
        ai_result = self._analyze_with_groq(
            stderr=stderr,
            failed_imports=failed_imports,
            installed_packages=installed_packages or [],
        )
        if ai_result:
            return ai_result

        return self._heuristic_analysis(
            stderr=stderr,
            failed_imports=failed_imports,
            installed_packages=installed_packages or [],
        )

    def _analyze_with_groq(
        self,
        stderr: str,
        failed_imports: list[str],
        installed_packages: list[str],
    ) -> dict[str, str] | None:
        stderr_excerpt = stderr[:MAX_STDERR_CHARS_FOR_AI]
        response = self.groq.chat_json(
            system_prompt=(
                "You are diagnosing Python dependency/import verification failures. "
                "Return strict JSON only."
            ),
            user_prompt=(
                "Analyze this failed import verification output and return JSON with keys: "
                "type, message, recommendation. Keep response concise and actionable.\n\n"
                f"failed_imports: {failed_imports}\n"
                f"installed_packages: {installed_packages}\n"
                f"stderr:\n{stderr_excerpt}"
            ),
            max_tokens=500,
        )
        if not response:
            return None

        result_type = response.get("type")
        message = response.get("message")
        recommendation = response.get("recommendation")
        if not isinstance(result_type, str) or not isinstance(message, str):
            return None

        out = {
            "type": result_type.strip() or "unknown",
            "message": message.strip() or "Could not confidently diagnose failure.",
        }
        if isinstance(recommendation, str) and recommendation.strip():
            out["recommendation"] = recommendation.strip()
        return out

    def _heuristic_analysis(
        self,
        stderr: str,
        failed_imports: list[str],
        installed_packages: list[str],
    ) -> dict[str, str]:
        joined = stderr.lower()
        normalized_packages = {package.lower() for package in installed_packages}

        if "no module named" in joined and failed_imports:
            missing = [
                item for item in failed_imports
                if item.lower() not in normalized_packages
            ]
            return {
                "type": "missing-package",
                "message": (
                    "Likely missing package(s) for imports: "
                    f"{', '.join(missing or failed_imports)}"
                ),
                "recommendation": (
                    "Review metadata/inferred mappings, add the missing package names, "
                    "and run verification again."
                ),
            }

        if "cannot import name" in joined:
            return {
                "type": "api-version-mismatch",
                "message": "Possible wrong package version or incompatible API.",
                "recommendation": "Pin/adjust package versions and retry.",
            }

        return {
            "type": "unknown",
            "message": "Could not confidently diagnose failure.",
            "recommendation": "Review stderr output and inspect package/import naming.",
        }
