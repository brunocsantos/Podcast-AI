"""Data models for the podcast pipeline."""

from datetime import date, datetime

from pydantic import BaseModel, HttpUrl


class Article(BaseModel):
    """A collected news article."""

    title: str
    url: str
    source: str
    summary: str | None = None
    published_at: datetime | None = None
    relevance_score: float = 0.0


class Topic(BaseModel):
    """A summarized topic grouping related articles."""

    title: str
    brief: str
    articles: list[Article]


class DialogueLine(BaseModel):
    """A single line of dialogue in the podcast script."""

    speaker: str
    text: str


class Script(BaseModel):
    """A complete podcast episode script."""

    episode_number: int
    date: date
    topics: list[Topic]
    dialogue: list[DialogueLine]


class Episode(BaseModel):
    """A published podcast episode."""

    episode_number: int
    title: str
    description: str
    audio_path: str
    audio_url: str | None = None
    duration_seconds: int = 0
    published_at: datetime
