from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Callable

from betteruv.core.models import InstallResult


class UVBackend:
    def __init__(self, uv_executable: str = "uv") -> None:
        self.uv_executable = uv_executable

    def is_available(self) -> bool:
        return shutil.which(self.uv_executable) is not None

    def _run_command(
        self,
        command: list[str],
        repo_root: Path,
        progress_callback: Callable[[str], None] | None = None,
    ) -> InstallResult:
        process = subprocess.Popen(
            command,
            cwd=repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        output_lines: list[str] = []
        assert process.stdout is not None
        for raw_line in process.stdout:
            line = raw_line.rstrip()
            if not line:
                continue
            output_lines.append(line)
            if progress_callback is not None:
                progress_callback(line)

        returncode = process.wait()
        combined_output = "\n".join(output_lines)
        return InstallResult(
            success=returncode == 0,
            command=command,
            stdout=combined_output,
            stderr="" if returncode == 0 else combined_output,
            returncode=returncode,
        )

    def install_packages(
        self,
        repo_root: Path,
        packages: list[str],
        ensure_project: bool = True,
        sync: bool = False,
        frozen_sync: bool = False,
        progress_callback: Callable[[str], None] | None = None,
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
            if progress_callback is not None:
                progress_callback(f"$ {' '.join(command)}")
            completed = self._run_command(
                command,
                repo_root=repo_root,
                progress_callback=progress_callback,
            )
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
