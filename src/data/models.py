"""Data models for Claude Code sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class Session:
    """Represents a single Claude Code session aggregated from history entries."""

    session_id: str
    project_path: str
    created_at: datetime
    last_active_at: datetime
    latest_command: str
    commands: List[str]
    todos: List[str] = field(default_factory=list)
