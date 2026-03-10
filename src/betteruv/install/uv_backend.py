from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from betteruv.core.models import InstallResult


class UVBackend:
    def __init__(self, uv_executable: str = "uv") -> None:
        self.uv_executable = uv_executable

    def is_available(self) -> bool:
        return shutil.which(self.uv_executable) is not None

    def _run_command(self, command: list[str], repo_root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )

    def install_packages(
        self,
        repo_root: Path,
        packages: list[str],
        ensure_project: bool = True,
        sync: bool = True,
        frozen_sync: bool = False,
    ) -> InstallResult:
        if not packages:
            return InstallResult(
                success=True,
                command=[],
                stdout="No packages to install.",
                stderr="",
                returncode=0,
            )

        if not self.is_available():
            return InstallResult(
                success=False,
                command=[self.uv_executable, "add", *packages],
                stdout="",
                stderr="uv executable not found on PATH.",
                returncode=127,
            )

        commands: list[list[str]] = []
        if ensure_project and not (repo_root / "pyproject.toml").exists():
            commands.append([self.uv_executable, "init", "--bare"])

        commands.append([self.uv_executable, "add", *packages])

        if sync:
            sync_command = [self.uv_executable, "sync"]
            if frozen_sync:
                sync_command.append("--frozen")
            commands.append(sync_command)

        stdout_parts: list[str] = []
        stderr_parts: list[str] = []
        last_returncode = 0
        failed_command: list[str] | None = None

        for command in commands:
            completed = self._run_command(command, repo_root=repo_root)
            last_returncode = completed.returncode
            stdout_parts.append(f"$ {' '.join(command)}\n{completed.stdout}".rstrip())
            stderr_parts.append(f"$ {' '.join(command)}\n{completed.stderr}".rstrip())
            if completed.returncode != 0:
                failed_command = command
                break

        success = failed_command is None
        command_for_result = failed_command or (commands[-1] if commands else [])

        return InstallResult(
            success=success,
            command=command_for_result,
            stdout="\n\n".join(part for part in stdout_parts if part),
            stderr="\n\n".join(part for part in stderr_parts if part),
            returncode=last_returncode,
        )