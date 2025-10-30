# Wilx Commands Reference

This document summarizes the commands implemented in `core/` and shows basic usage examples and notes.

## Command list (brief)

- ls — list directory contents
  - Supports `-a` (all), `-l` (long format), aligned columns.

- cat — print file(s) to stdout
  - Supports `-n` (number lines).

- mkdir — create directories
  - Supports `-p` / `--parents`.

- rm — remove files and directories
  - Supports `-r`, `-f`, and `--dry-run` for safety.

- mv — move/rename files
  - Supports `--dry-run`.

- cp — copy files and directories
  - Supports `-r` and `--dry-run`.

- touch — create/update mtime of files

- pwd — print working directory

- cd — change current working directory (affects the shell process only when run inside `shell.py`)

- echo — print arguments

- man — display help/doc for a command (reads module docstring and `--help` output)

- htop — fast process snapshot viewer
  - On Windows uses Win32 API via `ctypes` (fast, accurate); on Unix uses `ps`/`free`.
  - Columns: PID, NAME, TYPE (service/user), MEM(MB), MEM%.
  - Flags: `--watch N` to refresh, `-n/--top` to limit number, `--all` to show all.

- kill — Linux-like kill with safe defaults
  - `--dry-run`, `--force` / `-9`, `-y` to confirm, and protected process list.
  - On Windows it attempts graceful close (WM_CLOSE) before hard termination.

- killswitch — read kill log and attempt recoveries
  - `--list` shows recent kills; `--restart-explorer` attempts to relaunch `explorer.exe` if it was killed.

- nano / edit — tiny editor. `edit` is an alias that opens `nano`.
  - Curses-based full-screen editor when `curses` available; fallback line editor otherwise.
  - Keys: Ctrl-S save, Ctrl-O save-as, Ctrl-F search, Ctrl-U undo, Ctrl-Q quit.


## Examples

- List all files, long format:
  ```powershell
  ls -al
  ```

- Show a live snapshot every 2s:
  ```powershell
  htop --watch 2
  ```

- Dry-run killing a process:
  ```powershell
  kill --dry-run 1234
  ```

- Edit a file with the editor:
  ```powershell
  edit notes.txt
  ```


## Developer notes

- Each `core/<cmd>.py` must expose `execute(args: List[str]) -> int`.
- Prefer lazy imports for heavy modules and avoid importing large modules at top-level.

## Safety

- `kill` is intentionally defensive. The kill log file is at `~/.wilx_kill_log` and `killswitch` can read it to attempt recovery actions.
