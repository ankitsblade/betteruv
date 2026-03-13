import httpx
import requests
from bs4 import BeautifulSoup


def parse_title(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return soup.title.string.strip() if soup.title and soup.title.string else "untitled"


def build_preview() -> dict[str, object]:
    # No network calls in the demo runner: we only build client objects.
    requests_client = requests.Session()
    async_client = httpx.AsyncClient(timeout=4.0)
    return {
        "requests_client": requests_client.__class__.__name__,
        "httpx_client": async_client.__class__.__name__,
    }
