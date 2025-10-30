# Wilx Commands

This index lists available commands grouped by category.

## Filesystem

- [cat](commands/cat.md) — Simple `cat` implementation.
- [cd](commands/cd.md) — Change directory (cd).
- [cp](commands/cp.md) — Minimal cp command supporting -r for directories.
- [ls](commands/ls.md) — `ls` command for Wilx (MVP).
- [mkdir](commands/mkdir.md) — Minimal mkdir implementation supporting -p.
- [mv](commands/mv.md) — Minimal mv (move/rename) command.
- [pwd](commands/pwd.md) — Print working directory (pwd).
- [rm](commands/rm.md) — Minimal rm command: supports -r and -f.
- [touch](commands/touch.md) — Simple touch implementation: create file if missing or update mtime.

## Process

- [htop](commands/htop.md) — Formatted lightweight `htop`-like viewer for Wilx.
- [kill](commands/kill.md) — Kill processes by PID (Linux-like `kill`).
- [killswitch](commands/killswitch.md) — Attempt basic recovery actions after accidental kills.

## Editor

- [edit](commands/edit.md) — `edit` alias that opens files with the nano editor.
- [nano](commands/nano.md) — Tiny nano-like text editor for Wilx.

## Core

- [man](commands/man.md) — Simple man-like viewer for Wilx command modules.
- [shell](commands/shell.md) — *(no module docstring available)*

## Misc

- [echo](commands/echo.md) — Echo command: print arguments to stdout.

You can regenerate the per-command docs with:

```powershell
python scripts\generate_docs.py
```
