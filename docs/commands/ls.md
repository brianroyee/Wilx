# ls

## Description

`ls` command for Wilx (MVP).

This module exposes a single function `execute(args: list[str])` which
parses arguments and prints directory listings. It implements a small
subset of GNU `ls` flags:

- `ls` : list non-hidden files in current directory
- `ls -a` : include entries starting with '.'
- `ls -l` : long format with permissions, links, size and mtime

Only standard library modules are used.

## Help

```
usage: ls [-a] [-l] [-h] [paths ...]

positional arguments:
  paths       paths to list

options:
  -a, --all   do not ignore entries starting with .
  -l, --long  use a long listing format
  -h, --help  show this help message
```
