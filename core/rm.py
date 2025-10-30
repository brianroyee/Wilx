"""Minimal rm command: supports -r and -f.

Usage: rm [-f] [-r] PATH...
"""

from __future__ import annotations

import os
import shutil
import argparse
import sys
from typing import List


def execute(args: List[str]) -> int:
    parser = argparse.ArgumentParser(prog='rm', add_help=False)
    parser.add_argument('-r', '--recursive', action='store_true', help='remove directories and their contents recursively')
    parser.add_argument('-f', '--force', action='store_true', help='ignore nonexistent files and arguments, never prompt')
    parser.add_argument('--dry-run', action='store_true', help="show what would be done, but don't actually remove files")
    parser.add_argument('paths', nargs='+')
    parser.add_argument('-h', '--help', action='store_true', dest='show_help')

    ns = parser.parse_args(args)
    if ns.show_help:
        parser.print_help()
        return 0

    rc = 0
    for p in ns.paths:
        try:
            if os.path.isdir(p) and not os.path.islink(p):
                if ns.recursive:
                    action = f"rmtree '{p}'"
                    if ns.dry_run:
                        print(action)
                    else:
                        shutil.rmtree(p)
                else:
                    action = f"rmdir '{p}'"
                    if ns.dry_run:
                        print(action)
                    else:
                        os.rmdir(p)
            else:
                action = f"remove '{p}'"
                if ns.dry_run:
                    print(action)
                else:
                    os.remove(p)
        except FileNotFoundError:
            if not ns.force:
                print(f"rm: cannot remove '{p}': No such file or directory", file=sys.stderr)
                rc = 1
        except IsADirectoryError:
            print(f"rm: cannot remove '{p}': Is a directory", file=sys.stderr)
            rc = 1
        except PermissionError:
            print(f"rm: cannot remove '{p}': Permission denied", file=sys.stderr)
            rc = 1
        except Exception as e:
            print(f"rm: error removing '{p}': {e}", file=sys.stderr)
            rc = 1

    return rc
