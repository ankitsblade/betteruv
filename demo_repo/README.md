# Demo Repo for betteruv

This repo intentionally has no `requirements.txt` or `pyproject.toml` dependencies so `betteruv` runs in inference mode.

## Suggested test commands

From the project root:

```bash
python -m betteruv.cli.app scan demo_repo
python -m betteruv.cli.app resolve demo_repo --install False
```
