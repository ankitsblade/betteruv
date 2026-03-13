# betteruv

`betteruv` is a CLI that scans Python repos, infers dependencies from imports, installs with `uv`,
and verifies imports (optionally runs tests).

## What It Does

- Scans Python source files and extracts imports
- Classifies imports into stdlib/local/third-party
- Builds a dependency plan from metadata and scan results
- Uses AI fallback for unresolved or low-confidence mappings (when configured)
- Installs dependencies with `uv`
- Verifies imports and can run tests after resolve
- Writes `requirements.inferred.txt` for review

## Requirements

- Python 3.10+
- `uv` installed and on `PATH`

## Install

### Local editable install

```bash
git clone <your-repo-url>
cd betteruv
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Install from git on another system

```bash
pip install "git+https://github.com/<you>/betteruv.git"
```

### Global tool install with pipx

```bash
pipx install "git+https://github.com/<you>/betteruv.git"
```

## Usage

Scan a repository:

```bash
betteruv scan /path/to/repo
```

Resolve and install:

```bash
betteruv resolve /path/to/repo
```

Preview only (no install):

```bash
betteruv resolve /path/to/repo --no-install
```

Resolve and run tests:

```bash
betteruv resolve /path/to/repo --run-tests
```

Custom test command:

```bash
betteruv resolve /path/to/repo --run-tests --test-command "pytest -q"
```

Verify imports only:

```bash
betteruv verify /path/to/repo
```

## AI Configuration (Optional)

Set these for AI-assisted mapping and version inference:

```bash
export GROQ_API_KEY=your_groq_api_key
export BETTERUV_GROQ_MODEL=llama-3.3-70b-versatile
```

If AI is not configured, `betteruv` continues with deterministic mapping.

## Notes

- Works best on small to medium Python repos with incomplete metadata
- Generated dependency output should be reviewed before production use
- Import verification checks importability, not full runtime correctness
