#!/usr/bin/env python3

from __future__ import annotations

import os
import sys
import shlex
import importlib
from typing import List


def list_core_commands() -> List[str]:
    """Return a sorted list of available command module names in `core/`.

    This scans the `core` package directory for .py files (ignoring
    __init__.py and private files starting with underscore).
    """
    core_dir = os.path.join(os.path.dirname(__file__), 'core')
    cmds = []
    try:
        for fname in os.listdir(core_dir):
            if not fname.endswith('.py'):
                continue
            if fname == '__init__.py' or fname.startswith('_'):
                continue
            cmds.append(os.path.splitext(fname)[0])
    except Exception:
        # If the package isn't present or readable, return empty list.
        return []
    return sorted(cmds)


def parse_command(s: str) -> List[str]:
    """Parse a command line into tokens robustly across platforms.

    On Windows backslashes are common in paths and POSIX-style shlex
    parsing may raise ValueError when it encounters an incomplete escape.
    We try a couple of modes and fall back to a naive split.
    """
    orders = [True]
    if os.name == 'nt':
        orders = [False, True]
    for posix_mode in orders:
        try:
            toks = shlex.split(s, posix=posix_mode)
            # Normalize tokens: if a token is quoted when parsed in non-posix
            # mode it may retain quotes, so strip matching surrounding quotes.
            norm = []
            for t in toks:
                if len(t) >= 2 and ((t[0] == t[-1]) and t[0] in ('"', "'")):
                    norm.append(t[1:-1])
                else:
                    norm.append(t)
            return norm
        except ValueError:
            continue
    return s.split()


def run_command(cmd: str, args: List[str]) -> int:
    """Dynamically import `core.<cmd>` and execute it with args.

    Returns an integer exit code (0 success, non-zero error).
    """
    # cache imported command modules to avoid reloading on repeated calls
    if not hasattr(run_command, '_module_cache'):
        run_command._module_cache = {}
    cache = run_command._module_cache

    try:
        module = cache.get(cmd)
        if module is None:
            module = importlib.import_module(f'core.{cmd}')
            cache[cmd] = module
    except ModuleNotFoundError:
        print(f"wilx: {cmd}: command not found")
        return 127
    except Exception as exc:
        print(f"wilx: error loading command '{cmd}': {exc}")
        return 1

    if not hasattr(module, 'execute'):
        print(f"wilx: {cmd}: no execute(args) function in module")
        return 1

    try:
        result = module.execute(args)
        # command may return int or None — normalize to int
        if isinstance(result, int):
            return result
        return 0
    except SystemExit as se:
        # allow modules to call sys.exit(n) — map to exit code
        code = se.code
        return int(code) if isinstance(code, int) else 0
    except Exception as exc:
        print(f"wilx: {cmd}: runtime error: {exc}")
        return 1


def repl() -> int:
    """Main read-eval-print loop for the mini-shell.

    Keeps the project root on sys.path so `import core.foo` works when the
    shell is started from the project directory.
    """
    project_root = os.path.dirname(__file__)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    cwd = os.getcwd()

    while True:
        try:
            # show a simple prompt with the current working directory
            line = input(f"{cwd} $ ").strip()
            if not line:
                continue

            # Parse command line robustly across platforms
            parts = parse_command(line)
            if not parts:
                continue
            cmd, *args = parts

            # built-ins
            if cmd in ('exit', 'quit'):
                return 0

            if cmd == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                continue

            if cmd in ('help', '-h', '--help'):
                print("Wilx - minimal GNU-like shell (MVP)")
                print()
                print("Built-ins:")
                print("  exit, quit, clear, help")
                print()
                print("Available command modules in core/:")
                for c in list_core_commands():
                    print(f"  {c}")
                continue

            # dispatch to command modules
            rc = run_command(cmd, args)
            # update cwd in prompt in case a command changed it (future)
            cwd = os.getcwd()
            # we don't exit the shell on non-zero rc; commands control that

        except KeyboardInterrupt:
            # catch Ctrl-C and continue
            print()
            continue
        except EOFError:
            # Ctrl-Z/Ctrl-D / EOF: exit the shell
            print()
            break

    return 0


if __name__ == '__main__':
    sys.exit(repl())
