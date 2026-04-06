"""Generate podcast scripts using Claude API."""

import json
from datetime import date

import anthropic

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
) -> Script:
    """Generate a full podcast script from topics using Claude."""
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

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text
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
