"""Tests for data models."""

from datetime import date

from podcast_ai.models.schemas import Article, DialogueLine, Script, Topic


def test_article_creation():
    article = Article(title="Test", url="https://example.com", source="Test Source")
    assert article.title == "Test"
    assert article.summary is None
    assert article.relevance_score == 0.0


def test_script_creation():
    topic = Topic(title="Test Topic", brief="A brief", articles=[])
    line = DialogueLine(speaker="Lucas", text="Olá pessoal!")
    script = Script(
        episode_number=1,
        date=date.today(),
        topics=[topic],
        dialogue=[line],
    )
    assert script.episode_number == 1
    assert len(script.dialogue) == 1
    assert script.dialogue[0].speaker == "Lucas"
