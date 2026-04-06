"""CLI entrypoint and pipeline orchestrator for Podcast AI."""

import json
import shutil
import tempfile
from datetime import datetime, UTC
from pathlib import Path

import typer

from podcast_ai.utils.config import load_settings
from podcast_ai.utils.logging import get_logger, setup_logging

app = typer.Typer(name="podcast-ai", help="Automated AI-powered gaming podcast generator")
log = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@app.command()
def run(
    episode_number: int = typer.Option(1, help="Episode number"),
    config_path: Path = typer.Option(None, help="Path to settings.yaml"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
):
    """Run the full podcast generation pipeline."""
    setup_logging("DEBUG" if verbose else "INFO")
    settings = load_settings(config_path)

    log.info("pipeline_start", episode=episode_number)

    # Step 1: Collect news
    log.info("step", name="collect")
    from podcast_ai.collector.rss_collector import collect_from_feeds

    articles = collect_from_feeds(settings.collector)
    if not articles:
        log.error("no_articles_collected")
        raise typer.Exit(1)

    # Save collected articles
    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    with open(data_dir / "collected.json", "w") as f:
        json.dump([a.model_dump(mode="json") for a in articles], f, indent=2, ensure_ascii=False)

    # Step 2: Summarize into topics
    log.info("step", name="summarize")
    from podcast_ai.scriptwriter.summarizer import summarize_articles

    topics = summarize_articles(
        articles, settings.anthropic_api_key, settings.podcast.max_topics
    )
    if not topics:
        log.error("no_topics_generated")
        raise typer.Exit(1)

    # Step 3: Generate script
    log.info("step", name="script")
    from podcast_ai.scriptwriter.script_generator import generate_script

    script, title, description = generate_script(
        topics=topics,
        hosts=settings.podcast.hosts,
        api_key=settings.anthropic_api_key,
        episode_number=episode_number,
        target_minutes=settings.podcast.target_duration_minutes,
    )

    # Save script
    scripts_dir = data_dir / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    with open(scripts_dir / f"ep_{episode_number:03d}.json", "w") as f:
        json.dump(script.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

    # Step 4: Generate audio
    log.info("step", name="audio")
    from podcast_ai.audio.tts_engine import generate_audio_segments
    from podcast_ai.audio.audio_assembler import assemble_episode

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

    # Step 5: Publish feed
    log.info("step", name="publish")
    from podcast_ai.publisher.feed_generator import create_or_update_feed

    create_or_update_feed(
        podcast_config=settings.podcast,
        publisher_config=settings.publisher,
        episode_title=title,
        episode_description=description,
        audio_path=output_path,
        episode_number=episode_number,
    )

    log.info("pipeline_complete", episode=episode_number, output=str(output_path))
    typer.echo(f"\n✅ Episódio {episode_number} gerado com sucesso: {output_path}")


@app.command()
def collect(
    config_path: Path = typer.Option(None, help="Path to settings.yaml"),
    output: Path = typer.Option(None, help="Output JSON file"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):
    """Collect gaming news from RSS feeds."""
    setup_logging("DEBUG" if verbose else "INFO")
    settings = load_settings(config_path)

    from podcast_ai.collector.rss_collector import collect_from_feeds

    articles = collect_from_feeds(settings.collector)

    out_path = output or PROJECT_ROOT / "data" / "collected.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump([a.model_dump(mode="json") for a in articles], f, indent=2, ensure_ascii=False)

    typer.echo(f"Coletados {len(articles)} artigos -> {out_path}")


@app.command()
def script(
    from_file: Path = typer.Option(..., help="Path to collected articles JSON"),
    episode_number: int = typer.Option(1, help="Episode number"),
    config_path: Path = typer.Option(None, help="Path to settings.yaml"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):
    """Generate a podcast script from collected articles."""
    setup_logging("DEBUG" if verbose else "INFO")
    settings = load_settings(config_path)

    from podcast_ai.models.schemas import Article
    from podcast_ai.scriptwriter.summarizer import summarize_articles
    from podcast_ai.scriptwriter.script_generator import generate_script

    with open(from_file) as f:
        articles = [Article(**a) for a in json.load(f)]

    topics = summarize_articles(articles, settings.anthropic_api_key, settings.podcast.max_topics)
    result, title, description = generate_script(
        topics=topics,
        hosts=settings.podcast.hosts,
        api_key=settings.anthropic_api_key,
        episode_number=episode_number,
        target_minutes=settings.podcast.target_duration_minutes,
    )

    scripts_dir = PROJECT_ROOT / "data" / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    out_path = scripts_dir / f"ep_{episode_number:03d}.json"
    with open(out_path, "w") as f:
        json.dump(result.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

    typer.echo(f"Script gerado: {out_path} ({len(result.dialogue)} linhas de diálogo)")


@app.command()
def audio(
    from_file: Path = typer.Option(..., help="Path to script JSON"),
    config_path: Path = typer.Option(None, help="Path to settings.yaml"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):
    """Generate podcast audio from a script file."""
    setup_logging("DEBUG" if verbose else "INFO")
    settings = load_settings(config_path)

    from podcast_ai.models.schemas import Script as ScriptModel
    from podcast_ai.audio.tts_engine import generate_audio_segments
    from podcast_ai.audio.audio_assembler import assemble_episode

    with open(from_file) as f:
        script_data = ScriptModel(**json.load(f))

    with tempfile.TemporaryDirectory() as tmp_dir:
        segments = generate_audio_segments(
            dialogue=script_data.dialogue,
            hosts=settings.podcast.hosts,
            api_key=settings.elevenlabs_api_key,
            audio_config=settings.audio,
            output_dir=Path(tmp_dir),
        )

        episodes_dir = PROJECT_ROOT / settings.publisher.output_dir
        episodes_dir.mkdir(parents=True, exist_ok=True)
        output_path = episodes_dir / f"ep_{script_data.episode_number:03d}.mp3"

        assemble_episode(
            segments=segments,
            output_path=output_path,
            audio_config=settings.audio,
        )

    typer.echo(f"Áudio gerado: {output_path}")


if __name__ == "__main__":
    app()
