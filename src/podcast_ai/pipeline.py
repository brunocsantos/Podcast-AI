"""Core pipeline logic extracted for reuse by CLI and scheduler."""

import json
import tempfile
from pathlib import Path

from podcast_ai.utils.config import Settings
from podcast_ai.utils.logging import get_logger

log = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def run_pipeline(settings: Settings, episode_number: int | None = None) -> Path:
    """Run the full podcast generation pipeline.

    If episode_number is None, auto-increments from the episode tracker.
    Returns the path to the generated audio file.
    """
    from podcast_ai.collector.rss_collector import collect_from_feeds
    from podcast_ai.scriptwriter.summarizer import summarize_articles
    from podcast_ai.scriptwriter.script_generator import generate_script
    from podcast_ai.audio.tts_engine import generate_audio_segments
    from podcast_ai.audio.audio_assembler import assemble_episode
    from podcast_ai.publisher.episode_tracker import EpisodeTracker
    from podcast_ai.publisher.feed_generator import build_feed, upload_feed
    from podcast_ai.publisher.storage import upload_episode

    data_dir = PROJECT_ROOT / "data"
    tracker = EpisodeTracker(data_dir / "episodes.json")

    if episode_number is None:
        episode_number = tracker.next_episode_number()

    log.info("pipeline_start", episode=episode_number)

    # Step 1: Collect news
    log.info("step", name="collect")
    articles = collect_from_feeds(settings.collector)
    if not articles:
        raise RuntimeError("No articles collected from any feed")

    data_dir.mkdir(parents=True, exist_ok=True)
    with open(data_dir / "collected.json", "w") as f:
        json.dump([a.model_dump(mode="json") for a in articles], f, indent=2, ensure_ascii=False)

    # Step 2: Summarize into topics
    log.info("step", name="summarize")
    topics = summarize_articles(
        articles, settings.anthropic_api_key, settings.podcast.max_topics
    )
    if not topics:
        raise RuntimeError("Failed to generate topics from articles")

    # Step 3: Generate script
    log.info("step", name="script")
    script, title, description = generate_script(
        topics=topics,
        hosts=settings.podcast.hosts,
        api_key=settings.anthropic_api_key,
        episode_number=episode_number,
        target_minutes=settings.podcast.target_duration_minutes,
    )

    scripts_dir = data_dir / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    with open(scripts_dir / f"ep_{episode_number:03d}.json", "w") as f:
        json.dump(script.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

    # Step 4: Generate audio
    log.info("step", name="audio")
    with tempfile.TemporaryDirectory() as tmp_dir:
        segments = generate_audio_segments(
            dialogue=script.dialogue,
            hosts=settings.podcast.hosts,
            api_key=settings.elevenlabs_api_key,
            audio_config=settings.audio,
            output_dir=Path(tmp_dir),
        )

        episodes_dir = PROJECT_ROOT / settings.publisher.output_dir
        episodes_dir.mkdir(parents=True, exist_ok=True)
        output_path = episodes_dir / f"ep_{episode_number:03d}.mp3"

        intro_path = PROJECT_ROOT / "assets" / "intro.mp3"
        outro_path = PROJECT_ROOT / "assets" / "outro.mp3"

        assemble_episode(
            segments=segments,
            output_path=output_path,
            audio_config=settings.audio,
            intro_path=intro_path if intro_path.exists() else None,
            outro_path=outro_path if outro_path.exists() else None,
        )

    # Step 5: Upload audio to cloud storage
    log.info("step", name="upload")
    audio_url = upload_episode(
        audio_path=output_path,
        publisher_config=settings.publisher,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )

    # Step 6: Track episode and rebuild feed
    log.info("step", name="publish")
    topic_titles = [t.title for t in topics]
    tracker.add_episode(
        episode_number=episode_number,
        title=title,
        description=description,
        audio_path=str(output_path),
        audio_url=audio_url,
        topics=topic_titles,
    )

    feed_path = build_feed(
        podcast_config=settings.podcast,
        publisher_config=settings.publisher,
        episodes=tracker.get_all(),
    )
    upload_feed(feed_path, settings.publisher)

    log.info("pipeline_complete", episode=episode_number, audio=str(output_path))
    return output_path
