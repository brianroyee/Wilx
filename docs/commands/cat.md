# cat

## Description

Simple `cat` implementation.

Usage examples:
  cat file.txt
  cat file1 file2
  cat   # reads from stdin

This module exposes `execute(args: list[str]) -> int`.

## Help

```
usage: cat [-n] [-h] [paths ...]

positional arguments:
  paths         files to read

options:
  -n, --number  number all output lines
  -h, --help
```
