from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from betteruv.core.models import VerifyResult


def verify_imports(
    imports: list[str],
    python_executable: str | None = None,
    cwd: Path | None = None,
    use_uv_run: bool = False,
    uv_executable: str = "uv",
) -> VerifyResult:
    checked_imports = sorted(set(imports))
    if not checked_imports:
        return VerifyResult(success=True, checked_imports=[], failed_imports=[])

    interpreter = python_executable or shutil.which("python") or sys.executable

    lines = []
    for item in checked_imports:
        lines.append("try:")
        lines.append(f"    import {item}")
        lines.append("except Exception as exc:")
        lines.append(f"    print('FAILED::{item}::' + repr(exc))")

    script = "\n".join(lines) + "\n"

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as handle:
        handle.write(script)
        script_path = Path(handle.name)

    try:
        command = [interpreter, str(script_path)]
        if use_uv_run and shutil.which(uv_executable):
            command = [uv_executable, "run", *command]

        completed = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
    finally:
        try:
            script_path.unlink(missing_ok=True)
        except OSError:
            pass

    failed_imports: list[str] = []
    for line in completed.stdout.splitlines():
        if line.startswith("FAILED::"):
            parts = line.split("::", maxsplit=2)
            if len(parts) >= 2:
                failed_imports.append(parts[1])

    success = len(failed_imports) == 0 and completed.returncode == 0

    return VerifyResult(
        success=success,
        checked_imports=checked_imports,
        failed_imports=failed_imports,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )