"""Simple man-like viewer for Wilx command modules.

Usage:
  man <command>
  man        # lists available commands

Behavior:
- If a command name is given, `man` will display the module docstring
  (wrapped to terminal width) and then the command's help output (by
  invoking the module with ['--help'] and capturing its printed help).
- Falls back to a short message if the module cannot be loaded.

This keeps output plain-text and avoids external dependencies.
"""

from __future__ import annotations

import importlib
import shutil
import sys
import textwrap
from typing import List
import io
import contextlib


def _wrap(text: str) -> str:
    width = shutil.get_terminal_size((80, 20)).columns
    return textwrap.fill(text.strip(), width=width)


def _capture_help(module) -> str:
    """Call module.execute(['--help']) and capture stdout/stderr if possible."""
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            # Some modules expect '-h' or '--help' to be present; many use add_help=False
            try:
                module.execute(['--help'])
            except SystemExit:
                # argparse may call sys.exit after printing help; that's fine
                pass
    except Exception as e:
        return f"(error capturing help: {e})"
    return buf.getvalue()


def execute(args: List[str]) -> int:
    if not args:
        # list available commands
        try:
            import os
            core_dir = os.path.join(os.path.dirname(__file__))
            files = [f[:-3] for f in os.listdir(core_dir) if f.endswith('.py') and not f.startswith('_')]
            files.sort()
            print("Available commands in core/:")
            for f in files:
                print(f"  {f}")
            return 0
        except Exception as e:
            print(f"man: error listing commands: {e}", file=sys.stderr)
            return 1

    rc = 0
    for name in args:
        try:
            module = importlib.import_module(f'core.{name}')
        except ModuleNotFoundError:
            print(f"No manual entry for {name}")
            rc = 2
            continue
        except Exception as e:
            print(f"man: error loading {name}: {e}")
            rc = 1
            continue

        header = f"Manual for {name}"
        print(header)
        print('-' * len(header))
        doc = module.__doc__ or '(no documentation available)'
        print(_wrap(doc))
        print()
        print('SYNOPSIS:')
        help_text = _capture_help(module)
        if help_text:
            print(help_text.rstrip())
        else:
            print('(no help output)')
        print()

    return rc
