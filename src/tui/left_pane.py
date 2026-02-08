"""Left pane renderer for the TUI.

Draws a flat, scrollable session list occupying the left ~60% of the
terminal. Each row shows project directory, session ID, dates, and
latest command. The highlighted row uses the mode accent color.
In DELETE mode, rows are prefixed with [x] / [ ] selection markers.
"""

from __future__ import annotations

import curses
from typing import List, Set

from src.data.models import Session
from src.utils.formatting import format_datetime, truncate


def draw(stdscr: curses.window, sessions: List[Session], cursor: int,
         scroll_offset: int, mode: str, selected: Set[str],
         accent_pair: int, normal_pair: int, marker_pair: int,
         x: int, y: int, width: int, height: int) -> None:
    """Render the session list in the left pane area.

    Args:
        stdscr: The curses window to draw on.
        sessions: Full list of sessions.
        cursor: Index of the currently highlighted session.
        scroll_offset: First visible row index.
        mode: Current mode ("SELECT" or "DELETE").
        selected: Set of session IDs selected for deletion.
        accent_pair: Color pair for the highlighted cursor row.
        normal_pair: Color pair for normal rows.
        marker_pair: Color pair for the [x] marker in DELETE mode.
        x: Starting column of the pane.
        y: Starting row of the pane.
        width: Width of the pane in columns.
        height: Height of the pane in rows.
    """
    is_delete = mode == "DELETE"
    # Reserve space for selection marker in delete mode
    marker_width = 4 if is_delete else 0
    content_width = width - marker_width

    # Header takes 1 row; data rows fill the rest
    data_height = height - 1
    headers = ["Project", "ID", "Modified", "Created", "Last message"]

    # Pre-compute column values for all visible rows
    visible: List[tuple] = []  # (session_idx, project, sid, modified, created, cmd)
    for row_idx in range(data_height):
        session_idx = scroll_offset + row_idx
        if session_idx >= len(sessions):
            break
        s = sessions[session_idx]
        project = s.project_path.rsplit("/", 1)[-1] if "/" in s.project_path else s.project_path
        visible.append((
            session_idx,
            project,
            s.session_id[:8],
            format_datetime(s.last_active_at),
            format_datetime(s.created_at),
            s.latest_command.strip(),
        ))

    # Compute column widths from visible data and headers
    # Last column (command) gets whatever space remains
    gap = 2  # spaces between columns
    col_widths = [len(headers[i]) for i in range(4)]  # project, sid, modified, created
    for _, project, sid, modified, created, _ in visible:
        col_widths[0] = max(col_widths[0], len(project))
        col_widths[1] = max(col_widths[1], len(sid))
        col_widths[2] = max(col_widths[2], len(modified))
        col_widths[3] = max(col_widths[3], len(created))

    fixed_used = sum(col_widths) + gap * 4  # 4 gaps (between 5 columns)
    cmd_max = max(10, content_width - fixed_used)

    # Draw header row
    header_attr = curses.color_pair(accent_pair) | curses.A_BOLD
    header_line = (f"{headers[0]:<{col_widths[0]}}"
                   f"  {headers[1]:<{col_widths[1]}}"
                   f"  {headers[2]:<{col_widths[2]}}"
                   f"  {headers[3]:<{col_widths[3]}}"
                   f"  {headers[4]}")
    header_line = header_line[:content_width].ljust(content_width)
    try:
        if is_delete:
            stdscr.addstr(y, x, " " * marker_width, header_attr)
            stdscr.addstr(y, x + marker_width, header_line, header_attr)
        else:
            stdscr.addstr(y, x, header_line, header_attr)
    except curses.error:
        pass

    # Draw data rows
    for row_idx in range(data_height):
        screen_y = y + 1 + row_idx

        if row_idx >= len(visible):
            # Clear remaining rows
            try:
                stdscr.addstr(screen_y, x, " " * width, curses.color_pair(normal_pair))
            except curses.error:
                pass
            continue

        session_idx, project, sid, modified, created, cmd = visible[row_idx]
        is_cursor = session_idx == cursor
        attr = curses.color_pair(accent_pair) if is_cursor else curses.color_pair(normal_pair)

        # Truncate project and command to fit
        project_display = truncate(project, col_widths[0])
        cmd_display = truncate(cmd, cmd_max)

        # Build line with evenly padded columns
        line = (f"{project_display:<{col_widths[0]}}"
                f"  {sid:<{col_widths[1]}}"
                f"  {modified:<{col_widths[2]}}"
                f"  {created:<{col_widths[3]}}"
                f"  {cmd_display}")

        # Pad or truncate to content_width
        line = line[:content_width].ljust(content_width)

        try:
            if is_delete:
                # Draw selection marker
                is_selected = sessions[session_idx].session_id in selected
                marker = "[x] " if is_selected else "[ ] "
                marker_attr = attr
                stdscr.addstr(screen_y, x, marker, marker_attr)
                stdscr.addstr(screen_y, x + marker_width, line, attr)
            else:
                stdscr.addstr(screen_y, x, line, attr)
        except curses.error:
            pass
