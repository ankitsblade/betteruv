import pytest

from challengeapp.data_pipeline import build_dataframe
from challengeapp.http_clients import parse_title
from sharedutils.hashing import short_hash


def test_parse_title() -> None:
    assert parse_title("<html><title>x</title></html>") == "x"


@pytest.mark.smoke
def test_build_dataframe() -> None:
    frame, mean_value = build_dataframe()
    assert list(frame.columns) == ["id", "text", "value"]
    assert mean_value > 0


def test_short_hash() -> None:
    assert len(short_hash("abc")) == 10
