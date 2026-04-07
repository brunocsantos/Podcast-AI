"""Cloud storage upload for podcast audio files."""

import mimetypes
from pathlib import Path

import boto3
from botocore.config import Config as BotoConfig

from podcast_ai.utils.config import PublisherConfig
from podcast_ai.utils.logging import get_logger

log = get_logger(__name__)


def upload_episode(
    audio_path: Path,
    publisher_config: PublisherConfig,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
) -> str:
    """Upload an episode audio file to S3-compatible storage and return the public URL."""
    if publisher_config.storage_backend == "local":
        # For local storage, just return a file URL
        url = f"{publisher_config.base_url}/episodes/{audio_path.name}"
        log.info("local_storage", url=url)
        return url

    # S3 / R2 / compatible storage
    client_kwargs = {
        "service_name": "s3",
        "config": BotoConfig(signature_version="s3v4"),
    }

    if publisher_config.s3_endpoint_url:
        client_kwargs["endpoint_url"] = publisher_config.s3_endpoint_url

    if aws_access_key_id and aws_secret_access_key:
        client_kwargs["aws_access_key_id"] = aws_access_key_id
        client_kwargs["aws_secret_access_key"] = aws_secret_access_key

    if publisher_config.s3_region:
        client_kwargs["region_name"] = publisher_config.s3_region

    s3 = boto3.client(**client_kwargs)

    key = f"episodes/{audio_path.name}"
    content_type = mimetypes.guess_type(str(audio_path))[0] or "audio/mpeg"

    s3.upload_file(
        str(audio_path),
        publisher_config.s3_bucket,
        key,
        ExtraArgs={"ContentType": content_type, "ACL": "public-read"},
    )

    if publisher_config.s3_endpoint_url and "r2" in publisher_config.s3_endpoint_url:
        # Cloudflare R2 uses a custom public URL
        url = f"{publisher_config.base_url}/episodes/{audio_path.name}"
    else:
        url = f"https://{publisher_config.s3_bucket}.s3.amazonaws.com/{key}"

    log.info("s3_uploaded", bucket=publisher_config.s3_bucket, key=key, url=url)
    return url
