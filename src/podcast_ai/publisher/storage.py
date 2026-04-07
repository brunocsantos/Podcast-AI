"""Cloud storage upload for podcast audio files (S3 / Cloudflare R2)."""

import mimetypes
from pathlib import Path

from podcast_ai.utils.config import PublisherConfig
from podcast_ai.utils.logging import get_logger

log = get_logger(__name__)


def _get_s3_client(publisher_config: PublisherConfig, aws_access_key_id: str | None, aws_secret_access_key: str | None):
    """Create a boto3 S3 client configured for the storage backend."""
    import boto3
    from botocore.config import Config as BotoConfig

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

    return boto3.client(**client_kwargs)


def upload_file(
    file_path: Path,
    key: str,
    content_type: str,
    publisher_config: PublisherConfig,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
) -> str:
    """Upload any file to S3/R2 and return the public URL."""
    if publisher_config.storage_backend == "local":
        url = f"{publisher_config.base_url}/{key}"
        log.info("local_storage", key=key, url=url)
        return url

    s3 = _get_s3_client(publisher_config, aws_access_key_id, aws_secret_access_key)

    s3.upload_file(
        str(file_path),
        publisher_config.s3_bucket,
        key,
        ExtraArgs={"ContentType": content_type},
    )

    url = f"{publisher_config.base_url}/{key}"
    log.info("uploaded", bucket=publisher_config.s3_bucket, key=key, url=url)
    return url


def upload_episode(
    audio_path: Path,
    publisher_config: PublisherConfig,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
) -> str:
    """Upload an episode audio file and return the public URL."""
    content_type = mimetypes.guess_type(str(audio_path))[0] or "audio/mpeg"
    key = f"episodes/{audio_path.name}"
    return upload_file(audio_path, key, content_type, publisher_config, aws_access_key_id, aws_secret_access_key)


def upload_feed(
    feed_path: Path,
    publisher_config: PublisherConfig,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
) -> str:
    """Upload the RSS feed XML and return the public URL."""
    return upload_file(feed_path, "feed.xml", "application/rss+xml; charset=utf-8", publisher_config, aws_access_key_id, aws_secret_access_key)
