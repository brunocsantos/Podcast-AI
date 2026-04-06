"""ElevenLabs TTS engine for generating podcast audio."""

from pathlib import Path

from elevenlabs import ElevenLabs

from podcast_ai.models.schemas import DialogueLine
from podcast_ai.utils.config import AudioConfig, HostConfig
from podcast_ai.utils.logging import get_logger

log = get_logger(__name__)


def generate_audio_segments(
    dialogue: list[DialogueLine],
    hosts: list[HostConfig],
    api_key: str,
    audio_config: AudioConfig,
    output_dir: Path,
) -> list[Path]:
    """Generate individual audio segments for each dialogue line."""
    client = ElevenLabs(api_key=api_key)
    voice_map = {h.name: h.voice_id for h in hosts}
    output_dir.mkdir(parents=True, exist_ok=True)

    segments: list[Path] = []

    for i, line in enumerate(dialogue):
        voice_id = voice_map.get(line.speaker)
        if not voice_id:
            log.warning("unknown_speaker", speaker=line.speaker, index=i)
            continue

        segment_path = output_dir / f"segment_{i:04d}.mp3"

        audio_generator = client.text_to_speech.convert(
            voice_id=voice_id,
            text=line.text,
            model_id=audio_config.tts_model,
            output_format=audio_config.output_format,
        )

        with open(segment_path, "wb") as f:
            for chunk in audio_generator:
                f.write(chunk)

        segments.append(segment_path)
        log.info("segment_generated", index=i, speaker=line.speaker)

    return segments
