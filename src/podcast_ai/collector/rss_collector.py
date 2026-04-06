"""RSS feed collector for gaming news."""

from datetime import UTC, datetime, timedelta

import feedparser

from podcast_ai.models.schemas import Article
from podcast_ai.utils.config import CollectorConfig
from podcast_ai.utils.logging import get_logger

log = get_logger(__name__)


def collect_from_feeds(config: CollectorConfig) -> list[Article]:
    """Collect articles from all configured RSS feeds."""
    cutoff = datetime.now(UTC) - timedelta(hours=config.lookback_hours)
    all_articles: list[Article] = []

    for feed_source in config.feeds:
        try:
            articles = _parse_feed(feed_source.url, feed_source.name, cutoff)
            all_articles.extend(articles)
            log.info("feed_collected", source=feed_source.name, count=len(articles))
        except Exception as e:
            log.error("feed_failed", source=feed_source.name, error=str(e))

    all_articles = deduplicate(all_articles)
    log.info("collection_complete", total=len(all_articles))
    return all_articles


def _parse_feed(url: str, source_name: str, cutoff: datetime) -> list[Article]:
    """Parse a single RSS feed and return articles after the cutoff date."""
    feed = feedparser.parse(url)
    articles: list[Article] = []

    for entry in feed.entries:
        published = _parse_date(entry)
        if published and published < cutoff:
            continue

        summary = entry.get("summary", entry.get("description", ""))
        # Strip HTML tags from summary (basic approach)
        if summary:
            import re
            summary = re.sub(r"<[^>]+>", "", summary).strip()
            summary = summary[:500] if len(summary) > 500 else summary

        articles.append(
            Article(
                title=entry.get("title", "Untitled"),
                url=entry.get("link", ""),
                source=source_name,
                summary=summary or None,
                published_at=published,
            )
        )

    return articles


def _parse_date(entry) -> datetime | None:
    """Try to parse the published date from a feed entry."""
    for field in ("published_parsed", "updated_parsed"):
        parsed = entry.get(field)
        if parsed:
            from time import mktime
            return datetime.fromtimestamp(mktime(parsed), tz=UTC)
    return None


def deduplicate(articles: list[Article], threshold: float = 0.7) -> list[Article]:
    """Remove duplicate articles based on title similarity."""
    from difflib import SequenceMatcher

    unique: list[Article] = []
    for article in articles:
        is_duplicate = False
        for existing in unique:
            ratio = SequenceMatcher(None, article.title.lower(), existing.title.lower()).ratio()
            if ratio >= threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            unique.append(article)
    return unique
