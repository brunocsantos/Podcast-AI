"""Tests for the RSS collector module."""

from podcast_ai.collector.rss_collector import deduplicate
from podcast_ai.models.schemas import Article


def test_deduplicate_removes_similar_titles():
    articles = [
        Article(title="New Zelda Game Announced for 2026", url="https://a.com", source="IGN"),
        Article(title="New Zelda Game Announced", url="https://b.com", source="PC Gamer"),
        Article(title="Steam Sale Starts Next Week", url="https://c.com", source="Eurogamer"),
    ]
    result = deduplicate(articles, threshold=0.7)
    assert len(result) == 2


def test_deduplicate_keeps_unique_titles():
    articles = [
        Article(title="Zelda Announced", url="https://a.com", source="IGN"),
        Article(title="Steam Sale", url="https://b.com", source="PC Gamer"),
        Article(title="PS6 Specs Leaked", url="https://c.com", source="Eurogamer"),
    ]
    result = deduplicate(articles, threshold=0.7)
    assert len(result) == 3


def test_deduplicate_empty_list():
    assert deduplicate([]) == []
