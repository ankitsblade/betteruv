from pathlib import Path
import shlex
from time import perf_counter
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from betteruv.core.orchestrator import BetterUVOrchestrator

try:
    from dotenv import find_dotenv, load_dotenv
except ModuleNotFoundError:  # pragma: no cover
    find_dotenv = None  # type: ignore[assignment]
    load_dotenv = None  # type: ignore[assignment]

app = typer.Typer(help="Infer and install Python dependencies for metadata-poor repos.")
console = Console()


def _load_local_env() -> None:
    """Load env vars from a local .env file if python-dotenv is available."""
    if load_dotenv is None or find_dotenv is None:
        return
    env_path = find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path, override=False)


def _bool_label(value: bool) -> str:
    return "[green]yes[/green]" if value else "[dim]no[/dim]"


def _render_packages(packages: list[str], reasons: dict[str, str]) -> None:
    table = Table(title="Resolved Packages", show_lines=False)
    table.add_column("Package", style="cyan", no_wrap=True)
    table.add_column("Source", style="dim")
    if not packages:
        table.add_row("(none)", "No third-party imports detected")
    else:
        for package in packages:
            table.add_row(package, reasons.get(package, "-"))
    console.print(table)


@app.command()
def scan(
    path: str = typer.Argument(".", help="Path to the repository"),
    include_tests: bool = typer.Option(True, help="Include test files"),
) -> None:
    """Scan a repo and print dependency-related findings."""
    orchestrator = BetterUVOrchestrator()
    start = perf_counter()
    with console.status("Scanning repository..."):
        result = orchestrator.scan(Path(path), include_tests=include_tests)
    elapsed = perf_counter() - start

    console.print(Text("betteruv scan", style="bold cyan"))
    console.print(f"[dim]Repo:[/dim] {result.repo_profile.root}")
    console.print(f"[green]Complete[/green] in {elapsed:.2f}s")

    meta = Table(title="Metadata", show_header=True)
    meta.add_column("File", style="cyan")
    meta.add_column("Detected", style="white")
    meta.add_row("requirements.txt", _bool_label(result.repo_profile.has_requirements_txt))
    meta.add_row("pyproject.toml", _bool_label(result.repo_profile.has_pyproject_toml))
    meta.add_row("uv.lock", _bool_label(result.repo_profile.has_uv_lock))
    meta.add_row("setup.py", _bool_label(result.repo_profile.has_setup_py))
    console.print(meta)

    stats = Table(title="Scan Stats", show_header=True)
    stats.add_column("Metric", style="cyan")
    stats.add_column("Value", justify="right")
    stats.add_row("Python files", str(result.stats.python_files_scanned))
    stats.add_row("Raw imports", str(result.stats.raw_imports_found))
    stats.add_row("Unique imports", str(len(result.classification.all_top_level_imports)))
    stats.add_row("Third-party candidates", str(len(result.classification.third_party_imports)))
    console.print(stats)

    third_party = sorted(result.classification.third_party_imports)
    if third_party:
        console.print(Panel("\n".join(third_party), title="Third-party Imports", border_style="blue"))
    else:
        console.print(Panel("No third-party imports detected.", title="Third-party Imports", border_style="blue"))


@app.command()
def resolve(
    path: str = typer.Argument(".", help="Path to the repository"),
    include_tests: bool = typer.Option(True, help="Include test files"),
    install: bool = typer.Option(True, help="Install resolved dependencies"),
    write_requirements: bool = typer.Option(True, help="Write requirements.inferred.txt"),
    run_tests: bool = typer.Option(
        False,
        help="Run tests after successful resolve/install/verify",
    ),
    test_command: str = typer.Option(
        "pytest -q",
        help="Test command to run when --run-tests is enabled",
    ),
    init_project: bool = typer.Option(
        True,
        help="Initialize project with 'uv init --bare' if pyproject.toml is missing",
    ),
    sync: bool = typer.Option(
        False,
        help="Run 'uv sync' after adding dependencies",
    ),
    frozen_sync: bool = typer.Option(
        False,
        help="Run 'uv sync --frozen' (requires an up-to-date lockfile)",
    ),
) -> None:
    """Resolve and optionally install inferred dependencies."""
    orchestrator = BetterUVOrchestrator()
    start = perf_counter()
    with console.status("Resolving dependency plan...") as status:
        def _progress_update(message: str) -> None:
            clean = message.strip()
            if not clean:
                return
            if len(clean) > 100:
                clean = clean[:97] + "..."
            status.update(f"[bold cyan]Installing[/bold cyan] {clean}")

        result = orchestrator.resolve(
            Path(path),
            include_tests=include_tests,
            install=install,
            write_requirements=write_requirements,
            run_tests_after_resolve=run_tests,
            test_command=shlex.split(test_command),
            init_project=init_project,
            sync=sync,
            frozen_sync=frozen_sync,
            progress_callback=_progress_update if install else None,
        )
    elapsed = perf_counter() - start

    console.print(Text("betteruv resolve", style="bold cyan"))
    console.print(f"[dim]Mode:[/dim] [bold]{result.mode}[/bold]")
    console.print(f"[green]Complete[/green] in {elapsed:.2f}s")

    _render_packages(result.plan.packages, result.plan.mapping_reasons)

    if result.plan.unresolved_imports:
        console.print(
            Panel(
                "\n".join(result.plan.unresolved_imports),
                title="Unresolved Imports",
                border_style="yellow",
            )
        )

    if result.requirements_path:
        console.print(
            Panel(
                f"Wrote inferred requirements to:\n[cyan]{result.requirements_path}[/cyan]",
                title="Output",
                border_style="green",
            )
        )

    if result.install_result is not None:
        install_title = "Install" if result.install_result.success else "Install Failed"
        install_style = "green" if result.install_result.success else "red"
        if result.install_result.success:
            install_body = [
                f"Installed or updated {len(result.plan.packages)} packages.",
                f"Command: {' '.join(result.install_result.command)}",
            ]
            if sync:
                install_body.append("Environment sync requested.")
        else:
            install_body = [f"Command: {' '.join(result.install_result.command)}"]
            if result.install_result.stdout.strip():
                install_body.append("\nstdout:\n" + result.install_result.stdout.strip())
            if result.install_result.stderr.strip():
                install_body.append("\nstderr:\n" + result.install_result.stderr.strip())
        console.print(Panel("\n".join(install_body), title=install_title, border_style=install_style))

    if result.verify_result is not None:
        verify_style = "green" if result.verify_result.success else "red"
        if result.verify_result.failed_imports:
            failed = "\n".join(result.verify_result.failed_imports)
            verify_message = f"Failed imports:\n{failed}"
        else:
            verify_message = "All checked imports imported successfully."
        console.print(Panel(verify_message, title="Verification", border_style=verify_style))

    if result.failure_analysis is not None:
        analysis_lines = [
            result.failure_analysis.get("message", "Unknown verification failure."),
        ]
        recommendation = result.failure_analysis.get("recommendation")
        if recommendation:
            analysis_lines.append("")
            analysis_lines.append(recommendation)
        console.print(
            Panel(
                "\n".join(analysis_lines),
                title=f"Failure Analysis: {result.failure_analysis.get('type', 'unknown')}",
                border_style="yellow",
            )
        )

    if result.test_result is not None:
        test_title = "Tests Passed" if result.test_result.success else "Tests Failed"
        test_style = "green" if result.test_result.success else "red"
        test_lines = [f"Command: {' '.join(result.test_result.command)}"]
        if result.test_result.success:
            test_lines.append("Test run completed successfully.")
        else:
            if result.test_result.stdout.strip():
                test_lines.append("\nstdout:\n" + result.test_result.stdout.strip())
            if result.test_result.stderr.strip():
                test_lines.append("\nstderr:\n" + result.test_result.stderr.strip())
        console.print(Panel("\n".join(test_lines), title=test_title, border_style=test_style))


@app.command()
def verify(
    path: str = typer.Argument(".", help="Path to the repository"),
    include_tests: bool = typer.Option(True, help="Include test files"),
    python_executable: Optional[str] = typer.Option(None, help="Python executable to use"),
    use_uv_run: bool = typer.Option(
        False,
        help="Run verification via 'uv run' when uv is available",
    ),
) -> None:
    """Verify imports for a repo."""
    orchestrator = BetterUVOrchestrator()
    start = perf_counter()
    with console.status("Running import verification..."):
        result = orchestrator.verify(
            Path(path),
            include_tests=include_tests,
            python_executable=python_executable,
            use_uv_run=use_uv_run,
        )
    elapsed = perf_counter() - start

    title = "Verification" if result.success else "Verification Failed"
    border = "green" if result.success else "red"
    message_lines = [f"Checked imports: {len(result.checked_imports)}", f"Elapsed: {elapsed:.2f}s"]
    if result.failed_imports:
        message_lines.append("\nFailed imports:")
        message_lines.extend(result.failed_imports)
    else:
        message_lines.append("\nAll checked imports imported successfully.")

    console.print(Panel("\n".join(message_lines), title=title, border_style=border))


def main() -> None:
    _load_local_env()
    app()
