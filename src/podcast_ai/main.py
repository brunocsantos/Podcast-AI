"""CLI entrypoint and pipeline orchestrator for Podcast AI."""

import json
import tempfile
from pathlib import Path

import typer

from podcast_ai.utils.config import load_settings
from podcast_ai.utils.logging import get_logger, setup_logging

app = typer.Typer(name="podcast-ai", help="Automated AI-powered gaming podcast generator")
log = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@app.command()
def run(
    episode_number: int = typer.Option(None, help="Episode number (auto-increments if omitted)"),
    config_path: Path = typer.Option(None, help="Path to settings.yaml"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
):
    """Run the full podcast generation pipeline."""
    setup_logging("DEBUG" if verbose else "INFO")
    settings = load_settings(config_path)

    from podcast_ai.pipeline import run_pipeline

    output_path = run_pipeline(settings, episode_number)
    typer.echo(f"\nEpisódio gerado com sucesso: {output_path}")


@app.command()
def schedule(
    hour: int = typer.Option(None, help="Hour to run (0-23), uses config if omitted"),
    minute: int = typer.Option(None, help="Minute to run (0-59), uses config if omitted"),
    timezone: str = typer.Option(None, help="Timezone, uses config if omitted"),
    config_path: Path = typer.Option(None, help="Path to settings.yaml"),
):
    """Start the daily automatic podcast generation scheduler.

    Generates a new episode every day at the configured time.
    The podcast feed is updated automatically after each episode.

    To publish on Spotify:
    1. Configure S3/R2 storage in settings.yaml for public audio hosting
    2. Submit your feed URL to Spotify for Podcasters (podcasters.spotify.com)
    3. Start this scheduler - Spotify polls your feed automatically
    """
    settings = load_settings(config_path)

    from podcast_ai.scheduler import start_scheduler

    start_scheduler(
        hour=hour if hour is not None else settings.scheduler.hour,
        minute=minute if minute is not None else settings.scheduler.minute,
        timezone=timezone or settings.scheduler.timezone,
        config_path=config_path,
    )


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

    topics = summarize_articles(articles, settings.gemini_api_key, settings.podcast.max_topics)
    result, title, description = generate_script(
        topics=topics,
        hosts=settings.podcast.hosts,
        api_key=settings.gemini_api_key,
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


@app.command()
def episodes(
    config_path: Path = typer.Option(None, help="Path to settings.yaml"),
):
    """List all generated episodes."""
    from podcast_ai.publisher.episode_tracker import EpisodeTracker

    tracker = EpisodeTracker(PROJECT_ROOT / "data" / "episodes.json")
    all_eps = tracker.get_all()

    if not all_eps:
        typer.echo("Nenhum episódio gerado ainda.")
        return

    typer.echo(f"Total: {len(all_eps)} episódio(s)\n")
    for ep in all_eps:
        typer.echo(f"  #{ep.episode_number:03d} | {ep.title}")
        typer.echo(f"         {ep.published_at[:10]} | {ep.audio_path}")
        if ep.audio_url:
            typer.echo(f"         URL: {ep.audio_url}")
        typer.echo()


if __name__ == "__main__":
    app()
