# htop

## Description

Formatted lightweight `htop`-like viewer for Wilx.

This version keeps startup fast (no heavy imports) while presenting the
process snapshot in a boxed, aligned layout for readability. It uses
platform-native commands (tasklist/WMIC on Windows, ps/free on Unix) and
optionally queries `nvidia-smi` for GPU details if available.

Usage:
  htop            # snapshot
  htop --watch 2  # refresh every 2 seconds
  htop -n 12      # show top 12 processes

## Help

```
usage: htop [--watch [WATCH]] [--top TOP] [--all] [-h]

options:
  --watch, -w [WATCH]  continuously refresh every N seconds (default 1s)
  --top, -n TOP        number of top processes to show
  --all                show all processes
  -h, --help
```
