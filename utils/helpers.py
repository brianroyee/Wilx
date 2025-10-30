"""Helper utilities for Wilx.

This module contains tiny convenience helpers. Keep this file minimal and
portable so command modules can use it without pulling heavy deps.
"""

from __future__ import annotations

import os


def is_hidden(name: str) -> bool:
    """Return True if the file name should be considered hidden.

    On Unix this is a name starting with '.'; on Windows this function
    currently uses the same rule (portable and simple). This helper is
    intentionally minimal; developers may add platform-specific checks
    later if needed.
    """
    return os.path.basename(name).startswith('.')
