"""Simple `cat` implementation.

Usage examples:
  cat file.txt
  cat file1 file2
  cat   # reads from stdin

This module exposes `execute(args: list[str]) -> int`.
"""

from __future__ import annotations

import sys
import argparse
from typing import List


def _cat_file(path: str) -> int:
    try:
        with open(path, 'rb') as f:
            # read and write in binary to faithfully pass bytes to stdout
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                sys.stdout.buffer.write(chunk)
        return 0
    except FileNotFoundError:
        print(f"cat: {path}: No such file or directory", file=sys.stderr)
        return 1
    except IsADirectoryError:
        print(f"cat: {path}: Is a directory", file=sys.stderr)
        return 1
    except PermissionError:
        print(f"cat: {path}: Permission denied", file=sys.stderr)
        return 1


def execute(args: List[str]) -> int:
    parser = argparse.ArgumentParser(prog='cat', add_help=False)
    parser.add_argument('-n', '--number', action='store_true', help='number all output lines')
    parser.add_argument('paths', nargs='*', help='files to read')
    parser.add_argument('-h', '--help', action='store_true', dest='show_help')

    ns = parser.parse_args(args)
    if ns.show_help:
        parser.print_help()
        return 0

    # if no files given, read from stdin
    if not ns.paths:
        data = sys.stdin.buffer.read()
        sys.stdout.buffer.write(data)
        return 0

    exit_code = 0
    line_no = 1
    for p in ns.paths:
        # plain cat behavior: dump files sequentially
        try:
            with open(p, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    if ns.number:
                        sys.stdout.write(f"{line_no:6d}	{line}")
                        line_no += 1
                    else:
                        sys.stdout.write(line)
        except Exception as e:
            print(f"cat: {p}: {e}", file=sys.stderr)
            exit_code = 1

    return exit_code
