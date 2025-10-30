"""Minimal mkdir implementation supporting -p.

Usage: mkdir [-p] PATH...
"""

from __future__ import annotations

import os
import argparse
import sys
from typing import List


def execute(args: List[str]) -> int:
    parser = argparse.ArgumentParser(prog='mkdir', add_help=False)
    parser.add_argument('-p', '--parents', action='store_true', help='make parent directories as needed')
    parser.add_argument('paths', nargs='+')
    parser.add_argument('-h', '--help', action='store_true', dest='show_help')

    ns = parser.parse_args(args)
    if ns.show_help:
        parser.print_help()
        return 0

    rc = 0
    for p in ns.paths:
        try:
            if ns.parents:
                os.makedirs(p, exist_ok=True)
            else:
                os.mkdir(p)
        except FileExistsError:
            print(f"mkdir: cannot create directory '{p}': File exists", file=sys.stderr)
            rc = 1
        except PermissionError:
            print(f"mkdir: cannot create directory '{p}': Permission denied", file=sys.stderr)
            rc = 1
        except Exception as e:
            print(f"mkdir: {e}", file=sys.stderr)
            rc = 1

    return rc
