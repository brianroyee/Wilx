"""Minimal cp command supporting -r for directories.

Usage: cp [-r] SOURCE... DEST
"""

from __future__ import annotations

import shutil
import argparse
import sys
import os
from typing import List


def execute(args: List[str]) -> int:
    parser = argparse.ArgumentParser(prog='cp', add_help=False)
    parser.add_argument('-r', '--recursive', action='store_true', help='copy directories recursively')
    parser.add_argument('--dry-run', action='store_true', help="show what would be done, but don't actually copy files")
    parser.add_argument('paths', nargs='+')
    parser.add_argument('-h', '--help', action='store_true', dest='show_help')

    ns = parser.parse_args(args)
    if ns.show_help:
        parser.print_help()
        return 0

    paths = ns.paths
    if len(paths) < 2:
        print('cp: missing file operand', file=sys.stderr)
        return 2

    *sources, dest = paths

    try:
        if len(sources) > 1:
            if not os.path.isdir(dest):
                print(f"cp: target '{dest}' is not a directory", file=sys.stderr)
                return 1
            for s in sources:
                if os.path.isdir(s):
                    if ns.recursive:
                        action = f"copytree '{s}' -> '{os.path.join(dest, os.path.basename(s))}'"
                        if ns.dry_run:
                            print(action)
                        else:
                            shutil.copytree(s, os.path.join(dest, os.path.basename(s)))
                    else:
                        print(f"cp: -r not specified; omitting directory '{s}'", file=sys.stderr)
                else:
                    action = f"copy '{s}' -> '{dest}'"
                    if ns.dry_run:
                        print(action)
                    else:
                        shutil.copy2(s, dest)
        else:
            s = sources[0]
            if os.path.isdir(s):
                if ns.recursive:
                    action = f"copytree '{s}' -> '{dest}'"
                    if ns.dry_run:
                        print(action)
                    else:
                        shutil.copytree(s, dest)
                else:
                    print(f"cp: -r not specified; omitting directory '{s}'", file=sys.stderr)
                    return 1
            else:
                # dest may be a dir
                if os.path.isdir(dest):
                    action = f"copy '{s}' -> '{os.path.join(dest, os.path.basename(s))}'"
                    if ns.dry_run:
                        print(action)
                    else:
                        shutil.copy2(s, os.path.join(dest, os.path.basename(s)))
                else:
                    action = f"copy '{s}' -> '{dest}'"
                    if ns.dry_run:
                        print(action)
                    else:
                        shutil.copy2(s, dest)
    except Exception as e:
        print(f"cp: {e}", file=sys.stderr)
        return 1

    return 0
