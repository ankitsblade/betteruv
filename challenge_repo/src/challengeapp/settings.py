from datetime import datetime, timezone

from dotenv import load_dotenv
import yaml
from dateutil import parser


def load_settings() -> dict[str, object]:
    load_dotenv()
    config = yaml.safe_load(
        """
        project: betteruv-final-challenge
        timeout_seconds: 4
        include_embeddings: true
        """
    )
    config["boot_time"] = parser.parse("2026-03-13T11:30:00Z")
    config["loaded_at"] = datetime.now(timezone.utc)
    return config
