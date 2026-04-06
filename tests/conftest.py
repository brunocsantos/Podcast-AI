"""Shared test fixtures."""

import pytest

from podcast_ai.models.schemas import Article


@pytest.fixture
def sample_articles():
    return [
        Article(
            title="New Zelda Game Announced",
            url="https://example.com/zelda",
            source="IGN",
            summary="Nintendo announces a new Zelda title for 2026.",
        ),
        Article(
            title="Steam Summer Sale Starts Next Week",
            url="https://example.com/steam-sale",
            source="PC Gamer",
            summary="Valve confirms dates for the annual Steam Summer Sale.",
        ),
        Article(
            title="PlayStation 6 Specs Leaked",
            url="https://example.com/ps6",
            source="Eurogamer",
            summary="Leaked documents reveal PS6 hardware specifications.",
        ),
    ]
