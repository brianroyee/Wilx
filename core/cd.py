"""Change directory (cd).

Usage: cd [PATH]
If PATH is omitted, change to the user's home directory.
"""

from __future__ import annotations

import os
import argparse
import sys
from typing import List


def execute(args: List[str]) -> int:
    parser = argparse.ArgumentParser(prog='cd', add_help=False)
    parser.add_argument('path', nargs='?', default=None)
    parser.add_argument('-h', '--help', action='store_true', dest='show_help')

    ns = parser.parse_args(args)
    if ns.show_help:
        parser.print_help()
        return 0

    target = ns.path or os.path.expanduser('~')
    try:
        os.chdir(target)
    except FileNotFoundError:
        print(f"cd: {target}: No such file or directory", file=sys.stderr)
        return 1
    except NotADirectoryError:
        print(f"cd: {target}: Not a directory", file=sys.stderr)
        return 1
    except PermissionError:
        print(f"cd: {target}: Permission denied", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"cd: {e}", file=sys.stderr)
        return 1

    return 0
