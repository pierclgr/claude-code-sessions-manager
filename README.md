# Claude Code Sessions Manager

A terminal tool for browsing, resuming, and deleting [Claude Code](https://docs.anthropic.com/en/docs/claude-code) sessions across all your projects. Provides both an interactive full-screen TUI and non-interactive CLI subcommands.

Built with **Python 3.8+** using only the standard library (zero third-party dependencies). Works on **macOS** and **Linux**.

## Features

- **Interactive TUI** -- Full-screen curses interface with two-pane layout: session list on the left, session details on the right
- **SELECT mode** -- Browse all sessions and resume any of them with a single keystroke
- **DELETE mode** -- Batch-select sessions and delete them (history entry + all related files)
- **CLI subcommands** -- Non-interactive `ls`, `launch`, and `delete` commands for scripting and quick access
- **Cross-project view** -- Aggregates sessions from every project into a single list, sorted by most recent activity
- **Lazy detail loading** -- Per-session data (todos, commands) is loaded only when highlighted, keeping startup fast
- **Graceful degradation** -- Hides the right pane on narrow terminals, hides the banner on short terminals, falls back to 256-color when true-color is unavailable

## Prerequisites

- **Bash** 4.0+
- **Python** 3.8+
- **Claude Code** already installed
- A terminal with ANSI color support (24-bit true-color preferred; 256-color fallback available)

## Installation

```bash
# Clone the repository
git clone https://github.com/pierclgr/claude-code-session-manager.git
cd claude-code-sessions-manager

# Make the entry point executable
chmod +x claude-code-sessions
```

Optionally, add the directory to your `PATH` so you can run `claude-code-sessions` from anywhere:

```bash
# Add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
export PATH="/path/to/claude-code-sessions-manager:$PATH"
```

## Usage

### Interactive TUI

```bash
claude-code-sessions
```

Launches the full-screen session browser in SELECT mode.

#### TUI Layout

```
┌──────────────────────────────────┬──────────────────────┐
│  ASCII Banner                    │                      │
├──────────────────────────────────┤                      │
│                                  │  Session details     │
│  Session list (60%)              │  (40%)               │
│                                  │                      │
│  - Project name                  │  - Full project path │
│  - Session ID                    │  - Full session ID   │
│  - Modified / Created dates      │  - Recent commands   │
│  - Latest command                │  - Todos             │
│                                  │                      │
├──────────────────────────────────┴──────────────────────┤
│  Status bar: mode + keybindings                         │
└─────────────────────────────────────────────────────────┘
```

#### SELECT mode (default)

| Key              | Action                        |
| ---------------- | ----------------------------- |
| `Up` / `k`       | Move cursor up                |
| `Down` / `j`     | Move cursor down              |
| `Enter`          | Resume the highlighted session |
| `D`              | Switch to DELETE mode          |
| `Q`              | Quit                          |

#### DELETE mode

| Key              | Action                               |
| ---------------- | ------------------------------------ |
| `Up` / `k`       | Move cursor up                       |
| `Down` / `j`     | Move cursor down                     |
| `Tab`            | Toggle selection on current session  |
| `Enter`          | Delete selected sessions (with confirmation) |
| `S`              | Switch back to SELECT mode           |
| `Q`              | Quit                                 |

### CLI Subcommands

```bash
# List all sessions (tab-separated, suitable for piping)
claude-code-sessions ls

# Resume a session by ID (supports prefix matching)
claude-code-sessions launch <SESSION_ID>

# Delete a session by ID (with confirmation prompt)
claude-code-sessions delete <SESSION_ID>

# Show help
claude-code-sessions --help
```

#### `ls` output example

```
Session ID  Project                              Latest command    Created           Last Modified
221e3acb    /Users/you/my-project                /exit             2026-02-07 12:03  2026-02-07 12:06
f9569def    /Users/you/other-project             Fix the bug in…   2026-02-06 09:15  2026-02-06 10:30
```

## Project Structure

```
claude-code-sessions-manager/
├── claude-code-sessions           # Bash entry point (routes subcommands to Python)
├── src/
│   ├── commands/                  # Non-interactive subcommand handlers
│   │   ├── ls.py                  #   List sessions
│   │   ├── launch.py              #   Resume a session
│   │   └── delete.py              #   Delete a session
│   ├── data/                      # Data access layer (all ~/.claude/ I/O)
│   │   ├── models.py              #   Session dataclass
│   │   ├── history.py             #   Parse history.jsonl
│   │   ├── session.py             #   Parse per-session JSONL for details
│   │   └── delete.py              #   Atomic deletion operations
│   ├── tui/                       # Full-screen curses TUI
│   │   ├── app.py                 #   Main loop, state management, colors
│   │   ├── left_pane.py           #   Scrollable session list renderer
│   │   ├── right_pane.py          #   Session detail renderer
│   │   └── status_bar.py          #   Mode indicator + keybindings bar
│   └── utils/                     # Shared utilities
│       ├── paths.py               #   Claude directory / path resolution
│       └── formatting.py          #   Date/time formatting, text truncation
└── README.md                      # This file
```

## Environment Variables

| Variable          | Description                                      | Default        |
| ----------------- | ------------------------------------------------ | -------------- |
| `CLAUDE_DATA_DIR` | Override the Claude Code data directory           | `~/.claude/`   |

## How It Works

1. **Session discovery** -- Reads `~/.claude/history.jsonl`, groups entries by `sessionId`, and computes timestamps, latest commands, and project paths.
2. **Detail enrichment** -- When a session is highlighted in the TUI, its per-session JSONL file (`~/.claude/projects/<slug>/<id>.jsonl`) is parsed to extract todos and additional command history.
3. **Session resumption** -- Changes to the session's project directory and calls `claude --resume <SESSION_ID>` via `os.execvp`.
4. **Session deletion** -- Atomically rewrites `history.jsonl` (write to temp file, then rename) and recursively removes all files/directories under `~/.claude/` matching the session ID.
