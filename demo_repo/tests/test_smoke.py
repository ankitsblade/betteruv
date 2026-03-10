import pytest
import requests


def test_requests_available() -> None:
    assert requests.__name__ == "requests"


def test_pytest_available() -> None:
    assert pytest.__name__ == "pytest"
