"""Handler for the 'launch' subcommand.

Looks up a session by ID, changes to its project directory, and exec's
claude --resume to replace the current process.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from src.data import load_sessions


def run(session_id: str) -> None:
    """Resume a Claude Code session by its ID.

    Args:
        session_id: Full or partial session UUID to look up.
    """
    sessions = load_sessions()

    # Find matching session (exact or prefix match)
    match = None
    for session in sessions:
        if session.session_id == session_id or session.session_id.startswith(session_id):
            match = session
            break

    if match is None:
        print(f"Error: Session '{session_id}' not found.", file=sys.stderr)
        sys.exit(1)

    project_dir = Path(match.project_path)
    if not project_dir.is_dir():
        print(f"Error: Project directory '{match.project_path}' no longer exists.", file=sys.stderr)
        sys.exit(1)

    os.chdir(project_dir)
    os.execvp("claude", ["claude", "--resume", match.session_id])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: 'launch' requires a session ID argument.", file=sys.stderr)
        sys.exit(1)
    run(sys.argv[1])
