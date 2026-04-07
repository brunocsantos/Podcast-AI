"""Storage backends for podcast files (GitHub Pages, S3, or local)."""

import mimetypes
import shutil
import subprocess
import tempfile
from pathlib import Path

from podcast_ai.utils.config import PublisherConfig
from podcast_ai.utils.logging import get_logger

log = get_logger(__name__)


def publish_to_github_pages(
    publisher_config: PublisherConfig,
    site_dir: Path,
) -> str:
    """Publish the site directory to the gh-pages branch.

    site_dir should contain:
      - feed.xml
      - index.html
      - episodes/*.mp3
      - artwork.jpg (optional)

    Returns the public base URL.
    """
    repo_url = _get_remote_url()
    base_url = publisher_config.base_url

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Clone just the gh-pages branch (or create it)
        result = subprocess.run(
            ["git", "clone", "--branch", "gh-pages", "--single-branch", "--depth", "1", repo_url, str(tmp_path / "repo")],
            capture_output=True, text=True,
        )

        repo_path = tmp_path / "repo"
        if result.returncode != 0:
            # Branch doesn't exist yet, create an orphan
            repo_path.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=True)
            subprocess.run(["git", "checkout", "--orphan", "gh-pages"], cwd=repo_path, capture_output=True, check=True)
            subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=repo_path, capture_output=True, check=True)

        # Copy all files from site_dir to the repo
        # Keep existing episodes (don't delete old ones)
        episodes_dir = repo_path / "episodes"
        existing_episodes = set()
        if episodes_dir.exists():
            existing_episodes = {f.name for f in episodes_dir.iterdir()}

        # Copy new/updated files
        for src_file in site_dir.rglob("*"):
            if src_file.is_file():
                rel = src_file.relative_to(site_dir)
                dest = repo_path / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dest)

        # Add .nojekyll to prevent Jekyll processing
        (repo_path / ".nojekyll").touch()

        # Commit and push
        subprocess.run(["git", "add", "-A"], cwd=repo_path, capture_output=True, check=True)

        # Check if there are changes to commit
        status = subprocess.run(["git", "status", "--porcelain"], cwd=repo_path, capture_output=True, text=True)
        if not status.stdout.strip():
            log.info("gh_pages_no_changes")
            return base_url

        subprocess.run(
            ["git", "commit", "-m", "Update podcast feed and episodes"],
            cwd=repo_path, capture_output=True, check=True,
        )

        # Push with retry
        for attempt in range(4):
            result = subprocess.run(
                ["git", "push", "origin", "gh-pages", "--force"],
                cwd=repo_path, capture_output=True, text=True,
            )
            if result.returncode == 0:
                break
            if attempt < 3:
                import time
                time.sleep(2 ** (attempt + 1))
                log.warning("gh_pages_push_retry", attempt=attempt + 1)
        else:
            raise RuntimeError(f"Failed to push to gh-pages: {result.stderr}")

    log.info("gh_pages_published", url=base_url)
    return base_url


def _get_remote_url() -> str:
    """Get the git remote origin URL."""
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def upload_episode(
    audio_path: Path,
    publisher_config: PublisherConfig,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
) -> str:
    """Return the public URL for an episode. Actual upload happens in publish step."""
    return f"{publisher_config.base_url}/episodes/{audio_path.name}"


def upload_feed(
    feed_path: Path,
    publisher_config: PublisherConfig,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
) -> str:
    """Return the public URL for the feed. Actual upload happens in publish step."""
    return f"{publisher_config.base_url}/feed.xml"
