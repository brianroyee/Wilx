"""`edit` alias that opens files with the nano editor."""
from __future__ import annotations

import sys
from typing import List


def execute(argv: List[str]) -> int:
    # Delegate to core.nano
    try:
        from . import nano
    except Exception:
        import nano
    return nano.execute(argv)


if __name__ == '__main__':
    sys.exit(execute(sys.argv[1:]))
