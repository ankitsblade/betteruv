from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from betteruv.core.models import TestRunResult


def run_tests(
    *,
    cwd: Path,
    command: list[str],
    use_uv_run: bool = True,
    uv_executable: str = "uv",
) -> TestRunResult:
    effective_command = list(command)
    if use_uv_run and shutil.which(uv_executable):
        effective_command = [uv_executable, "run", "--project", str(cwd), *effective_command]

    completed = subprocess.run(
        effective_command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    return TestRunResult(
        success=completed.returncode == 0,
        command=effective_command,
        stdout=completed.stdout,
        stderr=completed.stderr,
        returncode=completed.returncode,
    )
