"""Generate and maintain the podcast RSS feed (Spotify-compatible)."""

from datetime import datetime, UTC
from pathlib import Path

from podgen import Category, Episode, Media, Person, Podcast

from podcast_ai.publisher.episode_tracker import EpisodeRecord
from podcast_ai.utils.config import PodcastConfig, PublisherConfig
from podcast_ai.utils.logging import get_logger

log = get_logger(__name__)


def build_feed(
    podcast_config: PodcastConfig,
    publisher_config: PublisherConfig,
    episodes: list[EpisodeRecord],
) -> Path:
    """Build the full podcast RSS feed from all tracked episodes.

    Spotify requires:
    - Valid RSS 2.0 with iTunes namespace
    - <itunes:image> with artwork URL (1400x1400 to 3000x3000 JPEG/PNG)
    - <itunes:category> tag
    - <itunes:author> and <itunes:owner>
    - <itunes:explicit> tag
    - Each <item> needs <enclosure> with valid audio URL, type, and length
    """
    feed_path = Path(publisher_config.feed_path)

    p = Podcast(
        name=podcast_config.name,
        description=podcast_config.description,
        website=publisher_config.base_url,
        language=podcast_config.language,
        category=Category("Leisure", "Video Games"),
        explicit=False,
        image=podcast_config.artwork_url or f"{publisher_config.base_url}/artwork.jpg",
        authors=[Person(podcast_config.author_name, podcast_config.author_email)],
        owner=Person(podcast_config.author_name, podcast_config.author_email),
        complete=False,
    )

    # Add all episodes (newest first for Spotify)
    for rec in sorted(episodes, key=lambda e: e.episode_number, reverse=True):
        audio_url = rec.audio_url or f"{publisher_config.base_url}/episodes/{Path(rec.audio_path).name}"
        audio_path = Path(rec.audio_path)
        audio_size = audio_path.stat().st_size if audio_path.exists() else 0

        ep = Episode(
            title=rec.title,
            summary=rec.description,
            long_summary=rec.description,
            media=Media(audio_url, size=audio_size, type="audio/mpeg"),
            publication_date=datetime.fromisoformat(rec.published_at),
        )
        ep.episode_number = rec.episode_number
        p.episodes.append(ep)

    feed_path.parent.mkdir(parents=True, exist_ok=True)
    p.rss_file(str(feed_path))

    log.info("feed_built", path=str(feed_path), episodes=len(episodes))
    return feed_path
