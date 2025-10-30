# kill

## Description

Kill processes by PID (Linux-like `kill`).

Usage examples:
  kill 1234          # send TERM (or taskkill) to pid 1234
  kill -9 1234       # send SIGKILL (force)
  kill -s KILL 1234  # named signal

On Windows this uses `taskkill` under the hood (uses /F for -9).

## Help

```
usage: kill [-h] [-9] [-f] [-s SIGNAL] [--dry-run] [-y] pids [pids ...]

positional arguments:
  pids                 PID(s) to kill

options:
  -h, --help           show this help message and exit
  -9                   force (SIGKILL)
  -f, --force          force (alias for -9)
  -s, --signal SIGNAL  signal number or name
  --dry-run            show what would be done without performing it
  -y, --yes            assume yes to confirmation prompts
```
