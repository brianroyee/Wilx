# Wilx — GNU-like tools for Windows (MVP)

> Wilx provides a small, modular command-line toolkit that brings common GNU-style commands to Windows with familiar flags and behavior. It's implemented in pure Python (standard library), small, fast, and extensible via `core/<command>.py` modules.

This README covers installation, running, commands, safety and dev notes.

## Quick install

1. Create and activate a Python virtual environment (recommended):

    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    ```

2. (Optional) Install the Windows curses package so the `nano` editor works in full-screen:

    ```powershell
    pip install -r requirements.txt
    # or only the curses shim on Windows
    pip install windows-curses
    ```

3. Run the shell directly:

    ```powershell
    python shell.py
    ```

   Or install the shim (optional) to run `wilx` from any CMD/PowerShell session — see `install_shim.ps1`.

## What you get

- `shell.py` — a small REPL that dispatches to command modules in `core/`.
- `core/<command>.py` modules — each exposes `execute(args: list[str]) -> int` and uses only the standard library.
- Implemented commands (examples): `ls`, `cat`, `mkdir`, `rm`, `mv`, `cp`, `touch`, `pwd`, `cd`, `echo`, `htop`, `kill`, `killswitch`, `nano`, `edit`, `man`.

The project intentionally keeps external dependencies to a minimum for fast startup.

## Usage examples

- Start the Wilx shell:

   ```powershell
   python shell.py
   # then at the prompt:
   ls -l
   cat README.md
   htop --all
   edit notes.txt   # opens with nano
   kill --dry-run 1234
   killswitch --list
   ```

## The `core` command contract

Commands live in `core/` as modules named after the command (`core/ls.py` -> `ls`). Each module must expose:

```python
def execute(args: List[str]) -> int:
      """Run command with argv-style args.
      Return exit code (0 success, >0 failure).
      """
```

The shell dynamically imports `core.<name>` and calls `execute()`.

## Notable commands and safety

- `htop` — fast snapshot viewer. On Windows it uses Win32 APIs (ctypes) for process enumeration and memory values; on Unix it falls back to `ps/free`.
   - Use `htop -n <num>` or `htop --all` to list many processes.

- `kill` — Linux-like kill with improvements for Windows. Key safety features:
   - Protected processes (explorer.exe, lsass.exe, winlogon.exe, csrss.exe, etc.) are refused unless `--force` is passed and confirmed.
   - `--dry-run` shows what would be done without performing kills.
   - Default behavior attempts a graceful close (WM_CLOSE) on Windows before termination.
   - Successful kills are logged to `~/.wilx_kill_log` for recovery.

- `killswitch` — reads the kill log and attempts basic recoveries (e.g., restart `explorer.exe`), best-effort only.

- `nano` / `edit` — small built-in editor. Installs `windows-curses` for full-screen mode on Windows. Fallback to a line editor exists when curses is unavailable.

## Performance and design notes

- Minimal startup latency is a design goal. The code prefers lazy imports and fast system calls. Where possible, Win32 APIs are used via `ctypes` to avoid external process parsing.
- Safety-first for destructive operations: `--dry-run`, confirmations, protected lists, and logs.

## Developer guide

- Adding a command: create `core/<name>.py` and implement `execute(args: list[str]) -> int`.
- Tests: there are no formal tests in this repo yet — add quick unit tests under `tests/` using `pytest` if desired.
- Style: keep external deps minimal. If you need richer UI, prefer optional dependencies documented in `requirements.txt`.

## Troubleshooting

- Backspace doesn't work in curses mode on Windows: install `windows-curses` and try a modern terminal (Windows Terminal). The editor also has a fallback line-editor.
- Kill fails due to permissions: many process inspection/termination operations require admin rights. Rerun your shell as Administrator when necessary.

## Security and risk

This tool exposes operations that can disrupt your system (killing processes, terminating services). Use `--dry-run` and avoid running `kill -f` on system-critical PIDs. `killswitch` can help recover `explorer.exe`, but it can't always undo system-level damage.

## Contribution

Contributions welcome. Create issues or PRs that add commands, tests, or documentation updates. Keep changes small and add tests when behavior changes.

## License
GNU GENERAL PUBLIC LICENSE V3

