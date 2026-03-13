# Final Challenge Repo for betteruv

This is the last, more complex test repository for `betteruv`.

It intentionally mixes:

- API/service imports (`fastapi`, `pydantic`, `uvicorn`)
- data stack (`pandas`, `numpy`, `sqlalchemy`, `redis`)
- scraping/parsing (`bs4`, `yaml`, `dateutil`)
- cloud/document stack (`boto3`, `google.cloud.storage`, `googleapiclient`, `fitz`)
- vision/model stack (`PIL`, `cv2`, `sklearn`)
- test-only imports (`pytest`)
- local `src/` packages that must not be treated as third-party

## Why this is a good stress test

- Some imports map directly to package names (`fastapi`, `redis`, `boto3`)
- Some need alias mapping (`yaml`, `bs4`, `dateutil`, `PIL`, `cv2`, `sklearn`, `jwt`)
- Some are intentionally hard mappings (`google`, `fitz`, `googleapiclient`)
- No `pyproject.toml` or `requirements.txt` is included, so resolver must infer everything

## Suggested commands

```bash
uv run betteruv scan challenge_repo
uv run betteruv resolve challenge_repo --no-install
uv run betteruv resolve challenge_repo
uv run betteruv verify challenge_repo
```

## Optional runtime smoke

```bash
cd challenge_repo
uv run scripts/run_challenge.py
```

The script only executes lightweight local logic and should not call external services.
