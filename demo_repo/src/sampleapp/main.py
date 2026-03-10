import requests
import yaml
from dateutil import parser

from sampleapp.fetch import fetch_title


def run() -> str:
    response = requests.get("https://example.com", timeout=5)
    data = yaml.safe_load("name: betteruv-demo")
    _ = parser.parse("2026-03-11")
    title = fetch_title(response.text)
    return f"{data['name']}:{title}"
