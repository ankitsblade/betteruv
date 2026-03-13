from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from challengeapp.orchestrator import run_pipeline


if __name__ == "__main__":
    print(run_pipeline())
