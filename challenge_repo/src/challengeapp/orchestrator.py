from challengeapp.api import health
from challengeapp.cloud_integrations import integration_summary
from challengeapp.data_pipeline import build_dataframe, local_sql_probe, vectorize_text
from challengeapp.documents import document_preview
from challengeapp.http_clients import build_preview, parse_title
from challengeapp.settings import load_settings
from sharedutils.hashing import short_hash


def run_pipeline() -> dict[str, object]:
    settings = load_settings()
    frame, mean_value = build_dataframe()
    dims = vectorize_text(frame)
    status = health()
    return {
        "project": settings["project"],
        "mean_value": mean_value,
        "tfidf_shape": dims,
        "http_clients": build_preview(),
        "sample_title": parse_title("<html><title>challenge</title></html>"),
        "sql": local_sql_probe(),
        "doc": document_preview(),
        "integration_types": integration_summary(),
        "health_status": status.status,
        "hash": short_hash(str(settings["boot_time"])),
    }
