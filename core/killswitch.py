"""Attempt basic recovery actions after accidental kills.

This provides tiny helpers such as restarting `explorer.exe` on Windows if it
was recorded in the kill log. Recovery is best-effort and cannot fully undo
arbitrary state changes caused by killing system processes.

Usage:
  killswitch --list        # show recent kills recorded
  killswitch --restart-explorer  # try to restart explorer.exe (Windows only)
  killswitch --auto --yes  # attempt automated recoveries without confirmation
"""
from __future__ import annotations

import os
import sys
import json
import time
import argparse
import subprocess
from typing import List
from pathlib import Path


_ENV_LOG = os.environ.get('WILX_KILL_LOG')
if _ENV_LOG:
    LOG_PATH = Path(_ENV_LOG).expanduser()
else:
    try:
        LOG_PATH = (Path(__file__).resolve().parents[1] / '.wilx_kill_log').expanduser()
    except Exception:
        LOG_PATH = Path(os.path.expanduser('~')) / '.wilx_kill_log'


def _read_log() -> List[dict]:
    p = Path(str(LOG_PATH))
    if not p.exists():
        return []
    out = []
    try:
        with p.open('r', encoding='utf-8') as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    out.append(json.loads(ln))
                except Exception:
                    continue
    except Exception:
        return []
    return out


def execute(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(prog='killswitch')
    parser.add_argument('--list', action='store_true', help='list recent kills recorded')
    parser.add_argument('--restart-explorer', action='store_true', help='attempt to restart explorer.exe on Windows')
    parser.add_argument('--auto', action='store_true', help='attempt actions without prompting')
    parser.add_argument('--yes', '-y', action='store_true', help='assume yes for confirmations')
    ns = parser.parse_args(argv)

    logs = _read_log()
    if ns.list:
        if not logs:
            print('No kills recorded in log.')
            return 0
        for e in logs[-50:]:
            t = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(e.get('time', 0)))
            print(f"{t} PID={e.get('pid')} NAME={e.get('name')} SIGNAL={e.get('signal')} FORCE={e.get('force')}")
        return 0

    if ns.restart_explorer:
        if os.name != 'nt':
            print('restart-explorer is only supported on Windows', file=sys.stderr)
            return 1
        # check log for explorer kills
        found = False
        for e in reversed(logs):
            if (e.get('name') or '').lower() == 'explorer.exe':
                found = True
                break
        if not found:
            print('No recent explorer.exe kill found in log.')
            return 0
        if not ns.auto and not ns.yes:
            try:
                resp = input('Attempt to restart explorer.exe now? [y/N]: ')
            except Exception:
                resp = 'n'
            if resp.strip().lower() not in ('y', 'yes'):
                print('Aborting restart.')
                return 1
        try:
            # start explorer, prefer subprocess.Popen so it detaches
            subprocess.Popen(['explorer'])
            print('Started explorer.exe (may take a moment to restore shell).')
            return 0
        except Exception as ex:
            print(f'Failed to start explorer.exe: {ex}', file=sys.stderr)
            return 1

    parser.print_help()
    return 0
