from bs4 import BeautifulSoup
import httpx


def fetch_title(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string if soup.title else "untitled"
    return title.strip()


def ping(url: str) -> int:
    response = httpx.get(url, timeout=5)
    return response.status_code
