"""Simple touch implementation: create file if missing or update mtime.
"""

from __future__ import annotations

import os
import time
import argparse
import sys
from typing import List


def execute(args: List[str]) -> int:
    parser = argparse.ArgumentParser(prog='touch', add_help=False)
    parser.add_argument('paths', nargs='+')
    parser.add_argument('-h', '--help', action='store_true', dest='show_help')

    ns = parser.parse_args(args)
    if ns.show_help:
        parser.print_help()
        return 0

    rc = 0
    for p in ns.paths:
        try:
            now = time.time()
            if not os.path.exists(p):
                open(p, 'a').close()
            os.utime(p, (now, now))
        except Exception as e:
            print(f"touch: cannot touch '{p}': {e}", file=sys.stderr)
            rc = 1

    return rc
