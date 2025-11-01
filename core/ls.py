"""`ls` command for Wilx (MVP).

This module exposes a single function `execute(args: list[str])` which
parses arguments and prints directory listings. It implements a small
subset of GNU `ls` flags:

- `ls` : list non-hidden files in current directory
- `ls -a` : include entries starting with '.'
- `ls -l` : long format with permissions, links, size and mtime

Only standard library modules are used.
"""

from __future__ import annotations

import os
import sys
import argparse
import datetime
import stat
import shutil
import math
import textwrap
from typing import List


def format_mode(mode: int) -> str:
    """Return a human readable file mode similar to ls -l (e.g. '-rwxr-xr-x').

    This is a simplified representation using stat flags.
    """
    is_dir = 'd' if stat.S_ISDIR(mode) else '-'
    perms = []
    flags = (
        (stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR),
        (stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP),
        (stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH),
    )
    for triplet in flags:
        perms.append('r' if mode & triplet[0] else '-')
        perms.append('w' if mode & triplet[1] else '-')
        perms.append('x' if mode & triplet[2] else '-')

    return is_dir + ''.join(perms)


def format_mtime(ts: float) -> str:
    dt = datetime.datetime.fromtimestamp(ts)
    return dt.strftime('%Y-%m-%d %H:%M')


def _get_owner_group(st):
    """Try to return owner and group names; return ('', '') when unavailable."""
    try:
        import pwd, grp  # type: ignore

        owner = pwd.getpwuid(st.st_uid).pw_name
        group = grp.getgrgid(st.st_gid).gr_name
        return owner, group
    except Exception:
        return '', ''


def _print_columns(entries: List[str], term_width: int = None) -> None:
    """Print entries in neat columns that fit the terminal width.

    Algorithm: choose the number of columns so that each column width
    (max name length + padding) fits into terminal width. Fill rows
    top-to-bottom like GNU ls.
    
    Args:
        entries: List of entry names to display
        term_width: Terminal width in columns (will be detected if None)
    """
    if not entries:
        return
    if term_width is None:
        term_width = shutil.get_terminal_size((80, 20)).columns
    maxlen = max(len(e) for e in entries)
    col_width = maxlen + 2
    cols = max(1, term_width // col_width)
    rows = math.ceil(len(entries) / cols)

    # build grid
    grid = []
    for r in range(rows):
        row_items = []
        for c in range(cols):
            idx = c * rows + r
            if idx < len(entries):
                row_items.append(entries[idx])
            else:
                row_items.append('')
        grid.append(row_items)

    for row in grid:
        line = ''
        for item in row:
            if item:
                line += item.ljust(col_width)
            else:
                line += ' ' * col_width
        print(line.rstrip())


def execute(args: List[str]) -> int:
    """Execute the ls command.

    Arguments
    - args: list of command-line arguments (e.g. ['-l', '/tmp'])

    Returns
    - integer exit code (0 success, non-zero on errors)
    """
    parser = argparse.ArgumentParser(prog='ls', add_help=False)
    parser.add_argument('-a', '--all', action='store_true', help='do not ignore entries starting with .')
    parser.add_argument('-l', '--long', action='store_true', help='use a long listing format')
    parser.add_argument('-h', '--help', action='store_true', dest='show_help', help='show this help message')
    parser.add_argument('paths', nargs='*', default=['.'], help='paths to list')

    ns = parser.parse_args(args)
    if ns.show_help:
        parser.print_help()
        return 0

    # Cache terminal width once per command execution
    try:
        term_width = shutil.get_terminal_size((80, 20)).columns
    except Exception:
        term_width = 80

    exit_code = 0
    for target in ns.paths:
        # If multiple paths provided, print header like GNU ls does
        if len(ns.paths) > 1:
            print(f"{target}:")

        try:
            if os.path.isdir(target):
                # Use os.scandir() for better performance, filtering during iteration
                base = target
                entries = []
                try:
                    with os.scandir(target) as it:
                        for entry in it:
                            name = entry.name
                            if ns.all or not name.startswith('.'):
                                entries.append(name)
                except Exception:
                    # Fallback to os.listdir if scandir fails
                    entries = os.listdir(target)
                    if not ns.all:
                        entries = [e for e in entries if not e.startswith('.')]
            else:
                # path is a file — show that single entry
                entries = [os.path.basename(target)]
                base = os.path.dirname(target) or '.'
        except FileNotFoundError:
            print(f"ls: cannot access '{target}': No such file or directory", file=sys.stderr)
            exit_code = 2
            continue
        except PermissionError:
            print(f"ls: cannot open directory '{target}': Permission denied", file=sys.stderr)
            exit_code = 2
            continue

        entries.sort()

        if ns.long:
            # gather stats first to compute column widths
            rows = []
            col_nlink = 0
            col_owner = 0
            col_group = 0
            col_size = 0
            for name in entries:
                full = os.path.join(base, name)
                try:
                    st = os.lstat(full)
                except FileNotFoundError:
                    # race / broken symlink — skip
                    continue
                mode = format_mode(st.st_mode)
                nlink = getattr(st, 'st_nlink', 1)
                size = st.st_size
                mtime = format_mtime(st.st_mtime)
                owner, group = _get_owner_group(st)
                col_nlink = max(col_nlink, len(str(nlink)))
                col_owner = max(col_owner, len(owner))
                col_group = max(col_group, len(group))
                col_size = max(col_size, len(str(size)))
                rows.append((mode, nlink, owner, group, size, mtime, name))

            for mode, nlink, owner, group, size, mtime, name in rows:
                # owner/group may be empty strings on Windows; leave spacing compact
                owner_field = owner.ljust(col_owner) if owner else ''
                group_field = group.ljust(col_group) if group else ''
                print(f"{mode} {str(nlink).rjust(col_nlink)} {owner_field} {group_field} {str(size).rjust(col_size)} {mtime} {name}")
        else:
            # pretty column output
            _print_columns(entries, term_width)

        # print a blank line between multiple targets
        if len(ns.paths) > 1:
            print()

    return exit_code
