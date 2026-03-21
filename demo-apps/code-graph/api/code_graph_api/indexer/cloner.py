import hashlib
import logging
import shutil
from pathlib import Path

import git

logger = logging.getLogger(__name__)

# Repos are cloned under CLONE_ROOT/<repo_hash>/
CLONE_ROOT = Path(".repos")


def repo_id(repo_url: str) -> str:
    """Stable short identifier for a repo URL."""
    return hashlib.sha1(repo_url.encode()).hexdigest()[:12]


def repo_path(repo_url: str) -> Path:
    return CLONE_ROOT / repo_id(repo_url)


def is_cloned(repo_url: str) -> bool:
    return repo_path(repo_url).exists()


def clone_or_pull(repo_url: str) -> Path:
    """
    Clones the repo if not present, pulls latest if already cloned.
    Returns the local path.
    """
    path = repo_path(repo_url)

    if path.exists():
        logger.info("Repo already cloned at %s, pulling latest", path)
        repo = git.Repo(path)
        repo.remotes.origin.pull()
    else:
        logger.info("Cloning %s → %s", repo_url, path)
        CLONE_ROOT.mkdir(parents=True, exist_ok=True)
        git.Repo.clone_from(repo_url, path, depth=1)  # shallow clone

    return path


def delete_clone(repo_url: str) -> None:
    path = repo_path(repo_url)
    if path.exists():
        shutil.rmtree(path)
        logger.info("Deleted clone at %s", path)