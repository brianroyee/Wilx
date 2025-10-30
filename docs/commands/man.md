# man

## Description

Simple man-like viewer for Wilx command modules.

Usage:
  man <command>
  man        # lists available commands

Behavior:
- If a command name is given, `man` will display the module docstring
  (wrapped to terminal width) and then the command's help output (by
  invoking the module with ['--help'] and capturing its printed help).
- Falls back to a short message if the module cannot be loaded.

This keeps output plain-text and avoids external dependencies.

## Help

```
No manual entry for --help
```
