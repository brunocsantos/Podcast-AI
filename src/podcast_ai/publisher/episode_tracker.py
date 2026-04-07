"""Episode tracker - persists episode state across runs."""

import json
from datetime import datetime, UTC
from pathlib import Path

from pydantic import BaseModel

from podcast_ai.utils.logging import get_logger

log = get_logger(__name__)

TRACKER_FILE = "data/episodes.json"


class EpisodeRecord(BaseModel):
    episode_number: int
    title: str
    description: str
    audio_path: str
    audio_url: str | None = None
    published_at: str
    topics: list[str] = []


class EpisodeTracker:
    """Tracks published episodes and auto-increments episode numbers."""

    def __init__(self, tracker_path: Path):
        self.tracker_path = tracker_path
        self.episodes: list[EpisodeRecord] = []
        self._load()

    def _load(self):
        if self.tracker_path.exists():
            with open(self.tracker_path) as f:
                data = json.load(f)
            self.episodes = [EpisodeRecord(**ep) for ep in data]
            log.info("tracker_loaded", count=len(self.episodes))

    def _save(self):
        self.tracker_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.tracker_path, "w") as f:
            json.dump(
                [ep.model_dump() for ep in self.episodes],
                f,
                indent=2,
                ensure_ascii=False,
            )

    def next_episode_number(self) -> int:
        if not self.episodes:
            return 1
        return max(ep.episode_number for ep in self.episodes) + 1

    def add_episode(
        self,
        episode_number: int,
        title: str,
        description: str,
        audio_path: str,
        audio_url: str | None = None,
        topics: list[str] | None = None,
    ) -> EpisodeRecord:
        record = EpisodeRecord(
            episode_number=episode_number,
            title=title,
            description=description,
            audio_path=audio_path,
            audio_url=audio_url,
            published_at=datetime.now(UTC).isoformat(),
            topics=topics or [],
        )
        self.episodes.append(record)
        self._save()
        log.info("episode_tracked", episode=episode_number, title=title)
        return record

    def get_all(self) -> list[EpisodeRecord]:
        return list(self.episodes)
