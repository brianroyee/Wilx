# nano

## Description

Tiny nano-like text editor for Wilx.

Behavior:
- If the environment has `curses`, launches a simple full-screen editor with:
  - Arrow key navigation, Insert/Delete, Enter
  - Ctrl-S to save, Ctrl-Q to quit (unsaved changes prompt)
- If `curses` isn't available (common on Windows without packages), falls back to
  a simple line-based editor that lets you view, append, delete lines, and save.

This is intentionally minimal — it's not a full nano clone, but provides an
easy-to-use in-terminal editing experience without external dependencies.

## Help

```
usage: nano [-h] [--line-numbers] [--history-file HISTORY_FILE] [file]

positional arguments:
  file                  file to edit

options:
  -h, --help            show this help message and exit
  --line-numbers        show line numbers (gutter)
  --history-file HISTORY_FILE
                        path to history file to record saves (default ~/.wilx_history)
```
