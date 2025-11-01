"""Helper utilities for Wilx.

This module contains tiny convenience helpers. Keep this file minimal and
portable so command modules can use it without pulling heavy deps.
"""

from __future__ import annotations

import os
from typing import List


def is_hidden(name: str) -> bool:
    """Return True if the file name should be considered hidden.

    On Unix this is a name starting with '.'; on Windows this function
    currently uses the same rule (portable and simple). This helper is
    intentionally minimal; developers may add platform-specific checks
    later if needed.
    """
    return os.path.basename(name).startswith('.')


def list_core_commands() -> List[str]:
    """Return a sorted list of available command module names in `core/`.

    This scans the `core` package directory for .py files (ignoring
    __init__.py and private files starting with underscore).
    """
    # Get the core directory relative to this file
    utils_dir = os.path.dirname(__file__)
    core_dir = os.path.join(os.path.dirname(utils_dir), 'core')
    cmds = []
    try:
        for fname in os.listdir(core_dir):
            if not fname.endswith('.py'):
                continue
            if fname == '__init__.py' or fname.startswith('_'):
                continue
            cmds.append(os.path.splitext(fname)[0])
    except Exception:
        # If the package isn't present or readable, return empty list.
        return []
    return sorted(cmds)
