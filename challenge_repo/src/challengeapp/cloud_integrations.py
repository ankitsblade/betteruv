import boto3
from google.cloud import storage
from googleapiclient.discovery import build
import redis


def integration_summary() -> dict[str, str]:
    s3 = boto3.client("s3", region_name="us-east-1")
    redis_client = redis.Redis(host="localhost", port=6379, db=0)
    gcs_client = storage.Client.create_anonymous_client()
    sheets = build("sheets", "v4", cache_discovery=False)
    return {
        "s3": s3.__class__.__name__,
        "redis": redis_client.__class__.__name__,
        "gcs": gcs_client.__class__.__name__,
        "sheets": sheets.__class__.__name__,
    }
