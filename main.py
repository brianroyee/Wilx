"""Top-level CLI entrypoint for the Wilx project.

Provides a small centralized dispatcher that supports global flags
and forwards subcommands to `core.<command>.execute(args)`.

If no command is given the interactive shell is started (prefer the
project-level `shell.repl` if present, otherwise fall back to
`core.shell.start_shell`).
"""
from __future__ import annotations

import argparse
import importlib
import sys
from typing import List


def _list_commands() -> List[str]:
    # prefer top-level `shell.py`'s discovery if available
    try:
        shell = importlib.import_module('shell')
        if hasattr(shell, 'list_core_commands'):
            return shell.list_core_commands()
    except Exception:
        pass
    try:
        core_shell = importlib.import_module('core.shell')
        if hasattr(core_shell, 'list_core_commands'):
            return core_shell.list_core_commands()
    except Exception:
        pass
    return []


def _run_subcommand(cmd: str, args: List[str]) -> int:
    try:
        module = importlib.import_module(f'core.{cmd}')
    except ModuleNotFoundError:
        print(f"wilx: {cmd}: command not found", file=sys.stderr)
        return 127
    except Exception as e:
        print(f"wilx: error loading command '{cmd}': {e}", file=sys.stderr)
        return 1

    if not hasattr(module, 'execute'):
        print(f"wilx: {cmd}: no execute(args) function in module", file=sys.stderr)
        return 1

    try:
        rc = module.execute(args)
        return int(rc) if isinstance(rc, int) else 0
    except SystemExit as se:
        return int(se.code) if isinstance(se.code, int) else 0
    except Exception as e:
        print(f"wilx: {cmd}: runtime error: {e}", file=sys.stderr)
        return 1


def main(argv: List[str] | None = None) -> int:
    argv = list(argv or sys.argv[1:])
    parser = argparse.ArgumentParser(prog='wilx', add_help=False)
    parser.add_argument('--version', action='store_true', help='print version')
    parser.add_argument('--list-commands', action='store_true', help='list available commands in core/')
    parser.add_argument('--config', help='path to config file (optional)')
    parser.add_argument('cmd', nargs='?', help='command to run (falls back to interactive shell)')
    parser.add_argument('args', nargs=argparse.REMAINDER, help='arguments for the command')

    ns = parser.parse_args(argv)

    if ns.version:
        # simple version source: package __version__ if present or fallback
        try:
            pkg = importlib.import_module('wilx')
            print(getattr(pkg, '__version__', '0.0.0'))
        except Exception:
            print('0.0.0')
        return 0

    if ns.list_commands:
        for c in _list_commands():
            print(f"  {c}")
        return 0

    if ns.cmd:
        return _run_subcommand(ns.cmd, ns.args)

    # No command -> start interactive shell
    # Prefer top-level `shell.repl`, else try core.shell.start_shell
    try:
        shell = importlib.import_module('shell')
        if hasattr(shell, 'repl'):
            return shell.repl()
    except Exception:
        pass

    try:
        core_shell = importlib.import_module('core.shell')
        if hasattr(core_shell, 'start_shell'):
            core_shell.start_shell()
            return 0
    except Exception:
        pass

    print('wilx: no shell available', file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
