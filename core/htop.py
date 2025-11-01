"""Formatted lightweight `htop`-like viewer for Wilx.

This version keeps startup fast (no heavy imports) while presenting the
process snapshot in a boxed, aligned layout for readability. It uses
platform-native commands (tasklist/WMIC on Windows, ps/free on Unix) and
optionally queries `nvidia-smi` for GPU details if available.

Usage:
  htop            # snapshot
  htop --watch 2  # refresh every 2 seconds
  htop -n 12      # show top 12 processes
"""

from __future__ import annotations

import os
import sys
import shutil
import argparse
import subprocess
import time
from typing import List, Tuple, Optional
import csv
import ctypes
from ctypes import wintypes


def _bar(value: float, width: int = 30) -> str:
    v = max(0.0, min(100.0, float(value)))
    filled = int(round((v / 100.0) * width))
    return '[' + ('#' * filled).ljust(width) + f'] {v:5.1f}%'


def _box(title: str, lines: List[str]) -> None:
    width = shutil.get_terminal_size((80, 20)).columns
    inner_width = max((len(l) for l in lines), default=len(title))
    inner_width = min(inner_width, width - 4)
    border = '+' + '-' * (inner_width + 2) + '+'
    print(border)
    title_line = f'| {title.ljust(inner_width)} |'
    print(title_line)
    print('+' + '=' * (inner_width + 2) + '+')
    for l in lines:
        print(f'| {l.ljust(inner_width)} |')
    print(border)


def _get_gpu_info() -> Optional[List[Tuple[str, int, int]]]:
    try:
        out = subprocess.check_output([
            'nvidia-smi',
            '--query-gpu=index,utilization.gpu,memory.used',
            '--format=csv,noheader,nounits'
        ], stderr=subprocess.DEVNULL)
        text = out.decode(errors='ignore').strip()
        if not text:
            return None
        rows = []
        for line in text.splitlines():
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 3:
                gid = parts[0]
                util = int(parts[1]) if parts[1].isdigit() else 0
                mem = int(parts[2]) if parts[2].isdigit() else 0
                rows.append((gid, util, mem))
        return rows
    except Exception:
        return None


def _parse_tasklist_csv(text: str) -> List[Tuple[str, int, int, str, int]]:
    """Parse tasklist CSV output and return tuples:
    (image_name, pid, mem_mb, session_name, session_num)
    """
    rows = []
    reader = csv.reader(text.splitlines())
    for r in reader:
        # Expected columns: Image Name, PID, Session Name, Session#, Mem Usage
        if len(r) < 5:
            continue
        name = r[0].strip('"')
        try:
            pid = int(r[1])
        except Exception:
            pid = 0
        session_name = r[2].strip('"') if len(r) > 2 else ''
        try:
            session_num = int(r[3].strip('"')) if len(r) > 3 and r[3].strip('"').isdigit() else -1
        except Exception:
            session_num = -1
        mem_str = r[4].strip().replace('"', '')
        mem_num = ''.join(ch for ch in mem_str if ch.isdigit())
        try:
            mem_k = int(mem_num)
            mem_mb = mem_k // 1024
        except Exception:
            mem_mb = 0
        rows.append((name, pid, mem_mb, session_name, session_num))
    return rows


def _snapshot_windows(top: int = 8) -> None:
    # CPU load
    cpu_line = '(cpu load not available)'
    try:
        out = subprocess.check_output(['wmic', 'cpu', 'get', 'loadpercentage', '/Value'], stderr=subprocess.DEVNULL)
        txt = out.decode(errors='ignore')
        for ln in txt.splitlines():
            if '=' in ln:
                k, v = ln.split('=', 1)
                if k.strip().lower() == 'loadpercentage':
                    cpu_line = f'CPU Load: {v.strip()}%'
                    break
    except Exception:
        pass

    # Memory - calculate total_mb once for reuse
    mem_line = '(memory info not available)'
    total_mb = None
    try:
        out = subprocess.check_output(['wmic', 'OS', 'get', 'FreePhysicalMemory,TotalVisibleMemorySize', '/Value'], stderr=subprocess.DEVNULL)
        txt = out.decode(errors='ignore')
        total = free = None
        for ln in txt.splitlines():
            if '=' in ln:
                k, v = ln.split('=', 1)
                if k.strip().lower() == 'totalvisiblememorysize':
                    total = int(v.strip())
                if k.strip().lower() == 'freephysicalmemory':
                    free = int(v.strip())
        if total is not None and free is not None:
            used_k = total - free
            used_mb = used_k // 1024
            total_mb = total // 1024  # Store for reuse in process percentage calculation
            percent = round((used_k / total) * 100, 1) if total else 0
            mem_line = f'Memory: {used_mb}MB / {total_mb}MB ({percent}%)'
    except Exception:
        pass

    # Processes via tasklist CSV -> produce simple table: PID | NAME | TYPE | MEM(MB) | MEM%
    rows = []
    try:
        out = subprocess.check_output(['tasklist', '/FO', 'CSV', '/NH'], stderr=subprocess.DEVNULL)
        txt = out.decode(errors='ignore')
        procs = _parse_tasklist_csv(txt)
        # procs: (name, pid, mem_mb, session_name, session_num)
        procs.sort(key=lambda x: x[2], reverse=True)
        iterable = procs if top is None else procs[:top]
        for name, pid, mem, session_name, session_num in iterable:
            ptype = 'service' if (session_name.lower() == 'services' or session_num == 0) else 'user'
            rows.append((pid, name, ptype, mem))
    except Exception:
        rows = []

    if not rows:
        print('No process information available')
        return

    # total_mb was already calculated above during memory display, reuse it

    pid_w = max(3, max(len(str(r[0])) for r in rows))
    name_w = max(4, min(40, max(len(r[1]) for r in rows)))
    type_w = max(4, max(len(r[2]) for r in rows))
    mem_w = max(7, max(len(str(r[3])) for r in rows) + 3)
    mempct_w = 6

    hdr = f"{'PID'.rjust(pid_w)}  {'NAME'.ljust(name_w)}  {'TYPE'.ljust(type_w)}  {'MEM(MB)'.rjust(mem_w)}  {'MEM%'.rjust(mempct_w)}"
    print(hdr)
    print('-' * len(hdr))
    for pid, name, ptype, mem in rows:
        mempct = round((mem / total_mb) * 100, 1) if total_mb else 0.0
        print(f"{str(pid).rjust(pid_w)}  {name[:name_w].ljust(name_w)}  {ptype.ljust(type_w)}  {str(mem).rjust(mem_w)}  {str(mempct).rjust(mempct_w)}")


def _snapshot_unix(top: int = 8) -> None:
    # Use RSS (KB) from ps to compute memory in MB and print simple table
    rows = []
    try:
        out = subprocess.check_output(['ps', '-eo', 'pid,ppid,rss,comm', '--sort=-rss'], stderr=subprocess.DEVNULL)
        txt = out.decode(errors='ignore')
        lines = txt.splitlines()[1:top+1]
        for ln in lines:
            parts = ln.split(None, 3)
            if len(parts) >= 4:
                pid_s, ppid_s, rss_s, cmd = parts
                try:
                    pid = int(pid_s)
                except Exception:
                    pid = 0
                try:
                    ppid = int(ppid_s)
                except Exception:
                    ppid = -1
                try:
                    rss_k = int(rss_s)
                    mem_mb = rss_k // 1024
                except Exception:
                    mem_mb = 0
                ptype = 'service' if ppid == 1 else 'user'
                rows.append((pid, cmd, ptype, mem_mb))
    except Exception:
        rows = []
    if not rows:
        print('No process information available')
        return

    # get total memory from free -m for percentage calculations
    total_mb = None
    try:
        out = subprocess.check_output(['free', '-m'], stderr=subprocess.DEVNULL).decode(errors='ignore')
        for ln in out.splitlines():
            if ln.lower().startswith('mem:'):
                parts = ln.split()
                total_mb = int(parts[1])
                break
    except Exception:
        total_mb = None

    pid_w = max(3, max(len(str(r[0])) for r in rows))
    name_w = max(4, min(40, max(len(r[1]) for r in rows)))
    type_w = max(4, max(len(r[2]) for r in rows))
    mem_w = max(7, max(len(str(r[3])) for r in rows) + 3)
    mempct_w = 6

    hdr = f"{'PID'.rjust(pid_w)}  {'NAME'.ljust(name_w)}  {'TYPE'.ljust(type_w)}  {'MEM(MB)'.rjust(mem_w)}  {'MEM%'.rjust(mempct_w)}"
    print(hdr)
    print('-' * len(hdr))
    for pid, name, ptype, mem in rows:
        mempct = round((mem / total_mb) * 100, 1) if total_mb else 0.0
        print(f"{str(pid).rjust(pid_w)}  {name[:name_w].ljust(name_w)}  {ptype.ljust(type_w)}  {str(mem).rjust(mem_w)}  {str(mempct).rjust(mempct_w)}")


def execute(args: List[str]) -> int:
    parser = argparse.ArgumentParser(prog='htop', add_help=False)
    parser.add_argument('--watch', '-w', type=float, nargs='?', const=1.0, help='continuously refresh every N seconds (default 1s)')
    parser.add_argument('--top', '-n', type=int, default=8, help='number of top processes to show')
    parser.add_argument('--all', action='store_true', help='show all processes')
    parser.add_argument('-h', '--help', action='store_true', dest='show_help')

    ns = parser.parse_args(args)
    if ns.show_help:
        parser.print_help()
        return 0

    is_win = os.name == 'nt'

    try:
        if ns.watch:
            interval = float(ns.watch)
            while True:
                os.system('cls' if is_win else 'clear')
                if is_win:
                    _snapshot_windows(top=ns.top)
                else:
                    _snapshot_unix(top=ns.top)
                time.sleep(interval)
        else:
            if is_win:
                _snapshot_windows(top=ns.top)
            else:
                _snapshot_unix(top=ns.top)

        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"htop: error: {e}", file=sys.stderr)
        return 1
