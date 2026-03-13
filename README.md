# betteruv (v0.5)

`betteruv` is a lightweight CLI that scans Python repos, infers missing dependencies, and installs them using `uv`.

This is **v0.5**: usable for demos and early workflows, with planned improvements listed below.

## What It Does

- Scans Python files and collects imports
- Classifies likely third-party imports
- Maps imports to package names
- Resolves and installs dependencies with `uv`
- Optionally writes `requirements.inferred.txt`
- Verifies imports after install

## Install

### Option 1: Local Dev (recommended for now)

```bash
git clone git@github.com:ankitsblade/betteruv.git
cd betteruv
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Requirements

- Python 3.10+
- `uv` installed and available in PATH

## Quick Usage

Scan a repo:

```bash
betteruv scan /path/to/repo
```

Resolve dependencies (default flow):

```bash
betteruv resolve /path/to/repo
```

Resolve without installing (preview only):

```bash
betteruv resolve /path/to/repo --no-install
```

Resolve a repo. Unresolved imports automatically fall back to AI-assisted mapping when available:

```bash
# Put keys in .env (auto-loaded by betteruv), or export in shell.
# GROQ_API_KEY=your_groq_api_key
# BETTERUV_GROQ_MODEL=llama-3.3-70b-versatile  # optional
betteruv resolve /path/to/repo
```

Verify imports:

```bash
betteruv verify /path/to/repo
```

Use `uv run` for verification:

```bash
betteruv verify /path/to/repo --use-uv-run
```

## v0.5 Notes

- Works best for small to medium Python repos with missing metadata
- Uses alias mapping and marks unknown imports as unresolved
- Automatically uses Groq (Llama 3.3 by default) as a fallback for unresolved imports when configured
- Output is designed to be clear and fast for iterative use

## Future Checklist

- [ ] Split runtime vs dev/test dependencies (`uv add` vs `uv add --dev`)
- [ ] Improve unresolved import handling and confidence scoring
- [ ] Add lockfile/export helpers (`uv lock`, `uv export`)
- [ ] Add optional plain/CI output mode
- [ ] Add richer repo-level reports (JSON output)
- [ ] Expand alias map coverage and quality tests
