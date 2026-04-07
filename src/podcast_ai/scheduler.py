"""Daily scheduler for automated podcast generation."""

import signal
import sys
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from podcast_ai.utils.config import load_settings
from podcast_ai.utils.logging import get_logger, setup_logging

log = get_logger(__name__)


def daily_episode_job(config_path: Path | None = None):
    """Generate a new podcast episode. Called by the scheduler."""
    from podcast_ai.pipeline import run_pipeline

    settings = load_settings(config_path)
    try:
        run_pipeline(settings)
        log.info("scheduled_episode_complete")
    except Exception as e:
        log.error("scheduled_episode_failed", error=str(e))


def start_scheduler(
    hour: int = 8,
    minute: int = 0,
    timezone: str = "America/Sao_Paulo",
    config_path: Path | None = None,
):
    """Start the daily podcast generation scheduler.

    By default, generates a new episode every day at 8:00 AM (Brasilia time).
    """
    setup_logging("INFO")

    scheduler = BlockingScheduler()
    trigger = CronTrigger(hour=hour, minute=minute, timezone=timezone)

    scheduler.add_job(
        daily_episode_job,
        trigger=trigger,
        kwargs={"config_path": config_path},
        id="daily_podcast",
        name="Daily Podcast Generation",
        max_instances=1,
        coalesce=True,
    )

    # Graceful shutdown
    def shutdown(signum, frame):
        log.info("scheduler_stopping")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    log.info(
        "scheduler_started",
        schedule=f"daily at {hour:02d}:{minute:02d}",
        timezone=timezone,
    )
    print(f"Scheduler iniciado - novo episódio diário às {hour:02d}:{minute:02d} ({timezone})")
    print("Pressione Ctrl+C para parar.")

    scheduler.start()
