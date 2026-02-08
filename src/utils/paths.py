"""Path utilities for locating Claude Code data files."""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_CLAUDE_DIR = Path.home() / ".claude"
HISTORY_FILE = "history.jsonl"


def get_claude_dir() -> Path:
    """Return Claude data dir. Honors CLAUDE_DATA_DIR env var, defaults to ~/.claude/."""
    env = os.environ.get("CLAUDE_DATA_DIR")
    if env:
        return Path(env)
    return DEFAULT_CLAUDE_DIR


def get_history_path() -> Path:
    """Return full path to history.jsonl."""
    return get_claude_dir() / HISTORY_FILE


def project_path_to_slug(project_path: str) -> str:
    """Convert '/Users/foo/bar' to '-Users-foo-bar'."""
    return project_path.replace("/", "-")


def get_session_jsonl_path(project_path: str, session_id: str) -> Path:
    """Return path: <claude_dir>/projects/<slug>/<session_id>.jsonl"""
    slug = project_path_to_slug(project_path)
    return get_claude_dir() / "projects" / slug / f"{session_id}.jsonl"
