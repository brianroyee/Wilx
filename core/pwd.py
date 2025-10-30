"""Print working directory (pwd).
"""

from __future__ import annotations

import os
from typing import List


def execute(args: List[str]) -> int:
    # ignore args for simplicity
    print(os.getcwd())
    return 0
