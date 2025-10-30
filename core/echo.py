"""Echo command: print arguments to stdout.

Supports -n to omit trailing newline.
"""

from __future__ import annotations

import argparse
import sys
from typing import List


def execute(args: List[str]) -> int:
    parser = argparse.ArgumentParser(prog='echo', add_help=False)
    parser.add_argument('-n', action='store_true', help='do not print the trailing newline')
    parser.add_argument('text', nargs='*')
    parser.add_argument('-h', '--help', action='store_true', dest='show_help')

    ns = parser.parse_args(args)
    if ns.show_help:
        parser.print_help()
        return 0

    out = ' '.join(ns.text)
    if ns.n:
        sys.stdout.write(out)
    else:
        print(out)
    return 0
