"""Kill processes by PID (Linux-like `kill`).

Usage examples:
  kill 1234          # send TERM (or taskkill) to pid 1234
  kill -9 1234       # send SIGKILL (force)
  kill -s KILL 1234  # named signal

On Windows this uses `taskkill` under the hood (uses /F for -9).
"""
from __future__ import annotations

import os
import sys
import argparse
import signal
import subprocess
from typing import List
import csv
import time
import json
# ctypes is only required on Windows when using WinAPI helpers; import lazily in those functions
from pathlib import Path

# processes we will protect by default from accidental kills unless --force is used
PROTECTED_NAMES = {
    'explorer.exe', 'winlogon.exe', 'lsass.exe', 'csrss.exe', 'dwm.exe',
    'svchost.exe', 'services.exe', 'System', 'System Idle Process', 'sihost.exe'
}


# Kill log location: allow override for portability. Priority:
# 1) WILX_KILL_LOG env var
# 2) project-local .wilx_kill_log (repo root)
# 3) fallback to home dir
_ENV_LOG = os.environ.get('WILX_KILL_LOG')
if _ENV_LOG:
    _KILL_LOG = Path(_ENV_LOG).expanduser()
else:
    try:
        _KILL_LOG = (Path(__file__).resolve().parents[1] / '.wilx_kill_log').expanduser()
    except Exception:
        _KILL_LOG = Path(os.path.expanduser('~')) / '.wilx_kill_log'


def _signal_to_int(sig: str) -> int:
    # Accept numeric or names like KILL or SIGKILL
    try:
        return int(sig)
    except Exception:
        s = sig.upper()
        if s.startswith('SIG'):
            s = s[3:]
        # map a few common signals
        mapping = {
            'KILL': signal.SIGKILL if hasattr(signal, 'SIGKILL') else 9,
            'TERM': signal.SIGTERM if hasattr(signal, 'SIGTERM') else 15,
            'INT': signal.SIGINT if hasattr(signal, 'SIGINT') else 2,
        }
        return mapping.get(s, signal.SIGTERM if hasattr(signal, 'SIGTERM') else 15)


def _get_proc_name(pid: int) -> str:
    """Return a best-effort process name for a PID (Windows via tasklist, Unix via ps)."""
    try:
        if os.name == 'nt':
            out = subprocess.check_output(['tasklist', '/FO', 'CSV', '/NH', '/FI', f'PID eq {pid}'], stderr=subprocess.DEVNULL)
            txt = out.decode(errors='ignore').strip()
            if not txt:
                return ''
            parts = list(csv.reader(txt.splitlines()))
            if parts and len(parts[0]) >= 1:
                return parts[0][0].strip('"')
            return ''
        else:
            out = subprocess.check_output(['ps', '-p', str(pid), '-o', 'comm='], stderr=subprocess.DEVNULL)
            return out.decode(errors='ignore').strip()
    except Exception:
        return ''


def _win_graceful_close(pid: int) -> bool:
    """Attempt to post WM_CLOSE to top-level windows belonging to the pid. Returns True if at least one message posted."""
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32

        # workaround for modifying outer scope in older Pythons: use a mutable array
        nonlocal_posted = (wintypes.DWORD * 1)(0)

        # callback for EnumWindows
        def enum_cb(hwnd, lParam):
            pid_arr = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_arr))
            if pid_arr.value == pid and user32.IsWindowVisible(hwnd):
                user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
                nonlocal_posted[0] = 1
            return True

        ENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        enum_proc = ENUMPROC(enum_cb)
        user32.EnumWindows(enum_proc, 0)
        return bool(nonlocal_posted[0])
    except Exception:
        return False


def _win_terminate(pid: int) -> bool:
    """Attempt to terminate process via TerminateProcess. Returns True on success."""
    try:
        import ctypes
        from ctypes import wintypes
        PROCESS_TERMINATE = 0x0001
        kernel32 = ctypes.windll.kernel32
        h = kernel32.OpenProcess(PROCESS_TERMINATE, False, int(pid))
        if not h:
            return False
        res = kernel32.TerminateProcess(h, 1)
        kernel32.CloseHandle(h)
        return bool(res)
    except Exception:
        return False


def _log_kill(entry: dict) -> None:
    try:
        # ensure parent exists when using project-local paths
        try:
            _KILL_LOG.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        with open(str(_KILL_LOG), 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
    except Exception:
        pass


def execute(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(prog='kill')
    parser.add_argument('-9', dest='sig9', action='store_true', help='force (SIGKILL)')
    parser.add_argument('-f', '--force', dest='force', action='store_true', help='force (alias for -9)')
    parser.add_argument('-s', '--signal', dest='signal', help='signal number or name', default=None)
    parser.add_argument('--dry-run', dest='dry_run', action='store_true', help='show what would be done without performing it')
    parser.add_argument('-y', '--yes', dest='yes', action='store_true', help='assume yes to confirmation prompts')
    parser.add_argument('pids', nargs='+', help='PID(s) to kill')
    ns = parser.parse_args(argv)

    is_win = os.name == 'nt'
    # determine signal
    if ns.sig9 or ns.force:
        sig = 'KILL'
    else:
        sig = ns.signal or 'TERM'

    try:
        signum = _signal_to_int(sig)
    except Exception:
        signum = _signal_to_int('TERM')

    ok = True
    for p in ns.pids:
        try:
            pid = int(p)
        except Exception:
            print(f'kill: invalid pid: {p}', file=sys.stderr)
            ok = False
            continue

        pname = _get_proc_name(pid)
        protected = pname.lower() in (n.lower() for n in PROTECTED_NAMES)

        if protected and not ns.force:
            print(f'kill: refusing to kill protected process {pname} ({pid}) without --force', file=sys.stderr)
            ok = False
            continue

        if protected and ns.force and not ns.yes:
            try:
                resp = input(f'Kill protected process {pname} ({pid})? [y/N]: ')
            except Exception:
                resp = 'n'
            if resp.strip().lower() not in ('y', 'yes'):
                print(f'kill: skipping {pname} ({pid})')
                ok = False
                continue

        if ns.dry_run:
            print(f'Would kill {pname or "<unknown>"} ({pid}) signal={sig}')
            continue

        try:
            if is_win:
                # Try a graceful close first (post WM_CLOSE) unless force was requested.
                did = False
                if not ns.force:
                    try:
                        did = _win_graceful_close(pid)
                    except Exception:
                        did = False
                # If force requested, or graceful failed, attempt TerminateProcess
                if ns.force and not did:
                    terminated = _win_terminate(pid)
                    did = bool(terminated)
                # fallback to taskkill if WinAPI didn't work
                if not did:
                    cmd = ['taskkill', '/PID', str(pid)]
                    if signum == (_signal_to_int('KILL') if hasattr(signal, 'SIGKILL') else 9):
                        cmd.append('/F')
                    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                os.kill(pid, signum)

            # log successful kill
            entry = {'time': int(time.time()), 'pid': pid, 'name': pname, 'signal': sig, 'force': bool(ns.force)}
            _log_kill(entry)
        except Exception as e:
            print(f'kill: failed to kill {pid}: {e}', file=sys.stderr)
            ok = False

    return 0 if ok else 1


def main() -> None:
    """Console entrypoint for use with python -m or PyInstaller builds.

    This bridges sys.argv to the `execute` function which expects a list of
    argument strings (similar to argparse usage in our other modules).
    """
    try:
        sys.exit(execute(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception as e:
        print(f'kill: unexpected error: {e}', file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
