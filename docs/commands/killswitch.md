# killswitch

## Description

Attempt basic recovery actions after accidental kills.

This provides tiny helpers such as restarting `explorer.exe` on Windows if it
was recorded in the kill log. Recovery is best-effort and cannot fully undo
arbitrary state changes caused by killing system processes.

Usage:
  killswitch --list        # show recent kills recorded
  killswitch --restart-explorer  # try to restart explorer.exe (Windows only)
  killswitch --auto --yes  # attempt automated recoveries without confirmation

## Help

```
usage: killswitch [-h] [--list] [--restart-explorer] [--auto] [--yes]

options:
  -h, --help          show this help message and exit
  --list              list recent kills recorded
  --restart-explorer  attempt to restart explorer.exe on Windows
  --auto              attempt actions without prompting
  --yes, -y           assume yes for confirmations
```
