"""Summarize and group collected articles into topics using Gemini."""

import json

import google.generativeai as genai

from podcast_ai.models.schemas import Article, Topic
from podcast_ai.utils.logging import get_logger

log = get_logger(__name__)

SUMMARIZE_PROMPT = """Analise os seguintes artigos de notícias sobre games e agrupe-os
em no máximo {max_topics} tópicos principais. Para cada tópico, escreva um resumo
conciso em português brasileiro.

Artigos:
{articles_text}

Responda APENAS com JSON válido no seguinte formato:
{{
    "topics": [
        {{
            "title": "Título do tópico",
            "brief": "Resumo conciso do tópico com os pontos principais...",
            "article_indices": [0, 1, 3]
        }}
    ]
}}

Os article_indices são os índices (começando em 0) dos artigos que pertencem a cada tópico.
"""


def summarize_articles(
    articles: list[Article], api_key: str, max_topics: int = 5
) -> list[Topic]:
    """Group and summarize articles into topics using Gemini."""
    if not articles:
        return []

    articles_text = "\n\n".join(
        f"[{i}] {a.title} ({a.source})\n{a.summary or 'Sem resumo disponível'}"
        for i, a in enumerate(articles)
    )

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    response = model.generate_content(
        SUMMARIZE_PROMPT.format(max_topics=max_topics, articles_text=articles_text),
        generation_config=genai.types.GenerationConfig(
            response_mime_type="application/json",
        ),
    )

    raw = response.text
    # Handle markdown code blocks in response
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    data = json.loads(raw)

    topics: list[Topic] = []
    for t in data["topics"]:
        topic_articles = [articles[i] for i in t["article_indices"] if i < len(articles)]
        topics.append(
            Topic(title=t["title"], brief=t["brief"], articles=topic_articles)
        )

    log.info("topics_generated", count=len(topics))
    return topics
