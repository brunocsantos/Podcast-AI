"""Assemble audio segments into a final podcast episode."""

from pathlib import Path

from pydub import AudioSegment

from podcast_ai.utils.config import AudioConfig
from podcast_ai.utils.logging import get_logger

log = get_logger(__name__)


def assemble_episode(
    segments: list[Path],
    output_path: Path,
    audio_config: AudioConfig,
    intro_path: Path | None = None,
    outro_path: Path | None = None,
) -> Path:
    """Concatenate audio segments with silence between turns into a final episode."""
    silence = AudioSegment.silent(duration=audio_config.silence_between_turns_ms)
    episode = AudioSegment.empty()

    # Add intro if available
    if intro_path and intro_path.exists():
        intro = AudioSegment.from_mp3(str(intro_path))
        episode += intro + silence
        log.info("intro_added")

    # Concatenate dialogue segments
    for i, segment_path in enumerate(segments):
        segment = AudioSegment.from_mp3(str(segment_path))
        episode += segment
        if i < len(segments) - 1:
            episode += silence

    # Add outro if available
    if outro_path and outro_path.exists():
        outro = AudioSegment.from_mp3(str(outro_path))
        episode += silence + outro
        log.info("outro_added")

    # Export final episode
    output_path.parent.mkdir(parents=True, exist_ok=True)
    episode.export(str(output_path), format="mp3", bitrate="128k")

    duration_seconds = len(episode) // 1000
    log.info("episode_assembled", path=str(output_path), duration_s=duration_seconds)
    return output_path
