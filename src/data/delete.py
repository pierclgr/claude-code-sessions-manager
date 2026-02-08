"""File operations for deleting Claude Code sessions.

Handles atomic rewrite of history.jsonl, deletion of per-session files
and directories, and searching for session artifacts under ~/.claude/.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import List, Optional, Set

from src.utils.paths import get_claude_dir, get_history_path, get_session_jsonl_path, project_path_to_slug


def find_session_artifacts(session_id: str, claude_dir: Optional[Path] = None) -> List[Path]:
    """Find all files and directories under the Claude data dir whose name contains the session ID.

    Excludes history.jsonl itself (that is handled separately by the rewrite).

    Args:
        session_id: The session UUID to search for.
        claude_dir: Optional override for the Claude data directory.

    Returns:
        List of Path objects matching the session ID, sorted for consistent ordering.
    """
    root = claude_dir if claude_dir is not None else get_claude_dir()
    matches: List[Path] = []

    for dirpath, dirnames, filenames in os.walk(root):
        for name in filenames:
            if session_id in name and name != "history.jsonl":
                matches.append(Path(dirpath) / name)
        for name in dirnames:
            if session_id in name:
                matches.append(Path(dirpath) / name)

    matches.sort()
    return matches


def delete_sessions_from_history(session_ids: Set[str], claude_dir: Optional[Path] = None) -> int:
    """Remove all history.jsonl lines whose sessionId is in the given set.

    Uses an atomic temp-file-then-rename approach: writes filtered lines to
    a .tmp file in the same directory, then renames it over the original.

    Args:
        session_ids: Set of session UUIDs to remove.
        claude_dir: Optional override for the Claude data directory.

    Returns:
        Number of lines removed.

    Raises:
        SystemExit: If history.jsonl cannot be read or the write fails.
    """
    history_path = get_history_path() if claude_dir is None else claude_dir / "history.jsonl"
    tmp_path = history_path.with_suffix(".jsonl.tmp")

    try:
        file = open(history_path, encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: {history_path} not found. Is Claude Code installed?", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"Error: Cannot read {history_path}. Check permissions.", file=sys.stderr)
        sys.exit(1)

    kept_lines: List[str] = []
    removed_count = 0

    with file:
        for line in file:
            stripped = line.strip()
            if not stripped:
                kept_lines.append(line)
                continue
            try:
                entry = json.loads(stripped)
            except json.JSONDecodeError:
                kept_lines.append(line)
                continue

            if entry.get("sessionId") in session_ids:
                removed_count += 1
            else:
                kept_lines.append(line)

    try:
        with open(tmp_path, "w", encoding="utf-8") as tmp_file:
            tmp_file.writelines(kept_lines)
        tmp_path.rename(history_path)
    except OSError as exc:
        # Clean up temp file on failure; original remains untouched
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        print(f"Error: Failed to write {history_path}: {exc}", file=sys.stderr)
        sys.exit(1)

    return removed_count


def delete_session_files(project_path: str, session_id: str, claude_dir: Optional[Path] = None) -> List[Path]:
    """Delete all files and directories associated with a session.

    Removes:
    1. The per-session .jsonl file under projects/<slug>/
    2. The per-session directory under projects/<slug>/
    3. Any other files/dirs under ~/.claude/ whose name contains the session ID
    4. The project directory itself if no .jsonl files remain

    Only deletes under the Claude data directory — never traverses outside it.

    Args:
        project_path: The session's project path (e.g. "/Users/foo/bar").
        session_id: The session UUID.
        claude_dir: Optional override for the Claude data directory.

    Returns:
        List of paths that were successfully deleted.
    """
    root = claude_dir if claude_dir is not None else get_claude_dir()
    deleted: List[Path] = []

    # 1. Delete the primary .jsonl file
    jsonl_path = get_session_jsonl_path(project_path, session_id)
    if claude_dir is not None:
        # Rebuild path under the overridden claude_dir
        slug = project_path_to_slug(project_path)
        jsonl_path = root / "projects" / slug / f"{session_id}.jsonl"

    if jsonl_path.exists():
        try:
            jsonl_path.unlink()
            deleted.append(jsonl_path)
        except OSError as exc:
            print(f"Warning: Could not delete {jsonl_path}: {exc}", file=sys.stderr)

    # 2. Delete the per-session directory (same path without .jsonl extension)
    session_dir = jsonl_path.with_suffix("")
    if session_dir.is_dir():
        try:
            shutil.rmtree(session_dir)
            deleted.append(session_dir)
        except OSError as exc:
            print(f"Warning: Could not delete {session_dir}: {exc}", file=sys.stderr)

    # 3. Search for any other artifacts matching the session ID
    artifacts = find_session_artifacts(session_id, claude_dir=root)
    for artifact in artifacts:
        if artifact in deleted:
            continue

        # Safety: only delete under the Claude data directory
        try:
            artifact.resolve().relative_to(root.resolve())
        except ValueError:
            continue

        try:
            if artifact.is_dir():
                shutil.rmtree(artifact)
            else:
                artifact.unlink()
            deleted.append(artifact)
        except OSError as exc:
            print(f"Warning: Could not delete {artifact}: {exc}", file=sys.stderr)

    # 4. Remove the project directory if it has no remaining .jsonl files
    slug = project_path_to_slug(project_path)
    project_dir = root / "projects" / slug
    if project_dir.is_dir():
        remaining_jsonl = list(project_dir.glob("*.jsonl"))
        if not remaining_jsonl:
            try:
                shutil.rmtree(project_dir)
                deleted.append(project_dir)
            except OSError as exc:
                print(f"Warning: Could not delete {project_dir}: {exc}", file=sys.stderr)

    return deleted
