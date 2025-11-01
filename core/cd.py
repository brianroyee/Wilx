"""Change directory (cd).

Usage: cd [PATH]
If PATH is omitted, change to the user's home directory.
"""

from __future__ import annotations

import os
import sys
from typing import List


def execute(args: List[str]) -> int:
    # Simplified argument parsing for simple command
    if args and args[0] in ('-h', '--help'):
        print('Usage: cd [PATH]')
        print('Change the current directory to PATH (defaults to home directory).')
        return 0

    target = args[0] if args else os.path.expanduser('~')
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
