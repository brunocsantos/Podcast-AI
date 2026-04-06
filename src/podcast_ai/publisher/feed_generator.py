"""Generate and update the podcast RSS feed."""

from datetime import datetime, UTC
from pathlib import Path

from podgen import Category, Episode, Media, Podcast

from podcast_ai.utils.config import PodcastConfig, PublisherConfig
from podcast_ai.utils.logging import get_logger

log = get_logger(__name__)


def create_or_update_feed(
    podcast_config: PodcastConfig,
    publisher_config: PublisherConfig,
    episode_title: str,
    episode_description: str,
    audio_path: Path,
    episode_number: int,
) -> Path:
    """Create or update the podcast RSS feed with a new episode."""
    feed_path = Path(publisher_config.feed_path)

    # Create the podcast feed
    p = Podcast(
        name=podcast_config.name,
        description=podcast_config.description,
        website=publisher_config.base_url,
        language=podcast_config.language,
        category=Category("Leisure", "Video Games"),
        explicit=False,
    )

    # Calculate audio file size
    audio_size = audio_path.stat().st_size if audio_path.exists() else 0
    audio_url = f"{publisher_config.base_url}/episodes/{audio_path.name}"

    # Create episode entry
    ep = Episode(
        title=episode_title,
        summary=episode_description,
        long_summary=episode_description,
        media=Media(audio_url, size=audio_size, type="audio/mpeg"),
        publication_date=datetime.now(UTC),
    )
    ep.episode_number = episode_number

    p.episodes.append(ep)

    # Write feed
    feed_path.parent.mkdir(parents=True, exist_ok=True)
    p.rss_file(str(feed_path))

    log.info("feed_updated", path=str(feed_path), episode=episode_number)
    return feed_path
