"""Configuration loader for settings.yaml and environment variables."""

from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_settings import BaseSettings


load_dotenv()

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent.parent / "config"


class HostConfig(BaseModel):
    name: str
    voice_id: str
    personality: str


class PodcastConfig(BaseModel):
    name: str = "Game Over Cast"
    language: str = "pt-BR"
    description: str = ""
    hosts: list[HostConfig] = []
    target_duration_minutes: int = 15
    max_topics: int = 5


class FeedSource(BaseModel):
    url: str
    name: str


class CollectorConfig(BaseModel):
    lookback_hours: int = 48
    feeds: list[FeedSource] = []


class AudioConfig(BaseModel):
    tts_model: str = "eleven_multilingual_v2"
    output_format: str = "mp3_44100_128"
    silence_between_turns_ms: int = 300


class PublisherConfig(BaseModel):
    storage_backend: str = "local"
    output_dir: str = "data/episodes"
    feed_path: str = "data/feed.xml"
    base_url: str = "https://example.com/podcast"


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    elevenlabs_api_key: str = ""

    podcast: PodcastConfig = PodcastConfig()
    collector: CollectorConfig = CollectorConfig()
    audio: AudioConfig = AudioConfig()
    publisher: PublisherConfig = PublisherConfig()


def load_settings(config_path: Path | None = None) -> Settings:
    """Load settings from YAML config and environment variables."""
    if config_path is None:
        config_path = CONFIG_DIR / "settings.yaml"

    yaml_data = {}
    if config_path.exists():
        with open(config_path) as f:
            yaml_data = yaml.safe_load(f) or {}

    return Settings(**yaml_data)
