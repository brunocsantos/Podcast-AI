"""Generate podcast scripts using Google Gemini API."""

import json
from datetime import date

from google import genai
from google.genai import types

from podcast_ai.models.schemas import DialogueLine, Script, Topic
from podcast_ai.scriptwriter.prompts import EPISODE_PROMPT, SYSTEM_PROMPT
from podcast_ai.utils.config import HostConfig
from podcast_ai.utils.logging import get_logger

log = get_logger(__name__)


def generate_script(
    topics: list[Topic],
    hosts: list[HostConfig],
    api_key: str,
    episode_number: int = 1,
    target_minutes: int = 15,
) -> tuple[Script, str, str]:
    """Generate a full podcast script from topics using Gemini."""
    hosts_description = "\n".join(
        f"- {h.name}: {h.personality}" for h in hosts
    )

    system = SYSTEM_PROMPT.format(
        hosts_description=hosts_description,
        target_minutes=target_minutes,
    )

    topics_text = "\n\n".join(
        f"### Tópico {i + 1}: {t.title}\n{t.brief}" for i, t in enumerate(topics)
    )

    user_message = EPISODE_PROMPT.format(
        episode_number=episode_number,
        date=date.today().isoformat(),
        topics_text=topics_text,
    )

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
        ),
    )

    raw = response.text
    # Handle markdown code blocks in response
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    data = json.loads(raw)

    dialogue = [DialogueLine(**line) for line in data["dialogue"]]

    script = Script(
        episode_number=episode_number,
        date=date.today(),
        topics=topics,
        dialogue=dialogue,
    )

    log.info(
        "script_generated",
        episode=episode_number,
        lines=len(dialogue),
        title=data.get("title", ""),
    )
    return script, data.get("title", f"Episódio {episode_number}"), data.get("description", "")
