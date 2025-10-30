"""Minimal mv (move/rename) command.

Usage: mv SOURCE... DEST
"""

from __future__ import annotations

import shutil
import argparse
import sys
import os
from typing import List


def execute(args: List[str]) -> int:
    parser = argparse.ArgumentParser(prog='mv', add_help=False)
    parser.add_argument('--dry-run', action='store_true', help="show what would be done, but don't actually move files")
    parser.add_argument('paths', nargs='+')
    parser.add_argument('-h', '--help', action='store_true', dest='show_help')

    ns = parser.parse_args(args)
    if ns.show_help:
        parser.print_help()
        return 0

    paths = ns.paths
    if len(paths) < 2:
        print('mv: missing file operand', file=sys.stderr)
        return 2

    *sources, dest = paths

    try:
        if len(sources) > 1:
            # dest must be a directory
            if not os.path.isdir(dest):
                print(f"mv: target '{dest}' is not a directory", file=sys.stderr)
                return 1
            for s in sources:
                action = f"move '{s}' -> '{dest}'"
                if ns.dry_run:
                    print(action)
                else:
                    shutil.move(s, dest)
        else:
            action = f"move '{sources[0]}' -> '{dest}'"
            if ns.dry_run:
                print(action)
            else:
                shutil.move(sources[0], dest)
    except Exception as e:
        print(f"mv: {e}", file=sys.stderr)
        return 1

    return 0
